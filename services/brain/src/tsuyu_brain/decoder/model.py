"""Small hand-written multiclass logistic and MLP decoders using autograd."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import Tensor

from tsuyu_brain.behavior import FEATURES, LABELS
from tsuyu_brain.connectome.malecns_outputs import EXTRA_OUTPUTS
from tsuyu_brain.decoder.dataset import Dataset
from tsuyu_brain.decoder.features import WINDOWS


def checkpoint_features(version: str) -> tuple[str, ...]:
    """Bind checkpoints to exact versioned output ordering, including time bins."""
    if version == "toy-v0":
        return FEATURES
    if version != "malecns-v1.0":
        raise ValueError("unsupported decoder checkpoint version")
    return (
        *FEATURES,
        *(f"{group}:window_{i}" for group in FEATURES for i in range(WINDOWS)),
        *(
            f"{contrast}:window_{i}"
            for contrast in ("right-left", "approach-avoid")
            for i in range(WINDOWS)
        ),
        *(
            f"{group}:{field}"
            for group in EXTRA_OUTPUTS
            for field in ("mean", *(f"window_{i}" for i in range(WINDOWS)))
        ),
    )


@dataclass
class Decoder:
    kind: str
    mean: Tensor
    scale: Tensor
    weights: list[Tensor]
    version: str = "toy-v0"

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
        features = checkpoint_features(self.version)
        if self.mean.numel() != len(features):
            raise ValueError("decoder feature schema does not match its connectome version")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "version": self.version,
                "features": features,
                "labels": LABELS,
                "kind": self.kind,
                "mean": self.mean,
                "scale": self.scale,
                "weights": [value.detach() for value in self.weights],
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path, *, version: str | None = None) -> Decoder:
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if (
            (version is not None and payload["version"] != version)
            or tuple(payload["features"]) != checkpoint_features(payload["version"])
            or payload["mean"].numel() != len(payload["features"])
            or tuple(payload["labels"]) != LABELS
        ):
            raise ValueError("incompatible decoder checkpoint")
        return cls(
            payload["kind"],
            payload["mean"],
            payload["scale"],
            payload["weights"],
            payload["version"],
        )


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
    model = Decoder(
        kind, data.features.mean(0), data.features.std(0).clamp_min(1), weights, data.version
    )
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
