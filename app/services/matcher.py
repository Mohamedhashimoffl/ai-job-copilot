from app.core.gemini_client import client
from app.core.supabase_client import supabase
from app.services.embeddings import get_embedding
import time

GEMINI_MODEL = "gemini-3.5-flash"


def analyze_fit(resume_id: str, job: dict) -> str:
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

    if not chunks:
        raise ValueError("No resume content found for this resume")

    resume_context = "\n---\n".join(c["chunk_text"] for c in chunks)

    prompt = f"""You are a careful technical recruiter evaluating a candidate.

JOB POSTING:
Title: {job["title"]}
Description: {job["description"]}

RELEVANT PARTS OF THE CANDIDATE'S RESUME:
{resume_context}

Task: Assess how well this candidate fits the role. Cover:
1. Strengths: which resume evidence supports the requirements
2. Gaps: requirements with no evidence in the resume
3. Overall judgment in 2-3 sentences

Rules: use ONLY the resume content above. If something isn't shown,
treat it as missing. Do not assume or invent skills."""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt
            )
            return response.text
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)
