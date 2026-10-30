"""LangGraph nodes for RAG workflow + ReAct Agent inside generate_content"""

import json
import os
from typing import List, Optional
from urllib.parse import quote

from src.state.rag_state import RAGState

from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
import requests


class RAGNodes:
    """Contains node functions for RAG workflow"""

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self._agent = None  # lazy-init agent

    def retrieve_docs(self, state: RAGState) -> RAGState:
        """Classic retriever node"""
        docs = self.retriever.invoke(state.question)
        return RAGState(
            question=state.question,
            retrieved_docs=docs
        )

    def _build_tools(self) -> List[Tool]:
        """Build retriever + wikipedia tools"""

        def retriever_tool_fn(query: str) -> str:
            docs: List[Document] = self.retriever.invoke(query)
            return self._serialize_documents(docs[:8])

        retriever_tool = Tool(
            name="retriever",
            description="Fetch passages from indexed corpus.",
            func=retriever_tool_fn,
        )

        wikipedia_tool = Tool(
            name="wikipedia",
            description="Search Wikipedia for general knowledge. Input should be a search query.",
            func=self._search_wikipedia,
        )

        return [retriever_tool, wikipedia_tool]

    @staticmethod
    def _serialize_documents(documents: List[Document]) -> str:
        return json.dumps(
            [
                {
                    "title": str(
                        document.metadata.get("title")
                        or document.metadata.get("source")
                        or f"Source {index}"
                    ),
                    "source": (
                        str(document.metadata["source"])
                        if document.metadata.get("source") is not None
                        else None
                    ),
                    "content": document.page_content,
                }
                for index, document in enumerate(documents, start=1)
            ],
            ensure_ascii=False,
        )

    @staticmethod
    def _search_wikipedia(query: str) -> str:
        """Search Wikipedia over HTTPS and return concise article extracts."""
        endpoint = "https://en.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": os.getenv("USER_AGENT", "AgenticRAG/0.1")
        }
        search_response = requests.get(
            endpoint,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query[:300],
                "srlimit": 3,
                "format": "json",
            },
            headers=headers,
            timeout=15,
        )
        search_response.raise_for_status()
        search_results = search_response.json()["query"]["search"]
        if not search_results:
            return "[]"

        page_response = requests.get(
            endpoint,
            params={
                "action": "query",
                "pageids": "|".join(str(result["pageid"]) for result in search_results),
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "exchars": 1200,
                "format": "json",
            },
            headers=headers,
            timeout=15,
        )
        page_response.raise_for_status()
        pages = page_response.json()["query"]["pages"]

        summaries = [
            {
                "title": result["title"],
                "source": "https://en.wikipedia.org/wiki/" + quote(result["title"].replace(" ", "_")),
                "content": pages[str(result["pageid"])].get("extract", ""),
            }
            for result in search_results
            if pages[str(result["pageid"])].get("extract")
        ]
        return json.dumps(summaries, ensure_ascii=False)

    def _build_agent(self):
        """ReAct agent with tools"""
        tools = self._build_tools()
        system_prompt = (
            "You are a helpful RAG agent. "
            "Prefer 'retriever' for user-provided docs; use 'wikipedia' for general knowledge. "
            "Return only the final useful answer."
        )
        self._agent = create_react_agent(self.llm, tools=tools,prompt=system_prompt)

    def generate_answer(self, state: RAGState) -> RAGState:
        """
        Generate answer using ReAct agent with retriever + wikipedia.
        """
        if self._agent is None:
            self._build_agent()

        result = self._agent.invoke({"messages": [HumanMessage(content=state.question)]})

        messages = result.get("messages", [])
        answer: Optional[str] = None
        if messages:
            answer_msg = messages[-1]
            answer = getattr(answer_msg, "content", None)

        used_tools = {
            message.name
            for message in messages
            if isinstance(message, ToolMessage)
        }
        retrieved_docs = []
        if used_tools:
            for message in messages:
                if not isinstance(message, ToolMessage):
                    continue
                try:
                    tool_documents = json.loads(message.content)
                except (TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(tool_documents, list):
                    continue
                retrieved_docs.extend(
                    Document(
                        page_content=document["content"],
                        metadata={
                            "title": document["title"],
                            "source": document.get("source"),
                        },
                    )
                    for document in tool_documents
                    if isinstance(document, dict)
                    and isinstance(document.get("title"), str)
                    and isinstance(document.get("content"), str)
                )
        else:
            retrieved_docs = state.retrieved_docs

        return RAGState(
            question=state.question,
            retrieved_docs=retrieved_docs,
            answer=answer or "Could not generate answer."
        )
