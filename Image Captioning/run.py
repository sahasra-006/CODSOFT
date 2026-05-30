"""
run.py — convenience launcher.
Usage: python run.py
"""
import uvicorn

if __name__ == "__main__":
    print("\n  App running at: http://localhost:8000\n")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
