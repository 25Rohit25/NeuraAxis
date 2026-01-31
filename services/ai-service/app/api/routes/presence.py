"""
NEURAXIS - Presence WebSocket Handler
Real-time presence tracking for collaborative case editing
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.security import ws_get_current_user
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["websocket-presence"])


# =============================================================================
# Data Structures
# =============================================================================


class PresenceUser(BaseModel):
    id: str
    user_id: str
    name: str
    color: str
    section: Optional[str] = None
    cursor: Optional[dict] = None
    last_seen: str


class PresenceManager:
    """Manages presence state for all cases."""

    def __init__(self):
        # case_id -> {user_id -> PresenceUser}
        self.case_presence: Dict[str, Dict[str, PresenceUser]] = {}
        # case_id -> Set[WebSocket]
        self.connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id
        self.socket_users: Dict[WebSocket, str] = {}
        # websocket -> case_id
        self.socket_cases: Dict[WebSocket, str] = {}

        # User colors for presence
        self.colors = [
            "#EF4444",
            "#F59E0B",
            "#10B981",
            "#3B82F6",
            "#8B5CF6",
            "#EC4899",
            "#06B6D4",
            "#84CC16",
            "#F97316",
            "#14B8A6",
            "#6366F1",
            "#A855F7",
        ]

    def get_color(self, user_id: str) -> str:
        """Get consistent color for user."""
        hash_val = sum(ord(c) for c in user_id)
        return self.colors[hash_val % len(self.colors)]

    async def connect(self, websocket: WebSocket, case_id: str, user_id: str, user_name: str):
        """Register a new connection."""
        await websocket.accept()

        # Initialize case structures if needed
        if case_id not in self.case_presence:
            self.case_presence[case_id] = {}
        if case_id not in self.connections:
            self.connections[case_id] = set()

        # Store connection mappings
        self.connections[case_id].add(websocket)
        self.socket_users[websocket] = user_id
        self.socket_cases[websocket] = case_id

        # Create presence entry
        presence = PresenceUser(
            id=str(uuid4()),
            user_id=user_id,
            name=user_name,
            color=self.get_color(user_id),
            last_seen=datetime.now().isoformat(),
        )
        self.case_presence[case_id][user_id] = presence

        # Notify others of new user
        await self.broadcast_to_case(
            case_id, {"type": "user_joined", "user": presence.dict()}, exclude=websocket
        )

        # Send current presence to new user
        await websocket.send_json(
            {
                "type": "presence_update",
                "users": [u.dict() for u in self.case_presence[case_id].values()],
            }
        )

    async def disconnect(self, websocket: WebSocket):
        """Handle disconnection."""
        user_id = self.socket_users.get(websocket)
        case_id = self.socket_cases.get(websocket)

        if case_id and user_id:
            # Remove presence
            if case_id in self.case_presence:
                self.case_presence[case_id].pop(user_id, None)

            # Remove connection
            if case_id in self.connections:
                self.connections[case_id].discard(websocket)
                if not self.connections[case_id]:
                    del self.connections[case_id]
                    del self.case_presence[case_id]

            # Notify others
            await self.broadcast_to_case(case_id, {"type": "user_left", "userId": user_id})

        # Clean up mappings
        self.socket_users.pop(websocket, None)
        self.socket_cases.pop(websocket, None)

    async def update_cursor(
        self, websocket: WebSocket, cursor: dict, section: Optional[str] = None
    ):
        """Update user's cursor position."""
        user_id = self.socket_users.get(websocket)
        case_id = self.socket_cases.get(websocket)

        if case_id and user_id:
            if user_id in self.case_presence.get(case_id, {}):
                presence = self.case_presence[case_id][user_id]
                presence.cursor = cursor
                presence.section = section
                presence.last_seen = datetime.now().isoformat()

                await self.broadcast_to_case(
                    case_id,
                    {
                        "type": "cursor_move",
                        "userId": user_id,
                        "cursor": cursor,
                        "section": section,
                    },
                    exclude=websocket,
                )

    async def update_section(self, websocket: WebSocket, section: str):
        """Update which section user is viewing/editing."""
        user_id = self.socket_users.get(websocket)
        case_id = self.socket_cases.get(websocket)

        if case_id and user_id:
            if user_id in self.case_presence.get(case_id, {}):
                self.case_presence[case_id][user_id].section = section
                self.case_presence[case_id][user_id].last_seen = datetime.now().isoformat()

                await self.broadcast_to_case(
                    case_id,
                    {"type": "section_changed", "userId": user_id, "section": section},
                    exclude=websocket,
                )

    async def heartbeat(self, websocket: WebSocket):
        """Handle heartbeat to keep connection alive."""
        user_id = self.socket_users.get(websocket)
        case_id = self.socket_cases.get(websocket)

        if case_id and user_id:
            if user_id in self.case_presence.get(case_id, {}):
                self.case_presence[case_id][user_id].last_seen = datetime.now().isoformat()

        await websocket.send_json({"type": "pong"})

    async def broadcast_to_case(
        self, case_id: str, message: dict, exclude: Optional[WebSocket] = None
    ):
        """Broadcast message to all users in a case."""
        if case_id not in self.connections:
            return

        disconnected = set()
        for ws in self.connections[case_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except:
                    disconnected.add(ws)

        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)

    def get_case_users(self, case_id: str) -> list:
        """Get all users present in a case."""
        if case_id not in self.case_presence:
            return []
        return [u.dict() for u in self.case_presence[case_id].values()]


