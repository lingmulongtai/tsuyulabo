from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.models import LedgerAccount, LedgerEntry, User
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.ledger import (
    add_material,
    get_account,
    remove_material,
    transfer,
    verify_balance,
)


async def test_balanced_transfer_and_insufficient_funds(session: AsyncSession) -> None:
    rewards = await get_account(session, "system:rewards", "shizuku")
    wallet = await get_account(session, "user:test", "shizuku")
    shop = await get_account(session, "system:shop", "shizuku")
    tx = await transfer(session, rewards, wallet, 300, "initial_grant", "test")
    entries = (await session.scalars(select(LedgerEntry).where(LedgerEntry.tx_id == tx))).all()
    assert sorted(entry.amount for entry in entries) == [-300, 300]
    await transfer(session, wallet, shop, 100, "purchase")
    with pytest.raises(APIError, match="残高") as error:
        await transfer(session, wallet, shop, 201, "purchase")
    assert error.value.code == "insufficient_funds"
    assert await session.scalar(select(func.count()).select_from(LedgerEntry)) == 4
    for account in [rewards, wallet, shop]:
        assert await verify_balance(session, account.id)
    assert wallet.balance == 200
    assert await session.scalar(select(func.sum(LedgerAccount.balance))) == 0


async def test_invalid_amounts_and_inventory(session: AsyncSession) -> None:
    user = User(display_name="test", friend_code="ABCDEFGH")
    session.add(user)
    await session.flush()
    assert await add_material(session, user.id, "banana", 5) == 5
    assert await remove_material(session, user.id, "banana", 3) == 2
    with pytest.raises(APIError):
        await remove_material(session, user.id, "banana", 3)
    assert await add_material(session, user.id, "banana", 1) == 3
    for amount in [0, -1, 1.5, True]:
        with pytest.raises(APIError):
            await add_material(session, user.id, "banana", amount)


async def test_concurrent_spending_cannot_overdraw(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions() as session, session.begin():
        rewards = await get_account(session, "system:rewards", "shizuku")
        wallet = await get_account(session, "user:test", "shizuku")
        await get_account(session, "system:shop", "shizuku")
        await transfer(session, rewards, wallet, 300, "initial_grant")

    async def spend() -> bool:
        try:
            async with sessions() as session, session.begin():
                wallet = await get_account(session, "user:test", "shizuku")
                shop = await get_account(session, "system:shop", "shizuku")
                await transfer(session, wallet, shop, 200, "purchase")
            return True
        except APIError as exc:
            assert exc.code == "insufficient_funds"
            return False

    assert sorted(await asyncio.gather(spend(), spend())) == [False, True]
    async with sessions() as session:
        wallet = await get_account(session, "user:test", "shizuku")
        assert wallet.balance == 100
        assert await verify_balance(session, wallet.id)


async def test_outer_rollback_undoes_transfer(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions() as session:
        rewards = await get_account(session, "system:rewards", "shizuku")
        wallet = await get_account(session, "user:test", "shizuku")
        await session.commit()
        await transfer(session, rewards, wallet, 300, "initial_grant")
        await session.rollback()
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
        assert await session.scalar(select(func.sum(LedgerAccount.balance))) == 0
