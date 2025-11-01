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

class PersonaResponse(BaseModel):
    persona: Persona
