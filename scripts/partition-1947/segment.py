"""Step 4: classify every pixel of the scan as Arab State, Jewish State, City of Jerusalem or outside.

The two states are told apart by colour (peach and turquoise). The City of Jerusalem is the white
hole in the Arab State around a seed point. Printed lines and text inside the country take the class
of the nearest coloured pixel, which puts each boundary in the middle of its printed line.
Output: work/labels.png (one byte per pixel, class ids from common.py) and a small preview."""
import cv2, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCAN_PNG, LABELS, WORK, A_, J_, JLM, OUT

im = cv2.imread(SCAN_PNG)
H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
A = (h >= 7) & (h <= 32) & (s >= 30) & (s <= 150) & (v >= 190)       # peach
J = (h >= 75) & (h <= 105) & (s >= 25) & (v >= 140)                   # turquoise
white = (s < 22) & (v >= 215)
del hsv, h, s, v

roi = np.zeros((H, W), bool); roi[830:13075, 862:6735] = True         # inside the neatline
roi[:2500, :2300] = False                                              # title and legend block
A &= roi; J &= roi
k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
# A 9x9 opening of the Arab colour is used for the landmass mask only: it removes pale-yellow road
# casings that run out across the frontier. The labels themselves use the 5x5 version.
A9 = cv2.morphologyEx(A.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)
A = cv2.morphologyEx(A.astype(np.uint8), cv2.MORPH_OPEN, k5).astype(bool)
J = cv2.morphologyEx(J.astype(np.uint8), cv2.MORPH_OPEN, k5).astype(bool)

# City of Jerusalem: flood the non-Arab pixels from a seed inside the zone (within a window around the
# city) and keep the white pixels of that hole. Roads cut the white area into several pieces, so a
# single white component is not enough.
x0, x1, y0, y1 = 3350, 4350, 5250, 6250
win = (~A[y0:y1, x0:x1]).astype(np.uint8)
win = cv2.morphologyEx(win, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))   # cut 1-px leaks through the Arab colour
sx, sy = 3845, 5840
cv2.floodFill(win, np.zeros((y1 - y0 + 2, x1 - x0 + 2), np.uint8), (sx - x0, sy - y0), 2, flags=4)
hole = win == 2
assert not (hole[0].any() or hole[-1].any() or hole[:, 0].any() or hole[:, -1].any()), "Jerusalem hole leaks to the window edge"
JL = np.zeros((H, W), bool)
JL[y0:y1, x0:x1] = hole & white[y0:y1, x0:x1]
print("Jerusalem hole px:", int(hole.sum()), "white px in it:", int(JL.sum()))

# The country: colour plus Jerusalem, closed over printed lines and text (81 px bridges the dense
# linework at Acre on the coast), keeping only the main landmass, with enclosed holes filled.
col = (A9 | J | JL).astype(np.uint8)
closed = cv2.morphologyEx(col, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81)))
n, cc, st, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
print("closed components:", n - 1, "largest:", int(st[big, cv2.CC_STAT_AREA]))
closed = (cc == big).astype(np.uint8); del cc
ff = closed.copy()
cv2.floodFill(ff, np.zeros((H + 2, W + 2), np.uint8), (0, 0), 2)
inside = (ff != 2) & roi
print("inside px:", int(inside.sum()))

# nearest coloured class for every pixel inside
lab = np.zeros((H, W), np.uint8)
lab[A] = A_; lab[J] = J_; lab[JL] = JLM
unknown = (lab == 0).astype(np.uint8)
dist, nearest = cv2.distanceTransformWithLabels(unknown, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
lut = np.concatenate([[0], lab[unknown == 0]]).astype(np.uint8)
filled = lut[nearest]
del nearest
final = np.where(inside, filled, OUT).astype(np.uint8)
print("max fill distance inside:", float(dist[inside].max()))

# small specks (e.g. red road ink inside the Jerusalem zone) take the class that surrounds them
k3 = np.ones((3, 3), np.uint8)
for c in (A_, J_, JLM):
    n, cc, st, _ = cv2.connectedComponentsWithStats((final == c).astype(np.uint8), connectivity=8)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 2000:
            continue
        x, y, w, h = st[i, :4]
        bx, by = max(0, x - 3), max(0, y - 3)
        sub = cc[by:y + h + 3, bx:x + w + 3] == i
        ring = cv2.dilate(sub.astype(np.uint8), k3).astype(bool) & ~sub
        vals = final[by:y + h + 3, bx:x + w + 3][ring]
        final[by:y + h + 3, bx:x + w + 3][sub] = np.bincount(vals, minlength=5).argmax()
    del cc

cv2.imwrite(LABELS, final)
pal = np.array([[0, 0, 0], [120, 190, 250], [200, 200, 90], [255, 255, 255], [235, 235, 235]], np.uint8)
cv2.imwrite(os.path.join(WORK, "labels_preview.png"), cv2.resize(pal[final], (W // 8, H // 8), interpolation=cv2.INTER_NEAREST))
for c, name in ((A_, "Arab State"), (J_, "Jewish State"), (JLM, "City of Jerusalem")):
    n, cc, st, ce = cv2.connectedComponentsWithStats((final == c).astype(np.uint8), connectivity=8)
    parts = sorted([int(st[i, cv2.CC_STAT_AREA]) for i in range(1, n)], reverse=True)
    print(f"{name}: {len(parts)} piece(s), areas in px {parts}")
