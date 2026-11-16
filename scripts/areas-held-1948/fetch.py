"""Step 1: download the two CIA 'Military situation' maps used for the first two snapshots."""
import os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import JUNE_URL, JULY_URL, JUNE_IMG, JULY_IMG, USER_AGENT

for url, path in ((JUNE_URL, JUNE_IMG), (JULY_URL, JULY_IMG)):
    if not os.path.exists(path):
        print("downloading", url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as r, open(path + ".part", "wb") as f:
            f.write(r.read())
        os.replace(path + ".part", path)
    print(path, os.path.getsize(path), "bytes")
