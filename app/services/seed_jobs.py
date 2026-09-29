from dotenv import load_dotenv

load_dotenv()

import os

from supabase import create_client

from app.services.embeddings import get_embedding

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))

sample_jobs = [
    {
        "title": "Backend Developer",
        "company": "TestCo",
        "description": "Looking for a backend engineer skilled in FastAPI, PostgreSQL, and REST API design.",
    },
    {
        "title": "Frontend Developer",
        "company": "TestCo",
        "description": "React developer needed for building responsive web interfaces.",
    },
    {
        "title": "Data Analyst",
        "company": "TestCo",
        "description": "Analyze datasets using SQL and Python, build dashboards.",
    },
]

for job in sample_jobs:
    embedding = get_embedding(job["description"], task_type="RETRIEVAL_DOCUMENT")
    supabase.table("job_postings").insert({**job, "embedding": embedding}).execute()

print("Seeded", len(sample_jobs), "jobs")
