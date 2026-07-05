"""Integration tests for faculty endpoints and authorization."""

from app.services.evaluation_service import evaluation_service
from tests.fixtures.transcripts import GOOD_STUDENT_MESSAGES, make_valid_evaluation_result

FACULTY_HEADERS = {"X-Demo-Role": "faculty"}


async def _completed_evaluated_session(client, scenario_id, monkeypatch) -> str:
    class FakeAgent:
        async def evaluate(self, **_: object):
            return make_valid_evaluation_result()

    monkeypatch.setattr(evaluation_service, "_agent", FakeAgent())

    create = await client.post("/api/v1/sessions", json={"scenario_id": scenario_id})
    session_id = create.json()["id"]
    for text in GOOD_STUDENT_MESSAGES:
        await client.post(
            f"/api/v1/sessions/{session_id}/messages", json={"content": text}
        )
    await client.post(f"/api/v1/sessions/{session_id}/complete")
    await client.post(f"/api/v1/sessions/{session_id}/evaluation")
    return session_id


async def test_student_cannot_access_faculty_endpoint(client):
    # No faculty header -> treated as the demo student -> forbidden.
    response = await client.get("/api/v1/faculty/sessions")
    assert response.status_code == 403


async def test_faculty_can_list_sessions(client, scenario_id, monkeypatch):
    await _completed_evaluated_session(client, scenario_id, monkeypatch)
    response = await client.get("/api/v1/faculty/sessions", headers=FACULTY_HEADERS)
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["overall_score"] == 4.0


async def test_faculty_can_review_a_session(client, scenario_id, monkeypatch):
    session_id = await _completed_evaluated_session(client, scenario_id, monkeypatch)

    review = await client.post(
        f"/api/v1/faculty/sessions/{session_id}/review",
        headers=FACULTY_HEADERS,
        json={
            "comments": "Good use of open-ended questions.",
            "adjusted_score": 4.0,
            "review_status": "reviewed",
        },
    )
    assert review.status_code == 200
    assert review.json()["review_status"] == "reviewed"

    detail = await client.get(
        f"/api/v1/faculty/sessions/{session_id}", headers=FACULTY_HEADERS
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["faculty_comment"] == "Good use of open-ended questions."
    assert body["status"] == "reviewed"
