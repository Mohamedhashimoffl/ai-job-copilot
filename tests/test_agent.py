from unittest.mock import MagicMock

import pytest

from app.services.agent_tools import AgentGuardrails, add_to_tracker


def test_add_to_tracker_skips_duplicates():
    db = MagicMock()
    db.table().select().eq().eq().execute.return_value.data = [
        {"id": "existing-app-id"}
    ]

    result = add_to_tracker(db, user_id="u1", job_id="j1")

    assert result["status"] == "already_tracked"
    assert result["application_id"] == "existing-app-id"


def test_max_tool_calls_raises():
    g = AgentGuardrails(max_tool_calls=2)
    g.check_tool_call("search_live_jobs", {"query": "a"})
    g.check_tool_call("search_live_jobs", {"query": "b"})
    with pytest.raises(RuntimeError):
        g.check_tool_call("search_live_jobs", {"query": "c"})


def test_repeat_detection_raises():
    g = AgentGuardrails(max_tool_calls=10)
    args = {"query": "python developer"}
    g.check_tool_call("search_live_jobs", args)
    g.check_tool_call("search_live_jobs", args)
    with pytest.raises(RuntimeError):
        g.check_tool_call("search_live_jobs", args)
