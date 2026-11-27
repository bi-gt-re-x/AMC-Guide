"""Every set within reach, with one or two challenges.

What a set holds, whatever it is for (backend/amc/practice.py's topic sets,
backend/amc/weak.py's weak-topics set): problems the student can do, and a
stretch or two at the end. Measured with backend/amc/smart.py's model, the
chance this student gets a problem right at their level in its topic:

* **in reach**: a chance of IN_REACH (one in two) or better.
* **a challenge**: below that, but no further above the student than
  backend/amc/reach.py's NEAR (about a 31% chance). A set holds
  `challenges_for(size)` of them: one in a short set, two from six problems.
* **beyond reach**: further above than that. Never in a set while anything
  closer is left; it is what "Too challenging?" puts on hold.

The challenge set (practice.py's `challenge` mode) is the weekly stretch, so
all of it is challenges; it still keeps out what is beyond reach.

`pitch` makes a set that, by swapping, after the set's own way of picking has
had its say: each swap takes the candidate the builder ranked highest that
fits, and one `like` the problem it replaces where it can (a real contest
problem for a real one, so the real-and-mock balance holds).
"""
from backend.amc import reach, smart

#: The chance at or above which a problem is within reach.
IN_REACH = 0.5
#: The chance of a problem NEAR above the student: the hardest a set may go.
FLOOR = smart.chance(0, reach.NEAR)
#: Where a challenge aims: between FLOOR and IN_REACH.
CHALLENGE_AIM = (IN_REACH + FLOOR) / 2


def challenges_for(size):
    """How many challenges a set of `size` holds: one, or two from six problems."""
    return 2 if size >= 6 else 1


def band(c):
    """'in' (within reach), 'stretch' (a challenge) or 'beyond'."""
    if c >= IN_REACH:
        return 'in'
    return 'stretch' if c >= FLOOR - 1e-9 else 'beyond'


def pitch(picked, candidates, chance, size, like=None, all_stretch=False, tier=None, strict=False):
    """`picked` (problem dicts) swapped until at most `challenges_for(size)`
    are challenges, at least one is (where the topic has one), and none is
    beyond reach (where anything closer is left). `candidates` is the
    builder's own ranking, best first; `chance(p)` the student's chance on
    `p`; `like(a, b)` whether `b` can stand in for `a` (default: any);
    `tier(p)`, lower first, what a challenge is chosen from before its
    distance from the aim counts (a topic's own problems before ones only
    tagged with it).

    `all_stretch`: every problem should be a challenge (the challenge set).
    `strict`: only a `like` problem may stand in (a spaced set stays problems
    met before, even if that leaves it without a challenge).
    """
    like = like or (lambda a, b: True)
    tier = tier or (lambda p: 0)
    picked = list(picked)
    ids = {p['id'] for p in picked}
    spare = [p for p in candidates if p['id'] not in ids]

    def swap(out, *wants, alike_only=False):
        """Replace `out` with the best spare in the first of `wants` (bands)
        that has one: alike problems in every band first, then (unless
        strict or `alike_only`) any."""
        def fits(want):
            rows = [p for p in spare if band(chance(p)) == want]
            if want == 'stretch':
                rows.sort(key=lambda p: (tier(p), abs(chance(p) - CHALLENGE_AIM)))
            return rows
        pick = next((p for want in wants for p in fits(want) if like(out, p)), None)
        if not pick and not strict and not alike_only:
            pick = next((p for want in wants for p in fits(want)), None)
        if not pick:
            return False
        picked[picked.index(out)] = pick
        spare.remove(pick)
        return True

    if all_stretch:
        for p in [p for p in picked if band(chance(p)) != 'stretch']:
            # Out of challenges: one beyond reach still gives way to an in-reach problem.
            swap(p, 'stretch', 'in') if band(chance(p)) == 'beyond' else swap(p, 'stretch')
        return picked

    want = challenges_for(size)
    # Beyond reach out: for a challenge while there is room for one, else an in-reach problem.
    for p in [p for p in picked if band(chance(p)) == 'beyond']:
        stretched = sum(1 for q in picked if band(chance(q)) == 'stretch')
        swap(p, 'stretch', 'in') if stretched < want else swap(p, 'in')
    # Too many challenges: the furthest from aim make way for in-reach problems.
    stretch = sorted([p for p in picked if band(chance(p)) == 'stretch'],
                     key=lambda p: -abs(chance(p) - CHALLENGE_AIM))
    for p in stretch[:max(0, len(stretch) - want)]:
        swap(p, 'in')
    # Too few: the hardest in-reach problems make way for challenges (the
    # easiest are what the set is built on), each for a challenge like it
    # where any of them has one, before any unlike swap.
    for alike_only in (True, False):
        for p in sorted([p for p in picked if band(chance(p)) == 'in'], key=chance):
            if sum(1 for q in picked if band(chance(q)) == 'stretch') >= want:
                return picked
            swap(p, 'stretch', alike_only=alike_only)
    return picked
