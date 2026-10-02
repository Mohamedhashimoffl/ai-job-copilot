from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user, get_token
from app.core.supabase_client import supabase
from app.services.matcher import analyze_fit
from app.services.cover_letter import generate_cover_letter
from app.services.embeddings import get_embedding


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
        result = analyze_fit(resume_id, jobs[0])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    supabase.table("matches").upsert(
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "score": result["score"],
            "explanation": result["explanation"],
            "strengths": result["strengths"],
            "gaps": result["gaps"],
        },
        on_conflict="resume_id,job_id",
    ).execute()

    return result


@router.get("/{resume_id}/cover-letter/{job_id}")
def cover_letter(
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
    job = jobs[0]

    matches = (
        supabase.table("matches")
        .select("*")
        .eq("resume_id", resume_id)
        .eq("job_id", job_id)
        .execute()
        .data
    )
    if not matches:
        raise HTTPException(
            status_code=404, detail="Run /analyze for this resume+job first"
        )
    match = matches[0]

    query_vec = get_embedding(job["description"], task_type="RETRIEVAL_QUERY")
    chunks = (
        supabase.rpc(
            "match_resume_chunks",
            {
                "p_resume_id": resume_id,
                "query_embedding": query_vec,
                "match_count": 5,
            },
        )
        .execute()
        .data
    )
    resume_context = "\n---\n".join(c["chunk_text"] for c in chunks)

    letter = generate_cover_letter(resume_context, job, match)
    return {"cover_letter": letter}
