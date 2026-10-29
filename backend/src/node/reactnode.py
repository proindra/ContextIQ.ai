"""LangGraph nodes for RAG workflow + ReAct Agent inside generate_content"""

import os
from typing import List, Optional
from src.state.rag_state import RAGState

from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage
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
            if not docs:
                return "No documents found."
            merged = []
            for i, d in enumerate(docs[:8], start=1):
                meta = d.metadata if hasattr(d, "metadata") else {}
                title = meta.get("title") or meta.get("source") or f"doc_{i}"
                merged.append(f"[{i}] {title}\n{d.page_content}")
            return "\n\n".join(merged)

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
            return "No good Wikipedia Search Result was found."

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
            f"Page: {result['title']}\nSummary: {pages[str(result['pageid'])].get('extract', '')}"
            for result in search_results
            if pages[str(result["pageid"])].get("extract")
        ]
        return "\n\n".join(summaries) or "No good Wikipedia Search Result was found."

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

        return RAGState(
            question=state.question,
            retrieved_docs=state.retrieved_docs,
            answer=answer or "Could not generate answer."
        )
