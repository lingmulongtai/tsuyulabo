from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from tsuyu_worker.main import WorkerSettings, slot_push
from tsuyu_worker.push import Sessions, send_reminders
from tsuyulabo_api.db.models import CareEvent, Notification, Week
from tsuyulabo_api.db.push import NotificationPreference, PushDelivery, PushSubscription
from tsuyulabo_api.domain.clock import JST

NOW = datetime(2026, 9, 27, 12, tzinfo=JST)


class FakeSender:
    def __init__(self, statuses: dict[str, int] | None = None) -> None:
        self.statuses = statuses or {}
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def send(self, subscription: PushSubscription, payload: dict[str, str]) -> int:
        self.calls.append((subscription.id, payload))
        return self.statuses.get(subscription.id, 201)


async def seed(sessions: Sessions) -> None:
    async with sessions() as session, session.begin():
        session.add_all(
            [
                PushSubscription(
                    id=user,
                    user_id=user,
                    endpoint=f"https://fcm.googleapis.com/{user}",
                    p256dh="fake",
                    auth="fake",
                    created_at=NOW - timedelta(days=1),
                )
                for user in ("u", "other")
            ]
        )


async def test_meal_cooked_slot_and_repeated_concurrent_jobs(sessions: Sessions) -> None:
    await seed(sessions)
    async with sessions() as session, session.begin():
        session.add(
            CareEvent(
                user_id="u",
                week_id="w",
                seq=3,
                kind="meal",
                research_day=3,
                slot="noon",
                created_at=NOW,
            )
        )
    sender = FakeSender()
    await asyncio.gather(*(send_reminders(sessions, sender, now=NOW) for _ in range(2)))
    assert [(user, payload["title"]) for user, payload in sender.calls] == [
        ("other", "ごはんの時間です")
    ]
    assert sender.calls[0][1]["url"] == "/care/meal"
    await send_reminders(sessions, sender, now=NOW + timedelta(minutes=1))
    assert len(sender.calls) == 1


async def test_default_quiet_hours_categories_and_inactive_week(sessions: Sessions) -> None:
    await seed(sessions)
    sender = FakeSender()
    await send_reminders(sessions, sender, now=NOW.replace(hour=4))
    assert not sender.calls
    async with sessions() as session, session.begin():
        session.add(NotificationPreference(user_id="u", preferences={"meal_slots": ["night"]}))
        (await session.get(Week, "other-w")).status = "eclosed"
    await send_reminders(sessions, sender, now=NOW)
    assert not sender.calls


async def test_eclosion_only_day_seven_night_and_preferences(sessions: Sessions) -> None:
    await seed(sessions)
    async with sessions() as session, session.begin():
        for user, week in (("u", "w"), ("other", "other-w")):
            (await session.get(Week, week)).started_at = NOW - timedelta(days=6)
            session.add(
                NotificationPreference(
                    user_id=user,
                    preferences={
                        "meal_slots": [],
                        "eclosion_night": user == "u",
                    },
                )
            )
    sender = FakeSender()
    await send_reminders(sessions, sender, now=NOW)
    assert not sender.calls
    await send_reminders(sessions, sender, now=NOW.replace(hour=18))
    assert len(sender.calls) == 1
    assert sender.calls[0][1]["title"] == "羽化の夜です"
    assert sender.calls[0][1]["url"] == "/presentation"
    await send_reminders(sessions, sender, now=NOW.replace(hour=18) + timedelta(days=1))
    assert len(sender.calls) == 1


@pytest.mark.parametrize("status", [404, 410])
async def test_dead_subscriptions_removed_and_failures_retried(
    sessions: Sessions, status: int
) -> None:
    await seed(sessions)
    sender = FakeSender({"u": status, "other": 503})
    counts = await send_reminders(sessions, sender, now=NOW)
    assert counts == {"sent": 0, "dead": 1, "failed": 1}
    async with sessions() as session:
        assert await session.get(PushSubscription, "u") is None
        assert list(await session.scalars(select(PushDelivery))) == []
    sender.statuses = {}
    assert (await send_reminders(sessions, sender, now=NOW + timedelta(minutes=1)))["sent"] == 1
    await send_reminders(sessions, sender, now=NOW + timedelta(minutes=6))
    assert len(sender.calls) == 3


async def test_friend_activity_deduplicated_and_quiet_hours_respected(sessions: Sessions) -> None:
    await seed(sessions)
    async with sessions() as session, session.begin():
        session.add(NotificationPreference(user_id="other", preferences={"friend_activity": False}))
        for user in ("u", "other"):
            session.add(Notification(user_id=user, kind="like", created_at=NOW))
        session.add(Notification(user_id="u", kind="gift", created_at=NOW - timedelta(hours=1)))
    sender = FakeSender()
    await send_reminders(sessions, sender, now=NOW, friends=True)
    await send_reminders(sessions, sender, now=NOW + timedelta(minutes=1), friends=True)
    assert len(sender.calls) == 1
    assert sender.calls[0][1]["url"] == "/friends"
    late = NOW.replace(hour=23)
    async with sessions() as session, session.begin():
        session.add(Notification(user_id="u", kind="gift", created_at=late))
    await send_reminders(sessions, sender, now=late, friends=True)
    assert len(sender.calls) == 1


async def test_cron_and_disabled_configuration() -> None:
    cron = WorkerSettings.cron_jobs[1]
    assert cron.hour == {4, 12, 18} and cron.minute == {0, 1, 2, 3, 4}
    assert cron.unique and not cron.run_at_startup
    assert await slot_push({}) == {"skipped": "push_disabled"}
