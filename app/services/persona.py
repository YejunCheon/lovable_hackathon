import json
from app.adapters.gemini import gemini_flash_json
from app.schemas.search import SearchRequest
from app.schemas.persona import PersonaResponse, Persona

async def build_persona(req: SearchRequest) -> PersonaResponse:
    """
    Builds a persona from a search request using the Gemini API.
    """
    # We can refine this prompt later.
    prompt = f"""
    Based on the following user query and organizational context, generate a detailed persona JSON object.
    The JSON object must follow the schema provided below.

    **User Query:** "{req.query_text}"

    **Organizational Context:** "{req.org_context}"

    **JSON Schema to follow:**
    {Persona.model_json_schema()}

    Please provide only the JSON object as the output.
    """

    json_string = await gemini_flash_json(prompt)
    
    # The output from the LLM should be a JSON object that we can parse directly.
    # The response from gemini_flash_json is a string that needs to be parsed.
    persona_data = json.loads(json_string)

    # Wrap it in the "persona" key as expected by PersonaResponse
    return PersonaResponse(persona=persona_data)
