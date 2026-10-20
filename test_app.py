from datetime import date

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test_expenses.db"),
    })
    with app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Expense Tracker" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_add_expense(client):
    response = client.post("/add", data={
        "title": "Lunch",
        "amount": "150",
        "category": "Food",
        "expense_date": date.today().isoformat(),
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Lunch" in response.data
    assert b"150.00" in response.data


def test_reject_invalid_amount(client):
    response = client.post("/add", data={
        "title": "Invalid expense",
        "amount": "-50",
        "category": "Food",
        "expense_date": date.today().isoformat(),
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid expense" not in response.data


def test_delete_expense(client):
    client.post("/add", data={
        "title": "Bus ticket",
        "amount": "30",
        "category": "Travel",
        "expense_date": date.today().isoformat(),
    })
    response = client.get("/")
    assert b"Bus ticket" in response.data
    # The first expense in this fresh test database receives ID 1.
    response = client.post("/delete/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Bus ticket" not in response.data


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"expense_tracker_http_requests_total" in response.data
