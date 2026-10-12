import os

import pytest

from app.core.supabase_client import user_client
from app.services.matcher import analyze_fit

# These tests call the real Gemini and Supabase APIs. To run them, set
# TEST_RESUME_ID (a resume id) and TEST_ACCESS_TOKEN (that user's login token).
TEST_RESUME_ID = os.getenv("TEST_RESUME_ID")
TEST_ACCESS_TOKEN = os.getenv("TEST_ACCESS_TOKEN")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (TEST_RESUME_ID and TEST_ACCESS_TOKEN),
        reason="set TEST_RESUME_ID and TEST_ACCESS_TOKEN to run",
    ),
]


def test_analyze_fit_returns_valid_shape():
    db = user_client(TEST_ACCESS_TOKEN)
    job = {
        "title": "Backend Developer",
        "description": "FastAPI, PostgreSQL, REST API experience required.",
    }
    result = analyze_fit(db, TEST_RESUME_ID, job)

    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert isinstance(result["explanation"], str) and len(result["explanation"]) > 0
    assert isinstance(result["strengths"], list)
    assert isinstance(result["gaps"], list)


def test_strong_match_scores_higher_than_weak_match():
    db = user_client(TEST_ACCESS_TOKEN)
    strong_job = {
        "title": "Backend Developer",
        "description": "FastAPI, PostgreSQL, Python backend development.",
    }
    weak_job = {
        "title": "Marine Biologist",
        "description": "Study ocean ecosystems, conduct field research on coral reefs.",
    }

    strong_result = analyze_fit(db, TEST_RESUME_ID, strong_job)
    weak_result = analyze_fit(db, TEST_RESUME_ID, weak_job)

    assert strong_result["score"] > weak_result["score"]
