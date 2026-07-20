"""
Conversation routes — create, list, get, delete conversations and messages.

Allows anonymous access for the public beta — conversations are stored
with a session-level user ID when no auth token is provided.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from api.dependencies import optional_user
from api.services.conversation import ConversationManager
from api.exceptions import NotFoundError

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
manager = ConversationManager()


def _get_user_id(request: Request, current_user: dict | None) -> str:
    """Extract user ID from auth or fall back to IP-based anonymous ID."""
    if current_user and current_user.get("sub"):
        return current_user["sub"]
    # Use client IP as anonymous user identifier
    client_ip = request.client.host if request.client else "anonymous"
    return f"anon-{client_ip}"


class CreateConversationRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    model: str = Field(default="gpt-4o-mini")


class AddMessageRequest(BaseModel):
    role: str = Field(..., pattern=r"^(system|user|assistant|tool)$")
    content: str = Field(..., min_length=1)
    token_count: int = Field(default=0, ge=0)


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    token_count: int = 0


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    model: str
    created_at: str
    updated_at: str
    message_count: int = 0
    messages: list[MessageResponse] = []


class ConversationListItem(BaseModel):
    id: str
    title: str
    model: str
    created_at: str
    updated_at: str
    message_count: int = 0


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: Request,
    body: CreateConversationRequest,
    current_user: dict | None = Depends(optional_user),
):
    """Create a new conversation."""
    user_id = _get_user_id(request, current_user)
    conv = manager.create_conversation(
        user_id=user_id,
        title=body.title,
        model=body.model,
    )
    return ConversationResponse(**conv)


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict | None = Depends(optional_user),
):
    """List conversations for the current user."""
    user_id = _get_user_id(request, current_user)
    convs = manager.list_conversations(user_id, limit=limit, offset=offset)
    return [ConversationListItem(**c) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: dict | None = Depends(optional_user),
):
    """Get a conversation with all messages."""
    conv = manager.get_conversation(conversation_id)
    if not conv:
        raise NotFoundError(message=f"Conversation '{conversation_id}' not found")
    return ConversationResponse(**conv)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    conversation_id: str,
    body: AddMessageRequest,
    current_user: dict | None = Depends(optional_user),
):
    """Add a message to a conversation."""
    conv = manager.get_conversation(conversation_id)
    if not conv:
        raise NotFoundError(message=f"Conversation '{conversation_id}' not found")
    msg = manager.add_message(conversation_id, body.role, body.content, token_count=body.token_count)
    return MessageResponse(**msg)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict | None = Depends(optional_user),
):
    """Get messages for a conversation."""
    conv = manager.get_conversation(conversation_id)
    if not conv:
        raise NotFoundError(message=f"Conversation '{conversation_id}' not found")
    messages = manager.get_messages(conversation_id, limit=limit, offset=offset)
    return [MessageResponse(**m) for m in messages]


@router.patch("/{conversation_id}/title")
async def update_title(
    conversation_id: str,
    body: UpdateTitleRequest,
    current_user: dict | None = Depends(optional_user),
):
    """Update conversation title."""
    success = manager.update_title(conversation_id, body.title)
    if not success:
        raise NotFoundError(message=f"Conversation '{conversation_id}' not found")
    return {"status": "ok", "title": body.title}


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: dict | None = Depends(optional_user),
):
    """Delete a conversation."""
    success = manager.delete_conversation(conversation_id)
    if not success:
        raise NotFoundError(message=f"Conversation '{conversation_id}' not found")
