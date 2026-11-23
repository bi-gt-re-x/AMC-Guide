"""How every official paper actually went, and a score read against it.

## The figures

`RESULTS` is the MAA's published statistics for each AMC 10, AMC 12 and AIME
since 2000, as collected on the AoPS wiki's "AMC historical results" page:
the mean (and median where given), the AIME floor, the scores at the top 25%,
10%, 5% (Honor Roll), 2.5% and 1% (Distinguished Honor Roll), the share of
students who qualified for the AIME, how many sat it, and for the AIME the
USAMO / USAJMO index cutoffs. A blank figure is one the page does not give.
Two are left out as plainly wrong: the 2003 AMC 10B mean (listed as 5).

Since 2026 the AIME floor is fixed at 100 on the AMC 10 and 85 on the AMC 12,
whatever the paper (`FIXED_FLOOR`), so the 2026 papers carry those.

## Reading a score against it

* `standing(contest_id, score)` places a score on the paper it was sat on:
  how far above or below that year's AIME floor, about what share of real
  students it beat (interpolated between the published cutoffs: the mean
  taken as the middle, then top 25%, 10%, the floor's share, 5%, 2.5%, 1%),
  and the award it would have earned (AIME qualifier, Honor Roll, DHR).
* `adjusted(contest_id, score)` is the same score on today's scale: the paper's
  mean and AIME floor mapped onto a typical recent paper's (`REFERENCE`), whose
  floor is the fixed 100 / 85. A 99 on the 2025 AMC 10B (floor 99) and a 105
  on the 2025 AMC 10A (floor 105) both read as about 100: the same result on
  papers of different difficulty. Best, average, improvement and the score
  chart use it, so an easier paper does not look like progress.

## Scoring rules

Until 2006 a blank was worth 2.5 points, not 1.5 (`blank_points`), and the
figures for those years are in those points. A sitting here is scored at 1.5
a blank like every other, so a sitting's standing on an old paper is worked
out from its own right and blank counts under that year's rules
(`rules_score`).
"""

#: The AIME floor since 2026, fixed whatever the paper.
FIXED_FLOOR = {'AMC 10': 100.0, 'AMC 12': 85.0}

#: A typical recent paper: what `adjusted` maps every paper onto. The means are
#: the 2020-2025 averages; the floors are the fixed ones. The AIME's is a
#: typical recent mean and top 5%.
REFERENCE = {
    'AMC 10': {'mean': 60.0, 'floor': 100.0},
    'AMC 12': {'mean': 62.0, 'floor': 85.0},
    'AIME': {'mean': 5.5, 'top5': 11.5},
}


def _r(**kw):
    return kw


