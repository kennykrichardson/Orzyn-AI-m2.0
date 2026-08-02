import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router

DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://orzyn-ai.onrender.com"
)


def get_cors_origins() -> list[str]:
    origins = os.getenv("ORZYN_CORS_ORIGINS")

    if not origins:
        return list(DEFAULT_CORS_ORIGINS)

    return [
        origin.strip()
        for origin in origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="Orzyn AI",
    version="2.0.0",
    description="Developer Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)   
