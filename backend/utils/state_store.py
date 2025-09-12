import secrets
import time
from typing import Dict


class StateStore:
    """Simple in-memory state store for OAuth flow"""

    def __init__(self):
        self._store: Dict[str, float] = {}
        self._cleanup_threshold = 600  # 10 minutes

    def generate_state(self) -> str:
        """Generate a random state string and store it"""
        state = secrets.token_urlsafe(32)
        self._store[state] = time.time()
        self._cleanup_expired()
        return state

    def validate_state(self, state: str) -> bool:
        """Validate and consume a state string"""
        if state not in self._store:
            return False

        # Check if state is expired (10 minutes)
        if time.time() - self._store[state] > self._cleanup_threshold:
            del self._store[state]
            return False

        # Remove state after validation (one-time use)
        del self._store[state]
        return True

    def _cleanup_expired(self):
        """Remove expired states"""
        current_time = time.time()
        expired_states = [
            state
            for state, timestamp in self._store.items()
            if current_time - timestamp > self._cleanup_threshold
        ]
        for state in expired_states:
            del self._store[state]


# Global state store instance
oauth_state_store = StateStore()
