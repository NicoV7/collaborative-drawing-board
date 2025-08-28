from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import create_tables
from .routes import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(
    title="Collaborative Drawing Board API", 
    version="1.0.0",
    lifespan=lifespan
)

# Include auth routes
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Collaborative Drawing Board API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}