import multiprocessing
import os
import sys

# Ensure PyInstaller frozen binary finds bundled C libraries (like tomo-recon.dll)
if getattr(sys, "frozen", False):
  bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
  os.environ["PATH"] = bundle_dir + os.path.pathsep + os.environ["PATH"]
  if hasattr(os, "add_dll_directory"):
    try:
      os.add_dll_directory(bundle_dir)
    except Exception:
      pass

multiprocessing.freeze_support()

from app.api.v1 import ingestion, preprocessing, preview
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch
import uvicorn

app = FastAPI(title="SINOVA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str | bool]:
  return {
      "status": "ok",
      "service": "sinova-backend",
      "cuda_available": torch.cuda.is_available(),
  }


app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(preview.router, prefix="/api/v1")
app.include_router(preprocessing.router, prefix="/api/v1")

if __name__ == "__main__":
  is_frozen = getattr(sys, "frozen", False)
  uvicorn.run(
      app if is_frozen else "main:app",
      host="127.0.0.1",
      port=8000,
      reload=not is_frozen,
  )