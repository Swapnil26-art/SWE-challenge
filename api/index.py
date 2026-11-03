import os
import sys

# Ensure root and backend directory are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app

# Vercel Serverless Function entry point
# Exposes WSGI Flask instance `app`
