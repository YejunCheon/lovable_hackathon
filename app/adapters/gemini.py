import google.generativeai as genai
from app.core.config import settings

# Configure the generative AI model
genai.configure(api_key=settings.GEMINI_API_KEY)

async def gemini_flash_json(prompt: str) -> str:
    """
    Calls the Gemini 1.5 Flash model with a specific prompt and returns the response as a JSON string.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    resp = await model.generate_content_async(
        [prompt],
        generation_config={"response_mime_type": "application/json"}
    )
    return resp.text
