import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def api_client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@mergington.edu"],
        },
        "Full Activity": {
            "description": "Already full",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": ["full@mergington.edu"],
        },
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as client:
        yield client


def test_get_activities_returns_activity_details(api_client):
    # Arrange
    expected_participants = ["existing@mergington.edu"]

    # Act
    response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants
    assert response.json()["Chess Club"]["max_participants"] == 2


def test_signup_adds_participant(api_client):
    # Arrange
    activity = "Chess Club"
    email = "new@mergington.edu"

    # Act
    response = api_client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    participants = api_client.get("/activities").json()[activity]["participants"]
    assert email in participants


def test_signup_rejects_duplicate_participant(api_client):
    # Arrange
    activity = "Chess Club"
    email = "existing@mergington.edu"

    # Act
    response = api_client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity(api_client):
    # Arrange
    activity = "Full Activity"

    # Act
    response = api_client.post(
        f"/activities/{activity}/signup",
        params={"email": "new@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_rejects_unknown_activity(api_client):
    # Arrange
    activity = "Unknown Activity"

    # Act
    response = api_client.post(
        f"/activities/{activity}/signup",
        params={"email": "new@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(api_client):
    # Arrange
    activity = "Chess Club"
    email = "existing@mergington.edu"

    # Act
    response = api_client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    participants = api_client.get("/activities").json()[activity]["participants"]
    assert email not in participants


@pytest.mark.parametrize(
    ("activity", "email", "expected_detail"),
    [
        ("Unknown Activity", "student@mergington.edu", "Activity not found"),
        ("Chess Club", "not-signed-up@mergington.edu", "Student is not signed up for this activity"),
    ],
)
def test_unregister_rejects_unknown_activity_or_participant(
    api_client, activity, email, expected_detail
):
    # Arrange
    url = f"/activities/{activity}/participants"
    params = {"email": email}

    # Act
    response = api_client.delete(url, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail
