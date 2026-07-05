"""Integration tests for the session and evaluation lifecycle."""

import pytest

from app.services.evaluation_service import evaluation_service
from tests.conftest import create_other_student_session
from tests.fixtures.transcripts import GOOD_STUDENT_MESSAGES, make_valid_evaluation_result


async def _start_session(client, scenario_id: str) -> str:
    response = await client.post("/api/v1/sessions", json={"scenario_id": scenario_id})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_student_starts_valid_session(client, scenario_id):
    response = await client.post("/api/v1/sessions", json={"scenario_id": scenario_id})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    # The first AI-client message is seeded.
    assert len(body["messages"]) == 1
    assert body["messages"][0]["speaker"] == "client"


async def test_student_sends_valid_message(client, scenario_id):
    session_id = await _start_session(client, scenario_id)
    response = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "It sounds like work has been weighing on you."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == session_id
    # The AI client replies (a safe fallback when Gemini is not configured).
    assert body["message"]["speaker"] == "client"
    assert body["message"]["content"]


async def test_list_my_sessions(client, scenario_id):
    await _start_session(client, scenario_id)
    await _start_session(client, scenario_id)
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 2
    assert {"session_id", "scenario_title", "status"} <= set(sessions[0].keys())


async def test_cannot_send_to_completed_session(client, scenario_id):
    session_id = await _start_session(client, scenario_id)
    complete = await client.post(f"/api/v1/sessions/{session_id}/complete")
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"

    response = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "One more thing..."},
    )
    assert response.status_code == 409


async def test_cannot_evaluate_before_minimum_messages(client, scenario_id):
    session_id = await _start_session(client, scenario_id)
    await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "Tell me more about your week."},
    )
    await client.post(f"/api/v1/sessions/{session_id}/complete")

    response = await client.post(f"/api/v1/sessions/{session_id}/evaluation")
    assert response.status_code == 400


async def test_cannot_access_other_students_session(client, session_factory, scenario_id):
    other_session_id = await create_other_student_session(session_factory, scenario_id)
    response = await client.get(f"/api/v1/sessions/{other_session_id}")
    assert response.status_code == 403


async def test_gemini_failure_returns_safe_error(client, scenario_id):
    """With no Gemini key configured, evaluation surfaces a 502, not a 500."""
    session_id = await _start_session(client, scenario_id)
    for text in GOOD_STUDENT_MESSAGES:
        await client.post(
            f"/api/v1/sessions/{session_id}/messages", json={"content": text}
        )
    await client.post(f"/api/v1/sessions/{session_id}/complete")

    response = await client.post(f"/api/v1/sessions/{session_id}/evaluation")
    assert response.status_code == 502


async def test_invalid_evaluation_is_rejected(client, scenario_id, monkeypatch):
    from app.core.exceptions import EvaluationValidationError

    class RejectingAgent:
        async def evaluate(self, **_: object):
            raise EvaluationValidationError("bad structure")

    monkeypatch.setattr(evaluation_service, "_agent", RejectingAgent())

    session_id = await _start_session(client, scenario_id)
    for text in GOOD_STUDENT_MESSAGES:
        await client.post(
            f"/api/v1/sessions/{session_id}/messages", json={"content": text}
        )
    await client.post(f"/api/v1/sessions/{session_id}/complete")

    response = await client.post(f"/api/v1/sessions/{session_id}/evaluation")
    assert response.status_code == 502


async def test_duplicate_evaluation_is_prevented(client, scenario_id, monkeypatch):
    calls = {"count": 0}

    class CountingAgent:
        async def evaluate(self, **_: object):
            calls["count"] += 1
            return make_valid_evaluation_result()

    monkeypatch.setattr(evaluation_service, "_agent", CountingAgent())

    session_id = await _start_session(client, scenario_id)
    for text in GOOD_STUDENT_MESSAGES:
        await client.post(
            f"/api/v1/sessions/{session_id}/messages", json={"content": text}
        )
    await client.post(f"/api/v1/sessions/{session_id}/complete")

    first = await client.post(f"/api/v1/sessions/{session_id}/evaluation")
    second = await client.post(f"/api/v1/sessions/{session_id}/evaluation")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert calls["count"] == 1


@pytest.mark.parametrize("content", ["", "   "])
async def test_blank_message_is_rejected(client, scenario_id, content):
    session_id = await _start_session(client, scenario_id)
    response = await client.post(
        f"/api/v1/sessions/{session_id}/messages", json={"content": content}
    )
    assert response.status_code == 422
