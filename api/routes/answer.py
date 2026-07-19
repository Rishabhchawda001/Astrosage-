"""
Answer generation routes — grounded answers with provenance.
"""
from __future__ import annotations

import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.services import get_answer_service

router = APIRouter(prefix="/api/v1/answer", tags=["answer"])


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of evidence sources")


class EvidenceItem(BaseModel):
    text: str
    scripture: str = ""
    level: str = ""
    score: float = 0


class AnswerBody(BaseModel):
    summary: str
    entities_found: list[str] = []
    evidence_count: int = 0
    confidence: str = ""


class Provenance(BaseModel):
    knowledge_version: str = "v1.0.0"
    source: str = "AstroSage Knowledge Engine"


class AnswerResponse(BaseModel):
    question: str
    answer: AnswerBody
    entities: list[dict] = []
    relationships: list[dict] = []
    sources: list[EvidenceItem] = []
    provenance: Provenance = Provenance()
    latency_ms: float = 0


@router.post("", response_model=AnswerResponse)
async def answer_question(body: AnswerRequest):
    """Answer a question using grounded knowledge from the knowledge base."""
    start = time.time()
    answer_service = get_answer_service()
    result = answer_service.answer(body.question, top_k=body.top_k)
    latency = round((time.time() - start) * 1000, 1)

    return AnswerResponse(
        question=result["question"],
        answer=AnswerBody(**result["answer"]),
        entities=result["entities"],
        relationships=result["relationships"],
        sources=[EvidenceItem(**s) for s in result["sources"]],
        provenance=Provenance(**result["provenance"]),
        latency_ms=latency,
    )
