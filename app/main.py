from fastapi import FastAPI
from app.api import routes_search, routes_candidates, routes_auth
from app.adapters.pg import connect_db, close_db

app = FastAPI(
    title="AI Talent Search API",
    description="API for finding the best talent using AI.",
    version="0.1.0",
)

app.include_router(routes_search.router, prefix="/v1")
app.include_router(routes_candidates.router, prefix="/v1")
app.include_router(routes_auth.router, prefix="/v1")

@app.on_event("startup")
async def startup_event():
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Talent Search API"}
