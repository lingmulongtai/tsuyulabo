from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.db.users import User
from tsuyulabo_api.services.jobs import get_job

router = APIRouter(prefix="/v1/jobs")


@router.get("/{job_id}")
async def read_job(
    job_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    job = await get_job(session, user.id, job_id)
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }
