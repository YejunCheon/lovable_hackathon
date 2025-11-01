import asyncio
import logging
from typing import List, Dict, Any

from app.adapters.gemini import gemini_flash_json
from app.schemas.judge import JudgeOutput
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def create_judge_prompt(persona: Dict[str, Any], candidate: Dict[str, Any]) -> str:
    """
    Creates the prompt for the AI Judge to evaluate a single candidate against a persona.
    """
    # Serialize candidate data to a string format for the prompt
    candidate_text = "\n".join([f"{key}: {value}" for key, value in candidate.items()])
    
    # The instruction for the model, based on PRD 4.2
    prompt = f"""You are an expert AI talent scout. Evaluate the following candidate based on the provided persona and the candidate's data. 

Your response MUST be a JSON object that strictly follows this format: 
{{
  "candidate_id": "{candidate.get('id')}",
  "fit_score": <0-100 integer score>,
  "reason_ko": "<conversational Korean summary ending with '~한 이유로 추천드려요.'>",
  "evidence": [
    {{"type": "<paper|project|skill>", "title": "<title>", "desc": "<description>", "year": <year>}},
    ...
  ]
}}

**Evaluation Criteria:**
1.  **Relevance:** How well do the candidate's skills, experience, and projects align with the persona's requirements (domains, skills, outcomes)?
2.  **Evidence:** The `evidence` array must contain at least two concrete examples from the candidate's data that justify the score.
3.  **Reasoning:** The `reason_ko` must be a concise, compelling, and conversational summary of why the candidate is a good fit.

--- 
**Persona:**
{persona}

---
**Candidate Data:**
{candidate_text}

---

Now, provide your evaluation in the specified JSON format only.
"""
    return prompt

async def judge_candidate(persona: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Judges a single candidate and returns the structured output.
    """
    prompt = create_judge_prompt(persona, candidate)
    
    try:
        response_text = await gemini_flash_json(prompt)
        # The gemini_flash_json function is expected to return a JSON string.
        # We will parse it into our Pydantic model for validation.
        judge_result = JudgeOutput.parse_raw(response_text)
        return judge_result.model_dump()
    except ValidationError as e:
        logger.error(f"Failed to validate Judge output for candidate {candidate.get('id')}: {e}")
        logger.error(f"Raw response was: {response_text}")
        return {"candidate_id": candidate.get('id'), "fit_score": 0, "reason_ko": "Error parsing judge response.", "evidence": []}
    except Exception as e:
        logger.error(f"An unexpected error occurred while judging candidate {candidate.get('id')}: {e}")
        return {"candidate_id": candidate.get('id'), "fit_score": 0, "reason_ko": "An unexpected error occurred.", "evidence": []}

async def judge_parallel(candidates: List[Dict[str, Any]], persona: Dict[str, Any], batch_size: int = 8) -> List[Dict[str, Any]]:
    """
    Judges a list of candidates in parallel batches.
    """
    judged_results = []
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        tasks = [judge_candidate(persona, cand) for cand in batch]
        batch_results = await asyncio.gather(*tasks)
        judged_results.extend(batch_results)
        logger.info(f"Judged batch {i//batch_size + 1}/{(len(candidates) + batch_size - 1)//batch_size}")
    
    return judged_results
