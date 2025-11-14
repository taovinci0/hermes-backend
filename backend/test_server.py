#!/usr/bin/env python3
"""Test script to start the server and check for errors."""

import sys
import traceback

try:
    print("1. Testing imports...")
    from api.main import app
    print("   ✅ App imported successfully")
    
    print("\n2. Testing uvicorn...")
    import uvicorn
    print(f"   ✅ Uvicorn version: {uvicorn.__version__}")
    
    print("\n3. Starting server on http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop")
    print("   Open http://localhost:8000/docs in your browser")
    print("-" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