# AMC 10 / AMC 12: mean, median, floor (AIME floor), floor_pct (share who
# qualified, in %), top25, top10, hr (top 5%), top2_5, dhr (top 1%), students.
# AIME: mean, median, top5, top2_5, top1, students, usamo / usajmo (index
# cutoffs: one number, or by AMC paper as {'A': .., 'B': ..}).
RESULTS = {
    # ------------------------------------------------------------------ 2026
    '2026-amc-10a': _r(floor=100), '2026-amc-10b': _r(floor=100),
    '2026-amc-12a': _r(floor=85), '2026-amc-12b': _r(floor=85),
    '2026-aime-i': _r(mean=6.27, median=6, top5=13, top2_5=14, top1=14, students=4752),
    '2026-aime-ii': _r(mean=6.56, median=6, top5=13, top2_5=14, top1=15, students=672),
    # ------------------------------------------------------------------ 2025
    '2025-amc-10a': _r(mean=57.13, floor=105, top25=69, top10=94.5, hr=112.5, top2_5=124.5, dhr=136.5,
                       students=31617),
    '2025-amc-10b': _r(mean=57.00, floor=99, floor_pct=6, top25=66, top10=87, hr=105, top2_5=120, dhr=133.5,
                       students=25195),
    # Problem 25 was voided; everyone got its 6 points.
    '2025-amc-12a': _r(mean=64.44, floor=96, floor_pct=13, top25=78, top10=106.5, hr=127.5, top2_5=141,
                       dhr=150, students=20446),
    '2025-amc-12b': _r(mean=65.99, floor=100.5, floor_pct=12.5, top25=81, top10=109.5, hr=127.5, top2_5=139.5,
                       dhr=145.5, students=16441),
    '2025-aime-i': _r(mean=6.16, median=6, top5=11, top2_5=12, top1=13, students=4690,
                      usamo={'A': 237, 'B': 249.5}, usajmo={'A': 233, 'B': 243}),
    '2025-aime-ii': _r(mean=6.24, median=6, top5=12, top2_5=12, top1=13, students=1518,
                       usamo={'A': 242, 'B': 251.5}, usajmo={'A': 233.5, 'B': 241}),
    # ------------------------------------------------------------------ 2024
    '2024-amc-10a': _r(mean=58, floor=94.5, floor_pct=7, hr=105, top2_5=118.5, dhr=132, students=30545),
    '2024-amc-10b': _r(mean=61.77, floor=105, floor_pct=7, hr=114, top2_5=126, dhr=138, students=23372),
    '2024-amc-12a': _r(mean=56.5, floor=76.5, floor_pct=16, hr=108, top2_5=123, dhr=133.5, students=22222),
    '2024-amc-12b': _r(mean=61.74, floor=88.5, floor_pct=15, hr=118.5, top2_5=132, dhr=139.5, students=16522),
    '2024-aime-i': _r(mean=5.89, median=5, top5=12, top2_5=13, top1=14, students=5571,
                      usamo={'A': 245, 'B': 248}, usajmo={'A': 236, 'B': 232}),
    '2024-aime-ii': _r(mean=5.45, median=5, top5=10, top2_5=11, top1=14, students=1152,
                       usamo={'A': 220, 'B': 228}, usajmo={'A': 230, 'B': 220}),
    # ------------------------------------------------------------------ 2023
    '2023-amc-10a': _r(mean=64.74, floor=103.5, floor_pct=7, hr=111, dhr=136.5, students=30043),
    '2023-amc-10b': _r(mean=63, floor=105, floor_pct=6, hr=112.5, dhr=135, students=22912),
    '2023-amc-12a': _r(mean=61.56, floor=85.5, floor_pct=16, hr=112.5, dhr=136.5, students=21937),
    '2023-amc-12b': _r(mean=61.5, floor=88.5, floor_pct=16, hr=115.5, dhr=139.5, students=16656),
    '2023-aime-i': _r(mean=4.28, median=5, top5=10, top2_5=11, top1=13, students=5853,
                      usamo={'A': 223, 'B': 227}, usajmo={'A': 194, 'B': 190.5}),
    '2023-aime-ii': _r(mean=4.41, median=4, top5=9, top2_5=11, top1=13, students=696,
                       usamo={'A': 214.5, 'B': 226}, usajmo={'A': 188, 'B': 180}),
    # ------------------------------------------------------------------ 2022
    '2022-amc-10a': _r(mean=58.33, floor=93, floor_pct=8, hr=99, dhr=120, students=27411),
    '2022-amc-10b': _r(mean=57.91, floor=94.5, floor_pct=8, hr=100.5, dhr=114, students=22885),
    '2022-amc-12a': _r(floor=85.5, floor_pct=13, hr=106.5, dhr=126, students=19393),
    '2022-amc-12b': _r(floor=81, floor_pct=15, hr=105, dhr=129, students=18073),
    '2022-aime-i': _r(mean=4.83, median=4, usamo={'A': 222, 'B': 227.5}, usajmo={'A': 203.5, 'B': 190.5}),
    '2022-aime-ii': _r(mean=4.40, median=4, usamo={'A': 208.5, 'B': 203}, usajmo={'A': 196.5, 'B': 182}),
    # ----------------------------------------------------- 2021 (fall, Nov)
    '2021-fall-amc-10a': _r(mean=59.63, floor=96, floor_pct=6.16, hr=100.5, dhr=117),
    '2021-fall-amc-10b': _r(mean=56.57, floor=96, floor_pct=6.25, hr=100.5, dhr=120),
    '2021-fall-amc-12a': _r(mean=63.65, floor=91.5, floor_pct=12.62, hr=111, dhr=130.5),
    '2021-fall-amc-12b': _r(mean=57.37, floor=84, floor_pct=11.86, hr=103.5, dhr=130.5),
    # ---------------------------------------------------- 2021 (spring, Feb)
    '2021-amc-10a': _r(mean=65.53, floor=103.5, hr=112.5, dhr=132),
    '2021-amc-10b': _r(mean=62.31, floor=102, hr=108, dhr=126),
    '2021-amc-12a': _r(mean=67.42, floor=93, hr=114, dhr=133.5),
    '2021-amc-12b': _r(mean=61.55, floor=91.5, hr=109.5, dhr=132),
    '2021-aime-i': _r(mean=5.44, median=5, usamo={'A': 229.5, 'B': 231.5}, usajmo={'A': 217, 'B': 213}),
    '2021-aime-ii': _r(mean=5.42, median=5, usamo={'A': 238, 'B': 238}, usajmo={'A': 223, 'B': 214.5}),
    # ------------------------------------------------------------------ 2020
    '2020-amc-10a': _r(mean=64.29, floor=103.5, hr=105, dhr=124.5),
    '2020-amc-10b': _r(mean=61.22, floor=102, hr=103.5, dhr=120),
    '2020-amc-12a': _r(mean=61.42, floor=87, hr=100.5, dhr=123),
    '2020-amc-12b': _r(mean=60.47, floor=87, hr=97.5, dhr=120),
    '2020-aime-i': _r(mean=5.69, median=6, usamo={'A': 233.5, 'B': 235}, usajmo={'A': 229.5, 'B': 230}),
    # Given online that year, as the AOIME.
    '2020-aime-ii': _r(mean=6.13, median=6, usamo={'A': 234, 'B': 234.5}, usajmo={'A': 233.5, 'B': 229.5}),
    # ------------------------------------------------------------------ 2019
    '2019-amc-10a': _r(mean=51.66, floor=103.5, hr=96, dhr=123),
    '2019-amc-10b': _r(mean=58.42, floor=108, hr=102, dhr=121.5),
    '2019-amc-12a': _r(mean=49.22, floor=84, dhr=121.5),
    '2019-amc-12b': _r(mean=56.73, floor=94.5, dhr=123),
    '2019-aime-i': _r(mean=5.88, median=6, usamo={'A': 220, 'B': 230.5}, usajmo={'A': 209.5, 'B': 216}),
    '2019-aime-ii': _r(mean=6.47, median=6, usamo={'A': 230.5, 'B': 236}, usajmo={'A': 216.5, 'B': 220.5}),
    # ------------------------------------------------------------------ 2018
    '2018-amc-10a': _r(mean=53.84, floor=111, hr=100.5, dhr=127.5),
    '2018-amc-10b': _r(mean=57.81, floor=108, hr=97.5, dhr=123),
    '2018-amc-12a': _r(mean=56.36, floor=93, dhr=120),
    '2018-amc-12b': _r(mean=57.85, floor=99, dhr=126),
    '2018-aime-i': _r(mean=5.09, median=5, usamo={'A': 215, 'B': 235}, usajmo={'A': 222, 'B': 212}),
    '2018-aime-ii': _r(mean=5.48, median=5, usamo={'A': 216, 'B': 230.5}, usajmo={'A': 222, 'B': 212}),
    # ------------------------------------------------------------------ 2017
    '2017-amc-10a': _r(mean=59.33, median=55.5, floor=112.5, hr=112.5, dhr=127.5),
    # The page gives the 10B's Honor Roll as 126.66666.
    '2017-amc-10b': _r(mean=66.56, median=61.5, floor=120, hr=126.67, dhr=136.5),
    '2017-amc-12a': _r(mean=57.0, median=52.5, floor=96, hr=96, dhr=115.5),
    '2017-amc-12b': _r(mean=58.35, median=54, floor=100.5, hr=100.5, dhr=129),
    '2017-aime-i': _r(mean=5.69, median=5, usamo={'A': 225.5, 'B': 235}, usajmo={'A': 224.5, 'B': 233}),
    '2017-aime-ii': _r(mean=5.64, median=5, usamo={'A': 221, 'B': 230.5}, usajmo={'A': 219, 'B': 225}),
    # ------------------------------------------------------------------ 2016
    '2016-amc-10a': _r(mean=65.31, floor=111, dhr=120),
    '2016-amc-10b': _r(mean=65.40, floor=111, dhr=124.5),
    '2016-amc-12a': _r(mean=60.32, floor=93, dhr=111),
    '2016-amc-12b': _r(mean=68.65, floor=100.5, dhr=127.5),
    '2016-aime-i': _r(mean=5.83, median=6, usamo=220, usajmo=210.5),
    '2016-aime-ii': _r(mean=4.43, median=4, usamo=205, usajmo=200),
    # ------------------------------------------------------------------ 2015
    '2015-amc-10a': _r(mean=73.39, floor=106.5, dhr=115.5),
    '2015-amc-10b': _r(mean=76.09, floor=120, dhr=132),
    '2015-amc-12a': _r(mean=69.90, floor=99, dhr=117),
    '2015-amc-12b': _r(mean=66.88, floor=100.5, dhr=126),
    '2015-aime-i': _r(mean=5.29, median=5, usamo=219, usajmo=213),
    '2015-aime-ii': _r(mean=6.63, median=6, usamo=229, usajmo=223.5),
    # ------------------------------------------------------------------ 2014
    '2014-amc-10a': _r(mean=63.34, floor=120, dhr=132),
    '2014-amc-10b': _r(mean=71.42, floor=120, dhr=132),
    '2014-amc-12a': _r(mean=63.60, floor=93, dhr=109.5),
    '2014-amc-12b': _r(mean=68.12, floor=100.5, dhr=121.5),
    '2014-aime-i': _r(mean=4.88, median=5, usamo=211.5, usajmo=211),
    '2014-aime-ii': _r(mean=5.49, median=5, usamo=211.5, usajmo=211),
    # ------------------------------------------------------------------ 2013
    '2013-amc-10a': _r(mean=72.50, floor=108, dhr=117),
    '2013-amc-10b': _r(mean=72.62, floor=120, dhr=129),
    '2013-amc-12a': _r(mean=65.06, floor=88.5, dhr=106.5),
    '2013-amc-12b': _r(mean=64.21, floor=93, dhr=108),
    '2013-aime-i': _r(mean=4.69, median=4, usamo=209, usajmo=210.5),
    '2013-aime-ii': _r(mean=6.56, median=6, usamo=209, usajmo=210.5),
    # ------------------------------------------------------------------ 2012
    '2012-amc-10a': _r(mean=72.51, floor=115.5, dhr=121.5),
    '2012-amc-10b': _r(mean=76.59, floor=120, dhr=133.5),
    '2012-amc-12a': _r(mean=64.62, floor=94.5, dhr=109.5),
    '2012-amc-12b': _r(mean=70.08, floor=99, dhr=114),
    '2012-aime-i': _r(mean=5.13, median=5, usamo=204.5, usajmo=204),
    '2012-aime-ii': _r(mean=4.94, median=5, usamo=204.5, usajmo=204),
    # ------------------------------------------------------------------ 2011
    '2011-amc-10a': _r(mean=64.24, floor=117, hr=117, dhr=129),
    '2011-amc-10b': _r(mean=71.78, floor=117, hr=117, dhr=133.5),
    '2011-amc-12a': _r(mean=65.38, floor=93, hr=92, dhr=112.5),
    '2011-amc-12b': _r(mean=64.71, floor=97.5, hr=92, dhr=121.5),
    '2011-aime-i': _r(mean=2.23, median=2, usamo=188, usajmo=179),
    '2011-aime-ii': _r(mean=5.47, median=5, usamo=215.5, usajmo=196.5),
    # ------------------------------------------------------------------ 2010
    '2010-amc-10a': _r(mean=70.8, floor=118.5, floor_pct=1.5, hr=118.5, dhr=121.5),
    '2010-amc-10b': _r(mean=68.3, floor=118.5, floor_pct=2.0, hr=118.5, dhr=124.5),
    '2010-amc-12a': _r(mean=62.5, floor=88.5, floor_pct=7.1, hr=88.5, dhr=108),
    '2010-amc-12b': _r(mean=59.8, floor=88.5, floor_pct=8.0, hr=88.5, dhr=108),
    '2010-aime-i': _r(mean=4.12, median=3, students=3618),
    '2010-aime-ii': _r(mean=5.91, median=6, students=2904),
    # ------------------------------------------------------------------ 2009
    '2009-amc-10a': _r(mean=70.4, floor=120, floor_pct=4.2, hr=120, dhr=133.5),
    '2009-amc-10b': _r(mean=74.4, floor=120, floor_pct=7.5, hr=124.5, dhr=141),
    '2009-amc-12a': _r(mean=68.0, floor=97.5, floor_pct=6.7, hr=100.5, dhr=117),
    '2009-amc-12b': _r(mean=71.7, floor=100, floor_pct=10.8, hr=108, dhr=124.5),
    '2009-aime-i': _r(mean=4.17, median=4),
    '2009-aime-ii': _r(mean=3.27, median=3),
    # ------------------------------------------------------------------ 2008
    '2008-amc-10a': _r(mean=58.1, floor=117, floor_pct=2.6, hr=100.5, dhr=127.5),
    '2008-amc-10b': _r(mean=66.6, floor=120, floor_pct=2.7, hr=100.5, dhr=127.5),
    '2008-amc-12a': _r(mean=65.6, floor=97.5, floor_pct=6.5, hr=97.5, dhr=120),
    '2008-amc-12b': _r(mean=68.9, floor=97.5, floor_pct=8.1, hr=97.5, dhr=120),
    '2008-aime-i': _r(mean=4.77, median=4),
    '2008-aime-ii': _r(mean=5.27, median=5),
    # ------------------------------------------------------------------ 2007
    '2007-amc-10a': _r(mean=67.9, floor=117),
    '2007-amc-10b': _r(mean=61.5, floor=115.5),
    '2007-amc-12a': _r(mean=66.8, floor=97.8),
    '2007-amc-12b': _r(mean=73.1, floor=100),
    '2007-aime-i': _r(mean=5, median=3),
    # ------------------------------------------------------------------ 2006
    '2006-amc-10a': _r(mean=79.0, floor=120, floor_pct=2.7),
    '2006-amc-10b': _r(mean=68.5, floor=120, floor_pct=2.3),
    '2006-amc-12a': _r(mean=85.7, floor=100, floor_pct=22.3),
    '2006-amc-12b': _r(mean=85.5, floor=100, floor_pct=21.2),
    # ------------------------------------------------------------------ 2005
    '2005-amc-10a': _r(mean=74.7, floor=120, floor_pct=1.9, hr=100, dhr=120),
    '2005-amc-10b': _r(mean=77.9, floor=120, floor_pct=1.6, hr=100, dhr=120),
    '2005-amc-12a': _r(mean=78.7, floor=100, floor_pct=11.2, hr=100, dhr=120),
    '2005-amc-12b': _r(mean=83.4, floor=100, floor_pct=12.8, hr=100, dhr=120),
    '2005-aime-i': _r(mean=2.754, students=11197, usamo=233),
    '2005-aime-ii': _r(mean=2.439, students=1279, usamo=220.5),
    # ------------------------------------------------------------------ 2004
    '2004-amc-10a': _r(mean=69.1, floor=110, floor_pct=1.4, hr=100, dhr=112.5),
    '2004-amc-10b': _r(mean=80.4, floor=115, floor_pct=2.1, hr=100, dhr=126),
    '2004-amc-12a': _r(mean=73.9, floor=100, floor_pct=8.1, hr=100, dhr=117),
    '2004-amc-12b': _r(mean=84.5, floor=100, floor_pct=19.2, hr=100, dhr=123),
    '2004-aime-i': _r(mean=2.246, students=9824),
    '2004-aime-ii': _r(mean=1.959, students=2121),
    # ------------------------------------------------------------------ 2003
    '2003-amc-10a': _r(mean=74.4, floor=119, floor_pct=2.0),
    '2003-amc-10b': _r(floor=120, floor_pct=1.2),            # the page's mean, 5, is a typo
    '2003-amc-12a': _r(mean=77.8, floor=100, floor_pct=12.2),
    '2003-amc-12b': _r(mean=76.6, floor=100, floor_pct=9.6),
    '2003-aime-i': _r(usamo=226), '2003-aime-ii': _r(usamo=226),
    # ------------------------------------------------------------------ 2002
    '2002-amc-10a': _r(mean=68.5, floor=115, floor_pct=1.2),
    '2002-amc-10b': _r(mean=74.9, floor=118, floor_pct=1.5),
    '2002-amc-12a': _r(mean=72.7, floor=100, floor_pct=7.2),
    '2002-amc-12b': _r(mean=80.8, floor=100, floor_pct=16.8),
    # ------------------------------------------------------------------ 2001
    '2001-amc-10': _r(mean=67.8, floor=116, floor_pct=1.7),
    '2001-amc-12': _r(mean=56.6, floor=84, floor_pct=3.4),
    # ------------------------------------------------------------------ 2000
    '2000-amc-10': _r(mean=64.2, floor=111),
    '2000-amc-12': _r(mean=64.9, floor=93, floor_pct=3.3),
    '2000-aime-i': _r(mean=4.20), '2000-aime-ii': _r(mean=4.13),
}


