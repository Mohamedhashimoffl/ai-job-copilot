from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user, get_token
from app.core.supabase_client import supabase
from datetime import datetime, timezone

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
    token: str = Depends(get_token),
):
    supabase.postgrest.auth(token)
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {VALID_STATUSES}"
        )
    result = (
        supabase.table("applications")
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
    token: str = Depends(get_token),
):
    supabase.postgrest.auth(token)
    query = (
        supabase.table("applications")
        .select("*, job_postings(title, company)")
        .eq("user_id", user.id)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.get("/needs-followup")
def get_followups(user=Depends(get_current_user), token: str = Depends(get_token)):
    supabase.postgrest.auth(token)
    apps = (
        supabase.table("applications")
        .select("*, job_postings(title, company)")
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
    application_id: str, user=Depends(get_current_user), token: str = Depends(get_token)
):
    supabase.postgrest.auth(token)
    results = (
        supabase.table("applications")
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
    token: str = Depends(get_token),
):
    supabase.postgrest.auth(token)
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {VALID_STATUSES}"
        )

    updates = payload.model_dump(exclude_none=True)
    if updates.get("status") == "applied" and "applied_at" not in updates:
        updates["applied_at"] = datetime.now(timezone.utc).isoformat()

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        supabase.table("applications")
        .update(updates)
        .eq("id", application_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found")
    return result.data[0]
