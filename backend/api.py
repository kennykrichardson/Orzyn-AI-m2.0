from fastapi import FastAPI

from backend.routes import router

app = FastAPI(
    title="Orzyn AI",
    version="2.0.0",
    description="Developer Intelligence Platform",
)

app.include_router(router)   