def _contest(contest_id):
    from backend.amc import catalog
    return catalog.PAST_BY_ID.get(contest_id)


def blank_points(contest_id):
    """Points a blank was worth on that paper: 2.5 until 2006, 1.5 since."""
    c = _contest(contest_id)
    if not c or c['level'] == 'AIME':
        return 0.0
    return 2.5 if c['year'] <= 2006 else 1.5


def rules_score(contest_id, correct, blank):
    """A sitting's score under the paper's own rules, from its right and blank counts."""
    return 6 * correct + blank_points(contest_id) * blank


def _anchors(level, r):
    """(score, percentile) points to interpolate a standing between, rising in both."""
    top = 15 if level == 'AIME' else 150
    middle = r.get('median') if r.get('median') is not None else r.get('mean')
    pts = [(0.0, 0.0)]
    if middle is not None:
        pts.append((float(middle), 50.0))
    if level == 'AIME':
        pts += [(r.get('top5'), 95.0), (r.get('top2_5'), 97.5), (r.get('top1'), 99.0)]
    else:
        pts += [(r.get('top25'), 75.0), (r.get('top10'), 90.0), (r.get('hr'), 95.0),
                (r.get('top2_5'), 97.5), (r.get('dhr'), 99.0)]
        if r.get('floor') is not None and r.get('floor_pct') is not None:
            pts.append((r['floor'], 100.0 - r['floor_pct']))
    pts = sorted((float(s), p) for s, p in pts if s is not None)
    out = []
    for s, p in pts:
        # Keep the points that rise in both: two cutoffs at one score keep the higher share.
        if out and s == out[-1][0]:
            out[-1] = (s, max(p, out[-1][1]))
        elif not out or p > out[-1][1]:
            out.append((s, p))
    if out[-1][0] < top:
        out.append((float(top), 100.0))
    return out


