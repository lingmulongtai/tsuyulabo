"""Small hand-written multiclass logistic and MLP decoders using autograd."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import Tensor

from tsuyu_brain.behavior import FEATURES, LABELS
from tsuyu_brain.decoder.dataset import Dataset


@dataclass
class Decoder:
    kind: str
    mean: Tensor
    scale: Tensor
    weights: list[Tensor]

    def logits(self, features: Tensor) -> Tensor:
        values = (features - self.mean) / self.scale
        if self.kind == "mlp":
            values = torch.tanh(values @ self.weights[0] + self.weights[1])
            return values @ self.weights[2] + self.weights[3]
        return values @ self.weights[0] + self.weights[1]

    def predict(self, features: Tensor) -> Tensor:
        with torch.no_grad():
            return self.logits(features).softmax(dim=-1)

    def save(self, path: str | Path) -> None:
        if self.mean.numel() != len(FEATURES):
            raise ValueError(
                "only the promoted toy feature schema can be saved as a game checkpoint"
            )
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "version": "toy-v0",
                "features": FEATURES,
                "labels": LABELS,
                "kind": self.kind,
                "mean": self.mean,
                "scale": self.scale,
                "weights": [value.detach() for value in self.weights],
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> Decoder:
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if (
            payload["version"] != "toy-v0"
            or tuple(payload["features"]) != FEATURES
            or tuple(payload["labels"]) != LABELS
        ):
            raise ValueError("incompatible decoder checkpoint")
        return cls(payload["kind"], payload["mean"], payload["scale"], payload["weights"])


def train_decoder(
    data: Dataset, kind: str = "logistic", seed: int = 11, epochs: int = 400
) -> Decoder:
    """Offline full-batch optimization; restore torch thread settings afterward."""
    if kind not in {"logistic", "mlp"} or epochs < 1:
        raise ValueError("invalid decoder kind or epochs")
    generator = torch.Generator().manual_seed(seed)
    width = data.features.shape[1]
    sizes = [width, len(LABELS)] if kind == "logistic" else [width, 16, len(LABELS)]
    weights: list[Tensor] = []
    for n_in, n_out in zip(sizes[:-1], sizes[1:], strict=True):
        weights.extend(
            [
                (0.1 * torch.randn(n_in, n_out, generator=generator)).requires_grad_(),
                torch.zeros(n_out, requires_grad=True),
            ]
        )
    model = Decoder(kind, data.features.mean(0), data.features.std(0).clamp_min(1), weights)
    # Large host thread pools dominate the tiny optimizer operations.
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        optimizer = torch.optim.Adam(weights, lr=0.04)
        counts = torch.bincount(data.labels, minlength=len(LABELS)).float().clamp_min(1)
        for _ in range(epochs):
            optimizer.zero_grad()
            logits = model.logits(data.features)
            log_probabilities = logits - logits.logsumexp(dim=1, keepdim=True)
            losses = -log_probabilities[torch.arange(len(data.labels)), data.labels]
            loss = (losses / counts[data.labels]).sum() / len(LABELS)
            loss = loss + 0.0001 * sum(value.square().mean() for value in weights)
            loss.backward()
            optimizer.step()
    finally:
        torch.set_num_threads(threads)
    model.weights = [value.detach() for value in weights]
    return model


def evaluate_decoder(model: Decoder, data: Dataset) -> dict[str, float | list[list[int]]]:
    predicted = model.predict(data.features).argmax(1)
    confusion = torch.bincount(
        data.labels * len(LABELS) + predicted, minlength=len(LABELS) ** 2
    ).reshape(len(LABELS), len(LABELS))
    return {
        "accuracy": float((predicted == data.labels).float().mean()),
        "confusion_matrix": confusion.tolist(),
    }
