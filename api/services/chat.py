"""
Chat service — LiteLLM-powered chat completions with model routing.

Routes requests to available models (local or cloud) based on configuration.
Provides streaming and non-streaming responses.
"""
from __future__ import annotations

import json
import logging
import time
from typing import AsyncGenerator, Optional

from api.config import settings
from api.services import get_search_service, get_graph_service

logger = logging.getLogger("astrosage.chat")


class ChatService:
    """
    AI chat service using LiteLLM for model routing.

    In production, routes to local vLLM instance first, falls back to
    cloud providers (OpenAI, Claude, Gemini) via LiteLLM.
    """

    def __init__(self):
        self._search = get_search_service()
        self._graph = get_graph_service()

    async def acompletion(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs,
    ) -> dict | AsyncGenerator[str, None]:
        """
        Async chat completion with LiteLLM routing.

        Falls back gracefully if no API key is configured for the requested model.
        """
        import litellm

        # Configure LiteLLM
        litellm.set_verbose = settings.debug
        litellm.drop_params = True  # Drop unsupported params for different providers

        # Build the system prompt with knowledge base context
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        # Augment with knowledge base context
        if last_user_msg:
            context = self._build_context(last_user_msg)
        else:
            context = ""

        # Build system message
        system_prompt = self._get_system_prompt()
        if context:
            system_prompt += f"\n\nRelevant knowledge:\n{context}"

        augmented_messages = [{"role": "system", "content": system_prompt}]
        augmented_messages.extend(
            msg for msg in messages if msg.get("role") != "system"
        )

        try:
            response = await litellm.acompletion(
                model=model,
                messages=augmented_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            if stream:
                return self._stream_response(response)

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

        except Exception as e:
            logger.error(f"LiteLLM completion failed for {model}: {e}")
            # Fallback: answer from knowledge base
            return self._fallback_answer(last_user_msg, model)

    async def acompletion_stream(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion."""
        result = await self.acompletion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        if isinstance(result, AsyncGenerator):
            async for chunk in result:
                yield chunk
        else:
            yield json.dumps(result)

    def _build_context(self, query: str, max_chunks: int = 5) -> str:
        """Build knowledge context for the query."""
        search_results = self._search.search(query, top_k=max_chunks)

        if not search_results:
            return ""

        context_parts = []
        for i, r in enumerate(search_results, 1):
            text = r.get("text", "")[:300]
            scripture = r.get("scripture_id", "")
            level = r.get("level", "")
            context_parts.append(f"[{i}] ({level}, {scripture}): {text}")

        return "\n".join(context_parts)

    def _get_system_prompt(self) -> str:
        """Build the system prompt for AstroSage AI."""
        return (
            "You are AstroSage AI, an evidence-first knowledge assistant specializing in "
            "Hindu scriptures, Vedic texts, Upanishads, Puranas, and related philosophical works. "
            "You have access to a frozen knowledge base containing 120K chunks from 54 scriptures, "
            "a knowledge graph with 391 entities and 5044 relationships.\n\n"
            "Rules:\n"
            "1. Base your answers on the provided knowledge context when available.\n"
            "2. Cite specific scriptures and sources when making claims.\n"
            "3. If you don't know something, say so — never fabricate references.\n"
            "4. Be precise and scholarly in your responses.\n"
            "5. Explain Sanskrit terms when introducing them.\n"
            "6. Respect all traditions and interpretations.\n"
            "7. When a question is outside your knowledge domain, acknowledge this politely."
        )

    async def _stream_response(self, response) -> AsyncGenerator[str, None]:
        """Process streaming response from LiteLLM."""
        async for chunk in response:
            content = chunk.choices[0].delta.content if chunk.choices else ""
            if content:
                yield content
            # Final chunk with usage info
            if chunk.choices[0].finish_reason == "stop" or chunk.choices[0].finish_reason == "end_turn":
                if hasattr(chunk, "usage") and chunk.usage:
                    usage_info = {
                        "_meta": {
                            "usage": {
                                "prompt_tokens": chunk.usage.prompt_tokens,
                                "completion_tokens": chunk.usage.completion_tokens,
                                "total_tokens": chunk.usage.total_tokens,
                            }
                        }
                    }
                    yield f"\n\n{json.dumps(usage_info)}"

    def _fallback_answer(self, question: str, model: str) -> dict:
        """Fallback answer from knowledge base when model is unavailable."""
        from api.services import get_answer_service
        answer_service = get_answer_service()
        result = answer_service.answer(question)

        summary = result["answer"]["summary"]
        entities = ", ".join(result["answer"]["entities_found"])
        sources_text = "\n".join(
            f"- {s.get('text', '')[:200]} ({s.get('scripture', '')})"
            for s in result["sources"][:3]
        )

        answer_text = (
            f"{summary}\n\n"
            f"Related entities: {entities}\n\n"
            f"Sources:\n{sources_text}\n\n"
            f"(Fallback mode: {model} unavailable, answered from local knowledge base)"
        )

        return {
            "content": answer_text,
            "model": "astrosage-knowledge-engine",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "fallback": True,
        }
