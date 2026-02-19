"""Minimal test server to verify uvicorn works"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal server works!"}

if __name__ == "__main__":
    uvicorn.run("test_server:app", host="0.0.0.0", port=8001, reload=False)
