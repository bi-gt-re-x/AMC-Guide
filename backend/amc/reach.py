"""Out of reach, for now: "Too challenging?" on a problem's details.

A problem rated well above where the student is gets nothing from coming
back every 3, 10 and 21 days: each time it is the same wall. So a problem can
be put **on hold** in the review log. It stays in the log (the note, the
misses, the stage are all kept) but is never due, never counted as due, and
never drawn into the weak-topics set, until the student's level comes
near its rating. Then it is released by itself, due that day, and goes on
from the stage it had.

## "Near", on the problems' own scale

The level is backend/amc/smart.py's `theta`: the rating the student solves
half the time, on the same 1-12 scale as the problems, fitted from their
answers. Here it is the level in the problem's own topic, leaning on the
overall level where the topic has few answers (as the weak-topics set pitches
problems), because a geometry problem is out of reach of a student's geometry,
not of their average.

A problem is **out of reach** when its rating is more than NEAR above that
level, and **near** (released) once it is within NEAR. NEAR is half an AoPS
point, about three problem numbers on an AMC 10: at that gap the model gives
roughly a 30% chance of solving it, which is a stretch worth taking; further
than that is the wall. The button is only offered for a problem that is out of
reach, and the server refuses to put one on hold that is not, so a problem is
never parked only to be released on the next page load.
"""
from backend.amc import problems as pb
from backend.amc import smart

#: How far above the student's level a problem may be and still be worked.
NEAR = 1.0


def levels(hist, today):
    """(overall level, {topic id: level}) from the account's answers."""
    points = smart.ability_points(hist, today)
    theta = smart.fit([pt[:3] for pt in points])[0]
    by_topic = {}
    for rating, ok, w, p in points:
        for tid in [p['topic']] + list(p.get('also') or []):
            by_topic.setdefault(tid, []).append((rating, ok, w))
    return theta, {tid: smart.fit(pts, mean=theta, sd=smart.TOPIC_SD)[0] for tid, pts in by_topic.items()}


def level_for(problem, theta, topic_theta):
    """The student's level for this problem: its main topic's."""
    return topic_theta.get(problem['topic'], theta)


def out_of_reach(problem, level):
    rating = problem.get('rating')
    return rating is not None and float(rating) - float(level) > NEAR


def view(problem, theta, topic_theta):
    """What the problem page shows: the level, and whether it is out of reach."""
    level = level_for(problem, theta, topic_theta)
    return {'level': round(level, 1), 'rating': problem.get('rating'), 'near': NEAR,
            'out_of_reach': out_of_reach(problem, level),
            # The level it comes back at: within NEAR of the rating.
            'returns_at': round(float(problem['rating']) - NEAR, 1) if problem.get('rating') is not None else None}


def releases(reviews, hist, today):
    """The on-hold rows whose problem is now near the student's level, as the
    rows to write: back to active, due today, the hold cleared."""
    held = [r for r in reviews if r['status'] == 'parked']
    if not held:
        return []
    theta, topic_theta = levels(hist, today)
    out = []
    for row in held:
        p = pb.get(row['problem_id'])
        if p and not out_of_reach(p, level_for(p, theta, topic_theta)):
            out.append({**row, 'status': 'active', 'due': today.isoformat(), 'parked_at': None})
    return out
