import json

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage, ToolMessage

from src.document_ingestion.document_processor import DocumentProcessor
from src.node.reactnode import RAGNodes
from src.state.rag_state import RAGState
from src.vectorstore.vectorstore import VectorStore


class KeywordEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        normalized = text.lower()
        return [
            float("agent" in normalized),
            float("diffusion" in normalized),
            float("video" in normalized),
        ]


def test_document_processor_splits_text_with_overlap() -> None:
    processor = DocumentProcessor(chunk_size=40, chunk_overlap=5, data_dir=".")
    document = Document(page_content="Agent research. " * 12, metadata={"source": "test"})

    chunks = processor.split_documents([document])

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 40 for chunk in chunks)
    assert all(chunk.metadata["source"] == "test" for chunk in chunks)


def test_faiss_retriever_returns_relevant_document() -> None:
    store = VectorStore(embedding=KeywordEmbeddings())
    store.create_vectorstore(
        [
            Document(page_content="Agent reasoning and tools", metadata={"title": "Agents"}),
            Document(page_content="Video diffusion generation", metadata={"title": "Diffusion"}),
        ]
    )

    results = store.get_retriever().invoke("agent")

    assert results
    assert results[0].metadata["title"] == "Agents"


def test_generate_answer_returns_sources_from_agent_tool_calls() -> None:
    agent_input: dict = {}

    class FakeAgent:
        def invoke(self, input: dict) -> dict:
            agent_input.update(input)
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps(
                            [
                                {
                                    "title": "attention.pdf",
                                    "source": "attention.pdf",
                                    "content": "Attention lets tokens weigh other tokens.",
                                }
                            ]
                        ),
                        tool_call_id="retriever-search",
                        name="retriever",
                    ),
                    ToolMessage(
                        content=json.dumps(
                            [
                                {
                                    "title": "Attention (machine learning)",
                                    "source": "https://en.wikipedia.org/wiki/Attention_(machine_learning)",
                                    "content": "Attention lets tokens weigh other tokens.",
                                }
                            ]
                        ),
                        tool_call_id="wiki-search",
                        name="wikipedia",
                    ),
                    AIMessage(content="Attention lets tokens weigh other tokens."),
                ]
            }

    nodes = RAGNodes(retriever=None, llm=None)
    nodes._agent = FakeAgent()
    state = RAGState(
        question="What is attention in transformers?",
        retrieved_docs=[
            Document(
                page_content="Attention lets tokens weigh other tokens.",
                metadata={"title": "attention.pdf", "source": "attention.pdf"},
            )
        ],
    )

    result = nodes.generate_answer(state)

    assert result.answer == "Attention lets tokens weigh other tokens."
    assert len(result.retrieved_docs) == 2
    assert result.retrieved_docs[0].metadata["title"] == "attention.pdf"
    assert result.retrieved_docs[1].metadata["title"] == "Attention (machine learning)"
    assert result.retrieved_docs[1].metadata["source"] == (
        "https://en.wikipedia.org/wiki/Attention_(machine_learning)"
    )
    assert "attention.pdf" in agent_input["messages"][0].content


def test_generate_answer_keeps_indexed_sources_without_tool_calls() -> None:
    class FakeAgent:
        def invoke(self, _input: dict) -> dict:
            return {"messages": [AIMessage(content="A grounded answer.")]}

    nodes = RAGNodes(retriever=None, llm=None)
    nodes._agent = FakeAgent()
    document = Document(
        page_content="Attention lets tokens weigh other tokens.",
        metadata={"title": "attention.pdf", "source": "data/attention.pdf"},
    )

    result = nodes.generate_answer(
        RAGState(question="What is attention?", retrieved_docs=[document])
    )

    assert result.retrieved_docs == [document]
