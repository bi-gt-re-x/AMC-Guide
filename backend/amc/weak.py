"""The weak-topics bank on the Review page: twelve problems from the topics the
account does worst in, drawn from the official papers, and from the AMC Guide and
Step mocks too when the reader asks for them.

**Weak** means *missed*. A topic comes first when the student has got its
problems wrong, ranked by the share missed, shrunk toward the middle so one
answer cannot condemn or clear a topic: (missed + 1) / (tried + 2), then by how
many are still in the error log and how many were missed. Topics never tried
come next, heaviest on the contest first, so a new account still gets a useful
set. Topics tried and never missed come last: they are not weaknesses, however
few answers they rest on.

**Which problems.** The pool is every problem at the account's contest level
(an AMC 12 student also gets AMC 10 problems) from the imported official papers,
plus the mock problems when asked. A problem already solved, or already waiting
in the error log, is left out: the log has its own schedule. Within a topic the
problems the student gets right about two times in three come first, judged by
their level *in that topic* (backend/amc/smart.py's fit of the topic's own
answers, shrunk toward their overall level, so a topic they are weak in gets
easier problems than their overall level would pick), unseen before missed, and a problem that calls
for a technique the student has missed in that topic is moved up: the same
idea again, in a problem not yet seen. The twelve go to the four weakest
topics that have problems left, more of them to the topics missed most (at
least two each), and the bank reaches further down the list when those run dry.

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
#: The least a chosen topic gets, so four topics share the set.
MIN_EACH = 2
#: How far a problem moves up when it needs a technique missed in its topic,
#: against `abs(chance - SWEET)`, which runs from 0 to about 0.67.
TECHNIQUE_PULL = 0.12
#: A topic's claim on the set when it has no misses to weigh: untried topics
#: share as evenly as missed ones of middling weakness, unmissed ones less.
UNTRIED_WEIGHT = 0.5
UNMISSED_WEIGHT = 0.25


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
        missed = tried - s['first_right']
        rows.append({
            'id': t['id'], 'name': t['name'], 'category': t['category'], 'weight': t['weight'],
            'attempted': tried, 'first_right': s['first_right'], 'accuracy': s['accuracy'],
            'missed': missed, 'in_review': s['review'],
            'score': round((s['first_right'] + 1) / (tried + 2), 3) if tried else None,
            # How weak, by misses: None for a topic never tried.
            'weakness': round((missed + 1) / (tried + 2), 3) if tried else None,
        })

    def rank(r):
        if r['missed']:
            return (0, -r['weakness'], -r['in_review'], -r['missed'], -r['weight'], r['name'])
        if not r['attempted']:
            return (1, 0, 0, 0, -r['weight'], r['name'])
        return (2, r['score'], 0, 0, -r['weight'], r['name'])
    rows.sort(key=rank)
    return rows


def _claim(topic):
    """How much of the set a topic should get, relative to the others chosen:
    its share missed, counting for more the more problems were missed (up to
    four), so one slip does not outweigh a pattern."""
    if topic['missed']:
        return topic['weakness'] * (1 + min(topic['missed'], 4) / 2)
    return UNTRIED_WEIGHT if not topic['attempted'] else UNMISSED_WEIGHT


def quotas(topics, size=SIZE, least=MIN_EACH):
    """Slots per topic, in proportion to each one's claim, at least `least`
    each (largest remainders get the leftovers, weakest first on a tie)."""
    if not topics:
        return []
    claims = [_claim(t) for t in topics]
    spare = size - least * len(topics)
    if spare <= 0:
        return [size // len(topics) + (1 if i < size % len(topics) else 0) for i in range(len(topics))]
    total = sum(claims)
    exact = [spare * c / total for c in claims]
    out = [least + int(e) for e in exact]
    order = sorted(range(len(topics)), key=lambda i: (-(exact[i] - int(exact[i])), i))
    for i in order[:size - sum(out)]:
        out[i] += 1
    return out


def _missed_techniques(hist):
    """{topic id: techniques of the problems missed first time in it}."""
    out = {}
    for pid, h in hist.items():
        if h.get('first_correct'):
            continue
        p = pb.get(pid)
        if not p:
            continue
        for tid in [p['topic']] + list(p.get('also') or []):
            out.setdefault(tid, set()).add(p['technique'])
    return out


def bank(hist, review_by_id, target, include_mocks, username, today=None, draw=0):
    """{'topics': [...], 'problems': [(problem, topic id, chance)], 'pool': {...}}."""
    today = today or date.today()
    topics = weak_topics(hist, review_by_id, target)
    points = smart.ability_points(hist, today)
    theta = smart.fit([pt[:3] for pt in points])[0]
    # Each topic's own level, from its own answers, leaning on the overall
    # level where it has few: the problems are pitched to the topic.
    by_topic = {}
    for rating, ok, w, p in points:
        for tid in [p['topic']] + list(p.get('also') or []):
            by_topic.setdefault(tid, []).append((rating, ok, w))
    topic_theta = {tid: smart.fit(pts, mean=theta, sd=smart.TOPIC_SD)[0] for tid, pts in by_topic.items()}
    rng = random.Random('{}|{}|{}'.format(username, today.isoformat(), int(draw)))
    missed_techniques = _missed_techniques(hist)

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
        if (h and h['solved']) or (rev and rev['status'] in ('active', 'parked')):
            continue
        pool['official' if official else 'mock'] += 1
        noise = rng.random() * 0.12
        for tid in [p['topic']] + list(p.get('also') or []):
            c = smart.chance(topic_theta.get(tid, theta), p['rating'])
            # Closest to two-in-three first; seen-and-missed after unseen; a
            # little noise so a new draw is a different set, not the same one
            # reshuffled.
            key = abs(c - SWEET) + (0.15 if h else 0) + noise
            # The technique this student has already missed here, again.
            pull = TECHNIQUE_PULL if p['technique'] in missed_techniques.get(tid, ()) else 0
            queues.setdefault(tid, []).append((key - pull, p['id'], p, c))
    for q in queues.values():
        q.sort(key=lambda row: (row[0], row[1]))

    order = [t for t in topics if queues.get(t['id'])]
    picked, used = [], set()

    def take(t):
        q = queues[t['id']]
        while q and q[0][1] in used:
            q.pop(0)
        if not q:
            return False
        _, pid, p, c = q.pop(0)
        used.add(pid)
        picked.append((p, t['id'], c))
        return True

    # First the weakest four, each up to its share; then, if any ran dry, the
    # rest of the set round-robin, reaching further down the list as needed.
    chosen = order[:SPREAD]
    for t, n in zip(chosen, quotas(chosen)):
        for _ in range(n):
            if len(picked) >= SIZE or not take(t):
                break
    reach = SPREAD
    while len(picked) < SIZE and order:
        moved = False
        for t in order[:reach]:
            if len(picked) < SIZE and take(t):
                moved = True
        if not moved:
            if reach >= len(order):
                break
            reach += 1
    # Easiest first, so the set gets harder as it goes.
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
