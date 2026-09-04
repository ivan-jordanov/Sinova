from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import export, ingestion, preprocessing, preview

app = FastAPI(title="SINOVA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sinova-backend"}


app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(preview.router, prefix="/api/v1")
app.include_router(preprocessing.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")