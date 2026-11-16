"""The weak-topics bank on the Review page: twelve problems from the topics the
account does worst in, drawn from the official papers, and from the Summit and
Step mocks too when the reader asks for them.

**Weak** means a low first-try accuracy, shrunk toward the middle so that two
answers cannot condemn a topic: (right + 1) / (tried + 2). Topics never tried
come after every tried one, the heaviest on the contest first, so a new account
still gets a useful set.

**Which problems.** The pool is every problem at the account's contest level
(an AMC 12 student also gets AMC 10 problems) from the imported official papers,
plus the mock problems when asked. A problem already solved, or already waiting
in the error log, is left out: the log has its own schedule. Within a topic the
problems the student gets right about two times in three come first (the level
is backend/amc/smart.py's fit), unseen before missed. The twelve are spread
three to a topic over the four weakest topics that have problems left, and the
bank reaches further down the list when those run dry.

The draw is seeded by account and day, so the set holds still while it is
worked through; "New set" asks for the next draw.
"""
import random
from datetime import date

from backend.amc import catalog, engine, smart
from backend.amc import problems as pb

SIZE = 12
SPREAD = 4
SWEET = 2 / 3


def _level_ok(p, target):
    return p['level'] == target or (target == 'AMC 12' and p['level'] == 'AMC 10')


def weak_topics(hist, review_by_id, target):
    """Every topic on the target contest, weakest first."""
    tstats = engine.topic_stats(hist, review_by_id)
    rows = []
    for t in catalog.TOPICS:
        if target not in t['levels']:
            continue
        s = tstats[t['id']]
        tried = s['attempted']
        rows.append({
            'id': t['id'], 'name': t['name'], 'category': t['category'], 'weight': t['weight'],
            'attempted': tried, 'first_right': s['first_right'], 'accuracy': s['accuracy'],
            'in_review': s['review'],
            'score': round((s['first_right'] + 1) / (tried + 2), 3) if tried else None,
        })
    rows.sort(key=lambda r: (r['score'] is None, r['score'] or 0, -r['in_review'], -r['weight'], r['name']))
    return rows


def bank(hist, review_by_id, target, include_mocks, username, today=None, draw=0):
    """{'topics': [...], 'problems': [(problem, topic id, chance)], 'pool': {...}}."""
    today = today or date.today()
    topics = weak_topics(hist, review_by_id, target)
    theta = smart.fit([pt[:3] for pt in smart._first_points(hist, today)])[0]
    rng = random.Random('{}|{}|{}'.format(username, today.isoformat(), int(draw)))

    pool = {'official': 0, 'mock': 0}
    queues = {}
    for p in pb.all_problems():
        if not _level_ok(p, target) or p.get('ai'):
            continue
        official = bool(p.get('official'))
        if not official and not include_mocks:
            continue
        h = hist.get(p['id'])
        rev = review_by_id.get(p['id'])
        if (h and h['solved']) or (rev and rev['status'] == 'active'):
            continue
        pool['official' if official else 'mock'] += 1
        c = smart.chance(theta, p['rating'])
        # Closest to two-in-three first; seen-and-missed after unseen; a little
        # noise so a new draw is a different set, not the same one reshuffled.
        key = abs(c - SWEET) + (0.15 if h else 0) + rng.random() * 0.12
        for tid in [p['topic']] + list(p.get('also') or []):
            queues.setdefault(tid, []).append((key, p['id'], p, c))
    for q in queues.values():
        q.sort(key=lambda row: (row[0], row[1]))

    order = [t for t in topics if queues.get(t['id'])]
    picked, used = [], set()
    reach = SPREAD
    while len(picked) < SIZE and order:
        moved = False
        for t in order[:reach]:
            q = queues[t['id']]
            while q and q[0][1] in used:
                q.pop(0)
            if q and len(picked) < SIZE:
                _, pid, p, c = q.pop(0)
                used.add(pid)
                picked.append((p, t['id'], c))
                moved = True
        if not moved:
            if reach >= len(order):
                break
            reach += 1
    picked.sort(key=lambda row: (row[0]['rating'], row[0]['id']))
    used_topics = {tid for _, tid, _ in picked}
    return {
        'theta': theta,
        # Weakest first, as they were ranked.
        'topics': [dict(t, picked=sum(1 for row in picked if row[1] == t['id']))
                   for t in topics if t['id'] in used_topics],
        'problems': picked,
        'pool': pool,
    }
