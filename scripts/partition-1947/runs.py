"""(module) Cut the Arab State's outline in labels.png into runs, by what lies across the boundary:
the Jewish State, the City of Jerusalem, or outside (sea and neighbouring countries)."""
import cv2, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A_, J_, JLM, OUT


def raw_runs(lab):
    """{J_: [...], JLM: [...]}: runs of Arab-boundary pixels facing that class, as
    {"closed": bool, "pts": (n, 2) array of x, y}. Runs facing outside are dropped."""
    H, W = lab.shape
    contours, _ = cv2.findContours((lab == A_).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    def across(x, y):
        vals = set()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H and lab[yy, xx] != A_:
                vals.add(int(lab[yy, xx]))
        for c in (JLM, J_, OUT):
            if c in vals:
                return c
        return 0

    runs = {J_: [], JLM: []}
    for cnt in contours:
        pts = cnt.reshape(-1, 2)
        if len(pts) < 10:
            continue
        tags = np.array([across(x, y) for x, y in pts])
        for i in range(len(tags)):
            if tags[i] == 0:
                tags[i] = tags[i - 1]
        for _ in range(2):        # tidy one-pixel flickers (a corner pixel touching another class diagonally)
            for i in range(len(tags)):
                if tags[i - 1] == tags[(i + 1) % len(tags)] != tags[i]:
                    tags[i] = tags[i - 1]
        if (tags == tags[0]).all():
            if tags[0] in runs:
                runs[tags[0]].append({"closed": True, "pts": pts})
            continue
        start = int(np.nonzero(tags != np.roll(tags, 1))[0][0])      # start the ring at a change of neighbour
        pts = np.roll(pts, -start, 0); tags = np.roll(tags, -start)
        cuts = list(np.nonzero(tags[1:] != tags[:-1])[0] + 1) + [len(tags)]
        s = 0
        for e in cuts:
            if tags[s] in runs and e - s >= 12:
                runs[tags[s]].append({"closed": False, "pts": pts[s:min(e + 1, len(pts))]})
            s = e
    return runs
