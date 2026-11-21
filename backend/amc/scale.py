"""The difficulty scale.

## Summit's 1-10 scale

Every problem on the site carries a `rating` from 1 to 10, in half points. It
is the AoPS competition rating, which runs from 0.5 (the easiest AMC 8
problems) to 6 (AIME 14 and 15, and the easiest olympiad problems), stretched
onto ten points: the AoPS rating times 10/6, to the nearest half. On the AoPS
scale a student working through these contests only ever sees numbers up to 6,
and a level of "2.1" reads as failing when it is a solid start on the AMC 10.

    AoPS     0.5  1   1.5  2   2.5  3   3.5  4   4.5  5   5.5  6
    Summit   1    1.5 2.5  3.5 4   5   6    6.5 7.5  8.5 9   10

So an AMC 10 #1 is a 1.5 and the last problems of an AIME are a 10.
`to_scale` and `to_aops` convert. Ratings are written and reasoned about in
AoPS terms (that is the scale the wider world uses, and the one the AI problem
writer is told about), and converted here, once, on the way in.

## Where a problem sits on a real paper

`RATING_BY_NUMBER` is the AoPS rating of each problem number on a typical
recent paper, in half points, checked against the 2023-2026 AMC 10s worked
through for this site: an AMC 10 runs from 1 to about 4, an AMC 12 from 1 to
4.5, and an AIME from 2.5 to 6. Real papers vary from year to year, so this is
where a problem sits on a typical paper, not a measurement of that problem.

Imported official problems are rated from it (backend/amc/official.py). The
Summit Mock sets carry their own per-problem ratings, from a review of each
problem against real papers (backend/amc/sets/ratings.py), because a problem
written for slot #20 is not always as hard as a real #20. It has no imports so
everything can use it.
"""

#: The AoPS rating of the hardest AIME problems: the top of Summit's scale.
AOPS_TOP = 6

RATING_BY_NUMBER = {
    'AMC 10': [1, 1, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2, 2, 2, 2, 2, 2.5,
               2.5, 2.5, 2.5, 3, 3, 3, 3.5, 3.5, 3.5, 4],
    'AMC 12': [1, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2, 2, 2, 2, 2.5, 2.5, 2.5,
               2.5, 3, 3, 3, 3.5, 3.5, 3.5, 4, 4, 4.5],
    'AIME': [2.5, 3, 3, 3.5, 3.5, 4, 4, 4.5, 4.5, 5, 5, 5.5, 5.5, 6, 6],
}


def to_scale(aops):
    """An AoPS competition rating on Summit's 1-10 scale, in half points."""
    value = float(aops) * 10 / AOPS_TOP
    return max(1.0, min(10.0, round(value * 2) / 2))


def to_aops(rating):
    """A Summit 1-10 rating back on the AoPS scale (not rounded)."""
    return float(rating) * AOPS_TOP / 10


#: `RATING_BY_NUMBER` on Summit's scale.
SCALE_BY_NUMBER = {level: [to_scale(r) for r in table] for level, table in RATING_BY_NUMBER.items()}


def aops_at(level, number):
    """The AoPS rating of problem `number` on a typical `level` paper."""
    table = RATING_BY_NUMBER[level]
    return table[min(max(number, 1), len(table)) - 1]


def rating_at(level, number):
    """Summit's 1-10 rating of problem `number` on a typical `level` paper."""
    return to_scale(aops_at(level, number))


def tier(rating):
    """The 1-5 difficulty the filters and the score projection use, from a
    Summit rating: 1 is a real AMC 10 #1-4 (AoPS 1), 2 AoPS 1.5, 3 AoPS 2,
    4 AoPS 2.5-3, and 5 is #22-25 and up (AoPS 3.5+)."""
    if rating <= 1.5:
        return 1
    if rating <= 2.5:
        return 2
    if rating <= 3.5:
        return 3
    if rating <= 5:
        return 4
    return 5