# Global presence manager
presence_manager = PresenceManager()


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/presence/{case_id}")
async def presence_websocket(
    websocket: WebSocket,
    case_id: str,
    token: str = Query(None),
):
    """WebSocket endpoint for real-time presence tracking."""

    # Authenticate user
    try:
        user = await ws_get_current_user(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception as e:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_name = f"{user.first_name} {user.last_name}"
    user_id = str(user.id)

    try:
        await presence_manager.connect(websocket, case_id, user_id, user_name)

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60,  # 1 minute timeout
                )

                msg_type = data.get("type")

                if msg_type == "heartbeat":
                    await presence_manager.heartbeat(websocket)

                elif msg_type == "cursor_move":
                    await presence_manager.update_cursor(
                        websocket, data.get("cursor", {}), data.get("section")
                    )

                elif msg_type == "section_focus":
                    await presence_manager.update_section(websocket, data.get("section", ""))

                elif msg_type == "join":
                    # Already handled in connect, but can update color
                    pass

            except asyncio.TimeoutError:
                # Send ping on timeout
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Presence WS error: {e}")
    finally:
        await presence_manager.disconnect(websocket)


# =============================================================================
# Collaborative Document WebSocket (Y.js compatible)
# =============================================================================


class CollaborativeDocManager:
    """Manages collaborative document sessions."""

    def __init__(self):
        # doc_id -> Set[WebSocket]
        self.doc_connections: Dict[str, Set[WebSocket]] = {}
        # doc_id -> Y.js document state (would be actual Y.Doc in production)
        self.doc_states: Dict[str, bytes] = {}

    async def connect(self, websocket: WebSocket, doc_id: str):
        """Connect to collaborative document."""
        await websocket.accept()

        if doc_id not in self.doc_connections:
            self.doc_connections[doc_id] = set()
        self.doc_connections[doc_id].add(websocket)

        # Send current document state if exists
        if doc_id in self.doc_states:
            await websocket.send_bytes(self.doc_states[doc_id])

    async def disconnect(self, websocket: WebSocket, doc_id: str):
        """Disconnect from collaborative document."""
        if doc_id in self.doc_connections:
            self.doc_connections[doc_id].discard(websocket)
            if not self.doc_connections[doc_id]:
                del self.doc_connections[doc_id]

    async def handle_update(self, websocket: WebSocket, doc_id: str, update: bytes):
        """Handle document update from client."""
        # Store update (in production, would merge with Y.Doc)
        if doc_id not in self.doc_states:
            self.doc_states[doc_id] = update
        else:
            # Would use Y.mergeUpdates in production
            self.doc_states[doc_id] = update

        # Broadcast to other clients
        if doc_id in self.doc_connections:
            disconnected = set()
            for ws in self.doc_connections[doc_id]:
                if ws != websocket:
                    try:
                        await ws.send_bytes(update)
                    except:
                        disconnected.add(ws)

            for ws in disconnected:
                await self.disconnect(ws, doc_id)


collab_manager = CollaborativeDocManager()


@router.websocket("/collab/{doc_id}")
async def collab_websocket(
    websocket: WebSocket,
    doc_id: str,
    token: str = Query(None),
):
    """
    WebSocket endpoint for collaborative document editing.
    Compatible with y-websocket protocol for Y.js integration.
    """

    # Authenticate
    try:
        user = await ws_get_current_user(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    try:
        await collab_manager.connect(websocket, doc_id)

        while True:
            try:
                # Receive binary Y.js updates
                data = await websocket.receive_bytes()
                await collab_manager.handle_update(websocket, doc_id, data)
            except:
                break

    except WebSocketDisconnect:
        pass
    finally:
        await collab_manager.disconnect(websocket, doc_id)


# =============================================================================
# REST Endpoints for Presence
# =============================================================================


@router.get("/presence/{case_id}/users")
async def get_presence_users(case_id: str):
    """Get all users currently viewing a case."""
    return {"users": presence_manager.get_case_users(case_id)}
