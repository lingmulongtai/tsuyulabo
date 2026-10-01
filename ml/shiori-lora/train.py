"""Qwen3.5 QLoRA SFT. --dry-run requires only the Python standard library."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from data import encode_assistant, load_data


def assistant_loss(torch: Any, model: Any, inputs: dict[str, Any]) -> tuple[Any, Any]:
    """Project only supervised positions into Qwen's large vocabulary (batch 1)."""
    inputs = dict(inputs)
    labels = inputs.pop("labels")
    if labels.shape[0] != 1:
        raise ValueError("sparse assistant loss requires batch size 1")
    positions = torch.nonzero(labels[0, 1:] != -100, as_tuple=True)[0]
    if not positions.numel():
        raise ValueError("empty assistant target")
    outputs = model(**inputs, logits_to_keep=positions, use_cache=False)
    target = labels[0, positions + 1]
    loss = torch.nn.functional.cross_entropy(outputs.logits[0].float(), target)
    return loss, outputs


def train(args: argparse.Namespace, rows: dict[str, Any], stats: dict[str, Any]) -> None:
    # All heavy dependencies are below the dry-run exit.
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForSeq2Seq,
        Qwen3_5ForConditionalGeneration,
        set_seed,
    )
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; no CPU training fallback")
    if int(os.environ.get("WORLD_SIZE", "1")) != 1:
        raise ValueError("this 6 GB recipe supports one GPU/process")
    torch.set_num_threads(2)
    set_seed(1000)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(args.base, use_fast=True, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    encoded = {
        split: Dataset.from_list(
            [encode_assistant(row, tokenizer, stats["max_length"]) for row in rows[split]]
        )
        for split in ("train", "valid")
    }
    max_actual = max(len(r["input_ids"]) for ds in encoded.values() for r in ds)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "data-check.json").write_text(
        json.dumps({"max_actual_tokens": max_actual, "stats": stats}, indent=2), encoding="utf-8"
    )
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        args.base,
        dtype=dtype,
        device_map={"": 0},
        trust_remote_code=False,
        attn_implementation="sdpa",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
            llm_int8_skip_modules=["visual", "lm_head"],
        ),
    )
    model.config.use_cache = False
    model.config.text_config.use_cache = False
    # PEFT promotes dense tensors to fp32. Stage the large frozen components on
    # CPU during that promotion so its temporary peak does not consume VRAM.
    staged = []
    for name, parameter in model.named_parameters():
        if any(part in name for part in ("embed_tokens", "lm_head", "visual")):
            staged.append((parameter, parameter.device))
            parameter.data = parameter.data.to("cpu")
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    for parameter, device in staged:
        parameter.data = parameter.data.to(device=device, dtype=dtype)
    # Full attention + gated DeltaNet projections + MLP; exclude the vision tower.
    suffixes = {
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
        "in_proj_qkv",
        "in_proj_z",
        "in_proj_b",
        "in_proj_a",
        "out_proj",
    }
    targets = [
        name
        for name, _ in model.named_modules()
        if re.search(r"language_model\.layers\.\d+\.", name) and name.rsplit(".", 1)[-1] in suffixes
    ]
    if not targets or not any("mlp" in name for name in targets):
        raise ValueError("unexpected Qwen3.5 module names; no attention/MLP LoRA targets")
    model = get_peft_model(
        model,
        LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=targets,
        ),
    )
    model.print_trainable_parameters()

    class AssistantTrainer(SFTTrainer):
        def compute_loss(
            self,
            model: Any,
            inputs: dict[str, Any],
            return_outputs: bool = False,
            num_items_in_batch: Any = None,
        ) -> Any:
            loss, outputs = assistant_loss(torch, model, inputs)
            return (loss, outputs) if return_outputs else loss

    config = SFTConfig(
        output_dir=str(args.out / "checkpoints"),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=args.lr,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=16,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=dtype == torch.bfloat16,
        fp16=dtype == torch.float16,
        optim="paged_adamw_8bit",
        warmup_ratio=0.05,
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=25,
        save_steps=25,
        save_total_limit=2,
        report_to="none",
        seed=1000,
        max_length=stats["max_length"],
        packing=False,
        prediction_loss_only=True,
        dataloader_num_workers=0,
        dataset_kwargs={"skip_prepare_dataset": True},
    )
    trainer = AssistantTrainer(
        model=model,
        args=config,
        train_dataset=encoded["train"],
        eval_dataset=encoded["valid"],
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, label_pad_token_id=-100),
    )
    # Loss is a per-example mean; let Trainer divide by accumulation steps.
    trainer.model_accepts_loss_kwargs = False
    trainer.train()
    metrics = trainer.evaluate()
    trainer.save_model(str(args.out))
    tokenizer.save_pretrained(args.out)
    metrics["peak_cuda_memory_bytes"] = torch.cuda.max_memory_allocated()
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (args.out / "loss-log.json").write_text(
        json.dumps(trainer.state.log_history, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="Qwen/Qwen3.5-2B")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.base not in {"Qwen/Qwen3.5-2B", "Qwen/Qwen3.5-4B"} and not Path(args.base).is_dir():
        parser.error("--base must be a supported Qwen repo ID or a downloaded local directory")
    if not math.isfinite(args.epochs) or args.epochs <= 0:
        parser.error("--epochs must be positive and finite")
    if args.max_steps != -1 and args.max_steps < 1:
        parser.error("--max-steps must be -1 or positive")
    if not math.isfinite(args.lr) or not 0 < args.lr < 1:
        parser.error("--lr must be finite and between 0 and 1")
    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        parser.error("--out must be absent or empty; use a new run directory")
    try:
        rows, stats = load_data(args.data)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.error(f"invalid dataset: {exc}")
    print(
        json.dumps(
            {
                "base": args.base,
                "examples": {k: len(v) for k, v in rows.items()},
                "max_length_estimate": stats["max_length"],
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )
    if not args.dry_run:
        train(args, rows, stats)


if __name__ == "__main__":
    main()
