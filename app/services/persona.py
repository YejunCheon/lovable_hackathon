import json
import logging
from app.adapters.gemini import gemini_flash_json
from app.schemas.search import SearchRequest
from app.schemas.persona import PersonaResponse, Persona

logger = logging.getLogger(__name__)

async def build_persona(req: SearchRequest) -> PersonaResponse:
    """
    Builds a persona from a search request using the Gemini API.
    """
    logger.info("=" * 60)
    logger.info(" Persona Builder 시작")
    logger.info("=" * 60)
    logger.info(f"📝 입력 쿼리: {req.query_text}")
    if req.org_context:
        logger.info(f"🏢 조직 컨텍스트: {req.org_context}")
    
    # Enhanced prompt that reflects actual candidate data structure
    prompt = f"""You are a talent search assistant. Based on the user's natural language query, extract structured search criteria to find the best matching candidates.

**User Query:** "{req.query_text}"

**Organizational Context:** {req.org_context or "Not provided"}

**Database Schema Information:**
- Candidates have: name, email, introduce (text), keywords (string array), skills (string array), cards (structured data)
- Keywords are typically domain/field tags (e.g., ["AI", "Machine Learning", "Computer Vision"])
- Skills are specific technical abilities (e.g., ["Python", "TensorFlow", "Deep Learning"])
- Cards contain structured profile information (research areas, publications, etc.)

**Your Task:**
Generate a structured persona JSON object that extracts search-relevant information from the query. Focus on:
1. **domains**: Research fields, academic disciplines, or industry domains mentioned
2. **skills_hard**: Technical skills, programming languages, tools, methodologies (each with name and level: "beginner", "intermediate", "advanced", or "expert")
3. **skills_soft**: Soft skills, collaboration styles, communication abilities
4. **titles**: Job titles, academic positions, or roles (e.g., "Professor", "Researcher", "Engineer")
5. **outcomes**: Desired achievements, publications, experience (e.g., "top-tier papers", "industry collaboration")
6. **query_text**: A refined, concise version of the search query optimized for semantic search

**Important Guidelines:**
- Extract Korean and English terms as they appear (candidates may have Korean keywords/skills)
- For skills_hard, infer appropriate levels based on context (if not specified, use "advanced")
- Keep domains and skills specific and searchable (avoid overly generic terms)
- If organizational context is provided, incorporate it into org_context fields (mission, stack, collab_style)

**CRITICAL: query_text Format:**
The `query_text` field will be used for vector embedding and MUST follow the same format as candidate vectors:
```
Introduction: [concise description based on domains, outcomes, and requirements]
Keywords: [space-separated list of domains and relevant terms]
Skills: [space-separated list of skill names from skills_hard]
```

This ensures the query vector matches the structure of candidate vectors, which are created from:
"Name: {{name}}\nIntroduction: {{introduce}}\nKeywords: {{keywords}}\nSkills: {{skills}}\nCards: {{cards}}"

**JSON Schema to follow:**
{Persona.model_json_schema()}

**Example for "AI 전문가를 찾고싶어":**
{{
  "titles": ["Professor", "Researcher", "AI Engineer"],
  "domains": ["Artificial Intelligence", "Machine Learning", "Deep Learning", "Computer Vision"],
  "skills_hard": [
    {{"name": "Python", "level": "expert"}},
    {{"name": "TensorFlow", "level": "advanced"}},
    {{"name": "Deep Learning", "level": "expert"}}
  ],
  "skills_soft": ["Research", "Innovation", "Problem Solving"],
  "seniority": ["senior", "expert"],
  "outcomes": ["AI research", "model development", "publications"],
  "query_text": "Introduction: AI 전문가, 머신러닝 및 딥러닝 연구 분야에서 전문성 보유\nKeywords: Artificial Intelligence Machine Learning Deep Learning Computer Vision\nSkills: Python TensorFlow Deep Learning"
}}

Generate the JSON object now (provide only valid JSON, no markdown formatting):"""

    logger.info("🤖 Gemini API 호출 중... (Persona 생성)")
    json_string = await gemini_flash_json(prompt)
    logger.info("✅ Gemini API 응답 수신 완료")
    
    # The output from the LLM should be a JSON object that we can parse directly.
    # The response from gemini_flash_json is a string that needs to be parsed.
    logger.info("📋 JSON 파싱 중...")
    
    # Clean JSON string: remove control characters and markdown code blocks if present
    import re
    # Remove markdown code block markers if present
    json_string = re.sub(r'^```json\s*', '', json_string, flags=re.IGNORECASE | re.MULTILINE)
    json_string = re.sub(r'^```\s*', '', json_string, flags=re.IGNORECASE | re.MULTILINE)
    json_string = json_string.strip()
    
    # Remove control characters except newlines and tabs
    json_string = ''.join(char for char in json_string if ord(char) >= 32 or char in '\n\t')
    
    try:
        persona_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"JSON string (first 500 chars): {json_string[:500]}")
        # Try to extract JSON from markdown or other formatting
        # Look for JSON object in the string
        match = re.search(r'\{.*\}', json_string, re.DOTALL)
        if match:
            logger.info("Attempting to extract JSON from formatted text...")
            try:
                persona_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse JSON from Gemini response: {e}")
        else:
            raise ValueError(f"Failed to parse JSON from Gemini response: {e}")
    
    # Log extracted persona information
    logger.info("✅ Persona 생성 완료:")
    logger.info(f"   - Query Text: {persona_data.get('query_text', 'N/A')}")
    logger.info(f"   - Domains: {persona_data.get('domains', [])}")
    logger.info(f"   - Skills: {[s.get('name', '') for s in persona_data.get('skills_hard', [])]}")
    logger.info(f"   - Titles: {persona_data.get('titles', [])}")
    logger.info("=" * 60)

    # Wrap it in the "persona" key as expected by PersonaResponse
    return PersonaResponse(persona=persona_data)
