"""
Session Store

In-memory storage for project sessions.
For hackathon: one project per session.
For production: replace with Redis + session tokens.
"""

from typing import Dict, Optional
from datetime import datetime
from threading import Lock

from app.domain.models import ProjectState


class Session:
    """Single project session."""
    
    def __init__(self, session_id: str, project_state: ProjectState):
        self.session_id = session_id
        self.project_state = project_state
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.descoped_item_ids = set()  # For scope change tracking
    
    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed = datetime.utcnow()


class SessionStore:
    """Thread-safe in-memory session storage."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize store."""
        if self._initialized:
            return
        self._sessions: Dict[str, Session] = {}
        self._lock = Lock()
        self._initialized = True
    
    def create_session(self, project_state: ProjectState) -> str:
        """
        Create a new session for a project.
        
        Args:
            project_state: ProjectState to store
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = project_state.project_id
        session = Session(session_id, project_state)
        
        with self._lock:
            self._sessions[session_id] = session
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session
    
    def get_project_state(self, session_id: str) -> Optional[ProjectState]:
        """
        Retrieve project state from session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ProjectState or None if not found
        """
        session = self.get_session(session_id)
        return session.project_state if session else None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def list_sessions(self) -> list:
        """
        List all active sessions.
        
        Returns:
            List of (session_id, project_name) tuples
        """
        with self._lock:
            return [
                (sid, s.project_state.project_info.project_name)
                for sid, s in self._sessions.items()
            ]
    
    def clear_all(self) -> None:
        """Clear all sessions (for testing)."""
        with self._lock:
            self._sessions.clear()


# Global singleton instance
store = SessionStore()
