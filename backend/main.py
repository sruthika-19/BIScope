from fastapi import FastAPI
from backend.routes.requirements import router as requirements_router
from backend.routes.standards import router as standards_router
from backend.routes.search import router as search_router
from backend.routes.evidence import router as evidence_router


app = FastAPI(
    title="BIScope API",
    description="AI-powered assistant for BIS standards and services",
    version="0.1.0"
)

app.include_router(requirements_router)
app.include_router(standards_router)
app.include_router(search_router)
app.include_router(evidence_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to BIScope API!"
    }