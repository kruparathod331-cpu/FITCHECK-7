"""
FitCheck Application Root Runner
Enables executing the application directly from the root workspace directory:
    python main.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' can be resolved directly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app, main

if __name__ == "__main__":
    main()
