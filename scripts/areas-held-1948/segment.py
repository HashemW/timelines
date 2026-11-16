"""Step 2: read the shading off the two CIA maps.

June (colour): 'Jewish held area' is red hatching over khaki; 'Jewish controlled area' is red hatching
over white. Each pixel is scored by the share of red, khaki and white in an 11 x 11 window.
July (black and white): 'Jewish gains between 1st and 2nd truces' is fine diagonal hatching. A Gabor
filter tuned to it (period 5.2 px, wave vector at 46.6 degrees) picks it out; the same hatching angle
on the inset map's slanted border is dropped later, by location."""
import cv2, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import JUNE_IMG, JULY_IMG, WORK


def clean(m, close, open_, min_area, hole):
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_, open_)))
    n, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    m = keep[cc].astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)      # fill small holes (labels)
    small = np.zeros(n, bool); small[1:] = st[1:, cv2.CC_STAT_AREA] < hole
    m[small[cc]] = 1
    return m


# ---- June 1948
im = cv2.imread(JUNE_IMG)
h, s, v = [c.astype(int) for c in cv2.split(cv2.cvtColor(im, cv2.COLOR_BGR2HSV))]
red = ((h <= 10) | (h >= 170)) & (s >= 90)
khaki = (h >= 11) & (h <= 32) & (s >= 35) & (v >= 110) & (v <= 225)
white = (v >= 225) & (s <= 45)
rf, kf, wf = [cv2.blur(m.astype(np.float32), (11, 11)) for m in (red, khaki, white)]
roi = np.zeros(red.shape, np.uint8); roi[73:858, 53:556] = 1; roi[60:316, 40:258] = 0      # main panel minus legend
held = clean(((rf > 0.18) & (kf > 0.12) & (wf < 0.2)).astype(np.uint8) & roi, 9, 5, 120, 500)
ctrl = clean(((rf > 0.18) & (wf > 0.15) & (kf < 0.12)).astype(np.uint8) & roi, 9, 5, 120, 500) & (1 - held)
np.save(os.path.join(WORK, "june_held.npy"), held); np.save(os.path.join(WORK, "june_ctrl.npy"), ctrl)
print("June: held px", int(held.sum()), "controlled px", int(ctrl.sum()))

# ---- July 1948
g = cv2.cvtColor(cv2.imread(JULY_IMG), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0


def energy(theta_deg, lam=5.17, sigma=4.0, ksize=21):
    th = np.radians(theta_deg)
    ke = cv2.getGaborKernel((ksize, ksize), sigma, th, lam, 1.0, 0, cv2.CV_32F); ke -= ke.mean()
    ko = cv2.getGaborKernel((ksize, ksize), sigma, th, lam, 1.0, np.pi / 2, cv2.CV_32F)
    return cv2.blur(cv2.filter2D(g, -1, ke) ** 2 + cv2.filter2D(g, -1, ko) ** 2, (25, 25))


E, O = energy(46.6), energy(136.6)
hatch = ((E > 14) & (E > 3 * O)).astype(np.uint8)
roi = np.zeros(hatch.shape, np.uint8); roi[175:2058, 232:1443] = 1; roi[150:765, 200:765] = 0
hatch = clean(hatch & roi, 11, 11, 800, 3000)
np.save(os.path.join(WORK, "july_gains.npy"), hatch)
print("July: hatched px", int(hatch.sum()))
