from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import github



app = FastAPI(
    title="RepoPilot AI",
    description="AI-powered GitHub repository reviewer",
    version="0.1.0",
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the GitHub router — all its routes are now active
app.include_router(github.router)

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Used by deployment platforms to verify the service is running.
    Also useful for you to confirm the server started correctly.

    """


    return {"status": "ok", "service": "RepoPilot AI"}

@app.get("/")
def basic():
    {
        "message":"Welcome to RepoPilot AI",
        "version":"0.1.0"   
    }
    return {"status": "ok", "service": "RepoPilot AI"}