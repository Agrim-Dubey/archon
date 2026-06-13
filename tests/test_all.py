"""Comprehensive test suite for fast-api-archon."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_registration_and_login(client: AsyncClient):
    email = "candidate_new@archon.dev"
    reg_resp = await client.post(
        "/register",
        json={"name": "Alice Candidate", "email": email, "password": "SecurePassword123!"},
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["email"] == email

    # Login
    login_resp = await client.post(
        "/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_list_questions(client: AsyncClient):
    resp = await client.get("/api/v1/interviews/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) >= 3
    assert any("WhatsApp" in q["title"] for q in questions)


@pytest.mark.asyncio
async def test_interview_lifecycle(client: AsyncClient, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Start interview
    start_resp = await client.post(
        "/api/v1/interviews/start",
        json={"question_id": "q-whatsapp-01"},
        headers=headers,
    )
    assert start_resp.status_code == 201
    it_data = start_resp.json()
    interview_id = it_data["id"]
    assert it_data["status"] == "IN_PROGRESS"

    # 2. Sync diagram
    diag_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/diagram/sync",
        json={
            "nodes": [
                {"id": "n1", "type": "gateway", "label": "API Gateway", "x": 100.0, "y": 200.0},
                {"id": "n2", "type": "database", "label": "PostgreSQL", "x": 300.0, "y": 400.0},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2", "type": "default"}],
        },
        headers=headers,
    )
    assert diag_resp.status_code == 200
    assert len(diag_resp.json()["nodes"]) == 2

    # 3. Submit interview
    submit_resp = await client.post(
        f"/api/v1/interviews/{interview_id}/submit",
        json={"notes": "All requirements addressed."},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "COMPLETED"

    # 4. Fetch Report
    rep_resp = await client.get(
        f"/api/v1/interviews/{interview_id}/report",
        headers=headers,
    )
    assert rep_resp.status_code == 200
    assert rep_resp.json()["overall_score"] > 0


@pytest.mark.asyncio
async def test_quiz_and_daily_challenge(client: AsyncClient, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}

    # List decks
    decks_resp = await client.get("/api/v1/quiz/decks")
    assert decks_resp.status_code == 200
    decks = decks_resp.json()
    assert len(decks) >= 1

    # Daily challenge
    daily_resp = await client.get("/api/v1/quiz/daily-challenge")
    assert daily_resp.status_code == 200
    q = daily_resp.json()
    assert "question" in q


@pytest.mark.asyncio
async def test_dashboard_and_analytics(client: AsyncClient, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}

    dash_resp = await client.get("/api/v1/dashboard/overview", headers=headers)
    assert dash_resp.status_code == 200
    assert "candidate_name" in dash_resp.json()

    analytics_resp = await client.get("/api/v1/analytics", headers=headers)
    assert analytics_resp.status_code == 200
    assert "radar_metrics" in analytics_resp.json()


@pytest.mark.asyncio
async def test_settings(client: AsyncClient, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}

    get_resp = await client.get("/api/v1/settings", headers=headers)
    assert get_resp.status_code == 200

    put_resp = await client.put(
        "/api/v1/settings",
        json={"primary_stack": "Go and Python", "target_level": "staff"},
        headers=headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["primary_stack"] == "Go and Python"
