import sys
import os

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from fastapi.routing import APIRoute

print("=== REGISTERED ROUTES ===")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"{route.methods} {route.path} -> {route.name}")
    else:
        print(f"OTHER: {route.path} ({type(route).__name__})")
