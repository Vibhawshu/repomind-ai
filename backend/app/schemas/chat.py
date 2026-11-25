from pydantic import BaseModel


class ChatRequest(BaseModel):
    repo_id: str
    question: str


class SourceRef(BaseModel):
    index: int
    file_path: str
    start_line: int
    end_line: int
    language: str | None = None
    symbol: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]