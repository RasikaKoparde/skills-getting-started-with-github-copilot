import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_state = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_state)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["max_participants"] == 12


def test_signup_and_remove_participant(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    encoded_name = quote(activity_name)

    signup_response = client.post(
        f"/activities/{encoded_name}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200
    assert email in activities[activity_name]["participants"]

    remove_response = client.delete(
        f"/activities/{encoded_name}/participants",
        params={"email": email},
    )
    assert remove_response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_duplicate_signup_returns_400(client):
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    encoded_name = quote(activity_name)

    response = client.post(
        f"/activities/{encoded_name}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_missing_activity_returns_404(client):
    response = client.post(
        "/activities/Does Not Exist/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
