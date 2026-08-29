from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(demo_client: TestClient) -> None:
    response = demo_client.get("/health")
    assert response.status_code == 200
    assert response.json()["product"] == "ClientDesk"
    assert response.json()["storage"] == "ok"


def test_demo_config_exposes_only_demo_portal_token(demo_client: TestClient) -> None:
    response = demo_client.get("/api/public/config")
    assert response.status_code == 200
    assert response.json()["demo"] is True
    assert response.json()["demo_token"]
    assert "admin_token" not in response.json()


def test_demo_portal_contains_project_data(demo_client: TestClient) -> None:
    token = demo_client.get("/api/public/config").json()["demo_token"]
    response = demo_client.get(f"/api/portal/{token}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["client"]["company"] == "Northlight Advisory"
    assert len(payload["milestones"]) == 4
    assert len(payload["approvals"]) == 1


def test_unknown_portal_is_not_found(demo_client: TestClient) -> None:
    assert demo_client.get("/api/portal/not-a-real-token").status_code == 404
    assert demo_client.get("/p/not-a-real-token").status_code == 404


def test_demo_approval_is_not_persisted(demo_client: TestClient) -> None:
    token = demo_client.get("/api/public/config").json()["demo_token"]
    portal = demo_client.get(f"/api/portal/{token}").json()
    approval_id = portal["approvals"][0]["id"]
    response = demo_client.post(
        f"/api/portal/{token}/approvals/{approval_id}",
        json={"status": "approved", "response": "Looks good"},
    )
    assert response.status_code == 200
    assert response.json()["demo"] is True
    fresh = demo_client.get(f"/api/portal/{token}").json()
    assert fresh["approvals"][0]["status"] == "pending"


def test_admin_requires_token(demo_client: TestClient) -> None:
    assert demo_client.get("/api/admin/overview").status_code == 401
    response = demo_client.get(
        "/api/admin/overview", headers={"X-Admin-Token": "clientdesk-demo-view"}
    )
    assert response.status_code == 200
    assert response.json()["demo"] is True


def test_admin_can_create_client(
    empty_client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = empty_client.post(
        "/api/admin/clients",
        headers=admin_headers,
        json={
            "name": "Jordan Lee",
            "company": "Orbit Studio",
            "email": "jordan@example.com",
            "project_name": "Brand launch",
            "progress": 10,
            "due_date": "2026-10-01",
            "plan": "Standard",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["company"] == "Orbit Studio"
    assert payload["portal_token"]
    assert empty_client.get(f"/api/portal/{payload['portal_token']}").status_code == 200


def test_client_can_respond_to_real_approval(
    empty_client: TestClient, admin_headers: dict[str, str]
) -> None:
    client = empty_client.post(
        "/api/admin/clients",
        headers=admin_headers,
        json={
            "name": "Jordan Lee",
            "company": "Orbit Studio",
            "email": "jordan@example.com",
            "project_name": "Brand launch",
        },
    ).json()
    approval = empty_client.post(
        f"/api/admin/clients/{client['id']}/approvals",
        headers=admin_headers,
        json={"title": "Approve home page", "details": "Review the final hero copy."},
    ).json()
    response = empty_client.post(
        f"/api/portal/{client['portal_token']}/approvals/{approval['id']}",
        json={"status": "changes_requested", "response": "Shorten the headline."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "changes_requested"

