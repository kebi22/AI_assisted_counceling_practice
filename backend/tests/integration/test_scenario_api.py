"""Integration tests for scenario retrieval."""


async def test_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_list_scenarios_returns_seeded_module1(client):
    response = await client.get("/api/v1/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 1
    assert scenarios[0]["title"] == "Module 1: Overwhelmed Teacher"


async def test_scenario_detail_excludes_system_prompt(client, scenario_id):
    response = await client.get(f"/api/v1/scenarios/{scenario_id}")
    assert response.status_code == 200
    body = response.json()
    assert "system_prompt" not in body
    assert body["client_name"] == "Jordan"
