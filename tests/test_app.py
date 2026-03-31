"""Comprehensive tests for FastAPI High School Management System API."""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        
        # Verify expected activities exist
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Drama Club", "Debate Team", "Science Club"
        ]
        for activity_name in expected_activities:
            assert activity_name in data
    
    def test_activities_have_correct_structure(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_activities_initial_participants(self, client):
        """Test that activities have expected initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Spot check a few activities
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert len(data["Basketball Team"]["participants"]) > 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        """Test successful signup to an activity"""
        email = "newstudent@mergington.edu"
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert email in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Verify student not in Chess Club initially
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify student is now in Chess Club
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup to non-existent activity returns 404"""
        response = client.post("/activities/NonExistent/signup?email=test@example.com")
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_invalid_email(self, client):
        """Test signup with invalid email returns 400"""
        response = client.post("/activities/Chess Club/signup?email=")
        assert response.status_code == 400
        assert "Invalid email" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Test that same student can sign up for multiple activities"""
        email = "newstudent@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify in both
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
    
    def test_signup_preserves_existing_participants(self, client):
        """Test that signup preserves existing participants"""
        email = "newstudent@mergington.edu"
        original_email = "michael@mergington.edu"
        
        # Get original count
        response = client.get("/activities")
        original_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up new student
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify original student still there and count increased
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert original_email in chess_club["participants"]
        assert len(chess_club["participants"]) == original_count + 1


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of participant from activity"""
        email = "michael@mergington.edu"
        response = client.delete(f"/activities/Chess Club/participants/{email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_remove_participant_actually_removes(self, client):
        """Test that removal actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify participant is in Chess Club initially
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Remove
        client.delete(f"/activities/Chess Club/participants/{email}")
        
        # Verify participant is no longer in Chess Club
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_remove_activity_not_found(self, client):
        """Test removal from non-existent activity returns 404"""
        response = client.delete("/activities/NonExistent/participants/test@example.com")
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_remove_participant_not_in_activity(self, client):
        """Test removal of non-existent participant returns 404"""
        email = "notmember@mergington.edu"
        response = client.delete(f"/activities/Chess Club/participants/{email}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
    
    def test_remove_preserves_other_participants(self, client):
        """Test that removing one participant doesn't affect others"""
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Remove one participant
        client.delete(f"/activities/Chess Club/participants/{email_to_remove}")
        
        # Verify other participant is still there
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert email_to_remove not in chess_club["participants"]
        assert email_to_keep in chess_club["participants"]
    
    def test_remove_then_signup_same_student(self, client):
        """Test that student can sign up again after being removed"""
        email = "michael@mergington.edu"
        
        # Remove from Chess Club
        client.delete(f"/activities/Chess Club/participants/{email}")
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up again
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup succeeded
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestHelperFunctions:
    """Direct tests for helper functions."""
    
    def test_find_activity_exists(self):
        """Test finding an existing activity"""
        from src.app import find_activity
        
        activity = find_activity("Chess Club")
        assert activity is not None
        assert "description" in activity
    
    def test_find_activity_not_exists(self):
        """Test finding a non-existent activity returns None"""
        from src.app import find_activity
        
        activity = find_activity("NonExistent")
        assert activity is None
    
    def test_is_valid_email_valid(self):
        """Test valid email validation"""
        from src.app import is_valid_email
        
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("student@mergington.edu") is True
    
    def test_is_valid_email_invalid(self):
        """Test invalid email validation"""
        from src.app import is_valid_email
        
        assert is_valid_email("") is False
        assert is_valid_email("   ") is False
        assert is_valid_email(None) is False
    
    def test_signup_participant_success(self):
        """Test successful participant signup"""
        from src.app import signup_participant
        
        response, status = signup_participant("Art Studio", "newstudent@mergington.edu")
        assert status == 200
        assert "message" in response
    
    def test_signup_participant_activity_not_found(self):
        """Test signup to non-existent activity"""
        from src.app import signup_participant
        
        response, status = signup_participant("NonExistent", "test@example.com")
        assert status == 404
        assert response["detail"] == "Activity not found"
    
    def test_signup_participant_duplicate(self):
        """Test duplicate signup"""
        from src.app import signup_participant
        
        response, status = signup_participant("Chess Club", "michael@mergington.edu")
        assert status == 400
        assert "already signed up" in response["detail"]
    
    def test_remove_participant_success(self):
        """Test successful participant removal"""
        from src.app import remove_participant
        
        response, status = remove_participant("Drama Club", "noah@mergington.edu")
        assert status == 200
        assert "message" in response
    
    def test_remove_participant_activity_not_found(self):
        """Test removal from non-existent activity"""
        from src.app import remove_participant
        
        response, status = remove_participant("NonExistent", "test@example.com")
        assert status == 404
        assert response["detail"] == "Activity not found"
    
    def test_remove_participant_not_found(self):
        """Test removal of non-existent participant"""
        from src.app import remove_participant
        
        response, status = remove_participant("Chess Club", "notmember@example.com")
        assert status == 404
        assert response["detail"] == "Participant not found"
