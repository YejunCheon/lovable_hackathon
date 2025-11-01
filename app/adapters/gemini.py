from google.genai import Client

from app.core.config import settings

client = Client(
    api_key=settings.GEMINI_API_KEY,
)

async def gemini_flash_json(prompt: str) -> str:
    """
    Calls the Gemini 2.5 Flash model with a specific prompt and returns the response as a JSON string.
    Reasoning is disabled for faster responses.
    
    Note: Gemini 2.5 Flash typically doesn't use reasoning mode by default.
    If reasoning is being used, you can disable it by:
    1. Using "gemini-2.5-flash" (non-reasoning version)
    2. Adding generation_config parameters if available in the SDK
    """
    
    # Try to disable reasoning if the parameter exists
    # Common parameters: reasoning_threshold, use_reasoning, reasoning_mode
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config = {
            "thinkingConfig": {"thinking_budget": 0},
            "response_mime_type": "application/json"
        }
    )

    return response.text
