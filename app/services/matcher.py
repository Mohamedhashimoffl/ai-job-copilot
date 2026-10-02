import json
import time
from pydantic import BaseModel
from google.genai import types
from app.core.gemini_client import client
from app.core.supabase_client import supabase
from app.services.embeddings import get_embedding

GEMINI_MODEL = "gemini-3.5-flash"


class FitAnalysis(BaseModel):
    score: int
    explanation: str
    strengths: list[str]
    gaps: list[str]


def analyze_fit(resume_id: str, job: dict) -> dict:
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

Evaluate fit. Rules: use ONLY the resume content above. If something
isn't shown, treat it as missing and list it under gaps. Do not assume
or invent skills. Be honest with the score — most real candidates are
not a 90+ fit."""

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=FitAnalysis,
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt, config=config
            )
            return json.loads(response.text)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
