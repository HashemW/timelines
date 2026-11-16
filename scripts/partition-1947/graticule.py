"""Step 2: follow the printed graticule (meridians 35E and 36E, parallels 30-33N) across the scan.

Each line is tracked in steps of 30 px. At each step a short profile across the predicted position is
averaged over 25 px along the line, the darkest point is refined to sub-pixel accuracy, and the
prediction is carried forward linearly. A quadratic is then fitted to the points with outlier
rejection. The lines are slightly bowed (up to ~18 px), which is why the georeferencing in georef.py
follows them instead of using a single affine fit.

Start positions were read off this scan, next to the frame's degree marks. The 33N parallel is hidden
under the title block on the left, so it is followed from the right-hand edge."""
import cv2, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCAN_PNG, GRATICULE

g = cv2.cvtColor(cv2.imread(SCAN_PNG), cv2.COLOR_BGR2GRAY).astype(np.float32)

# name: vertical line?, position across the line where tracking starts, start and end along it (scan px)
LINES = {
    "lon35": dict(vertical=True, start_pos=3155, start_t=900, t_end=13000),
    "lon36": dict(vertical=True, start_pos=5838, start_t=900, t_end=13000),
    "lat32": dict(vertical=False, start_pos=4979, start_t=900, t_end=7000),
    "lat31": dict(vertical=False, start_pos=8166, start_t=900, t_end=7000),
    "lat30": dict(vertical=False, start_pos=11358, start_t=900, t_end=7000),
    "lat33": dict(vertical=False, start_pos=1738, start_t=6650, t_end=900),
}


def track(vertical, start_pos, start_t, t_end, step=30, half=10, avg=12, min_contrast=18):
    """Points (along, across, contrast) on one thin dark line."""
    pts = []
    pred = start_pos
    t = start_t
    direction = 1 if t_end > start_t else -1
    while (t - t_end) * direction < 0:
        lo, hi = int(round(pred)) - half, int(round(pred)) + half + 1
        if vertical:
            prof = g[max(0, t - avg):t + avg + 1, lo - 8:hi + 8].mean(axis=0)
        else:
            prof = g[lo - 8:hi + 8, max(0, t - avg):t + avg + 1].mean(axis=1)
        inner = prof[8:-8]
        i = int(np.argmin(inner))
        bg = np.percentile(prof, 80)
        contrast = bg - inner[i]
        if contrast > min_contrast:
            # sub-pixel position: darkness-weighted centroid over +-3 px
            a, b = max(0, i - 3), min(len(inner), i + 4)
            w = np.clip(bg - inner[a:b], 0, None)
            c = (np.arange(a, b) * w).sum() / w.sum() if w.sum() > 0 else i
            pos = lo + c
            pts.append((t, float(pos), float(contrast)))
            if len(pts) >= 4:
                tt = np.array([p[0] for p in pts[-12:]]); pp = np.array([p[1] for p in pts[-12:]])
                pred = np.polyval(np.polyfit(tt, pp, 1), t + direction * step)
            else:
                pred = pos
        t += direction * step
    return pts


def robust_quad(pts, iters=5, thr=2.5):
    t = np.array([p[0] for p in pts]); x = np.array([p[1] for p in pts])
    keep = np.ones(len(t), bool)
    for _ in range(iters):
        k = np.polyfit(t[keep], x[keep], 2)
        r = x - np.polyval(k, t)
        s = max(1.0, 1.4826 * np.median(np.abs(r[keep])))
        keep = np.abs(r) < thr * s
    return k, keep, r


out = {}
for name, kw in LINES.items():
    pts = track(**kw)
    k, keep, r = robust_quad(pts)
    t = np.array([p[0] for p in pts])
    print(f"{name}: {keep.sum()}/{len(pts)} points kept, along {t[keep].min()}..{t[keep].max()} px, "
          f"residual sd {r[keep].std():.2f} px")
    out[name] = {"pts": [p for p, kp in zip(pts, keep) if kp], "quad": list(map(float, k))}
json.dump(out, open(GRATICULE, "w"))
