"""
NEURAXIS - Session Management Service
======================================
Redis-based session management with security features.
"""

import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# Session configuration
SESSION_TTL_HOURS = 24
MAX_SESSIONS_PER_USER = 5


@dataclass
class Session:
    """User session data."""

    id: str
    user_id: str
    organization_id: str
    email: str
    role: str
    ip_address: str
    user_agent: str
    created_at: str
    last_activity_at: str
    expires_at: str
    is_mfa_verified: bool = False
    refresh_token_hash: Optional[str] = None


class SessionManager:
    """Redis-based session manager."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "neuraxis:session:"
        self.user_sessions_prefix = "neuraxis:user_sessions:"

    def _session_key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        return f"{self.user_sessions_prefix}{user_id}"

    async def create_session(
        self,
        user_id: str | UUID,
        organization_id: str | UUID,
        email: str,
        role: str,
        ip_address: str,
        user_agent: str,
        refresh_token: Optional[str] = None,
    ) -> Session:
        """Create a new session."""
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=SESSION_TTL_HOURS)

        session = Session(
            id=session_id,
            user_id=str(user_id),
            organization_id=str(organization_id),
            email=email,
            role=role,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",
            created_at=now.isoformat(),
            last_activity_at=now.isoformat(),
            expires_at=expires.isoformat(),
            refresh_token_hash=self._hash_token(refresh_token) if refresh_token else None,
        )

        # Store session
        await self.redis.setex(
            self._session_key(session_id),
            SESSION_TTL_HOURS * 3600,
            json.dumps(asdict(session)),
        )

        # Track user's sessions
        await self.redis.sadd(self._user_sessions_key(str(user_id)), session_id)

        # Enforce max sessions
        await self._enforce_max_sessions(str(user_id))

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        data = await self.redis.get(self._session_key(session_id))
        if not data:
            return None
        return Session(**json.loads(data))

    async def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.last_activity_at = datetime.now(timezone.utc).isoformat()
        ttl = await self.redis.ttl(self._session_key(session_id))
        if ttl > 0:
            await self.redis.setex(
                self._session_key(session_id),
                ttl,
                json.dumps(asdict(session)),
            )
        return True

    async def set_mfa_verified(self, session_id: str) -> bool:
        """Mark session as MFA verified."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.is_mfa_verified = True
        ttl = await self.redis.ttl(self._session_key(session_id))
        if ttl > 0:
            await self.redis.setex(
                self._session_key(session_id),
                ttl,
                json.dumps(asdict(session)),
            )
        return True

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        session = await self.get_session(session_id)
        if session:
            await self.redis.srem(self._user_sessions_key(session.user_id), session_id)
        return bool(await self.redis.delete(self._session_key(session_id)))

    async def revoke_all_user_sessions(
        self, user_id: str, except_session: Optional[str] = None
    ) -> int:
        """Revoke all sessions for a user."""
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))
        count = 0
        for sid in session_ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            if sid_str != except_session:
                await self.redis.delete(self._session_key(sid_str))
                count += 1
        if except_session:
            await self.redis.delete(self._user_sessions_key(user_id))
            await self.redis.sadd(self._user_sessions_key(user_id), except_session)
        else:
            await self.redis.delete(self._user_sessions_key(user_id))
        return count

    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user."""
        session_ids = await self.redis.smembers(self._user_sessions_key(user_id))
        sessions = []
        for sid in session_ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            session = await self.get_session(sid_str)
            if session:
                sessions.append(session)
        return sessions

    async def _enforce_max_sessions(self, user_id: str):
        """Remove oldest sessions if exceeding limit."""
        sessions = await self.get_user_sessions(user_id)
        if len(sessions) > MAX_SESSIONS_PER_USER:
            sorted_sessions = sorted(sessions, key=lambda s: s.created_at)
            for session in sorted_sessions[:-MAX_SESSIONS_PER_USER]:
                await self.revoke_session(session.id)

    @staticmethod
    def _hash_token(token: str) -> str:
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()


# Lockout management
class LockoutManager:
    """Account lockout management."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "neuraxis:lockout:"
        self.max_attempts = 5
        self.lockout_minutes = 30

    async def record_failed_attempt(self, email: str) -> tuple[int, bool]:
        """Record failed login. Returns (attempts, is_locked)."""
        key = f"{self.prefix}{email}"
        attempts = await self.redis.incr(key)
        if attempts == 1:
            await self.redis.expire(key, self.lockout_minutes * 60)
        is_locked = attempts >= self.max_attempts
        return attempts, is_locked

    async def is_locked(self, email: str) -> tuple[bool, int]:
        """Check if account is locked. Returns (is_locked, remaining_seconds)."""
        key = f"{self.prefix}{email}"
        attempts = await self.redis.get(key)
        if not attempts or int(attempts) < self.max_attempts:
            return False, 0
        ttl = await self.redis.ttl(key)
        return True, max(0, ttl)

    async def reset_attempts(self, email: str):
        """Reset failed attempts after successful login."""
        await self.redis.delete(f"{self.prefix}{email}")

    async def get_attempts(self, email: str) -> int:
        """Get current failed attempts count."""
        val = await self.redis.get(f"{self.prefix}{email}")
        return int(val) if val else 0
