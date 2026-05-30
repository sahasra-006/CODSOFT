#!/usr/bin/env python3
"""
StudyBot - Entry Point
Run with: python run.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn


def main():
    print("\n" + "="*60)
    print("  🤖  StudyBot — AI Study Assistant")
    print("="*60)
    print("  Starting server at: http://localhost:8000")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
