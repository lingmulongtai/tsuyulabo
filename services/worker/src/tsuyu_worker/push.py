"""Short-lived reminders with persistent per-device delivery claims."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.models import CareEvent, Notification, User, Week
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.db.push import NotificationPreference, PushDelivery, PushSubscription
from tsuyulabo_api.domain.clock import local, research_day, slot_of, slot_start
from tsuyulabo_api.services.push import PushSender
from tsuyulabo_api.services.push_preferences import PushPreferences

logger = logging.getLogger(__name__)
Sessions = async_sessionmaker[AsyncSession]


async def pending_messages(
    session: AsyncSession, subscription: PushSubscription, now: datetime, *, friends: bool
) -> list[tuple[str, dict[str, str]]]:
    row = await session.get(NotificationPreference, subscription.user_id)
    prefs = PushPreferences.model_validate(row.preferences if row else {})
    if prefs.is_quiet(now):
        return []
    if friends:
        if not prefs.friend_activity:
            return []
        notices = await session.scalars(
            select(Notification).where(
                Notification.user_id == subscription.user_id,
                Notification.kind.in_(["like", "gift", "eclosion"]),
                Notification.created_at > now - timedelta(minutes=5),
                Notification.created_at >= subscription.created_at,
                Notification.created_at <= now,
                Notification.read_at.is_(None),
            )
        )
        return [
            (
                f"friend:{notice.id}",
                {
                    "title": "フレンドからのお知らせ",
                    "body": {
                        "like": "いいねが届きました",
                        "gift": "おすそわけが届きました",
                        "eclosion": "フレンドの子が羽化しました",
                    }[notice.kind],
                    "url": "/friends",
                    "tag": f"friend:{notice.id}",
                },
            )
            for notice in notices
        ]

    # Only send at the real slot boundary (and a four-minute retry window).
    if now - slot_start(now) >= timedelta(minutes=5):
        return []
    user = await session.get(User, subscription.user_id)
    game_now = now + timedelta(seconds=user.dev_time_offset_s)
    week = await session.scalar(
        select(Week).where(
            Week.user_id == user.id, Week.status == "active", Week.started_at <= game_now
        )
    )
    if week is None:
        return []
    day, slot = research_day(week.started_at, game_now), slot_of(game_now)
    messages = []
    if 1 <= day <= 7 and slot in prefs.meal_slots:
        cooked = await session.scalar(
            select(CareEvent.id)
            .where(
                CareEvent.week_id == week.id,
                CareEvent.kind == "meal",
                CareEvent.research_day == day,
                CareEvent.slot == slot,
            )
            .limit(1)
        )
        if cooked is None:
            key = f"meal:{week.id}:{day}:{slot}"
            messages.append(
                (
                    key,
                    {
                        "title": "ごはんの時間です",
                        "body": "研究室でごはんを作ろう。",
                        "url": "/care/meal",
                        "tag": key,
                    },
                )
            )
    if day == 7 and slot == "night" and prefs.eclosion_night:
        key = f"eclosion:{week.id}"
        messages.append(
            (
                key,
                {
                    "title": "羽化の夜です",
                    "body": "今週の研究を振り返って、羽化を見届けよう。",
                    "url": "/presentation",
                    "tag": key,
                },
            )
        )
    return messages


async def send_reminders(
    sessions: Sessions, sender: PushSender, *, now: datetime | None = None, friends: bool = False
) -> dict[str, int]:
    now = local(now or datetime.now(UTC))
    counts = {"sent": 0, "dead": 0, "failed": 0}
    async with sessions() as session, session.begin():
        await session.execute(
            delete(PushDelivery).where(PushDelivery.created_at < now - timedelta(days=8))
        )
        ids = list(await session.scalars(select(PushSubscription.id)))
    for subscription_id in ids:
        try:
            async with sessions() as session:
                subscription = await session.get(PushSubscription, subscription_id)
                if subscription is None:
                    continue
                messages = await pending_messages(session, subscription, now, friends=friends)
            for key, payload in messages:
                # Commit before network IO: concurrent/repeated jobs cannot send the same event.
                async with sessions() as session, session.begin():
                    claimed = await insert_if_absent(
                        session,
                        PushDelivery,
                        {
                            "subscription_id": subscription_id,
                            "event_key": key,
                            "created_at": now,
                        },
                        ["subscription_id", "event_key"],
                    )
                if not claimed:
                    continue
                try:
                    status = await sender.send(subscription, payload)
                except Exception:
                    status = 503
                async with sessions() as session, session.begin():
                    if status in (404, 410):
                        await session.execute(
                            delete(PushSubscription).where(PushSubscription.id == subscription_id)
                        )
                        counts["dead"] += 1
                        break
                    if 200 <= status < 300:
                        counts["sent"] += 1
                    else:
                        # Permit retry during the bounded reminder window, including 429.
                        await session.execute(
                            delete(PushDelivery).where(
                                PushDelivery.subscription_id == subscription_id,
                                PushDelivery.event_key == key,
                            )
                        )
                        counts["failed"] += 1
        except Exception:
            # Never log endpoint capability URLs, encryption keys, or provider responses.
            logger.warning("push subscription delivery failed")
            counts["failed"] += 1
    return counts
