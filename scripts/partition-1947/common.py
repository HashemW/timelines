"""Shared paths and constants for the partition-plan tracing scripts."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")                      # downloads and intermediate images (gitignored)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# UN Map No. 103, November 1947 ("A/516 Annex A"), UN Digital Library record 409073
SCAN_URL = "https://digitallibrary.un.org/record/409073/files/103_1.tif"
SCAN_TIF = os.path.join(WORK, "103_1.tif")
SCAN_PNG = os.path.join(WORK, "map1947.png")
GRATICULE = os.path.join(WORK, "graticule.json")
LABELS = os.path.join(WORK, "labels.png")
EXTRACT = os.path.join(WORK, "extract.json")

BORDERS = os.path.join(REPO, "data", "topics", "1948-war", "borders")
MANDATE = os.path.join(BORDERS, "mandate-boundary.geojson")
OUTPUT = os.path.join(BORDERS, "partition-plan-1947.geojson")

USER_AGENT = "timelines-research/0.1"

# class ids in labels.png
A_, J_, JLM, OUT = 1, 2, 3, 4      # Arab State, Jewish State, City of Jerusalem, outside

os.makedirs(WORK, exist_ok=True)
