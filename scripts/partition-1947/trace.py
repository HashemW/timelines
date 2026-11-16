"""Run every step in order (python scripts/partition-1947/trace.py). Rewrites the layer's GeoJSON."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for step in ("fetch.py", "graticule.py", "segment.py", "build.py", "export.py"):
    print(f"--- {step}", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True)
