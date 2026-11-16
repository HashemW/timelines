"""Step 1: download the UN's scan of the map (about 43 MB) and convert it to PNG."""
import os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCAN_URL, SCAN_TIF, SCAN_PNG, USER_AGENT
from PIL import Image

if not os.path.exists(SCAN_TIF):
    print("downloading", SCAN_URL)
    req = urllib.request.Request(SCAN_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as r, open(SCAN_TIF + ".part", "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    os.replace(SCAN_TIF + ".part", SCAN_TIF)
print("scan:", SCAN_TIF, os.path.getsize(SCAN_TIF), "bytes")

if not os.path.exists(SCAN_PNG):
    Image.MAX_IMAGE_PIXELS = None              # 7578 x 14043 px, larger than Pillow's default limit
    Image.open(SCAN_TIF).convert("RGB").save(SCAN_PNG)
print("png:", SCAN_PNG)
