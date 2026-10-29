from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.document_ingestion.document_processor import DocumentProcessor
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
