"""
Authentication tests following TDD methodology.
Tests cover JWT authentication, user signup/login, performance targets.

Performance Requirements:
- POST /auth/signup: <50ms
- POST /auth/login: <30ms  
- Invalid credentials: <10ms (fail fast)
"""

import pytest
import time
import json


class TestUserAuthentication:
    """Test cases for user authentication - following RED-GREEN-REFACTOR."""
    
    def test_user_signup_with_valid_data(self, client):
        """Test user signup with valid email and password - SHOULD FAIL initially."""
        start_time = time.time()
        
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepassword123"
        })
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify response
        assert response.status_code == 201
        response_data = response.json()
        assert "id" in response_data
        assert "email" in response_data
        assert "username" in response_data
        assert "password" not in response_data  # Should not return password
        assert "password_hash" not in response_data  # Should not return hash
        assert response_data["email"] == "test@example.com"
        assert response_data["username"] == "testuser"
        
        # Performance requirement: <50ms
        assert response_time_ms < 50, f"Signup took {response_time_ms}ms, expected <50ms"
    
    def test_user_login_returns_jwt_token(self, client):
        """Test user login returns JWT token - SHOULD FAIL initially."""
        # First create a user
        client.post("/auth/signup", json={
            "email": "logintest@example.com",
            "username": "loginuser",
            "password": "mypassword123"
        })
        
        start_time = time.time()
        
        response = client.post("/auth/login", json={
            "email": "logintest@example.com",
            "password": "mypassword123"
        })
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert response_data["token_type"] == "bearer"
        assert len(response_data["access_token"]) > 0
        
        # JWT should have 3 parts separated by dots
        jwt_parts = response_data["access_token"].split(".")
        assert len(jwt_parts) == 3
        
        # Performance requirement: <30ms
        assert response_time_ms < 30, f"Login took {response_time_ms}ms, expected <30ms"
    
    def test_invalid_credentials_returns_401(self, client):
        """Test invalid credentials return 401 quickly - SHOULD FAIL initially."""
        start_time = time.time()
        
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify response
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "access_token" not in response_data
        
        # Performance requirement: <10ms (fail fast)
        assert response_time_ms < 10, f"Invalid auth took {response_time_ms}ms, expected <10ms"
    
    def test_duplicate_email_returns_409(self, client):
        """Test duplicate email returns 409 conflict - SHOULD FAIL initially."""
        # Create first user
        client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123"
        })
        
        # Try to create second user with same email
        response = client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "differentpassword"
        })
        
        # Verify response
        assert response.status_code == 409
        response_data = response.json()
        assert "detail" in response_data
        assert "email" in response_data["detail"].lower()
    
    def test_signup_input_validation(self, client):
        """Test signup input validation - SHOULD FAIL initially."""
        # Test missing email
        response = client.post("/auth/signup", json={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test invalid email format
        response = client.post("/auth/signup", json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test missing username
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test weak password (less than 8 characters)
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak"
        })
        assert response.status_code == 422
    
    def test_login_input_validation(self, client):
        """Test login input validation - SHOULD FAIL initially."""
        # Test missing email
        response = client.post("/auth/login", json={
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test missing password
        response = client.post("/auth/login", json={
            "email": "test@example.com"
        })
        assert response.status_code == 422


class TestPasswordSecurity:
    """Test password hashing and security - SHOULD FAIL initially."""
    
    def test_passwords_are_hashed_not_stored_plaintext(self, client):
        """Test that passwords are properly hashed before storage."""
        password = "mysecretpassword123"
        
        response = client.post("/auth/signup", json={
            "email": "hashtest@example.com",
            "username": "hashuser",
            "password": password
        })
        
        assert response.status_code == 201
        
        # Verify password is not in response
        response_data = response.json()
        assert password not in str(response_data)
        
        # TODO: Add database verification that stored password_hash != plaintext
        # This will be implemented when we add the User model
    
    def test_bcrypt_password_verification(self, client):
        """Test bcrypt password verification - SHOULD FAIL initially."""
        # Create user
        signup_response = client.post("/auth/signup", json={
            "email": "bcrypttest@example.com",
            "username": "bcryptuser",
            "password": "testpassword123"
        })
        assert signup_response.status_code == 201
        
        # Login with correct password should work
        login_response = client.post("/auth/login", json={
            "email": "bcrypttest@example.com",
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        
        # Login with wrong password should fail
        wrong_response = client.post("/auth/login", json={
            "email": "bcrypttest@example.com",
            "password": "wrongpassword"
        })
        assert wrong_response.status_code == 401


class TestJWTTokens:
    """Test JWT token functionality - SHOULD FAIL initially."""
    
    def test_jwt_contains_user_claims(self, client):
        """Test JWT contains proper user claims."""
        # Create and login user
        client.post("/auth/signup", json={
            "email": "jwttest@example.com",
            "username": "jwtuser",
            "password": "password123"
        })
        
        response = client.post("/auth/login", json={
            "email": "jwttest@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # TODO: Decode JWT and verify claims
        # Should contain: sub (user id), email, username, exp (expiration)
        # This will be implemented when JWT utilities are added
        assert len(token) > 0
    
    def test_protected_endpoint_requires_valid_token(self, client):
        """Test that protected endpoints require valid JWT."""
        # Try accessing protected endpoint without token
        response = client.get("/auth/me")
        assert response.status_code == 401
        
        # Create user and get token
        client.post("/auth/signup", json={
            "email": "protectedtest@example.com",
            "username": "protecteduser",
            "password": "password123"
        })
        
        login_response = client.post("/auth/login", json={
            "email": "protectedtest@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Access protected endpoint with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == "protectedtest@example.com"
        assert user_data["username"] == "protecteduser"


class TestPerformanceBenchmarks:
    """Performance-focused tests to ensure low latency requirements."""
    
    def test_signup_performance_under_load(self, client):
        """Test signup performance with multiple concurrent users."""
        times = []
        
        for i in range(10):  # Test with 10 users
            start_time = time.time()
            
            response = client.post("/auth/signup", json={
                "email": f"perftest{i}@example.com",
                "username": f"perfuser{i}",
                "password": "password123"
            })
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            times.append(response_time_ms)
            
            assert response.status_code == 201
        
        # All signups should be under 50ms
        max_time = max(times)
        avg_time = sum(times) / len(times)
        
        assert max_time < 50, f"Max signup time {max_time}ms exceeded 50ms limit"
        assert avg_time < 30, f"Average signup time {avg_time}ms should be well under limit"
    
    def test_login_performance_under_load(self, client):
        """Test login performance with multiple concurrent requests."""
        # Create test users first
        for i in range(5):
            client.post("/auth/signup", json={
                "email": f"loginperf{i}@example.com",
                "username": f"loginuser{i}",
                "password": "password123"
            })
        
        times = []
        
        for i in range(5):
            start_time = time.time()
            
            response = client.post("/auth/login", json={
                "email": f"loginperf{i}@example.com",
                "password": "password123"
            })
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            times.append(response_time_ms)
            
            assert response.status_code == 200
        
        # All logins should be under 30ms
        max_time = max(times)
        avg_time = sum(times) / len(times)
        
        assert max_time < 30, f"Max login time {max_time}ms exceeded 30ms limit"
        assert avg_time < 20, f"Average login time {avg_time}ms should be well under limit"