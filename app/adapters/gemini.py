import google.generativeai as genai

from app.core.config import settings

# Configure the generative AI model
genai.configure(api_key=settings.GEMINI_API_KEY)

async def embed_query(text: str) -> list[float]:
    """
    Generates an embedding for the given text using the 'text-embedding-004' model.
    The result is padded to 1536 dimensions to match the database schema.
    """
    result = await genai.embed_content_async(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"
    )
    embedding = result['embedding']
    # Pad the embedding with zeros to 1536 dimensions
    if len(embedding) < 1536:
        padding = [0.0] * (1536 - len(embedding))
        embedding.extend(padding)
    return embedding

async def gemini_flash_json(prompt: str) -> str:
    """
    Calls the Gemini 2.5 Flash model with a specific prompt and returns the response as a JSON string.
    Reasoning is disabled for faster responses.
    
    Note: Gemini 2.5 Flash typically doesn't use reasoning mode by default.
    If reasoning is being used, you can disable it by:
    1. Using "gemini-2.5-flash" (non-reasoning version)
    2. Adding generation_config parameters if available in the SDK
    """
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    # Try to disable reasoning if the parameter exists
    # Common parameters: reasoning_threshold, use_reasoning, reasoning_mode
    generation_config={
        "response_mime_type": "application/json",
        "temperature": 0,  # deterministic
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 512,  # 필요 이상으로 크면 느려짐
    }    
    resp = await model.generate_content_async(
        [prompt],
        # generation_config=generation_config
    )
    return resp.text
