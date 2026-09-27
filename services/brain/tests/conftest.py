"""Small CPU networks avoid host thread-pool overhead during package tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import torch


@pytest.fixture(scope="session", autouse=True)
def brain_test_threads() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)
