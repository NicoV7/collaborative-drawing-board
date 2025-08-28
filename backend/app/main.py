from fastapi import FastAPI

app = FastAPI(title="Collaborative Drawing Board API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Collaborative Drawing Board API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}