"""Serve the local backend and frontend together; run from the project environment."""
import os
import sys
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent


def main():
    os.chdir(ROOT / "backend")
    sys.path.insert(0, str(ROOT / "backend"))
    from server import app

    app.mount("/", StaticFiles(directory=str(ROOT / "docs"), html=True), name="frontend")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
