from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user, get_token
from app.core.supabase_client import supabase
from app.services.matcher import analyze_fit

router = APIRouter()


@router.get("/{resume_id}")
def get_matches(
    resume_id: str, user=Depends(get_current_user), token: str = Depends(get_token)
):
    supabase.postgrest.auth(token)
    result = supabase.rpc("match_jobs", {"resume_id": resume_id}).execute()
    return result.data


@router.get("/{resume_id}/analyze/{job_id}")
def analyze(
    resume_id: str,
    job_id: str,
    user=Depends(get_current_user),
    token: str = Depends(get_token),
):
    supabase.postgrest.auth(token)
    jobs = (
        supabase.table("job_postings")
        .select("id,title,company,description")
        .eq("id", job_id)
        .execute()
        .data
    )
    if not jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        analysis = analyze_fit(resume_id, jobs[0])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"analysis": analysis}
