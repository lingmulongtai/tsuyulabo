# Shiori QLoRA → Windows Ollama

This trains on fictional tool traces, not player data. Start with **2B** on the RTX 4050
(6 GB). The script accepts 4B for a later experiment, but 4B fitting 6 GB is unverified.
The repository's CPU uv workspace and lockfile never include these training packages.

## Compatibility checked on 2026-10-01

The exact post-trained repositories are [Qwen/Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B)
and [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B). They include a vision tower;
the scripts use `Qwen3_5ForConditionalGeneration`, train only language attention / gated
DeltaNet / MLP projections, and freeze vision and embeddings. Transformers 5.3.0 provides
[this architecture and tensor-valued logits_to_keep](https://github.com/huggingface/transformers/blob/v5.3.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py).
The [TRL 0.29.0 SFT API](https://huggingface.co/docs/trl/v0.29.0/sft_trainer) accepts pretokenized
datasets; our labels supervise assistant text **and tool calls**, masking system, user and
tool-result tokens. Native Qwen delimiters and token offsets avoid changing its chat template.

[PyTorch's CUDA 12.8 wheels](https://pytorch.org/get-started/previous-versions/) match the pinned
torch/torchvision pair. The pinned environment is a documented candidate, not a GPU-certified
combination. Both requirements files resolve for Linux x86_64 / Python 3.12 using
`uv pip compile` (PyPI + official PyTorch index, best-match index strategy). No CUDA
packages were installed here. Resolution and architecture checks do not replace the smoke run.

Ollama's [Modelfile reference](https://docs.ollama.com/modelfile) does not establish Qwen3.5
safetensors LoRA `ADAPTER` compatibility. Accordingly, the supported recipe here is **merge
the unquantized HF base + adapter → GGUF → Q4_K_M → ollama create**. The current
[llama.cpp Qwen converter](https://github.com/ggml-org/llama.cpp/blob/master/conversion/qwen.py)
registers Qwen3.5. Record the converter revision used; support evolves.

## 1. Generate and check data on Windows (PowerShell, repository root)

```powershell
.\.tools\uv.exe run python -m tsuyu_shiori.dataset --out data/shiori-sft
.\.tools\uv.exe run python ml/shiori-lora/train.py --dry-run --data data/shiori-sft --out ml/shiori-lora/artifacts/dry-run
.\.tools\uv.exe run pytest services/shiori services/worker --basetemp .codex-runs/pytest-training
.\.tools\uv.exe run ruff check .
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider mock
```

Defaults: 4,000 train / 400 valid / 159 test. Each JSONL contains only `messages` and `tools`.
Keep each `.meta.jsonl` and `stats.json` beside its split: they hold seed/template provenance,
hashes and length estimates. Test contains the original eval's 61 questions and 98 completely
held-out paraphrases, all on seed 37. Train uses 1000–1040; valid uses 2000–2004. Missing-record
cases mean an absent topic in a nonempty week, so inspected evidence IDs exist. Entirely empty
weeks use the runtime UI empty state and are not fabricated into cited SFT answers.

## 2. Fresh WSL2 Ubuntu 24.04

Install/update the Windows NVIDIA driver with WSL CUDA support. Do not install a Linux NVIDIA
display driver inside WSL. From an elevated Windows PowerShell, if WSL is not already installed:

```powershell
wsl --install -d Ubuntu-24.04
wsl --update
wsl -d Ubuntu-24.04
```

After creating your Ubuntu user, run the following **inside Ubuntu**. Change `REPO` if the
commander copied this branch into another checkout. Use the Linux filesystem for weights
and environments; the small source/data files can remain in the Windows checkout.

```bash
sudo apt-get update
sudo apt-get install -y python3.12-venv python3-dev build-essential cmake git
nvidia-smi
export REPO=/mnt/c/Users/lingm/dev/tsuyulabo-agents/W11-shiori-lora-data
export RUN="$HOME/shiori-gpu"
mkdir -p "$RUN"
python3.12 -m venv "$RUN/venv"
source "$RUN/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$REPO/ml/shiori-lora/requirements.txt"
python -m pip check
python -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available()); assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

## 3. Download, validate, smoke train, then train

The models are public; credentials are not required. Downloading 2B needs several GB of
disk. Leave room for the base, two checkpoints, adapter, merged weights and two GGUFs
(roughly 20 GB for a 2B run). CPU merging benefits from at least 16 GB available system RAM.

```bash
hf download Qwen/Qwen3.5-2B --local-dir "$RUN/base-2b"
python "$REPO/ml/shiori-lora/train.py" --dry-run \
  --base "$RUN/base-2b" --data "$REPO/data/shiori-sft" --out "$RUN/adapter-smoke"
python "$REPO/ml/shiori-lora/train.py" \
  --base "$RUN/base-2b" --data "$REPO/data/shiori-sft" --out "$RUN/adapter-smoke" --max-steps 2
cat "$RUN/adapter-smoke/metrics.json"
python "$REPO/ml/shiori-lora/train.py" \
  --base "$RUN/base-2b" --data "$REPO/data/shiori-sft" --out "$RUN/adapter-v1" --epochs 2 --lr 0.0002
cat "$RUN/adapter-v1/metrics.json"
```

Use a fresh `--out` for every run. `--max-steps` overrides epochs. The default recipe is NF4
double quantization, r=16 / alpha=32 / dropout=0.05, batch 1, accumulation 16, gradient
checkpointing, paged 8-bit AdamW, BF16 when supported and no packing. Sparse vocabulary
projection computes logits only where an assistant target exists. Large frozen dense weights
are staged on CPU during PEFT preparation to avoid temporary FP32 copies on the GPU.

Dry-run checks arguments, chat structure, paired tool-call IDs, hashes and split leakage using
only stdlib, with no model download. Before loading weights, a real run measures all train/valid
tokens with the exact Qwen template, validates assistant masks and refuses truncation if any
row exceeds `stats.json.max_length`. See `data-check.json`; estimates are not tokenizer lengths.
Losses appear in stdout and `loss-log.json`; validation runs every 25 steps and at completion.
`metrics.json` records the final validation loss and peak allocated CUDA bytes. Compare that
peak with `nvidia-smi` because allocator reservation and other processes also occupy memory.

If the smoke run OOMs, close other GPU workloads and keep batch 1. Do not silently truncate
traces or train on CPU. A 6 GB fit and training throughput remain hardware acceptance items.
NF4 Qwen3.5 quality is also uncertain: [Unsloth's own guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune)
advises BF16 LoRA over QLoRA for quantization fidelity. QLoRA here follows this task's VRAM
constraint, and requires held-out evaluation rather than assuming loss means quality.

## 4. Merge and convert in WSL

Build a current converter with two CPU jobs; CUDA compilation is unnecessary for conversion.
Install its dependencies into the isolated training venv using the training pins as constraints.
If the current converter requires incompatible pins, pip must fail; inspect the converter revision
and resolve that incompatibility before export rather than silently replacing training dependencies.

```bash
git clone https://github.com/ggml-org/llama.cpp.git "$RUN/llama.cpp"
git -C "$RUN/llama.cpp" rev-parse HEAD | tee "$RUN/llama-cpp-revision.txt"
cmake -S "$RUN/llama.cpp" -B "$RUN/llama.cpp/build" -DGGML_CUDA=OFF -DLLAMA_CURL=OFF
cmake --build "$RUN/llama.cpp/build" --config Release --target llama-quantize -j 2
python -m pip install -r "$RUN/llama.cpp/requirements.txt" -c "$REPO/ml/shiori-lora/requirements.txt"
python -m pip check
python "$REPO/ml/shiori-lora/export.py" --dry-run \
  --adapter "$RUN/adapter-v1" --out "$RUN/export-v1" --llama-cpp "$RUN/llama.cpp"
```

`export.py` uses the same isolated Python for the merge and converter:

```bash
python "$REPO/ml/shiori-lora/export.py" \
  --adapter "$RUN/adapter-v1" --out "$RUN/export-v1" --llama-cpp "$RUN/llama.cpp"
mkdir -p "$REPO/ml/shiori-lora/artifacts/ollama-v1"
cp "$RUN/export-v1/shiori-Q4_K_M.gguf" "$REPO/ml/shiori-lora/artifacts/ollama-v1/"
cp "$RUN/export-v1/export.json" "$REPO/ml/shiori-lora/artifacts/ollama-v1/"
```

The script loads the original BF16 base on **CPU**, safely merges the adapter and saves HF
safetensors/tokenizer. It runs `convert_hf_to_gguf.py --outtype bf16 --no-mtp`, then
`llama-quantize ... Q4_K_M 2`. No vision projector is exported: Shiori is text-only.
It preserves intermediates for diagnosis and records the actual llama.cpp revision. If the
converter rejects Qwen3.5 or `--no-mtp`, stop and inspect/update the converter; never relabel
the architecture to force import. Direct `FROM qwen3.5:2b-q4_K_M` + `ADAPTER ./adapter` is
not an established path for this architecture and is not the default recipe.

## 5. Import and evaluate on the Windows host

Return to **Windows PowerShell**, repository root. Windows Ollama must already be installed
and running. Its base tag must match the HF **2B post-trained** checkpoint. Keep the snapshot
of its native chat/tool TEMPLATE and parameters; do not hand-write a generic Qwen template.

```powershell
ollama pull qwen3.5:2b-q4_K_M
$baseModelfile = (ollama show qwen3.5:2b-q4_K_M --modelfile) -join "`n"
[System.IO.File]::WriteAllText((Join-Path $PWD 'ml/shiori-lora/artifacts/ollama-v1/base.Modelfile'), $baseModelfile, [System.Text.UTF8Encoding]::new($false))
.\.tools\uv.exe run python ml/shiori-lora/modelfile.py --base-modelfile ml/shiori-lora/artifacts/ollama-v1/base.Modelfile --gguf ml/shiori-lora/artifacts/ollama-v1/shiori-Q4_K_M.gguf --out ml/shiori-lora/artifacts/ollama-v1/Modelfile
ollama create tsuyu-shiori:2b-lora-v1 -f ml/shiori-lora/artifacts/ollama-v1/Modelfile
ollama show tsuyu-shiori:2b-lora-v1 --modelfile
$env:SHIORI_LIVE_EVAL = '1'
$env:OLLAMA_NUM_CTX = '4096'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider ollama --qa-model tsuyu-shiori:2b-lora-v1 --test-file data/shiori-sft/test.jsonl --limit 3
.\.tools\uv.exe run python -m tsuyu_shiori.eval --provider ollama --qa-model tsuyu-shiori:2b-lora-v1 --test-file data/shiori-sft/test.jsonl
Remove-Item Env:SHIORI_LIVE_EVAL
```

The initial limit applies to both existing and extra cases. `report.json` includes the
`heldout` score, per-intent accuracy, native/delivered answers and fallback counts. Existing
61-question gates and CLI exit status remain unchanged. The extra score has its own `passed`
field (accuracy ≥0.8, verification ≥0.95, readability 1.0); inspect it explicitly. Fallbacks
never count as native success. Counts and their expected IDs must share a sentence; copy
experiments require their actual trial/action counts and cautious causal wording.

To use the trained model in the game, set `SHIORI_PROVIDER=ollama` and
`OLLAMA_QA_MODEL=tsuyu-shiori:2b-lora-v1`; keep a separately accepted journal model until
morning-memo validation has been run. This dataset targets question answering.

## Optional Unsloth path

[Unsloth supports Qwen3.5 2B/4B fine-tuning](https://unsloth.ai/docs/models/qwen3.5/fine-tune).
Its optional pinned package is kept in `requirements-unsloth.txt`. That older Unsloth release
requires Transformers 5.2.0, TRL 0.24.0 and datasets 4.3.0, so it has an independently resolved
environment rather than inheriting the stock script's newer pins. Use a **separate** venv:

```bash
python3.12 -m venv "$RUN/unsloth-venv"
"$RUN/unsloth-venv/bin/python" -m pip install -r "$REPO/ml/shiori-lora/requirements-unsloth.txt"
"$RUN/unsloth-venv/bin/python" -m pip check
```

Follow its linked maintained Qwen3.5-2B notebook if the stock path cannot fit or is too slow.
`train.py` deliberately uses the pinned stock Transformers/PEFT path; installing Unsloth alone
does not switch backends. Port the same native tool template and assistant-only labels before
using the notebook. This optional faster route has not been executed on the GPU.

## Verification boundary

Windows offline tests, complete synthetic generation, Mock evaluation and stdlib dry-runs
are the available evidence. No WSL session, GPU training, CPU weight merge, GGUF conversion,
Ollama import or live LLM evaluation was run by this task. Real GPU memory, convergence,
latency and contract accuracy must be checked by the commander using the commands above.
