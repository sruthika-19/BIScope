from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as terminology_router
from dotenv import load_dotenv

app = FastAPI(
    title="BIScope API",
    description="API for BIScope - Indian Standards and BIS services assistant",
    version="1.0.0"
)

load_dotenv()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "BIScope API"
    }

# Register the terminology router
app.include_router(terminology_router, prefix="/api/v1")