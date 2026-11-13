"""
SPECTRA-X / Planet X Interactive Observatory
SessionManager — Cryptographically Isolated Ephemeral Sessions
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Features:
1. Cryptographically secure UUID session generation (uuid4).
2. Ephemeral session state isolation (dataset mode, targets, uploads, reviews, results).
3. Session scratch directory isolation at: scratch/sessions/<session_id>/
4. Configurable TTL (default: 7200 seconds / 2 hours) with automatic reaping.
5. Path-traversal defense and safe directory deletion (strictly bounded to scratch/sessions/).
6. Thread-safe operations via reentrant locking.
"""

import os
import sys
import time
import uuid
import shutil
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger("observatory.session_manager")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_SESSIONS_DIR = os.path.join(BASE_DIR, "scratch", "sessions")
DEFAULT_SESSION_TTL_SECONDS = 7200.0  # 2 hours


@dataclass
class SessionState:
    """Represents isolated state for a single user analysis session."""
    session_id: str
    created_at: float
    last_accessed: float
    ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS
    dataset_mode: str = "EMPTY"  # "EMPTY" | "SAMPLE" | "USER_UPLOAD"
    sample_pair_id: Optional[str] = None
    target_coordinates: Optional[Dict[str, float]] = None
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    session_dir: str = ""

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Determines if session has exceeded its time-to-live threshold."""
        now = current_time if current_time is not None else time.time()
        return (now - self.last_accessed) > self.ttl_seconds

    def touch(self, current_time: Optional[float] = None) -> None:
        """Updates last_accessed timestamp to keep session alive."""
        self.last_accessed = current_time if current_time is not None else time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes public session metadata for API responses."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "ttl_seconds": self.ttl_seconds,
            "expires_in_seconds": max(0.0, self.ttl_seconds - (time.time() - self.last_accessed)),
            "dataset_mode": self.dataset_mode,
            "sample_pair_id": self.sample_pair_id,
            "target_coordinates": self.target_coordinates,
            "uploaded_files_count": len(self.uploaded_files),
            "candidates_count": len(self.candidates),
            "selected_candidate_id": self.selected_candidate_id,
            "reviews_count": len(self.reviews),
            "has_analysis_results": bool(self.analysis_results),
            "session_dir": self.session_dir
        }


class SessionManager:
    """
    Thread-safe session manager providing isolated storage and automatic TTL reaping.
    Guarantees no state leakage across independent user sessions.
    """

    def __init__(
        self,
        sessions_dir: str = DEFAULT_SESSIONS_DIR,
        default_ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS
    ):
        self._sessions_dir = os.path.abspath(sessions_dir)
        self._default_ttl = float(default_ttl_seconds)
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.RLock()

        os.makedirs(self._sessions_dir, exist_ok=True)

    @property
    def sessions_dir(self) -> str:
        return self._sessions_dir

    def create_session(self) -> SessionState:
        """
        Creates a new isolated session with a cryptographically secure UUID.
        Initializes an empty session directory under scratch/sessions/<session_id>/.
        """
        with self._lock:
            # Periodically reap expired sessions
            self.cleanup_expired_sessions()

            session_id = str(uuid.uuid4())
            session_path = os.path.join(self._sessions_dir, session_id)
            os.makedirs(session_path, exist_ok=True)

            now = time.time()
            session = SessionState(
                session_id=session_id,
                created_at=now,
                last_accessed=now,
                ttl_seconds=self._default_ttl,
                dataset_mode="EMPTY",
                session_dir=session_path
            )

            self._sessions[session_id] = session
            logger.info("Created session %s at %s", session_id, session_path)
            return session

    def get_session(self, session_id: Optional[str], auto_touch: bool = True) -> Optional[SessionState]:
        """
        Retrieves active session state by UUID.
        Returns None if session_id is None, invalid, missing, or expired.
        """
        if not session_id or not isinstance(session_id, str):
            return None

        clean_id = session_id.strip()
        with self._lock:
            session = self._sessions.get(clean_id)
            if session is None:
                return None

            now = time.time()
            if session.is_expired(now):
                logger.info("Session %s expired (TTL %ss exceeded). Reaping.", clean_id, session.ttl_seconds)
                self._destroy_session(clean_id)
                return None

            if auto_touch:
                session.touch(now)

            return session

    def reset_session(self, session_id: str) -> bool:
        """
        Resets an active session back to EMPTY workspace state and purges scratch files.
        Retains the session ID and touches last_accessed.
        """
        if not session_id or not isinstance(session_id, str):
            return False

        with self._lock:
            session = self.get_session(session_id, auto_touch=True)
            if session is None:
                return False

            # Purge scratch files inside session_dir safely
            self._purge_session_dir_contents(session.session_dir)

            session.dataset_mode = "EMPTY"
            session.sample_pair_id = None
            session.target_coordinates = None
            session.uploaded_files.clear()
            session.candidates.clear()
            session.selected_candidate_id = None
            session.reviews.clear()
            session.analysis_results.clear()
            session.touch()

            logger.info("Reset session %s to EMPTY state", session_id)
            return True

    def delete_session(self, session_id: str) -> bool:
        """Terminates session immediately and permanently removes scratch directory."""
        if not session_id or not isinstance(session_id, str):
            return False

        with self._lock:
            return self._destroy_session(session_id.strip())

    def cleanup_expired_sessions(self) -> int:
        """
        Scans all registered sessions and purges those past their TTL.
        Also sweeps unindexed orphan directories in scratch/sessions/.
        Returns the number of sessions cleaned up.
        """
        reaped_count = 0
        now = time.time()

        with self._lock:
            expired_ids = [
                s_id for s_id, s in self._sessions.items()
                if s.is_expired(now)
            ]
            for s_id in expired_ids:
                if self._destroy_session(s_id):
                    reaped_count += 1

            # Sweep orphan folders in sessions_dir older than TTL
            try:
                if os.path.exists(self._sessions_dir):
                    for entry in os.listdir(self._sessions_dir):
                        entry_path = os.path.join(self._sessions_dir, entry)
                        if os.path.isdir(entry_path) and entry not in self._sessions:
                            # Check age of directory
                            mtime = os.path.getmtime(entry_path)
                            if (now - mtime) > self._default_ttl:
                                self._safe_delete_session_path(entry_path)
                                reaped_count += 1
            except Exception as e:
                logger.warning("Error sweeping orphan sessions: %s", e)

        return reaped_count

    def get_active_session_count(self) -> int:
        """Returns total active non-expired sessions."""
        with self._lock:
            return len(self._sessions)

    def _destroy_session(self, session_id: str) -> bool:
        """Internal helper to remove session from dictionary and delete directory."""
        session = self._sessions.pop(session_id, None)
        if session is not None:
            self._safe_delete_session_path(session.session_dir)
            return True
        return False

    def _purge_session_dir_contents(self, path: str) -> None:
        """Removes all files and subdirectories inside path without deleting path itself."""
        if not self._is_safe_session_path(path) or not os.path.exists(path):
            return
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except Exception as e:
                logger.warning("Failed purging %s: %s", item_path, e)

    def _safe_delete_session_path(self, path: str) -> None:
        """
        Safely deletes a session directory.
        Defensive security check: Enforces that path is strictly a subfolder of self._sessions_dir.
        """
        if not self._is_safe_session_path(path):
            logger.error("Security violation: Refusing to delete non-session path: %s", path)
            return

        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
                logger.debug("Successfully removed session directory: %s", path)
            except Exception as e:
                logger.warning("Failed deleting session path %s: %s", path, e)

    def _is_safe_session_path(self, path: str) -> bool:
        """Validates that path is strictly within the allowed sessions directory."""
        if not path:
            return False
        abs_target = os.path.abspath(path)
        abs_root = self._sessions_dir

        # Target must be strictly inside sessions_dir, not root itself
        return abs_target.startswith(abs_root + os.sep) and abs_target != abs_root

