"""How hard each AMC Guide Mock problem really is, on the AoPS scale.

A set's problems are written for a slot on the paper, and at first each was
rated by its slot (backend/amc/scale.py, `RATING_BY_NUMBER`). A review of every
problem against the 2023-2026 AMC 10s and recent AMC 12s and AIMEs found the
AMC Guide Mocks run easier than real papers, and more so toward the end: most of
an AMC 10's #15-25 sit half a point to a point below a real problem in the same
place, the AMC 12 sets' #20-25 lean on well-known techniques, and the AIME sets
open at AMC 10 level (#1-5 around 1.5-2.5, where a real AIME starts at 2.5-3)
and close about a point below a real #13-15.

So each problem's rating comes from here, not from its slot: what a student
sees ("4.5 / 10"), the filters, and the ability model in backend/amc/smart.py
all use the problem's own difficulty. The paper order is unchanged.

Ratings are AoPS competition ratings in half points, one per problem in paper
order. An AMC 12 set lists only its own problems (the ones not shared with its
AMC 10, in order); a shared problem keeps the rating of its AMC 10 original,
since difficulty belongs to the problem and not to where it is printed.
tests/test_amc_sets.py checks that every list is complete.

Sets 6 and 7 were written later and rated the same way: each problem against
the problems of sets 1-5 it most resembles (a two-chain decomposition like
10-3-22's run of consecutive numbers, an expected wait like 10-4-21's), not by
the slot it fills. So they sit on the same scale and, like the first five, run
a little easier than a real paper toward the end.
"""

AOPS = {
    # ------------------------------------------------------------ AMC 10, #1-25
    'mock10-1': [1, 1, 1, 1, 1, 1.5, 2, 1, 1.5, 1, 2, 1.5, 2, 1.5, 2.5,
                 2.5, 2, 2, 2.5, 2.5, 2, 3, 3, 3, 3.5],
    'mock10-2': [1, 1, 1, 1.5, 1.5, 1, 2, 1.5, 1, 1.5, 1.5, 1.5, 2, 2, 2,
                 2, 2, 2, 2.5, 2.5, 3, 2.5, 3, 3.5, 3],
    'mock10-3': [1, 1, 1, 1, 1, 1, 2, 1, 1.5, 1.5, 2, 1, 2, 1.5, 1.5,
                 2, 2.5, 2, 2.5, 2.5, 3, 3, 3, 3, 3.5],
    'mock10-4': [1, 1, 1, 1, 1, 1, 1, 1, 1.5, 1.5, 1.5, 1.5, 2, 1.5, 2,
                 2.5, 2, 1.5, 2.5, 2, 2.5, 3, 3, 3, 3.5],
    'mock10-5': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1.5, 2, 1.5, 2,
                 2, 2, 2, 2, 2, 2, 2.5, 2.5, 3, 3.5],
    'mock10-6': [1, 1, 1, 1, 1.5, 1.5, 1.5, 1, 1.5, 1, 1.5, 1.5, 2, 1.5, 2,
                 2, 2, 1.5, 2, 2.5, 2.5, 2.5, 3, 2.5, 3],
    'mock10-7': [1, 1, 1, 1, 1, 1, 1.5, 1, 1.5, 2, 1.5, 2, 1.5, 1.5, 1.5,
                 1.5, 2, 2.5, 2, 2, 2.5, 2.5, 2.5, 2.5, 3],
    # ------------------------------------- AMC 12, own problems only, in order
    # (#1-8, 10, 12, 14, 16, 19, 22, 23, 24, 25; the rest are shared)
    'mock12-1': [1, 1, 1, 1, 1.5, 1, 1, 1, 1.5, 1.5, 1.5, 2, 2, 3, 3, 3, 4],
    'mock12-2': [1, 1, 1, 1, 1.5, 1, 1.5, 1.5, 1, 1.5, 1.5, 1.5, 2.5, 3, 3.5, 3, 3.5],
    'mock12-3': [1, 1, 1, 1, 1.5, 1, 1, 1, 1.5, 1.5, 2, 1.5, 2, 2.5, 3, 2.5, 3.5],
    'mock12-4': [1, 1, 1, 1, 1, 1, 1, 1.5, 1, 1, 2, 2, 1.5, 2.5, 3, 2.5, 4],
    'mock12-5': [1, 1, 1, 1, 1, 1, 1.5, 1, 1.5, 2, 1, 2.5, 2.5, 3, 3, 3, 3.5],
    'mock12-6': [1, 1, 1, 1, 1, 1, 1, 1, 1.5, 2, 2, 2.5, 3, 2.5, 3, 3, 3.5],
    'mock12-7': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1.5, 2, 2, 2.5, 2.5, 3, 3, 3.5],
    # -------------------------------------------------------------- AIME, #1-15
    'mockaime-1': [1.5, 1.5, 1.5, 2.5, 1.5, 2.5, 2.5, 3, 3, 3, 3.5, 3.5, 4, 4, 5],
    'mockaime-2': [1.5, 1.5, 2, 2, 1.5, 3, 2, 2.5, 2.5, 3, 3.5, 4, 4, 4, 4.5],
    'mockaime-3': [1.5, 2, 2.5, 1.5, 2.5, 2, 2, 2.5, 3, 3.5, 3.5, 3, 4, 3.5, 5],
    'mockaime-4': [1.5, 2, 1.5, 2.5, 2, 2.5, 2.5, 2, 2.5, 3, 2.5, 3.5, 3.5, 3.5, 4.5],
    'mockaime-5': [1, 2, 1, 2.5, 2, 2.5, 2, 3.5, 2.5, 3, 2.5, 3.5, 2.5, 3.5, 4.5],
    'mockaime-6': [2, 2, 2.5, 2, 2, 2, 2.5, 3, 2.5, 2.5, 3.5, 3, 3.5, 4, 5],
    'mockaime-7': [2, 2, 2, 2, 2.5, 2.5, 2, 3, 2.5, 3, 3.5, 3, 3, 3, 3.5],
}
