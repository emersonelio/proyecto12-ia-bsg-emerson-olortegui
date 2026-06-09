from pydantic import BaseModel
from typing import List, Optional


class AskRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    document_id: Optional[str] = None
    chunk_id: Optional[int] = None
    source_file: Optional[str] = None
    text: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]