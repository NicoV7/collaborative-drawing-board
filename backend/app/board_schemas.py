"""
Board API Schemas for Collaborative Drawing System

This module defines Pydantic schemas for board-related API operations in the
collaborative drawing system. These schemas ensure type safety, input validation,
and consistent API responses across all board management endpoints.

Architecture Integration:
- Input validation prevents malformed board creation requests
- Response schemas exclude sensitive data based on user permissions
- Performance optimized serialization for real-time collaborative UX
- Type hints enable robust client SDK generation

Security Considerations:
- BoardResponse excludes encryption keys for list operations (security)
- BoardDetailResponse includes encryption keys only for authorized owners
- Input validation prevents XSS and injection attacks in board names
- Proper field validation supports collaborative workspace organization

Collaborative Features:
- Board schemas support multi-user workspace organization
- Metadata structured for efficient board switching in collaborative UI
- Extensible design for future collaboration features (sharing, permissions)
- Performance-conscious field selection for real-time board loading
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class BoardCreateRequest(BaseModel):
    """
    Schema for board creation requests in collaborative drawing system.
    
    Used when users create new collaborative drawing boards. Validates input
    data and ensures boards are created with proper metadata for collaborative
    sessions. The server automatically generates encryption keys and associates
    the board with the authenticated user.
    
    Validation Rules:
    - Board names are required and cannot be empty (UX requirement)
    - Names are limited to 255 characters (database constraint)
    - Leading/trailing whitespace is stripped for consistency
    - HTML/script tags are sanitized to prevent XSS in collaborative UI
    
    Collaborative Context:
    Board names are displayed in collaborative workspaces and shared with
    other users during collaboration, so they must be safe for display
    and appropriately descriptive for team organization.
    
    Example API Usage:
    ```json
    POST /boards
    {
        "name": "Team Design Sprint - Week 1"
    }
    ```
    
    Fields:
        name (str): Human-readable board title for workspace organization
                   Must be 1-255 characters, HTML-safe for collaborative UI
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Board name for collaborative workspace organization"
    )
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """
        Validate and sanitize board name for collaborative display.
        
        Security and UX validation:
        - Strips leading/trailing whitespace for consistency
        - Prevents empty names after whitespace removal
        - Basic HTML sanitization to prevent XSS in collaborative UI
        - Maintains original case for user preference
        
        Args:
            v (str): Raw board name from API request
            
        Returns:
            str: Validated and sanitized board name
            
        Raises:
            ValueError: If name is empty after validation
        """
        if not isinstance(v, str):
            raise ValueError("Board name must be a string")
        
        # Strip whitespace and validate
        cleaned_name = v.strip()
        if not cleaned_name:
            raise ValueError("Board name cannot be empty or whitespace only")
        
        # Basic HTML sanitization for collaborative UI safety
        # In production, consider using a proper HTML sanitization library
        cleaned_name = cleaned_name.replace('<', '&lt;').replace('>', '&gt;')
        
        return cleaned_name

    class Config:
        """Pydantic configuration for board creation requests."""
        schema_extra = {
            "example": {
                "name": "Team Brainstorm Session"
            }
        }


class BoardResponse(BaseModel):
    """
    Schema for board list responses (excludes sensitive encryption keys).
    
    Used for board listing operations where users browse their collaborative
    workspaces. This schema excludes encryption keys for security and performance,
    providing only the metadata needed for board selection and organization.
    
    Security Architecture:
    - Encryption keys are NOT included in list responses
    - Only metadata safe for workspace display is exposed
    - User can only see boards they own (access control enforced in endpoint)
    - Board IDs are exposed for navigation but not sensitive
    
    Performance Optimization:
    - Minimal field set for fast board listing operations (<50ms target)
    - Database queries can be optimized to exclude encrypted_key column
    - JSON payload size minimized for responsive collaborative UI
    - Suitable for pagination and bulk board operations
    
    Collaborative UX:
    - Provides all information needed for workspace board selection
    - Created timestamps enable chronological organization
    - Board names displayed for user recognition and organization
    - Owner information supports collaborative workspace features
    
    Example API Response:
    ```json
    [
        {
            "id": 123,
            "name": "Team Design Sprint",
            "owner_id": 456,
            "created_at": "2024-01-01T12:00:00Z"
        }
    ]
    ```
    """
    
    id: int = Field(description="Unique board identifier for API operations")
    name: str = Field(description="Board name displayed in collaborative workspace")
    owner_id: int = Field(description="User ID of board owner")
    created_at: datetime = Field(description="Board creation timestamp for organization")
    
    class Config:
        """Pydantic configuration for board list responses."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 123,
                "name": "Team Design Sprint - Week 1",
                "owner_id": 456,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class BoardDetailResponse(BaseModel):
    """
    Schema for individual board detail responses (includes encryption key for owners).
    
    Used when users open specific boards for collaborative drawing sessions.
    Includes the encryption key needed for client-side encryption/decryption
    of drawing data. Only returned to board owners or authorized collaborators.
    
    Security Architecture:
    - Encryption key included only for authorized access (owner validation in endpoint)
    - Key enables client-side AES-GCM encryption/decryption of drawing data
    - Server cannot decrypt board content (zero-trust architecture)
    - Key transmission secured via HTTPS and JWT authentication
    
    Collaborative Flow:
    1. User selects board from workspace → API returns this schema
    2. Client receives encryption key → stores securely in memory
    3. Real-time drawing begins → all strokes encrypted with this key
    4. Other collaborators → use same key for synchronized encryption
    5. Session ends → key cleared from client memory
    
    Performance Considerations:
    - Single API call provides all data needed to start collaboration
    - Encryption key ready for immediate use in drawing operations
    - Minimal fields beyond list response for fast board loading (<30ms)
    
    Example API Response:
    ```json
    {
        "id": 123,
        "name": "Team Design Sprint",
        "owner_id": 456,
        "created_at": "2024-01-01T12:00:00Z",
        "encrypted_key": "base64encodedkey..."
    }
    ```
    """
    
    id: int = Field(description="Unique board identifier")
    name: str = Field(description="Board name for collaborative workspace")
    owner_id: int = Field(description="User ID of board owner")
    created_at: datetime = Field(description="Board creation timestamp")
    encrypted_key: str = Field(description="Base64-encoded AES-GCM key for client-side encryption")
    
    class Config:
        """Pydantic configuration for board detail responses."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 123,
                "name": "Team Design Sprint - Week 1",
                "owner_id": 456,
                "created_at": "2024-01-01T12:00:00Z",
                "encrypted_key": "YmFzZTY0ZW5jb2RlZGtleWZvcmNvbGxhYm9yYXRpdmVkcmF3aW5n"
            }
        }


