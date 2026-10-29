"""HTTP request and response models for the search API."""

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question must not be blank.")
        return question


class SourceDocument(BaseModel):
    title: str
    source: str | None = None
    content: str


class SearchResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceDocument]
    elapsed_seconds: float


class HealthResponse(BaseModel):
    status: str
