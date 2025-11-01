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
    
    # Prompt: Generate persona with structured SQL filters for precise matching
    prompt = f"""You are a talent search assistant. Transform the user's natural language query into a structured "persona" that will generate precise SQL WHERE conditions for database search.

**PURPOSE**: The persona will generate search_filters that translate directly into SQL WHERE clauses:
1. **Structured SQL Search**: Uses LLM-generated WHERE conditions (PRIMARY METHOD)
2. Field-specific matching using PostgreSQL JSONB operators and text matching

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

**TARGET SCHEMA (candidates table):**
```
name: TEXT
introduce: TEXT  
keywords: JSONB array of strings (e.g., ["AI", "Machine Learning"])
skills: JSONB array of strings (e.g., ["Python", "TensorFlow"])
cards: JSONB array of objects
```

**Your Task - Generate TWO outputs:**
1. **Extract structured data** (domains, skills_hard, etc.) - for display/context
2. **Generate search_filters** - for precise SQL WHERE clause matching

**search_filters MUST be field-specific WHERE conditions:**
- **keywords_any**: Array of keywords that should match candidates.keywords (use domains)
  - Example: ["AI", "인공지능", "Machine Learning", "머신러닝"]
  - PostgreSQL: `keywords ?| array['AI', 'Machine Learning']`
- **skills_any**: Array of skills that should match candidates.skills (use skills_hard names)
  - Example: ["Python", "TensorFlow", "Deep Learning"]
  - PostgreSQL: `skills ?| array['Python', 'TensorFlow']`
- **introduce_contains**: Key terms that should appear in introduce field
  - Example: ["연구", "research", "개발"]
  - PostgreSQL: `introduce ILIKE '%연구%' OR introduce ILIKE '%research%'`
- **name_contains**: Terms for name field (if title/role specified)
  - Optional, only if user mentioned specific titles

**Extract information:**
1. **domains**: → Use for keywords_any in search_filters
2. **skills_hard**: → Extract skill names for skills_any in search_filters
3. **outcomes**: → Use for introduce_contains in search_filters
4. **titles**: Job titles/roles (use for name_contains if relevant)
5. **query_text**: Simplified version for vector embedding (optional)

**Important Guidelines:**
- Extract Korean AND English terms (candidates have both)
- Keep terms specific and searchable (avoid generic terms)
- **search_filters is the PRIMARY method** - generate comprehensive filters
- **query_text** is optional (for legacy vector search, can be simplified)
- If org_context provided, incorporate into org_context fields

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
  "query_text": "AI Expert AI 전문가 Machine Learning Deep Learning Python TensorFlow",
  "search_filters": {{
    "keywords_any": ["AI", "인공지능", "Artificial Intelligence", "Machine Learning", "머신러닝", "Deep Learning", "딥러닝", "Computer Vision"],
    "skills_any": ["Python", "TensorFlow", "Deep Learning", "딥러닝"],
    "introduce_contains": ["AI", "인공지능", "연구", "research", "머신러닝"]
  }}
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

    # Normalize None values to empty dicts for nested models
    # Pydantic requires dict or model instance, not None
    if persona_data.get('constraints_hard') is None:
        persona_data['constraints_hard'] = {}
    if persona_data.get('preferences_soft') is None:
        persona_data['preferences_soft'] = {}
    if persona_data.get('org_context') is None:
        persona_data['org_context'] = {}
    if persona_data.get('search_filters') is None:
        persona_data['search_filters'] = {}

    # Wrap it in the "persona" key as expected by PersonaResponse
    return PersonaResponse(persona=persona_data)