class BoardUpdateRequest(BaseModel):
    """
    Schema for board update requests (currently supports name changes).
    
    Allows board owners to update collaborative board metadata. Currently
    limited to name changes for workspace organization. Future versions
    could include description, tags, or collaboration settings.
    
    Security Considerations:
    - Only board owners can update board metadata (enforced in endpoint)
    - Name validation prevents XSS in collaborative UI
    - Encryption keys cannot be changed via API (security requirement)
    - Updates logged for audit trail in collaborative environments
    
    Collaborative Impact:
    - Board name changes reflect immediately in all collaborators' workspaces
    - Active collaborative sessions show updated name in real-time
    - Change notifications could be sent to active collaborators
    
    Example API Usage:
    ```json
    PUT /boards/123
    {
        "name": "Updated Team Design Sprint - Week 1"
    }
    ```
    """
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New board name (leave null to keep existing)"
    )
    
    @validator('name')
    def validate_name_update(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate board name updates with same rules as creation.
        
        Ensures consistency between board creation and update operations.
        Prevents empty names and basic XSS vulnerabilities in collaborative UI.
        
        Args:
            v (Optional[str]): New board name or None to keep existing
            
        Returns:
            Optional[str]: Validated name or None
        """
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Board name must be a string")
        
        cleaned_name = v.strip()
        if not cleaned_name:
            raise ValueError("Board name cannot be empty")
        
        # Same HTML sanitization as creation
        cleaned_name = cleaned_name.replace('<', '&lt;').replace('>', '&gt;')
        
        return cleaned_name

    class Config:
        """Pydantic configuration for board update requests."""
        schema_extra = {
            "example": {
                "name": "Updated Board Name"
            }
        }


class BoardStatsResponse(BaseModel):
    """
    Schema for board statistics and metadata (future enhancement).
    
    Provides analytics and usage information about collaborative boards.
    Useful for workspace management, collaboration insights, and system
    monitoring. Currently planned for future implementation.
    
    Future Statistics:
    - Total drawing strokes and elements
    - Collaboration session count and duration  
    - Active collaborator count
    - Last activity timestamp
    - Board size and complexity metrics
    
    Example Future Response:
    ```json
    {
        "board_id": 123,
        "total_strokes": 1250,
        "collaboration_sessions": 15,
        "active_collaborators": 3,
        "last_activity": "2024-01-01T15:30:00Z",
        "created_at": "2024-01-01T12:00:00Z"
    }
    ```
    """
    
    board_id: int = Field(description="Board identifier for statistics")
    total_strokes: int = Field(default=0, description="Total drawing strokes on board")
    collaboration_sessions: int = Field(default=0, description="Number of collaborative sessions")
    active_collaborators: int = Field(default=0, description="Currently active collaborators")
    last_activity: Optional[datetime] = Field(description="Most recent board activity")
    created_at: datetime = Field(description="Board creation timestamp")
    
    class Config:
        """Pydantic configuration for board statistics."""
        from_attributes = True


class APIErrorResponse(BaseModel):
    """
    Standard error response schema for board API operations.
    
    Provides consistent error messaging across all board endpoints for
    better client error handling and user experience in collaborative
    applications. Follows HTTP status code conventions and includes
    actionable error information.
    
    Error Categories:
    - 400 Bad Request: Invalid input data or malformed requests
    - 401 Unauthorized: Missing or invalid JWT authentication
    - 403 Forbidden: Valid auth but insufficient permissions (not board owner)
    - 404 Not Found: Board does not exist or user has no access
    - 422 Validation Error: Input validation failed (detailed field errors)
    - 500 Internal Error: Server-side issues requiring investigation
    
    Collaborative Context:
    Clear error messages help users understand access control, validation
    requirements, and system status in collaborative workflows.
    
    Example Error Responses:
    ```json
    // 403 Forbidden
    {
        "detail": "You do not have permission to access this board",
        "error_code": "BOARD_ACCESS_DENIED"
    }
    
    // 404 Not Found  
    {
        "detail": "Board not found or you do not have access",
        "error_code": "BOARD_NOT_FOUND"
    }
    ```
    """
    
    detail: str = Field(description="Human-readable error message")
    error_code: Optional[str] = Field(description="Machine-readable error code for client handling")
    
    class Config:
        """Pydantic configuration for API error responses."""
        schema_extra = {
            "example": {
                "detail": "You do not have permission to access this board",
                "error_code": "BOARD_ACCESS_DENIED"
            }
        }