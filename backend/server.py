#!/usr/bin/env python
"""Run server with exception handling"""
import uvicorn
import sys

if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="debug",
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
