"""The difficulty scale.

## Summit's 1-10 scale

Every problem on the site carries a `rating` from 1 to 10, where 1 is the
first problem of an AMC 10 and 10 is the hardest AIME problem. It is the AoPS
competition rating stretched to fill the range: AoPS rates the AMC and AIME
from 1 to 6.5 (the hardest AIME problems), and leaves 7 and up to olympiads
nobody here is preparing for. On the AoPS scale a student working through these
contests only ever sees the bottom two-thirds of the numbers, and a level of
"2.1 / 10" reads as failing when it is a solid start on the AMC 10. So the
site maps AoPS 1 to 1 and AoPS 6.5 to 10, linearly, in half points:

    AoPS     1  1.5  2  2.5  3  3.5  4  4.5  5  5.5  6  6.5
    Summit   1  2    2.5 3.5 4.5 5   6  6.5  7.5 8.5 9  10

`to_scale` and `to_aops` convert. Ratings are written and reasoned about in
AoPS terms (that is the scale the wider world uses, and the one the AI problem
writer is told about), and converted here, once, on the way in.

## Where a problem sits on a real paper

`RATING_BY_NUMBER` is the AoPS rating of each problem number on a typical
recent paper, in half points, checked against the 2023-2026 AMC 10s worked
through for this site: an AMC 10 runs from 1 to about 4, an AMC 12 from 1 to
4.5, and an AIME from 2.5 to 6.5. Real papers vary from year to year, so this is
where a problem sits on a typical paper, not a measurement of that problem.

Imported official problems are rated from it (backend/amc/official.py). The
Summit Mock sets carry their own per-problem ratings, from a review of each
problem against real papers (backend/amc/sets/ratings.py), because a problem
written for slot #20 is not always as hard as a real #20. It has no imports so
everything can use it.
"""

#: The AoPS rating of the hardest AIME problems: the top of Summit's scale.
AOPS_TOP = 6.5

RATING_BY_NUMBER = {
    'AMC 10': [1, 1, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2, 2, 2, 2, 2, 2.5,
               2.5, 2.5, 2.5, 3, 3, 3, 3.5, 3.5, 3.5, 4],
    'AMC 12': [1, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2, 2, 2, 2, 2.5, 2.5, 2.5,
               2.5, 3, 3, 3, 3.5, 3.5, 3.5, 4, 4, 4.5],
    'AIME': [2.5, 3, 3, 3.5, 3.5, 4, 4, 4.5, 4.5, 5, 5, 5.5, 5.5, 6, 6.5],
}


def to_scale(aops):
    """An AoPS competition rating on Summit's 1-10 scale, in half points."""
    value = 1 + (float(aops) - 1) * 9 / (AOPS_TOP - 1)
    return max(1.0, min(10.0, round(value * 2) / 2))


def to_aops(rating):
    """A Summit 1-10 rating back on the AoPS scale (not rounded)."""
    return 1 + (float(rating) - 1) * (AOPS_TOP - 1) / 9


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
    Summit rating: 1 is a real AMC 10 #1-4, 5 is #22-25 and up (AoPS 3.5+)."""
    if rating <= 1:
        return 1
    if rating <= 2:
        return 2
    if rating <= 2.5:
        return 3
    if rating <= 4.5:
        return 4
    return 5
