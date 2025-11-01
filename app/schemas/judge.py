from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union

class Evidence(BaseModel):
    """
    Represents a piece of evidence supporting the judge's decision.
    Uses a flexible dictionary structure to accommodate different evidence types.
    """
    type: str = Field(..., description="Type of evidence, e.g., 'paper', 'project', 'skill'.")
    title: Union[str, None] = Field(None, description="Title of the paper, project, etc.")
    desc: Union[str, None] = Field(None, description="Description of the evidence.")
    year: Union[int, None] = Field(None, description="Year the evidence occurred.")
    link: Union[str, None] = Field(None, description="A URL link to the evidence.")
    role: Union[str, None] = Field(None, description="Role in the project or activity.")

class JudgeOutput(BaseModel):
    """
    Defines the structured output from the AI Judge for a single candidate.
    """
    candidate_id: str = Field(..., description="The ID of the candidate being judged.")
    fit_score: int = Field(..., ge=0, le=100, description="The suitability score from 0 to 100.")
    reason_ko: str = Field(..., description="The reason for the recommendation in conversational Korean.")
    evidence: List[Evidence] = Field(..., description="A list of evidence supporting the score and reason.")
