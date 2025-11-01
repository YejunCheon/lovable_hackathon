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
    
    # Prompt designed to match candidate vector structure exactly
    prompt = f"""You are a talent search assistant. Generate a persona that matches the database candidate structure to enable optimal vector similarity search.

**User Query:** "{req.query_text}"

**Organizational Context:** {req.org_context or "Not provided"}

**CRITICAL: Database Schema (candidates table):**
```
id SERIAL PRIMARY KEY
name TEXT NOT NULL
email TEXT NOT NULL UNIQUE
introduce TEXT
keywords JSONB (array of strings)
skills JSONB (array of strings)
cards JSONB (array of objects)
vector VECTOR(1536)
created_at TIMESTAMP
```

**How Candidate Vectors are Created:**
Candidates are embedded using this exact format:
```
Name: {{candidate_name}}
Introduction: {{introduce}}
Keywords: {{keywords joined by space}}
Skills: {{skills joined by space}}
Cards: {{cards joined by space}}
```

**Your Task:**
Generate a persona that, when embedded using the SAME format, will match candidates well. Extract:
1. **domains**: Research fields, domains, disciplines (will become "Keywords" section)
2. **skills_hard**: Technical skills with levels (names will become "Skills" section)
3. **skills_soft**: Soft skills, collaboration styles
4. **titles**: Job titles, academic positions
5. **outcomes**: Desired achievements, publications, experience (will inform "Introduction")
6. **query_text**: MUST use the EXACT same format as candidate vectors

**CRITICAL: query_text MUST Match Candidate Vector Format:**
The query_text field MUST use the EXACT same format as candidate vectors shown above. Generate it using the structure:
Name: [from titles or generic role if mentioned]
Introduction: [from outcomes and user requirements]
Keywords: [all domains space-separated]
Skills: [all skills_hard names space-separated]
Cards: [relevant research topics if any, space-separated]

**Important Guidelines:**
- Extract Korean AND English terms as candidates may have either
- For skills_hard levels: "beginner", "intermediate", "advanced", "expert" (default: "advanced")
- Keywords should be domain/field tags: ["AI", "Machine Learning", "Computer Vision"]
- Skills should be specific technical abilities: ["Python", "TensorFlow", "Deep Learning"]
- Keep all terms searchable and specific (avoid generic terms)
- If org_context provided, incorporate into org_context fields (mission, stack, collab_style)

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
  "query_text": "Name: AI Expert\nIntroduction: AI 전문가, 머신러닝 및 딥러닝 연구 분야에서 전문성 보유\nKeywords: Artificial Intelligence Machine Learning Deep Learning Computer Vision AI 인공지능 머신러닝 딥러닝\nSkills: Python TensorFlow Deep Learning\nCards: AI research model development"
}}

**Note:** The query_text format must EXACTLY match how candidate vectors are structured for optimal vector similarity search.

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
    
    # Parse and display query_text structure (matching candidate vector format)
    query_text = persona_data.get('query_text', '')
    if query_text:
        logger.info("   📋 Query Text (Vector Format):")
        # Split by lines to show structure
        for line in query_text.split('\n'):
            if line.strip():
                logger.info(f"      {line}")
    else:
        logger.info("   - Query Text: N/A")
    
    logger.info("=" * 60)

    # Wrap it in the "persona" key as expected by PersonaResponse
    return PersonaResponse(persona=persona_data)
