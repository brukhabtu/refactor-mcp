"""
Sample Python module for testing refactoring operations.

This module contains various Python constructs to test:
- Function definitions and calls
- Class definitions with methods
- Variable assignments
- Lambda expressions
- Nested functions
- Import statements
"""

import os
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


# Global constants
DEFAULT_MAX_SIZE = 100
SUPPORTED_FORMATS = ["json", "xml", "csv"]


# Global variables
current_user = None
session_data = {}


def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user information by ID.
    
    This function demonstrates a simple lookup pattern
    that could be refactored for extraction testing.
    """
    if user_id <= 0:
        return None
    
    # Lambda for validation testing
    is_valid_id = lambda x: x > 0 and x < 1000000
    
    if not is_valid_id(user_id):
        raise ValueError("Invalid user ID")
    
    # Nested function for extraction testing
    def format_user_data(data):
        """Format user data for display."""
        return {
            "id": data.get("id"),
            "name": data.get("name", "Unknown"),
            "email": data.get("email", "")
        }
    
    # Simulate database lookup
    user_data = {"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
    return format_user_data(user_data)


def process_users(user_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Process multiple users.
    
    Contains extractable elements for testing.
    """
    results = []
    
    # Filter function for extraction testing
    valid_users = filter(lambda uid: uid > 0, user_ids)
    
    for user_id in valid_users:
        user_info = get_user_info(user_id)
        if user_info:
            results.append(user_info)
    
    # Sort by name for consistent output
    return sorted(results, key=lambda u: u["name"])


@dataclass
class UserSession:
    """
    User session data class.
    
    Contains methods that can be renamed and extracted.
    """
    user_id: int
    username: str
    is_active: bool = True
    permissions: List[str] = None
    
    def __post_init__(self):
        """Initialize default permissions."""
        if self.permissions is None:
            self.permissions = ["read"]
    
    def add_permission(self, permission: str) -> bool:
        """
        Add a permission to the user.
        
        Method that could be renamed during testing.
        """
        if permission not in self.permissions:
            self.permissions.append(permission)
            return True
        return False
    
    def remove_permission(self, permission: str) -> bool:
        """Remove a permission from the user."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            return True
        return False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def get_display_name(self) -> str:
        """Get formatted display name."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.username} ({status})"


class SessionManager:
    """
    Session management class.
    
    Contains multiple methods for refactoring testing.
    """
    
    def __init__(self):
        self.sessions: Dict[int, UserSession] = {}
        self.max_sessions = DEFAULT_MAX_SIZE
    
    def create_session(self, user_id: int, username: str) -> UserSession:
        """Create a new user session."""
        if len(self.sessions) >= self.max_sessions:
            raise ValueError("Maximum sessions reached")
        
        # Validation lambda for extraction testing
        validate_username = lambda name: len(name) >= 3 and name.isalnum()
        
        if not validate_username(username):
            raise ValueError("Invalid username")
        
        session = UserSession(user_id, username)
        self.sessions[user_id] = session
        return session
    
    def get_session(self, user_id: int) -> Optional[UserSession]:
        """Get session by user ID."""
        return self.sessions.get(user_id)
    
    def end_session(self, user_id: int) -> bool:
        """End a user session."""
        if user_id in self.sessions:
            del self.sessions[user_id]
            return True
        return False
    
    def get_active_sessions(self) -> List[UserSession]:
        """Get all active sessions."""
        # Filter expression for extraction testing
        active_filter = lambda s: s.is_active
        return list(filter(active_filter, self.sessions.values()))
    
    def cleanup_inactive_sessions(self) -> int:
        """Remove inactive sessions and return count."""
        inactive_sessions = [
            user_id for user_id, session in self.sessions.items()
            if not session.is_active
        ]
        
        for user_id in inactive_sessions:
            del self.sessions[user_id]
        
        return len(inactive_sessions)


# Utility functions for testing
def calculate_hash(data: str) -> str:
    """Calculate simple hash of data."""
    return str(hash(data) % 10000)


def format_response(data: Any, format_type: str = "json") -> str:
    """Format response data."""
    if format_type not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {format_type}")
    
    # Format selection logic for extraction testing
    if format_type == "json":
        import json
        return json.dumps(data)
    elif format_type == "xml":
        return f"<data>{data}</data>"
    else:  # csv
        return str(data).replace(" ", ",")


def main():
    """
    Main function demonstrating usage.
    
    Contains various patterns for testing.
    """
    # Create session manager
    manager = SessionManager()
    
    # Create some test sessions
    test_users = [
        (1, "alice"),
        (2, "bob"),
        (3, "charlie")
    ]
    
    # Process users with lambda
    valid_users = list(filter(lambda u: len(u[1]) > 3, test_users))
    
    for user_id, username in valid_users:
        try:
            session = manager.create_session(user_id, username)
            session.add_permission("write")
            print(f"Created session for {session.get_display_name()}")
        except ValueError as e:
            print(f"Error creating session: {e}")
    
    # Get active sessions
    active = manager.get_active_sessions()
    print(f"Active sessions: {len(active)}")
    
    # Cleanup
    cleaned = manager.cleanup_inactive_sessions()
    print(f"Cleaned up {cleaned} inactive sessions")


if __name__ == "__main__":
    main()