def percentile(contest_id, score):
    """About what share of the real field `score` beat on that paper (0-100), or None."""
    c, r = _contest(contest_id), RESULTS.get(contest_id)
    if not c or not r:
        return None
    pts = _anchors(c['level'], r)
    if len(pts) < 3:               # nothing between 0 and a perfect score
        return None
    score = float(score)
    for (s0, p0), (s1, p1) in zip(pts, pts[1:]):
        if score <= s1:
            return round(p0 + (p1 - p0) * (score - s0) / (s1 - s0), 1) if s1 > s0 else p1
    return 100.0


def adjusted(contest_id, score):
    """`score` on a typical recent paper of the same contest, to the nearest half
    (the score itself where the paper's figures are not known)."""
    c, r = _contest(contest_id), RESULTS.get(contest_id)
    if not c or not r:
        return score
    level = c['level']
    ref = REFERENCE[level]
    if level == 'AIME':
        top, cap, lo_key, hi_key = 15.0, 15.0, 'mean', 'top5'
    else:
        top, cap, lo_key, hi_key = 150.0, 150.0, 'mean', 'floor'
    lo, hi = r.get(lo_key), r.get(hi_key)
    score = float(score)
    if lo is not None and hi is not None and hi - lo > 5 * (0.1 if level == 'AIME' else 1):
        value = ref[lo_key] + (score - lo) * (ref[hi_key] - ref[lo_key]) / (hi - lo)
    elif hi is not None:
        value = score + ref[hi_key] - hi            # shift by the floor alone
    elif lo is not None:
        value = score + ref[lo_key] - lo
    else:
        return score
    return max(0.0, min(cap, round(value * 2) / 2))


