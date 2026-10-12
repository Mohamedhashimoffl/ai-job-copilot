from datetime import datetime, timedelta, timezone
from app.api.applications import needs_followup, FOLLOWUP_RULES


def make_app(status: str, days_ago: int):
    applied = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"status": status, "applied_at": applied}


def test_flags_old_applied():
    assert needs_followup(make_app("applied", 8)) is True


def test_does_not_flag_recent_applied():
    assert needs_followup(make_app("applied", 2)) is False


def test_resolved_statuses_never_flagged():
    for status in ["draft", "rejected", "offer"]:
        assert needs_followup(make_app(status, 30)) is False


def test_missing_applied_at_never_flagged():
    assert needs_followup({"status": "applied", "applied_at": None}) is False
