from fastapi import FastAPI
from app.api import routes_search

app = FastAPI(
    title="AI Talent Search API",
    description="API for finding the best talent using AI.",
    version="0.1.0",
)

app.include_router(routes_search.router, prefix="/v1")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Talent Search API"}
