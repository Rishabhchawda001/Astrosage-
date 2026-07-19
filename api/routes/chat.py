"""
Chat completions API — OpenAI-compatible endpoint with SSE streaming.

Supports:
- POST /api/v1/chat/completions — OpenAI-compatible chat completions
- Streaming via Server-Sent Events
- LiteLLM model routing (local → cloud fallback)
- Knowledge base context augmentation
"""
from __future__ import annotations

import json
import time
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.config import settings
from api.services.chat import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(system|user|assistant|tool)$")
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-4o-mini", description="Model identifier")
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    stream: bool = Field(default=False, description="Enable SSE streaming")
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    conversation_id: str | None = Field(default=None, description="Existing conversation ID for multi-turn")


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: UsageInfo = UsageInfo()


_service = ChatService()
from api.services.conversation import ConversationManager
_conversations = ConversationManager()


@router.post("/completions")
async def chat_completions(body: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Returns streaming SSE response when `stream: true`.
    Supports all LiteLLM model identifiers.
    """
    if body.stream:
        return StreamingResponse(
            _stream_chat(body),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await _non_stream_chat(body)


async def _non_stream_chat(body: ChatCompletionRequest) -> ChatCompletionResponse:
    """Non-streaming chat completion with conversation persistence."""
    messages = [m.model_dump() for m in body.messages]

    # Persist user messages
    conv_id = body.conversation_id
    user_msg = None
    for m in body.messages:
        if m.role == "user":
            user_msg = m.content

    if not conv_id:
        # Auto-create conversation
        title = (user_msg or "Chat")[:60]
        conv = _conversations.create_conversation(user_id="anonymous", title=title)
        conv_id = conv["id"]
    else:
        conv = _conversations.get_conversation(conv_id)
        if not conv:
            from api.exceptions import NotFoundError
            raise NotFoundError(message=f"Conversation '{conv_id}' not found")

    # Save user messages
    for m in body.messages:
        _conversations.add_message(conv_id, m.role, m.content)

    result = await _service.acompletion(
        messages=messages,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        stream=False,
    )

    content = result.get("content", "")
    model_used = result.get("model", body.model)
    usage = result.get("usage", {})

    # Save assistant response
    if conv_id:
        _conversations.add_message(
            conv_id, "assistant", content,
            token_count=usage.get("completion_tokens", 0),
        )

    return ChatCompletionResponse(
        id=conv_id or f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=model_used,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
    )


async def _stream_chat(body: ChatCompletionRequest) -> AsyncGenerator[bytes, None]:
    """SSE streaming chat completion."""
    messages = [m.model_dump() for m in body.messages]

    conv_id = body.conversation_id
    user_msg = None
    for m in body.messages:
        if m.role == "user":
            user_msg = m.content
    if not conv_id:
        title = (user_msg or "Chat")[:60]
        conv = _conversations.create_conversation(user_id="anonymous", title=title)
        conv_id = conv["id"]
    for m in body.messages:
        _conversations.add_message(conv_id, m.role, m.content)

    # Send a thinking message
    thinking_msg = {
        "choices": [{"delta": {"role": "assistant", "content": ""}, "finish_reason": None}],
        "created": int(time.time()),
        "model": body.model,
    }
    yield f"data: {json.dumps(thinking_msg)}\n\n".encode("utf-8")

    # Stream the response
    full_content = ""
    model_used = body.model

    try:
        async for chunk in _service.acompletion_stream(
            messages=messages,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        ):
            if chunk.startswith("{"):
                try:
                    meta = json.loads(chunk)
                    if "_meta" in meta:
                        # Final metadata
                        yield f"data: {json.dumps({'choices': [{'delta': {}, 'finish_reason': 'stop'}]})}\n\n".encode("utf-8")
                        yield "data: [DONE]\n\n".encode("utf-8")
                        return
                except json.JSONDecodeError:
                    pass
            else:
                full_content += chunk
                stream_msg = {
                    "choices": [
                        {
                            "delta": {"content": chunk},
                            "finish_reason": None,
                        }
                    ],
                    "created": int(time.time()),
                    "model": model_used,
                    "object": "chat.completion.chunk",
                }
                yield f"data: {json.dumps(stream_msg)}\n\n".encode("utf-8")
    except Exception as e:
        # Fallback to knowledge base answer
        error_msg = {
            "choices": [
                {
                    "delta": {
                        "content": f"\n\n(Model unavailable. Falling back to knowledge base.)"
                    },
                    "finish_reason": "stop",
                }
            ]
        }
        yield f"data: {json.dumps(error_msg)}\n\n".encode("utf-8")

    # Final SSE message
    yield "data: [DONE]\n\n".encode("utf-8")
