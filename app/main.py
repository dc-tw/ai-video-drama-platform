from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AI Video Drama Platform",
    version="0.1.0",
    description="Story planning and AIGC pipeline orchestration API.",
)
app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
