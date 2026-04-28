import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Original activities data for resetting
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture
def client():
    """Reset the in-memory activities data and provide a test client."""
    global activities
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield TestClient(app)


def test_get_root(client):
    """Test GET / redirects to static index.html."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test GET /activities returns all activities."""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    # Check structure
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert activity["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_success(client):
    """Test successful signup adds participant."""
    response = client.post("/activities/Chess%20Club/signup?email=new@student.edu")
    assert response.status_code == 200
    data = response.json()
    assert "Signed up new@student.edu for Chess Club" == data["message"]
    # Verify added
    response2 = client.get("/activities")
    data2 = response2.json()
    assert "new@student.edu" in data2["Chess Club"]["participants"]


def test_signup_duplicate(client):
    """Test signup fails if already signed up."""
    response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    data = response.json()
    assert "Student already signed up for this activity" == data["detail"]


def test_signup_activity_not_found(client):
    """Test signup fails for non-existent activity."""
    response = client.post("/activities/NonExistent/signup?email=test@test.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" == data["detail"]


def test_delete_success(client):
    """Test successful delete removes participant."""
    response = client.delete("/activities/Chess%20Club/participants/michael@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered michael@mergington.edu from Chess Club" == data["message"]
    # Verify removed
    response2 = client.get("/activities")
    data2 = response2.json()
    assert "michael@mergington.edu" not in data2["Chess Club"]["participants"]


def test_delete_not_signed_up(client):
    """Test delete fails if not signed up."""
    response = client.delete("/activities/Chess%20Club/participants/nonexistent@test.com")
    assert response.status_code == 400
    data = response.json()
    assert "Student not signed up for this activity" == data["detail"]


def test_delete_activity_not_found(client):
    """Test delete fails for non-existent activity."""
    response = client.delete("/activities/NonExistent/participants/test@test.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" == data["detail"]