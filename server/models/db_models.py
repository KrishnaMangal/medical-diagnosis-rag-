from pydantic import BaseModel, Field
from typing import Optional ,list
from datetime import datetime
import time


class UserOut(BaseModel):
    username: str
    role: str

class ReprtMeta(BaseModel):# storing metadata of the report
    doc_id: str
    filename: str
    uploader: str
    uploaded_at: float
    num_chunks: int

class DiagnosisRecord(BaseModel):#Ye RAG question-answer history store karega.
    doc_id: str
    requester: str
    question: str
    answer: str
    source: Optional[list]=None
    timestamp: float = Field(default_factory=lambda: time.time())
   