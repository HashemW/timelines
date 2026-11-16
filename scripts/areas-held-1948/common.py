"""Shared paths, sources and the lon/lat grid for the 'areas held' scripts."""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")                      # downloads and intermediate arrays (gitignored)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BORDERS = os.path.join(REPO, "data", "topics", "1948-war", "borders")
PARTITION = os.path.join(BORDERS, "partition-plan-1947.geojson")
ARMISTICE = os.path.join(BORDERS, "armistice-lines-1949.geojson")
OUTPUT = os.path.join(BORDERS, "areas-held-1948-1949.geojson")
USER_AGENT = "timelines-research/0.1"

# CIA Map Branch, "Military situation" maps (US government works, public domain)
JUNE_URL = "https://upload.wikimedia.org/wikipedia/commons/6/60/Palestine_Military_Situation%2C_June_11%2C_1948%2C_Truman_Papers.jpg"
JULY_URL = "https://www.jewishvirtuallibrary.org/jsource/images/maps/cia_truce_071848.jpg"
JUNE_IMG = os.path.join(WORK, "cia_1948-06-11.jpg")
JULY_IMG = os.path.join(WORK, "cia_1948-07-18.jpg")

# the grid everything is drawn on: 0.0015 degrees (about 150 m)
LON0, LAT1, D = 34.15, 33.40, 0.0015
GW, GH = 1200, 2667


def ll2g(lon, lat):
    return (np.asarray(lon) - LON0) / D - 0.5, (LAT1 - np.asarray(lat)) / D - 0.5


def g2ll(c, r):
    return LON0 + (np.asarray(c) + 0.5) * D, LAT1 - (np.asarray(r) + 0.5) * D


os.makedirs(WORK, exist_ok=True)
