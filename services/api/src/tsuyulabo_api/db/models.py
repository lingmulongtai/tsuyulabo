"""Import this registry before creating tables or inspecting metadata."""

from __future__ import annotations

from tsuyulabo_api.db.base import Base
from tsuyulabo_api.db.daily_circuit import DailyCircuitAttempt
from tsuyulabo_api.db.economy import IdempotencyKey, Inventory, LedgerAccount, LedgerEntry
from tsuyulabo_api.db.mating import MatingProposal, PendingEgg
from tsuyulabo_api.db.maze import MazeEntry, MazeRace, MazeSlot
from tsuyulabo_api.db.rearing import (
    Adult,
    CareEvent,
    LarvaState,
    Puzzle,
    SleepSession,
    TeamSlot,
    Week,
)
from tsuyulabo_api.db.research import Experiment, Job, Paper, ShioriMessage
from tsuyulabo_api.db.social import Friendship, Gift, Like, Notification
from tsuyulabo_api.db.users import User

__all__ = [
    "Adult",
    "Base",
    "CareEvent",
    "DailyCircuitAttempt",
    "Experiment",
    "Friendship",
    "Gift",
    "IdempotencyKey",
    "Inventory",
    "Job",
    "LarvaState",
    "LedgerAccount",
    "LedgerEntry",
    "Like",
    "MatingProposal",
    "MazeEntry",
    "MazeRace",
    "MazeSlot",
    "Notification",
    "Paper",
    "PendingEgg",
    "Puzzle",
    "ShioriMessage",
    "SleepSession",
    "TeamSlot",
    "User",
    "Week",
]
