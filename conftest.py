"""Ensures the project root is always importable as the package root for tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
