from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HardSkills(BaseModel):
    name: str
    level: str

class HardConstraints(BaseModel):
    location_any_of: Optional[List[str]] = None
    must_have: Optional[List[str]] = None

class SoftPreferences(BaseModel):
    nice_to_have: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None

class OrgContext(BaseModel):
    mission: Optional[str] = None
    stack: Optional[List[str]] = None
    collab_style: Optional[List[str]] = None

class SearchFilters(BaseModel):
    """Field-specific search filters for SQL WHERE clauses"""
    keywords_any: Optional[List[str]] = None  # keywords 배열에 이 중 하나라도 포함
    keywords_all: Optional[List[str]] = None   # keywords 배열에 모두 포함
    skills_any: Optional[List[str]] = None     # skills 배열에 이 중 하나라도 포함
    skills_all: Optional[List[str]] = None     # skills 배열에 모두 포함
    name_contains: Optional[List[str]] = None # name에 포함되는 단어들 (OR 조건)
    introduce_contains: Optional[List[str]] = None  # introduce에 포함되는 단어들 (OR 조건)
    cards_contains: Optional[List[str]] = None # cards JSONB에 포함되는 단어들

class Persona(BaseModel):
    titles: List[str] = []
    domains: List[str] = []
    skills_hard: List[HardSkills] = []
    skills_soft: List[str] = []
    seniority: List[str] = []
    outcomes: List[str] = []
    constraints_hard: HardConstraints = Field(default_factory=HardConstraints)
    preferences_soft: SoftPreferences = Field(default_factory=SoftPreferences)
    org_context: OrgContext = Field(default_factory=OrgContext)
    query_text: str
    search_filters: SearchFilters = Field(default_factory=SearchFilters)  # SQL WHERE 조건

class PersonaResponse(BaseModel):
    persona: Persona
