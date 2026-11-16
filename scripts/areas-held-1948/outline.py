"""(module) Cut the outline of one class in a label image into runs, by which class lies across it.
(Same method as ../partition-1947/runs.py, kept separate so the two folders don't import each other.)"""
import cv2, numpy as np


def runs_facing(lab, cls, facing, priority):
    """Runs of the outline of class `cls` whose neighbour across is class `facing`.
    `priority` orders the neighbour classes when a pixel touches several. Returns [{"closed", "pts"}]."""
    H, W = lab.shape
    contours, _ = cv2.findContours((lab == cls).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    def across(x, y):
        vals = set()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H and lab[yy, xx] != cls:
                vals.add(int(lab[yy, xx]))
        for c in priority:
            if c in vals:
                return c
        return 0

    out = []
    for cnt in contours:
        pts = cnt.reshape(-1, 2)
        if len(pts) < 10:
            continue
        tags = np.array([across(x, y) for x, y in pts])
        for i in range(len(tags)):
            if tags[i] == 0:
                tags[i] = tags[i - 1]
        for _ in range(2):
            for i in range(len(tags)):
                if tags[i - 1] == tags[(i + 1) % len(tags)] != tags[i]:
                    tags[i] = tags[i - 1]
        if (tags == tags[0]).all():
            if tags[0] == facing:
                out.append({"closed": True, "pts": pts})
            continue
        start = int(np.nonzero(tags != np.roll(tags, 1))[0][0])
        pts = np.roll(pts, -start, 0); tags = np.roll(tags, -start)
        cuts = list(np.nonzero(tags[1:] != tags[:-1])[0] + 1) + [len(tags)]
        s = 0
        for e in cuts:
            if tags[s] == facing and e - s >= 12:
                out.append({"closed": False, "pts": pts[s:min(e + 1, len(pts))]})
            s = e
    return out
