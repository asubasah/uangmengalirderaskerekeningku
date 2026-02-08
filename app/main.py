from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import collect
from app.core.config import settings
from app.db.init_db import init_db
import logging

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to init DB
@app.on_event("startup")
def on_startup():
    init_db()

# Include Routers
app.include_router(collect.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "YouTube Winning Pattern Detector Backend is running"}
