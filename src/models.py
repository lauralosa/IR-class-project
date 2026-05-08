from pydantic import BaseModel, Field
from typing import List, Optional

class Publication(BaseModel):
    id: int
    title: str
    authors: List[str]
    abstract: str
    year: str
    keywords: List[str] = []
    affiliations: List[str] = []
    doi: Optional[str] = "N/A"
    pdf_url: Optional[str] = None
    # REQ-B10: Caminhos para auditoria e rapidez
    raw_text_path: Optional[str] = None
    processed_text_path: Optional[str] = None

class SearchResult(BaseModel):
    id: int
    title: str
    score: float
    authors: List[str]
    pdf_url: Optional[str]