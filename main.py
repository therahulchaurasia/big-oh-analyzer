import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as analyze_router

app = FastAPI()

ALLOWED_ORIGIN = os.getenv("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(analyze_router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "Backend is running"}