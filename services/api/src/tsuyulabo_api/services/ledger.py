from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.base import new_id
from tsuyulabo_api.db.economy import Inventory, LedgerAccount, LedgerEntry
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.errors import APIError

CURRENCIES = ("shizuku", "research_points", "kohaku")
MATERIALS = ("banana", "apple", "grape", "yeast", "agar", "royal_jelly")


def positive_amount(amount: int) -> None:
    if type(amount) is not int or amount <= 0:
        raise APIError("validation_error", "数量は正の整数で指定してください", 422)


async def get_account(session: AsyncSession, owner: str, currency: str) -> LedgerAccount:
    if currency not in CURRENCIES:
        raise APIError("validation_error", "通貨が不正です", 422)
    await insert_if_absent(
        session,
        LedgerAccount,
        {"id": new_id(), "owner": owner, "currency": currency, "balance": 0},
        ["owner", "currency"],
    )
    return (
        await session.scalars(
            select(LedgerAccount).where(
                LedgerAccount.owner == owner, LedgerAccount.currency == currency
            )
        )
    ).one()


async def verify_balance(session: AsyncSession, account_id: str) -> bool:
    account = await session.get(LedgerAccount, account_id, populate_existing=True)
    total = await session.scalar(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.account_id == account_id
        )
    )
    return account is not None and account.balance == total


async def transfer(
    session: AsyncSession,
    from_account: LedgerAccount,
    to_account: LedgerAccount,
    amount: int,
    reason: str,
    ref: str | None = None,
) -> str:
    """Post a balanced pair; the caller owns the outer transaction and commit."""
    positive_amount(amount)
    if from_account.id == to_account.id or from_account.currency != to_account.currency:
        raise APIError("validation_error", "異なる同一通貨の口座を指定してください", 422)
    if from_account.currency == "kohaku":
        raise APIError("validation_error", "アルファ版ではこはくを使用できません", 422)
    tx_id = new_id()
    async with session.begin_nested():
        # Lock in stable order on Postgres. SQLite transactions already own the writer lock.
        accounts = (
            await session.scalars(
                select(LedgerAccount)
                .where(LedgerAccount.id.in_([from_account.id, to_account.id]))
                .order_by(LedgerAccount.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).all()
        if len(accounts) != 2:
            raise APIError("not_found", "口座が見つかりません", 404)
        for account in accounts:
            if not await verify_balance(session, account.id):
                raise APIError("ledger_invariant_failed", "台帳と残高が一致しません", 500)
        debit = update(LedgerAccount).where(LedgerAccount.id == from_account.id)
        if not from_account.owner.startswith("system:"):
            debit = debit.where(LedgerAccount.balance >= amount)
        result = await session.execute(debit.values(balance=LedgerAccount.balance - amount))
        if result.rowcount != 1:
            raise APIError("insufficient_funds", "残高が足りません", 409)
        await session.execute(
            update(LedgerAccount)
            .where(LedgerAccount.id == to_account.id)
            .values(balance=LedgerAccount.balance + amount)
        )
        session.add_all(
            [
                LedgerEntry(
                    tx_id=tx_id, account_id=from_account.id, amount=-amount, reason=reason, ref=ref
                ),
                LedgerEntry(
                    tx_id=tx_id, account_id=to_account.id, amount=amount, reason=reason, ref=ref
                ),
            ]
        )
        await session.flush()
    return tx_id


async def balances(session: AsyncSession, user_id: str) -> dict[str, int]:
    accounts = await session.scalars(
        select(LedgerAccount).where(LedgerAccount.owner == f"user:{user_id}")
    )
    return dict.fromkeys(CURRENCIES, 0) | {
        account.currency: account.balance for account in accounts
    }


async def change_inventory(
    session: AsyncSession, user_id: str, material: str, amount: int, *, remove: bool = False
) -> int:
    positive_amount(amount)
    if material not in MATERIALS:
        raise APIError("validation_error", "材料が不正です", 422)
    async with session.begin_nested():
        await insert_if_absent(
            session,
            Inventory,
            {"user_id": user_id, "material": material, "amount": 0},
            ["user_id", "material"],
        )
        statement = update(Inventory).where(
            Inventory.user_id == user_id, Inventory.material == material
        )
        if remove:
            statement = statement.where(Inventory.amount >= amount)
        result = await session.scalar(
            statement.values(amount=Inventory.amount + (-amount if remove else amount)).returning(
                Inventory.amount
            )
        )
        if result is None:
            raise APIError("insufficient_funds", "材料が足りません", 409)
        return result


async def add_material(session: AsyncSession, user_id: str, material: str, amount: int) -> int:
    return await change_inventory(session, user_id, material, amount)


async def remove_material(session: AsyncSession, user_id: str, material: str, amount: int) -> int:
    return await change_inventory(session, user_id, material, amount, remove=True)
