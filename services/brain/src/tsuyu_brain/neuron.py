"""Batched, current-based leaky integrate-and-fire neurons (milliseconds)."""

from __future__ import annotations

import math

import torch
from torch import Tensor

DT_MS = 0.5


class LIFPopulation:
    """Euler membrane integration with exponentially decaying synaptic current.

    Incoming spikes add current impulses; refractory neurons keep their reset
    voltage while synaptic current continues to decay. State has shape [batch, n].
    """

    def __init__(
        self,
        n: int,
        batch: int = 1,
        threshold: float | Tensor = 1.0,
        dt_ms: float = DT_MS,
        tau_m_ms: float = 20.0,
        tau_syn_ms: float = 5.0,
        refractory_ms: float = 2.0,
    ) -> None:
        if n < 1 or batch < 1 or min(dt_ms, tau_m_ms, tau_syn_ms) <= 0:
            raise ValueError("population sizes and time constants must be positive")
        if refractory_ms < 0 or not torch.all(torch.as_tensor(threshold) > 0):
            raise ValueError("invalid refractory period or threshold")
        self.voltage = torch.zeros(batch, n)
        self.current = torch.zeros_like(self.voltage)
        self.refractory = torch.zeros(batch, n, dtype=torch.int64)
        self.threshold = threshold
        self.dt_ms = dt_ms
        self.leak = dt_ms / tau_m_ms
        self.decay = math.exp(-dt_ms / tau_syn_ms)
        self.refractory_steps = math.ceil(refractory_ms / dt_ms)

    def step(self, impulses: Tensor, tonic: float | Tensor = 0.0) -> Tensor:
        self.current = self.current * self.decay + impulses
        active = self.refractory == 0
        self.refractory = (self.refractory - 1).clamp_min(0)
        self.voltage = torch.where(
            active, self.voltage + self.leak * (self.current + tonic - self.voltage), 0.0
        )
        spikes = self.voltage >= self.threshold
        self.voltage.masked_fill_(spikes, 0.0)
        self.refractory.masked_fill_(spikes, self.refractory_steps)
        return spikes


def poisson_input(rates_hz: Tensor, generator: torch.Generator, dt_ms: float = DT_MS) -> Tensor:
    """Bin a Poisson process into presence/absence of at least one event."""
    if dt_ms <= 0 or not torch.isfinite(rates_hz).all() or (rates_hz < 0).any():
        raise ValueError("finite nonnegative rates and positive dt required")
    probability = -torch.expm1(-rates_hz * dt_ms / 1000.0)
    return torch.rand(rates_hz.shape, generator=generator) < probability
