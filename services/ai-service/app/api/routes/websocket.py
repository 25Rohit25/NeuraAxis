"""
NEURAXIS - WebSocket Events for Real-time Case Updates
WebSocket handler for case notifications and live updates
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["websocket"])


# =============================================================================
# Connection Manager
# =============================================================================


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # user_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # All connections for broadcast
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.all_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        self.all_connections.discard(websocket)

    async def send_personal(self, user_id: str, message: dict):
        """Send message to a specific user's connections."""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict, exclude_user: str = None):
        """Broadcast message to all connected clients."""
        disconnected = []

        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.all_connections.discard(conn)


# Global connection manager
manager = ConnectionManager()


# =============================================================================
# Event Types
# =============================================================================


class CaseEvent(BaseModel):
    type: str  # case_created, case_updated, case_assigned, etc.
    case_id: str
    case_number: str
    data: dict
    triggered_by: dict
    timestamp: str


class CaseNotification(BaseModel):
    id: str
    type: str
    title: str
    message: str
    case_id: str
    case_number: str
    read: bool = False
    created_at: str


# =============================================================================
# Event Broadcasting Functions
# =============================================================================


async def broadcast_case_event(
    event_type: str,
    case_id: str,
    case_number: str,
    data: dict,
    triggered_by_id: str,
    triggered_by_name: str,
    target_user_ids: list = None,
):
    """Broadcast a case event to relevant users."""

    event = {
        "type": "case_event",
        "payload": {
            "type": event_type,
            "case_id": case_id,
            "case_number": case_number,
            "data": data,
            "triggered_by": {
                "id": triggered_by_id,
                "name": triggered_by_name,
            },
            "timestamp": datetime.now().isoformat(),
        },
    }

    if target_user_ids:
        # Send to specific users
        for user_id in target_user_ids:
            await manager.send_personal(user_id, event)
    else:
        # Broadcast to all
        await manager.broadcast(event, exclude_user=triggered_by_id)


async def send_notification(
    user_id: str,
    event_type: str,
    title: str,
    message: str,
    case_id: str,
    case_number: str,
):
    """Send a notification to a specific user."""

    notification = {
        "type": "notification",
        "payload": {
            "id": str(uuid4()),
            "type": event_type,
            "title": title,
            "message": message,
            "case_id": case_id,
            "case_number": case_number,
            "read": False,
            "created_at": datetime.now().isoformat(),
        },
    }

    await manager.send_personal(user_id, notification)


# =============================================================================
# Case Event Helpers
# =============================================================================


async def notify_case_created(
    case_id: str,
    case_number: str,
    patient_name: str,
    assigned_to_id: str,
    created_by_id: str,
    created_by_name: str,
):
    """Notify about new case creation."""

    # Send event
    await broadcast_case_event(
        event_type="case_created",
        case_id=case_id,
        case_number=case_number,
        data={"patient_name": patient_name},
        triggered_by_id=created_by_id,
        triggered_by_name=created_by_name,
    )

    # Notify assigned doctor
    if assigned_to_id and assigned_to_id != created_by_id:
        await send_notification(
            user_id=assigned_to_id,
            event_type="case_assigned",
            title="New Case Assigned",
            message=f"You have been assigned a new case for {patient_name}",
            case_id=case_id,
            case_number=case_number,
        )


async def notify_case_assigned(
    case_id: str,
    case_number: str,
    patient_name: str,
    new_assignee_id: str,
    old_assignee_id: str,
    assigned_by_id: str,
    assigned_by_name: str,
):
    """Notify about case assignment change."""

    # Broadcast event
    await broadcast_case_event(
        event_type="case_assigned",
        case_id=case_id,
        case_number=case_number,
        data={
            "patient_name": patient_name,
            "new_assignee_id": new_assignee_id,
            "old_assignee_id": old_assignee_id,
        },
        triggered_by_id=assigned_by_id,
        triggered_by_name=assigned_by_name,
    )

    # Notify new assignee
    await send_notification(
        user_id=new_assignee_id,
        event_type="case_assigned",
        title="Case Assigned to You",
        message=f"Case {case_number} for {patient_name} has been assigned to you",
        case_id=case_id,
        case_number=case_number,
    )

    # Notify old assignee if different
    if old_assignee_id and old_assignee_id != new_assignee_id:
        await send_notification(
            user_id=old_assignee_id,
            event_type="case_assigned",
            title="Case Reassigned",
            message=f"Case {case_number} has been reassigned to another doctor",
            case_id=case_id,
            case_number=case_number,
        )


