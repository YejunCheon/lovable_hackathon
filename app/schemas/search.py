from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class SearchRequest(BaseModel):
    query_text: str
    org_context: Optional[Dict[str, Any]] = None

class CandidateSearchResult(BaseModel):
    """Search result candidate matching DB schema"""
    id: int
    name: str
    description: Optional[str] = None  # From introduce field
    keywords: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    cards: Optional[List[Dict[str, Any]]] = None
    fit_score: Optional[float] = None  # From retrieval score
    reason_ko: Optional[str] = None  # From judge (if available)
    email: Optional[str] = None
    created_at: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response matching PRD specification"""
    query_summary: str
    candidates_top4: List[CandidateSearchResult]
    latency_ms: Optional[int] = None
