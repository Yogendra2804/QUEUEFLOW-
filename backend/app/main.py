"""
QueueFlow FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.api import auth, queues, tokens, analytics

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables on startup — idempotent
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="QueueFlow API",
    description="Queue management system for Rugas Technologies evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(queues.router)
app.include_router(tokens.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "QueueFlow API is running", "docs": "/docs"}