async def notify_case_status_changed(
    case_id: str,
    case_number: str,
    patient_name: str,
    old_status: str,
    new_status: str,
    changed_by_id: str,
    changed_by_name: str,
    assigned_to_id: str = None,
):
    """Notify about case status change."""

    # Broadcast event
    await broadcast_case_event(
        event_type="case_status_changed",
        case_id=case_id,
        case_number=case_number,
        data={
            "patient_name": patient_name,
            "old_status": old_status,
            "new_status": new_status,
        },
        triggered_by_id=changed_by_id,
        triggered_by_name=changed_by_name,
    )

    # Notify assigned doctor if not the one who changed it
    if assigned_to_id and assigned_to_id != changed_by_id:
        status_labels = {
            "pending": "Pending",
            "in_progress": "In Progress",
            "review": "Under Review",
            "completed": "Completed",
            "archived": "Archived",
        }

        await send_notification(
            user_id=assigned_to_id,
            event_type="case_status_changed",
            title=f"Case Status: {status_labels.get(new_status, new_status)}",
            message=f"Case {case_number} status changed to {status_labels.get(new_status, new_status)}",
            case_id=case_id,
            case_number=case_number,
        )


async def notify_case_priority_changed(
    case_id: str,
    case_number: str,
    patient_name: str,
    old_priority: str,
    new_priority: str,
    changed_by_id: str,
    changed_by_name: str,
    assigned_to_id: str = None,
):
    """Notify about case priority change."""

    # Broadcast event
    await broadcast_case_event(
        event_type="case_priority_changed",
        case_id=case_id,
        case_number=case_number,
        data={
            "patient_name": patient_name,
            "old_priority": old_priority,
            "new_priority": new_priority,
        },
        triggered_by_id=changed_by_id,
        triggered_by_name=changed_by_name,
    )

    # Notify assigned doctor for high/critical priority
    if assigned_to_id and assigned_to_id != changed_by_id:
        if new_priority in ["high", "critical"]:
            priority_labels = {
                "critical": "🚨 Critical",
                "high": "⚠️ High Priority",
            }

            await send_notification(
                user_id=assigned_to_id,
                event_type="case_priority_changed",
                title=f"Priority Escalation: {priority_labels.get(new_priority, new_priority)}",
                message=f"Case {case_number} has been marked as {new_priority} priority",
                case_id=case_id,
                case_number=case_number,
            )


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/ws/cases")
async def websocket_cases(websocket: WebSocket):
    """WebSocket endpoint for real-time case updates."""

    # TODO: Authenticate user from token
    # For now, use a placeholder user ID
    user_id = "00000000-0000-0000-0000-000000000001"

    await manager.connect(websocket, user_id)

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "message": "Connected to case updates",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong, subscriptions, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0,  # Send ping every 30 seconds
                )

                # Handle incoming messages
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data.get("type") == "subscribe":
                    # Subscribe to specific case updates
                    case_id = data.get("case_id")
                    if case_id:
                        await websocket.send_json(
                            {
                                "type": "subscribed",
                                "case_id": case_id,
                            }
                        )

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint specifically for notifications."""

    # TODO: Authenticate user from token
    user_id = "00000000-0000-0000-0000-000000000001"

    await manager.connect(websocket, user_id)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "channel": "notifications",
            }
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

                if data.get("type") == "mark_read":
                    notification_id = data.get("notification_id")
                    # Would update notification read status in DB
                    await websocket.send_json(
                        {
                            "type": "notification_read",
                            "notification_id": notification_id,
                        }
                    )

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)
