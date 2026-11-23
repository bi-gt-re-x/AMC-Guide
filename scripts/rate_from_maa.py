"""Rate official problems by how many students got them right, in half steps.

    .venv-fastapi/bin/python scripts/rate_from_maa.py            # writes backend/amc/maa_ratings.json
    .venv-fastapi/bin/python scripts/rate_from_maa.py --check    # report only

A problem's place on the paper says roughly how hard it is (backend/amc/scale.py,
`RATING_BY_NUMBER`), but papers vary: some #8s are harder than some #14s. The
MAA publishes the share of students who answered each problem correctly, and
`furonghuang-lab/Easy2Hard-Bench` (config E2H-AMC, field `item_difficulty`)
carries it for 1,771 AMC 10, AMC 12 and AIME problems from 2003 to 2022.

Each problem starts from its slot's rating and moves by how much harder or
easier it was than the typical problem in that slot (on the log-odds of the
share right, in rating points from how the slots line up, halved, at most two
points), to the nearest half. Each slot still averages its table rating, so
the score model in backend/amc/smart.py reads a paper as before. A problem
without the figure keeps the rating of its slot. backend/amc/official.py reads
the file.
"""
import argparse
import math
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from backend.amc import catalog  # noqa: E402
from backend.amc.scale import SCALE_BY_NUMBER  # noqa: E402

OUT = os.path.join(ROOT, 'backend', 'amc', 'maa_ratings.json')
E2H = ('furonghuang-lab/Easy2Hard-Bench', 'E2H-AMC', ('train', 'eval'))
LEVEL = {'AMC10': 'AMC 10', 'AMC12': 'AMC 12', 'AIME': 'AIME'}


def problem_id(row):
    """An E2H row's AMC Guide problem id, or None."""
    level, year, n = LEVEL.get(row.get('tag')), int(row['year']), int(row['index'])
    if not level:
        return None
    if level == 'AIME':
        cid = '{}-aime-{}'.format(year, row['subtest'].lower())
    else:
        short = '10' if level == 'AMC 10' else '12'
        paper = row['subtest'][-1].lower()
        # 2021 ran twice; E2H marks the fall sitting with its month.
        season = 'fall-' if year == 2021 and row.get('month') == 'Nov' else ''
        cid = '{}-{}amc-{}{}'.format(year, season, short, paper if year >= 2002 else '')
    return '{}-{}'.format(cid, n) if cid in catalog.PAST_BY_ID else None


#: How much of a problem's gap from its slot to keep: year-to-year differences in
#: who sits the paper account for part of it, so it is halved.
SHRINK = 0.5
#: No problem moves more than this far from its slot's rating.
MAX_SHIFT = 2.0


def _logit(share):
    p = min(max(share / 100.0, 0.005), 0.995)
    return math.log(p / (1 - p))


def ratings(rows):
    """{problem id: rating on the 1-12 scale, in half steps}."""
    by_level = {}
    for r in rows:
        pid = problem_id(r)
        if pid and r.get('item_difficulty') is not None:
            by_level.setdefault(LEVEL[r['tag']], {})[pid] = (int(r['index']), _logit(float(r['item_difficulty'])))
    out = {}
    for level, found in by_level.items():
        table = SCALE_BY_NUMBER[level]
        # The typical share right at each slot, on the log-odds scale.
        slots = {}
        for n, x in found.values():
            slots.setdefault(n, []).append(x)
        mean = {n: sum(xs) / len(xs) for n, xs in slots.items()}
        # Rating points per unit of log-odds, from how the slots line up.
        pts = [(mean[n], table[n - 1]) for n in mean]
        mx = sum(x for x, _ in pts) / len(pts)
        my = sum(y for _, y in pts) / len(pts)
        slope = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
        for pid, (n, x) in found.items():
            shift = max(-MAX_SHIFT, min(MAX_SHIFT, SHRINK * slope * (x - mean[n])))
            value = max(1.0, min(12.0, table[n - 1] + shift))
            out[pid] = round(value * 2) / 2
    return dict(sorted(out.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--check', action='store_true', help='report, write nothing')
    ap.add_argument('--rows', help='E2H rows as JSON instead of fetching them')
    args = ap.parse_args()
    if args.rows:
        with open(args.rows) as f:
            rows = json.load(f)
    else:
        import import_amc12_hf as hf
        rows = [r for split in E2H[2] for r in hf.fetch_rows(E2H[0], E2H[1], split)]
    found = ratings(rows)
    halves = sum(1 for v in found.values() if v % 1)
    print('{} problems rated from the MAA share right, {} on a half step'.format(len(found), halves))
    if not args.check:
        with open(OUT, 'w') as f:
            json.dump(found, f, indent=0, sort_keys=True)
            f.write('\n')
        print('Wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
