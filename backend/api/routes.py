"""Search and health endpoints."""

import logging
import time
from pathlib import Path
from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import HealthResponse, SearchRequest, SearchResponse, SourceDocument

logger = logging.getLogger(__name__)
router = APIRouter()


class RAGRunner(Protocol):
    def run(self, question: str) -> dict[str, Any]: ...


def get_rag_system(request: Request) -> RAGRunner:
    rag_system = getattr(request.app.state, "rag_system", None)
    if rag_system is None:
        raise HTTPException(status_code=503, detail="The RAG system is not ready.")
    return rag_system


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    rag_system: RAGRunner = Depends(get_rag_system),
) -> SearchResponse:
    started_at = time.perf_counter()
    try:
        result = rag_system.run(payload.question)
    except Exception as exc:
        logger.exception("RAG search failed.")
        raise HTTPException(
            status_code=502,
            detail="Search failed while contacting the language model or a search tool.",
        ) from exc

    answer = str(result.get("answer") or "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail="The RAG system returned an empty answer.")

    sources = []
    for index, document in enumerate(result.get("retrieved_docs") or [], start=1):
        metadata = document.metadata or {}
        source = metadata.get("source")
        title = metadata.get("title") or (Path(str(source)).name if source else f"Source {index}")
        sources.append(
            SourceDocument(
                title=str(title),
                source=str(source) if source else None,
                content=document.page_content,
            )
        )

    return SearchResponse(
        question=payload.question,
        answer=answer,
        sources=sources,
        elapsed_seconds=round(time.perf_counter() - started_at, 3),
    )
