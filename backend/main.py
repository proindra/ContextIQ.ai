"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from api.routes import RAGRunner, router
from src.config.config import Config
from src.document_ingestion.document_processor import DocumentProcessor
from src.graph_builder.graph_builder import GraphBuilder
from src.vectorstore.vectorstore import VectorStore

logger = logging.getLogger(__name__)


def build_rag_system() -> GraphBuilder:
    llm = Config.get_llm()
    processor = DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        data_dir=Config.DATA_DIR,
    )
    documents = processor.process_urls(Config.DEFAULT_URLS)
    if not documents:
        raise RuntimeError("No documents were loaded; the RAG index cannot be created.")

    vector_store = VectorStore()
    vector_store.create_vectorstore(documents)
    graph_builder = GraphBuilder(
        retriever=vector_store.get_retriever(),
        llm=llm,
    )
    graph_builder.build()
    return graph_builder


def create_app(rag_system: RAGRunner | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        if app.state.rag_system is None:
            try:
                app.state.rag_system = await run_in_threadpool(build_rag_system)
            except Exception:
                logger.exception("Failed to initialize the RAG application.")
                raise
        yield

    app = FastAPI(
        title="ContextIQ.ai API",
        description="Agentic document search and question answering.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.rag_system = rag_system
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in Config.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router, prefix="/api")
    return app


app = create_app()
