from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

# Resolve paths relative to this file's actual location (fixes the empty __file__ bug)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Import detector after path setup
from phishing_detector import detector

app = FastAPI(title="Phish-Guard API", version="1.0.0")

# Enable CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Models ---
class VerifyRequest(BaseModel):
    url: str

class ReportRequest(BaseModel):
    url: str
    reason: str = "suspicious"

# --- API Endpoints ---

@app.post("/verify")
def verify_url_endpoint(request: VerifyRequest):
    """Verifies if a URL is safe or phishing."""
    try:
        result = detector.verify_url(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/report")
def report_url_endpoint(request: ReportRequest):
    """Endpoint for user-submitted threat reports."""
    print(f"[REPORT] URL: {request.url} | Reason: {request.reason}")
    return {"status": "success", "message": "Report received. Our security team will review."}

@app.get("/api/stats")
def get_stats():
    """Returns live engine stats for the landing page."""
    return {
        "trusted_domains": len(detector.trusted_domains),
        "cached_predictions": len(detector.prediction_cache.cache),
        "blocklist_size": len(detector.blocklist),
        "model_status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Phish-Guard is running"}

# --- Static Files / Landing Page ---
# Mount static files BEFORE the root GET to avoid conflicts
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[INFO] Serving static files from: {STATIC_DIR}")
else:
    print(f"[WARN] Static directory not found at: {STATIC_DIR}")

@app.get("/")
def serve_landing_page():
    """Serves the landing page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Phish-Guard Backend is Running!", "status": "active", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
