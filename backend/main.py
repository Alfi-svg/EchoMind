from __future__ import annotations

import os

# MUST be set before TensorFlow is imported anywhere
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Force CPU only (disable GPU/MPS visibility)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"          # harmless on Mac, still helps
os.environ["TF_DISABLE_MPS"] = "1"                # best effort

# Extra: prevents some graph compilation paths from using MPSGraph
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.logging_setup import setup_logging
from backend.routes.web import router as web_router
from backend.routes.api import router as api_router
from backend.services.storage import ensure_dirs

import os

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Offline AI Hackathon System", version="1.0.0")

# Mount storage for generated TTS files
app.mount("/generated", StaticFiles(directory="backend/storage"), name="generated")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(web_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# static
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(web_router)
app.include_router(api_router)

@app.on_event("startup")
def _startup():
    ensure_dirs()
    logger.info("Startup complete. Offline AI system is ready.")
