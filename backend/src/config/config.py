"""Configuration module for Agentic RAG system"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

class Config:
    """Configuration class for RAG system"""

    # API configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Model Configuration
    LLM_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    FRONTEND_ORIGINS = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    # Document Processing
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    DATA_DIR = BACKEND_DIR / "data"

    # Default URLs
    DEFAULT_URLS = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2024-04-12-diffusion-video/"
    ]

    @classmethod
    def get_llm(cls):
        """Initialize and return the LLM model"""
        if not cls.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file or environment."
            )
        return ChatGroq(model=cls.LLM_MODEL, api_key=cls.GROQ_API_KEY)