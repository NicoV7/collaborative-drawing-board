"""
Board Management Tests - Phase 3 TDD Implementation

This test suite covers the collaborative drawing board management system including:
- Board CRUD operations (Create, Read, Update, Delete)
- Access control and ownership validation
- AES-GCM encryption key generation for end-to-end security
- Performance requirements for low-latency collaborative drawing

Architecture Context:
In the collaborative drawing board application, boards are the core entity that contain:
- Metadata (name, owner, creation date)
- Encrypted drawing data (strokes, shapes, annotations)
- Encryption keys for client-side AES-GCM encryption
- Access control for multi-user collaboration

Performance Requirements:
- POST /boards: <100ms (includes AES-GCM key generation)
- GET /boards: <50ms (user's board list with pagination)
- GET /boards/{id}: <30ms (single board lookup with auth)
- DELETE /boards/{id}: <50ms (cascade delete with cleanup)

Security Considerations:
- All board access requires JWT authentication
- Only board owners can modify/delete boards
- Encryption keys are generated server-side but used client-side
- SQL injection prevention via SQLAlchemy ORM
"""

import pytest
import time
import json
import base64
from typing import Dict, Any


class TestBoardCreation:
    """
    Test board creation functionality including encryption key generation.
    
    These tests verify that the collaborative drawing board system can:
    1. Create new boards with proper metadata
    2. Generate AES-GCM encryption keys for client-side encryption
    3. Associate boards with authenticated users
    4. Enforce performance requirements for real-time collaboration
    """
    
    def test_create_board_with_valid_data(self, client):
        """
        Test creating a new board with valid data and auto-generated encryption key.
        
        Architecture Notes:
        - Each board gets a unique AES-GCM key for end-to-end encryption
        - The key is generated server-side but used client-side only
        - Board ownership is tied to the authenticated JWT user
        - Performance must support real-time collaborative scenarios
        
        Security:
        - Encryption key should be base64-encoded for JSON transport
        - Key generation uses cryptographically secure random sources
        - Only the board owner receives the encryption key
        """
        # Create and authenticate user first
        client.post("/auth/signup", json={
            "email": "boardowner@example.com",
            "username": "boardowner",
            "password": "securepassword123"
        })
        
        login_response = client.post("/auth/login", json={
            "email": "boardowner@example.com",
            "password": "securepassword123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        
        response = client.post("/boards", json={
            "name": "My Collaborative Drawing Board"
        }, headers=headers)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify response structure
        assert response.status_code == 201
        board_data = response.json()
        
        # Validate board metadata
        assert "id" in board_data
        assert "name" in board_data
        assert "owner_id" in board_data
        assert "created_at" in board_data
        assert "encrypted_key" in board_data
        assert board_data["name"] == "My Collaborative Drawing Board"
        
        # Validate encryption key properties
        encrypted_key = board_data["encrypted_key"]
        assert isinstance(encrypted_key, str)
        assert len(encrypted_key) > 0
        
        # Key should be base64-encoded (for AES-GCM key transport)
        try:
            decoded_key = base64.b64decode(encrypted_key)
            # AES-GCM keys should be 32 bytes (256-bit)
            assert len(decoded_key) == 32
        except Exception:
            pytest.fail("Encryption key should be valid base64-encoded 256-bit key")
        
        # Performance requirement: <100ms (includes key generation)
        assert response_time_ms < 100, f"Board creation took {response_time_ms}ms, expected <100ms"
    
    def test_create_board_requires_authentication(self, client):
        """
        Test that board creation requires valid JWT authentication.
        
        Security Architecture:
        - All board operations require authenticated users
        - Prevents anonymous board creation and potential abuse
        - Ensures proper ownership tracking for access control
        """
        response = client.post("/boards", json={
            "name": "Unauthorized Board"
        })
        
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data
    
    def test_create_board_validates_input(self, client):
        """
        Test board creation input validation for security and data integrity.
        
        Validation Requirements:
        - Board name must be provided and non-empty
        - Name length limits prevent database overflow
        - Sanitization prevents XSS in collaborative UI
        """
        # Setup authenticated user
        client.post("/auth/signup", json={
            "email": "validator@example.com",
            "username": "validator",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "validator@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test missing name
        response = client.post("/boards", json={}, headers=headers)
        assert response.status_code == 422
        
        # Test empty name
        response = client.post("/boards", json={
            "name": ""
        }, headers=headers)
        assert response.status_code == 422
        
        # Test name too long (assuming 255 char limit)
        long_name = "x" * 256
        response = client.post("/boards", json={
            "name": long_name
        }, headers=headers)
        assert response.status_code == 422


class TestBoardListing:
    """
    Test board listing functionality for collaborative workspace management.
    
    Architecture Notes:
    - Users can list boards they own or have been granted access to
    - Supports pagination for users with many collaborative boards
    - Includes board metadata but not sensitive encryption keys
    - Optimized queries for low-latency collaborative UX
    """
    
    def test_list_user_boards(self, client):
        """
        Test listing boards owned by authenticated user.
        
        Collaboration Features:
        - Shows all boards user owns for workspace organization
        - Excludes sensitive encryption keys from list view
        - Supports collaborative scenarios where users have many boards
        - Performance optimized for real-time board switching
        """
        # Setup user and create multiple boards
        client.post("/auth/signup", json={
            "email": "listowner@example.com",
            "username": "listowner",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "listowner@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test boards
        board_names = ["Design Mockups", "Team Brainstorm", "Project Planning"]
        for name in board_names:
            client.post("/boards", json={"name": name}, headers=headers)
        
        start_time = time.time()
        
        response = client.get("/boards", headers=headers)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify response structure
        assert response.status_code == 200
        boards_data = response.json()
        
        # Should return list of boards
        assert isinstance(boards_data, list)
        assert len(boards_data) == 3
        
        # Verify board data structure (excluding sensitive encryption keys)
        for board in boards_data:
            assert "id" in board
            assert "name" in board
            assert "owner_id" in board
            assert "created_at" in board
            # Encryption keys should NOT be in list view for security
            assert "encrypted_key" not in board
        
        # Verify board names match created boards
        returned_names = [board["name"] for board in boards_data]
        for name in board_names:
            assert name in returned_names
        
        # Performance requirement: <50ms for board list
        assert response_time_ms < 50, f"Board listing took {response_time_ms}ms, expected <50ms"
    
    def test_list_boards_requires_authentication(self, client):
        """
        Test that board listing requires authentication for security.
        
        Security Rationale:
        - Prevents unauthorized access to board metadata
        - Ensures users only see their own collaborative boards
        - Protects against enumeration of private boards
        """
        response = client.get("/boards")
        assert response.status_code == 401
    
    def test_list_boards_empty_for_new_user(self, client):
        """
        Test that new users have empty board list initially.
        
        User Experience:
        - New users start with clean workspace
        - Confirms proper board ownership isolation
        - Supports onboarding flow for collaborative drawing
        """
        # Create new user without any boards
        client.post("/auth/signup", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "newuser@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/boards", headers=headers)
        
        assert response.status_code == 200
        boards_data = response.json()
        assert isinstance(boards_data, list)
        assert len(boards_data) == 0


class TestBoardRetrieval:
    """
    Test individual board retrieval with access control.
    
    Security Architecture:
    - Only board owners can access full board details
    - Includes encryption key for client-side decryption
    - Prevents unauthorized access to collaborative content
    - Supports real-time collaborative loading scenarios
    """
    
    def test_get_board_by_id_as_owner(self, client):
        """
        Test retrieving board details by ID as the owner.
        
        Collaboration Flow:
        1. User selects board from their workspace
        2. System loads full board metadata including encryption key
        3. Client uses encryption key to decrypt collaborative content
        4. Real-time collaboration session begins
        
        Security:
        - Only owners receive encryption keys
        - Validates JWT token before board access
        - Prevents unauthorized access to collaborative content
        """
        # Setup user and create board
        client.post("/auth/signup", json={
            "email": "getowner@example.com",
            "username": "getowner",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "getowner@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create board
        create_response = client.post("/boards", json={
            "name": "Private Design Board"
        }, headers=headers)
        board_id = create_response.json()["id"]
        
        start_time = time.time()
        
        response = client.get(f"/boards/{board_id}", headers=headers)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify successful retrieval
        assert response.status_code == 200
        board_data = response.json()
        
        # Validate complete board data (including encryption key for owner)
        assert board_data["id"] == board_id
        assert board_data["name"] == "Private Design Board"
        assert "owner_id" in board_data
        assert "created_at" in board_data
        assert "encrypted_key" in board_data  # Key included for owner
        
        # Performance requirement: <30ms for single board lookup
        assert response_time_ms < 30, f"Board retrieval took {response_time_ms}ms, expected <30ms"
    
    def test_get_board_access_denied_for_non_owner(self, client):
        """
        Test access control - non-owners cannot access board details.
        
        Security Requirements:
        - Prevents unauthorized access to collaborative boards
        - Protects encryption keys from unauthorized users
        - Ensures proper isolation between user workspaces
        - Returns 403 Forbidden for non-owners (not 404 to prevent enumeration)
        """
        # Create owner and board
        client.post("/auth/signup", json={
            "email": "owner@example.com",
            "username": "owner",
            "password": "password123"
        })
        owner_login = client.post("/auth/login", json={
            "email": "owner@example.com",
            "password": "password123"
        })
        owner_token = owner_login.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        create_response = client.post("/boards", json={
            "name": "Private Board"
        }, headers=owner_headers)
        board_id = create_response.json()["id"]
        
        # Create different user (non-owner)
        client.post("/auth/signup", json={
            "email": "nonowner@example.com",
            "username": "nonowner",
            "password": "password123"
        })
        nonowner_login = client.post("/auth/login", json={
            "email": "nonowner@example.com",
            "password": "password123"
        })
        nonowner_token = nonowner_login.json()["access_token"]
        nonowner_headers = {"Authorization": f"Bearer {nonowner_token}"}
        
        # Attempt access as non-owner
        response = client.get(f"/boards/{board_id}", headers=nonowner_headers)
        
        assert response.status_code == 403
        error_data = response.json()
        assert "detail" in error_data
        assert "permission" in error_data["detail"].lower()
    
    def test_get_board_not_found(self, client):
        """
        Test retrieval of non-existent board returns 404.
        
        Error Handling:
        - Distinguishes between access denied (403) and not found (404)
        - Provides clear error messages for collaborative UX
        - Prevents information leakage about existing boards
        """
        # Setup authenticated user
        client.post("/auth/signup", json={
            "email": "searcher@example.com",
            "username": "searcher",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "searcher@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Attempt to get non-existent board
        response = client.get("/boards/99999", headers=headers)
        
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
    
    def test_get_board_requires_authentication(self, client):
        """
        Test that board retrieval requires authentication.
        
        Security:
        - All board access requires valid JWT token
        - Prevents anonymous access to collaborative content
        - Maintains consistent security across all board operations
        """
        response = client.get("/boards/1")
        assert response.status_code == 401


class TestBoardDeletion:
    """
    Test board deletion functionality with proper access control.
    
    Collaborative Impact:
    - Permanently removes board and all associated drawing data
    - Cascades to delete all strokes, shapes, and collaborative history
    - Invalidates any active collaborative sessions on the board
    - Requires explicit owner authorization to prevent accidental deletion
    """
    
    def test_delete_board_as_owner(self, client):
        """
        Test successful board deletion by owner.
        
        Deletion Process:
        1. Validate user is board owner
        2. Terminate any active collaborative sessions
        3. Delete all associated drawing data (strokes, annotations)
        4. Remove board metadata
        5. Clean up encryption keys and resources
        
        Performance Considerations:
        - Should complete within reasonable time even for large boards
        - May need background cleanup for boards with extensive history
        """
        # Setup user and create board
        client.post("/auth/signup", json={
            "email": "delowner@example.com",
            "username": "delowner",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "delowner@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create board to delete
        create_response = client.post("/boards", json={
            "name": "Board to Delete"
        }, headers=headers)
        board_id = create_response.json()["id"]
        
        # Verify board exists
        get_response = client.get(f"/boards/{board_id}", headers=headers)
        assert get_response.status_code == 200
        
        start_time = time.time()
        
        # Delete board
        response = client.delete(f"/boards/{board_id}", headers=headers)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Verify successful deletion
        assert response.status_code == 204  # No content for successful deletion
        
        # Verify board no longer exists
        get_response = client.get(f"/boards/{board_id}", headers=headers)
        assert get_response.status_code == 404
        
        # Performance: Should complete reasonably quickly
        assert response_time_ms < 100, f"Board deletion took {response_time_ms}ms, expected <100ms"
    
    def test_delete_board_access_denied_for_non_owner(self, client):
        """
        Test access control - non-owners cannot delete boards.
        
        Security Rationale:
        - Prevents malicious deletion of collaborative work
        - Protects against accidental deletion by collaborators
        - Maintains data integrity in multi-user environments
        - Returns 403 to indicate permission issue (not 404)
        """
        # Create owner and board
        client.post("/auth/signup", json={
            "email": "delowner@example.com",
            "username": "delowner",
            "password": "password123"
        })
        owner_login = client.post("/auth/login", json={
            "email": "delowner@example.com",
            "password": "password123"
        })
        owner_token = owner_login.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        create_response = client.post("/boards", json={
            "name": "Protected Board"
        }, headers=owner_headers)
        board_id = create_response.json()["id"]
        
        # Create different user (potential attacker)
        client.post("/auth/signup", json={
            "email": "attacker@example.com",
            "username": "attacker",
            "password": "password123"
        })
        attacker_login = client.post("/auth/login", json={
            "email": "attacker@example.com",
            "password": "password123"
        })
        attacker_token = attacker_login.json()["access_token"]
        attacker_headers = {"Authorization": f"Bearer {attacker_token}"}
        
        # Attempt unauthorized deletion
        response = client.delete(f"/boards/{board_id}", headers=attacker_headers)
        
        assert response.status_code == 403
        error_data = response.json()
        assert "detail" in error_data
        
        # Verify board still exists
        get_response = client.get(f"/boards/{board_id}", headers=owner_headers)
        assert get_response.status_code == 200
    
    def test_delete_board_not_found(self, client):
        """
        Test deletion of non-existent board returns 404.
        
        Error Handling:
        - Clear distinction between not found vs access denied
        - Consistent error responses across board operations
        - Prevents confusion in collaborative UI error messages
        """
        # Setup authenticated user
        client.post("/auth/signup", json={
            "email": "deleter@example.com",
            "username": "deleter",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "deleter@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Attempt to delete non-existent board
        response = client.delete("/boards/99999", headers=headers)
        
        assert response.status_code == 404
    
    def test_delete_board_requires_authentication(self, client):
        """
        Test that board deletion requires authentication.
        
        Security:
        - Prevents anonymous board deletion
        - Consistent with other board operation security
        - Protects collaborative content from unauthorized access
        """
        response = client.delete("/boards/1")
        assert response.status_code == 401


class TestBoardPerformance:
    """
    Performance tests for board operations in collaborative scenarios.
    
    Performance Requirements Context:
    - Real-time collaboration requires low-latency board operations
    - Users expect instant board switching and loading
    - Multiple concurrent users accessing boards simultaneously
    - Board creation with encryption should not impact user experience
    
    Benchmarking Scenarios:
    - Single user operations (baseline performance)
    - Multiple concurrent operations (scalability testing)
    - Large board datasets (performance under load)
    """
    
    def test_board_operations_performance_targets(self, client):
        """
        Test that all board operations meet performance requirements.
        
        Performance Architecture:
        - Database queries optimized with proper indexing
        - Encryption key generation uses efficient algorithms
        - JWT validation cached to avoid repeated overhead
        - Response sizes minimized for faster network transfer
        
        Collaborative Impact:
        - Fast board switching enables fluid collaborative workflows
        - Low latency reduces friction in real-time drawing sessions
        - Consistent performance supports predictable user experience
        """
        # Setup authenticated user
        client.post("/auth/signup", json={
            "email": "performance@example.com",
            "username": "performance",
            "password": "password123"
        })
        login_response = client.post("/auth/login", json={
            "email": "performance@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test CREATE performance (<100ms)
        create_times = []
        for i in range(5):
            start_time = time.time()
            response = client.post("/boards", json={
                "name": f"Performance Test Board {i}"
            }, headers=headers)
            end_time = time.time()
            
            assert response.status_code == 201
            create_times.append((end_time - start_time) * 1000)
        
        avg_create_time = sum(create_times) / len(create_times)
        max_create_time = max(create_times)
        
        assert max_create_time < 100, f"Board creation max time {max_create_time}ms exceeded 100ms"
        assert avg_create_time < 75, f"Board creation avg time {avg_create_time}ms should be well under limit"
        
        # Test LIST performance (<50ms)
        list_times = []
        for i in range(5):
            start_time = time.time()
            response = client.get("/boards", headers=headers)
            end_time = time.time()
            
            assert response.status_code == 200
            list_times.append((end_time - start_time) * 1000)
        
        avg_list_time = sum(list_times) / len(list_times)
        max_list_time = max(list_times)
        
        assert max_list_time < 50, f"Board listing max time {max_list_time}ms exceeded 50ms"
        assert avg_list_time < 30, f"Board listing avg time {avg_list_time}ms should be well under limit"
        
        # Test GET performance (<30ms) - use first created board
        boards_response = client.get("/boards", headers=headers)
        board_id = boards_response.json()[0]["id"]
        
        get_times = []
        for i in range(5):
            start_time = time.time()
            response = client.get(f"/boards/{board_id}", headers=headers)
            end_time = time.time()
            
            assert response.status_code == 200
            get_times.append((end_time - start_time) * 1000)
        
        avg_get_time = sum(get_times) / len(get_times)
        max_get_time = max(get_times)
        
        assert max_get_time < 30, f"Board retrieval max time {max_get_time}ms exceeded 30ms"
        assert avg_get_time < 20, f"Board retrieval avg time {avg_get_time}ms should be well under limit"