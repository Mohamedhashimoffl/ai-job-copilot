from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user, get_db

router = APIRouter()

VALID_STATUSES = {"draft", "applied", "interview", "rejected", "offer"}
FOLLOWUP_RULES = {"applied": 7, "interview": 3}


class ApplicationCreate(BaseModel):
    job_id: str
    status: str = "draft"


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    applied_at: Optional[str] = None


def needs_followup(application: dict) -> bool:
    status = application["status"]
    if status not in FOLLOWUP_RULES:
        return False
    if not application.get("applied_at"):
        return False
    applied_at = datetime.fromisoformat(
        application["applied_at"].replace("Z", "+00:00")
    )
    days_elapsed = (datetime.now(timezone.utc) - applied_at).days
    return days_elapsed >= FOLLOWUP_RULES[status]


@router.post("")
def create_application(
    payload: ApplicationCreate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {VALID_STATUSES}"
        )

    existing = (
        db.table("applications")
        .select("*")
        .eq("user_id", user.id)
        .eq("job_id", payload.job_id)
        .execute()
        .data
    )
    if existing:
        return existing[0]

    result = (
        db.table("applications")
        .insert(
            {
                "user_id": user.id,
                "job_id": payload.job_id,
                "status": payload.status,
            }
        )
        .execute()
    )
    return result.data[0]


@router.get("")
def list_applications(
    status: Optional[str] = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    query = (
        db.table("applications")
        .select("*, job_postings(title, company, source_url)")
        .eq("user_id", user.id)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.get("/needs-followup")
def get_followups(user=Depends(get_current_user), db=Depends(get_db)):
    apps = (
        db.table("applications")
        .select("*, job_postings(title, company, source_url)")
        .eq("user_id", user.id)
        .execute()
        .data
    )

    flagged = [a for a in apps if needs_followup(a)]
    for a in flagged:
        applied_at = datetime.fromisoformat(a["applied_at"].replace("Z", "+00:00"))
        a["days_waiting"] = (datetime.now(timezone.utc) - applied_at).days
        a["followup_threshold"] = FOLLOWUP_RULES[a["status"]]

    return sorted(flagged, key=lambda a: a["days_waiting"], reverse=True)


@router.get("/{application_id}")
def get_application(
    application_id: str, user=Depends(get_current_user), db=Depends(get_db)
):
    results = (
        db.table("applications")
        .select("*, job_postings(*)")
        .eq("id", application_id)
        .eq("user_id", user.id)
        .execute()
        .data
    )
    if not results:
        raise HTTPException(status_code=404, detail="Application not found")
    return results[0]


@router.patch("/{application_id}")
def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {VALID_STATUSES}"
        )

    updates = payload.model_dump(exclude_none=True)

    # Start the follow-up clock the first time an application is marked
    # applied or interview, without resetting it on later status changes.
    if updates.get("status") in ("applied", "interview") and "applied_at" not in updates:
        current = (
            db.table("applications")
            .select("applied_at")
            .eq("id", application_id)
            .eq("user_id", user.id)
            .execute()
            .data
        )
        if current and not current[0].get("applied_at"):
            updates["applied_at"] = datetime.now(timezone.utc).isoformat()

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        db.table("applications")
        .update(updates)
        .eq("id", application_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found")
    return result.data[0]
