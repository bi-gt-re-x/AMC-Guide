"""Too challenging, for now: "Too challenging?" on a problem's details.

A problem the student finds beyond them gets nothing from coming back every
3, 10 and 21 days: each time it is the same wall. So a problem can be put
**on hold** in the review log. It stays in the log (the note, the misses, the
stage are all kept) but is never due, never counted as due, and never drawn
into the weak-topics set, until the student's level comes near it. Then it is
released by itself, due that day, and goes on from the stage it had.

## The level, on the problems' own scale

The level is backend/amc/smart.py's `theta`: the rating the student solves
half the time, on the same 1-12 scale as the problems, fitted from their
answers. Here it is the level in the problem's own topic, leaning on the
overall level where the topic has few answers (as the weak-topics set pitches
problems), because a geometry problem is out of reach of a student's geometry,
not of their average.

## When it comes back

The student decides a problem is too hard, so the button is offered on every
problem, not only on ones the model calls out of reach: a 6.5 against a level
of 5.9 is "within reach" to the model and still a wall to the student. What
the model decides is when it comes back, at the later of

* **near its rating**: within NEAR of it. NEAR is half an AoPS point, about
  three problem numbers on an AMC 10; at that gap the model gives roughly a
  30% chance, a stretch worth taking.
* **grown since**: STEP above the level the student was at when they put it
  on hold (`parked_level`, kept on the row). Without it, a problem the model
  already thought near would come straight back on the next page load.

`out_of_reach` (more than NEAR below the rating) is still reported, for the
wording; it no longer decides whether the button shows.
"""
from backend.amc import problems as pb
from backend.amc import smart

#: How far below a problem's rating the level may be for it to come back.
NEAR = 1.0
#: How much the level has to grow past where it was put on hold.
STEP = 0.5


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


def returns_at(problem, parked_level):
    """The level a problem put on hold at `parked_level` comes back at."""
    grown = float(parked_level) + STEP
    rating = problem.get('rating')
    return round(max(float(rating) - NEAR, grown) if rating is not None else grown, 1)


def view(problem, theta, topic_theta, parked_level=None):
    """What the pages show: the level now, and the level it comes back at —
    for one on hold, from where it was put on hold; otherwise, if it were put
    on hold now."""
    level = level_for(problem, theta, topic_theta)
    held_at = level if parked_level is None else parked_level
    return {'level': round(level, 1), 'rating': problem.get('rating'), 'near': NEAR,
            'out_of_reach': out_of_reach(problem, level),
            'returns_at': returns_at(problem, held_at)}


def releases(reviews, hist, today):
    """The on-hold rows the student's level has now reached, as the rows to
    write: back to active, due today, the hold cleared."""
    held = [r for r in reviews if r['status'] == 'parked']
    if not held:
        return []
    theta, topic_theta = levels(hist, today)
    out = []
    for row in held:
        p = pb.get(row['problem_id'])
        if not p:
            continue
        level = level_for(p, theta, topic_theta)
        # A row without the level it was held at (none should be) waits for the rating alone.
        held_at = row.get('parked_level')
        target = returns_at(p, held_at) if held_at is not None else (
            float(p['rating']) - NEAR if p.get('rating') is not None else None)
        if target is not None and level >= target:
            out.append({**row, 'status': 'active', 'due': today.isoformat(), 'parked_at': None, 'parked_level': None})
    return out
