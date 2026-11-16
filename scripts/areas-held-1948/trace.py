"""Run every step in order (python scripts/areas-held-1948/trace.py). Rewrites the layer's GeoJSON.
Needs the partition plan and armistice layers that are already in the repo."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for step in ("fetch.py", "segment.py", "build.py", "export.py"):
    print(f"--- {step}", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True)
