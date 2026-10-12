from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user, get_db
from app.services.agent_tools import run_agent
from app.services.cover_letter import generate_cover_letter
from app.services.embeddings import get_embedding
from app.services.matcher import analyze_fit

router = APIRouter()


@router.get("/{resume_id}")
def get_matches(resume_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    result = db.rpc("match_jobs", {"resume_id": resume_id}).execute()
    return result.data


@router.get("/{resume_id}/analyze/{job_id}")
def analyze(
    resume_id: str,
    job_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    jobs = (
        db.table("job_postings")
        .select("id,title,company,description")
        .eq("id", job_id)
        .execute()
        .data
    )
    if not jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        result = analyze_fit(db, resume_id, jobs[0])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    db.table("matches").upsert(
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
    db=Depends(get_db),
):
    jobs = (
        db.table("job_postings")
        .select("id,title,company,description")
        .eq("id", job_id)
        .execute()
        .data
    )
    if not jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[0]

    matches = (
        db.table("matches")
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
        db.rpc(
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


@router.post("/{resume_id}/auto-apply")
def auto_apply(
    resume_id: str,
    goal: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    return run_agent(db, user, resume_id, goal)
