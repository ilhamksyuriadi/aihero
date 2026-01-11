"""
Simple test to verify basic imports work.
Run from project root: uv run python simple_test.py
"""

print("Testing imports...")

print("1. Testing basic imports...")
import sys
print(f"   Python: {sys.version}")

print("2. Testing requests...")
import requests
print("   ✅ requests")

print("3. Testing frontmatter...")
import frontmatter
print("   ✅ frontmatter")

print("4. Testing minsearch...")
import minsearch
print("   ✅ minsearch")

print("5. Testing pydantic_ai...")
import pydantic_ai
print("   ✅ pydantic_ai")

print("6. Testing sentence_transformers (this may take a moment)...")
import sentence_transformers
print("   ✅ sentence_transformers")

print("\n✅ All imports successful!")
print("\nNow testing app imports...")

print("7. Testing app.ingest...")
from app import ingest
print("   ✅ app.ingest")

print("8. Testing app.search_tools...")
from app import search_tools
print("   ✅ app.search_tools")

print("9. Testing app.logs...")
from app import logs
print("   ✅ app.logs")

print("\n🎉 All tests passed! Your environment is set up correctly.")
print("\nNext steps:")
print("1. Set your API key in .env file")
print("2. Run: uv run python -m app.main")
