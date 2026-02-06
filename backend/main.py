from fastapi import FastAPI
from pydantic import BaseModel
import boto3

app = FastAPI(title="Workshop Backend API", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/")
async def root():
    return {"message": "Welcome to Workshop Backend API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="API is running")