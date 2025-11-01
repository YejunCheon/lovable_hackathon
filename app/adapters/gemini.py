import google.generativeai as genai
from app.core.config import settings

# Configure the generative AI model
genai.configure(api_key=settings.GEMINI_API_KEY)

async def embed_query(text: str) -> list[float]:
    """
    Generates an embedding for the given text using the 'text-embedding-004' model.
    """
    result = await genai.embed_content_async(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

async def gemini_flash_json(prompt: str) -> str:
    """
    Calls the Gemini 1.5 Flash model with a specific prompt and returns the response as a JSON string.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = await model.generate_content_async(
        [prompt],
        generation_config={"response_mime_type": "application/json"}
    )
    return resp.text