def floor(contest_id):
    c, r = _contest(contest_id), RESULTS.get(contest_id) or {}
    if r.get('floor') is not None:
        return float(r['floor'])
    if c and c['year'] >= 2026 and c['level'] in FIXED_FLOOR:
        return FIXED_FLOOR[c['level']]
    return None


def award(contest_id, score):
    """The best of DHR, Honor Roll and AIME qualifier the score would have earned, or ''."""
    r = RESULTS.get(contest_id) or {}
    if r.get('dhr') is not None and score >= r['dhr']:
        return 'Distinguished Honor Roll'
    if r.get('hr') is not None and score >= r['hr']:
        return 'Honor Roll'
    f = floor(contest_id)
    if f is not None and score >= f:
        return 'AIME qualifier'
    return ''


def standing(contest_id, score, correct=None, blank=None):
    """A score read against the paper it was sat on, for the pages and the coach.

    With the sitting's right and blank counts, an old paper's standing is
    worked out under that year's scoring (a blank was 2.5 until 2006); the
    adjusted score is always from the score as sat here.
    """
    c = _contest(contest_id)
    if not c:
        return None
    r = RESULTS.get(contest_id) or {}
    as_then = score
    if correct is not None and blank is not None and c['level'] != 'AIME' and blank_points(contest_id) != 1.5:
        as_then = rules_score(contest_id, correct, blank)
    f = floor(contest_id)
    pct = percentile(contest_id, as_then)
    return {
        'score': score,
        'scored_as': as_then,
        'adjusted': adjusted(contest_id, as_then) if (r or f is not None) else score,
        'percentile': pct,
        'top': None if pct is None else max(1, round(100 - pct)) if pct < 99.5 else 1,
        'floor': f,
        'vs_floor': None if f is None else round(as_then - f, 1),
        'award': award(contest_id, as_then),
        'mean': r.get('mean'),
        'students': r.get('students'),
    }


def paper(contest_id):
    """The figures for one paper, for its page (None when nothing is known)."""
    r = dict(RESULTS.get(contest_id) or {})
    f = floor(contest_id)
    if f is not None:
        r['floor'] = f
    if not r:
        return None
    r['blank_points'] = blank_points(contest_id)
    return r


def of_row(row):
    """`standing` for a stored sitting or logged score (an amc_mocks row), or None.
    A logged score has no right/blank counts, so it is read as given."""
    if not _contest(row.get('contest_id')):
        return None
    timed = row.get('kind') == 'mock'
    return standing(row['contest_id'], row['score'],
                    row.get('correct') if timed else None, row.get('blank') if timed else None)
