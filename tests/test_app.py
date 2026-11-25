from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_given_root_request_when_requested_then_redirects_to_index(client):
    # Given the FastAPI application is available.
    # When the root path is requested without following redirects.
    response = client.get("/", follow_redirects=False)

    # Then the browser is redirected to the static index page.
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_given_seeded_activities_when_listing_then_returns_participants(client):
    # Given the activity list has its seeded contents.
    # When the activities endpoint is requested.
    response = client.get("/activities")

    # Then the activities and their participants are returned.
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert response.json()["Soccer Club"]["participants"] == []


def test_given_valid_activity_when_signing_up_then_adds_participant(client):
    # Given a valid activity and a student who is not signed up.
    activity = "Soccer Club"
    email = "student@example.com"

    # When the student signs up.
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Then signup succeeds and the participant appears in the activity.
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"
    assert email in client.get("/activities").json()[activity]["participants"]


def test_given_existing_signup_when_signing_up_again_then_returns_conflict(client):
    # Given a student is already signed up for Chess Club.
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # When that student attempts to sign up again.
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Then the API rejects the duplicate signup.
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_given_unknown_activity_when_signing_up_then_returns_not_found(client):
    # Given an activity that does not exist.
    # When a student attempts to sign up for it.
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    # Then the API reports that the activity was not found.
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_given_registered_participant_when_unregistering_then_removes_participant(client):
    # Given a student registered for Chess Club.
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # When the student is unregistered.
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Then the API confirms removal and the activity no longer lists the student.
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity}"
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_given_unregistered_participant_when_unregistering_then_returns_not_found(client):
    # Given a valid activity and a student not registered for it.
    # When the student is unregistered.
    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    # Then the API reports that the student was not signed up.
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_given_unknown_activity_when_unregistering_then_returns_not_found(client):
    # Given an activity that does not exist.
    # When a student is unregistered from it.
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    # Then the API reports that the activity was not found.
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
