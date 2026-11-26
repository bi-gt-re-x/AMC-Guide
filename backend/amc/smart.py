r"""Smart analytics: a model of the student, not just counts.

## Ability on the problems' own scale

Every problem carries an AMC Guide 1-12 rating (backend/amc/scale.py: the AoPS
rating times 2, so an AMC 10 #1 is a 2 and the hardest AIME problem a 12). We model the chance of solving a problem
of rating r at the first try as

    P(r) = 1 / (1 + exp(SLOPE * (r - theta)))

so `theta` is the rating the student solves half the time, on the same scale
as the problems. It is fitted by maximum a posteriori from first attempts only
(a second try after seeing a solution says nothing about contest day), with a
normal prior so that three answers cannot claim a 9.

**Kept, not just met.** A problem answered again `engine.RETEST_DAYS` or more
after the try before it (a review at 10 or 21 days, a spaced set, an accuracy
set's old misses) is a fresh retrieval, and the latest such answer counts too,
at `RETEST_WEIGHT` of a first try: memory of the solution makes it weaker
evidence, but it is how a topic that has been put right shows it, and how one
that has slipped away again shows that. `ability_points` is the list every fit
reads; counts of answers and first-try accuracy stay on first tries.

**Recent answers count more.** Each first attempt is weighted by its age, with
a half-life of `HALF_LIFE` days and a floor, so the level follows the student's
current form instead of averaging in where they were two months ago, while old
evidence never quite stops counting.

Each topic and each technique gets its own theta with the overall one as its
prior, so a topic with two answers sits near the student's overall level and
moves away only as evidence comes in.

## What follows from it

* **Predicted scores** for each contest, using the real paper's ratings by
  problem number and the best answer-or-skip strategy (answer when the chance
  beats the 1.5 points of a blank), with a range from theta's uncertainty and
  the chance of reaching the cutoff, by simulation.
* **Timed predictions.** The student's own pace is modeled from their first
  attempts (time grows with how hard a problem is for *them*), and a sitting is
  walked through in order against the clock: problems they would answer cost
  their expected time, the ones worth skipping cost a quick read. What does not
  fit in the time is left blank. The gap between the untimed and timed
  prediction is the points speed is costing.
* **The reachable part of a paper**: up to which number the student is more
  likely right than wrong.
* **Points at stake by topic**: how many points on their contest it would add
  to bring each weak topic up to their overall level (or 1.2 points above it, for
  a topic already there), from how often the topic appears and where on the
  paper. The focus list is sorted by it, and holds only topics the student has
  answered: one never tried is not known to be weak, so it is not called a
  weakness (here, in the AI coach's reading, or for "my weakest topic").
* **What to do next**: unsolved problems in those topics that they get right
  between half and three-quarters of the time (hard enough to teach, easy
  enough to finish), no more than two from one topic.
* **Patterns**: careless misses (wrong on problems well below their level),
  time sinks, rushed answers, solutions revealed before trying, and timed mocks
  that come in well below what the model expects (test-day pressure).
* **Trend**: theta refitted at the end of each of the last six weeks.

Nothing here needs a model key; backend/amc/coach.py and the AI diagnosis in
backend/api/amc_ai.py read this and write prose on top of it.
"""
import math
import random
from datetime import date, timedelta

from backend.amc import catalog, engine, results
from backend.amc import problems as pb
from backend.amc.scale import SCALE_BY_NUMBER

#: Bumped whenever the model or its scale changes, so a cached AI reading of
#: the old numbers (backend/api/amc_ai.py) is not shown beside the new ones.
MODEL_VERSION = 'summit-scale-4'
#: Logistic slope per AMC Guide rating point (1.6 per AoPS point, halved).
SLOPE = 0.8
#: Prior on a new student: about an AMC 10 #8-10 (AoPS 2), give or take a lot.
#: These, and every gap in rating points below, are in AMC Guide points (AoPS x 2).
PRIOR_MEAN = 4.0
PRIOR_SD = 2.95
TOPIC_SD = 1.55
#: Days for an answer's weight to halve, and the least weight an old answer keeps.
HALF_LIFE = 45
MIN_WEIGHT = 0.3
CUTOFFS = {'AMC 10': 100, 'AMC 12': 85}
#: Contest length in seconds, and seconds per problem at contest pace.
TIME_LIMIT = {'AMC 10': 75 * 60, 'AMC 12': 75 * 60, 'AIME': 180 * 60}
PACE = {'AMC 10': 180, 'AMC 12': 180, 'AIME': 720}
#: Seconds spent reading a problem before deciding to skip it.
SKIP_COST = {'AMC 10': 30, 'AMC 12': 30, 'AIME': 90}
#: The band of first-try chances a "do next" problem should fall in.
LEARN_BAND = (0.5, 0.75)


def chance(theta, rating):
    return 1 / (1 + math.exp(SLOPE * (rating - theta)))


def fit(points, mean=PRIOR_MEAN, sd=PRIOR_SD):
    """MAP theta and its standard error from [(rating, correct)] or
    [(rating, correct, weight)]."""
    theta = mean
    info = 1 / sd ** 2
    for _ in range(40):
        grad = -(theta - mean) / sd ** 2
        info = 1 / sd ** 2
        for point in points:
            rating, right = point[0], point[1]
            w = point[2] if len(point) > 2 else 1.0
            p = chance(theta, rating)
            grad += w * SLOPE * ((1 if right else 0) - p)
            info += w * SLOPE ** 2 * p * (1 - p)
        step = grad / info
        theta += max(-1.5, min(1.5, step))
        if abs(step) < 1e-6:
            break
    return round(theta, 2), round(1 / math.sqrt(info), 2)


def _weight(at, today):
    """How much an answer given on `at` (ISO date or time) counts on `today`."""
    try:
        age = (today - date.fromisoformat(str(at)[:10])).days
    except ValueError:
        return 1.0
    return max(MIN_WEIGHT, 0.5 ** (max(0, age) / HALF_LIFE))


def _first_points(hist, today=None, keep=None):
    """[(rating, first try right, weight, problem)] for every problem answered."""
    today = today or date.today()
    out = []
    for pid, h in hist.items():
        p = pb.get(pid)
        if p and (keep is None or keep(p)) and h.get('first_source') != 'reveal':
            out.append((p['rating'], h['first_correct'], _weight(h.get('first_at') or h.get('last_at'), today), p))
    return out


#: How much a spaced retest counts beside a first try (see the module's note).
RETEST_WEIGHT = 0.5


def ability_points(hist, today=None, keep=None):
    """`_first_points` and, for each problem retested after a gap, its latest
    retest at RETEST_WEIGHT: what the ability fits read."""
    today = today or date.today()
    out = _first_points(hist, today, keep)
    for pid, h in hist.items():
        again = h.get('retest')
        p = pb.get(pid) if again else None
        if p and (keep is None or keep(p)):
            out.append((p['rating'], again['correct'], RETEST_WEIGHT * _weight(again['at'], today), p))
    return out


def _expected(theta, level):
    """Expected score with the best answer-or-skip choice on each problem."""
    table = SCALE_BY_NUMBER[level]
    if level == 'AIME':
        return sum(chance(theta, r) for r in table)
    return sum(max(6 * chance(theta, r), 1.5) for r in table)


def projected(hist, level, today=None):
    """The expected score on a `level` paper, or None before there is enough to go on."""
    if len(hist) < engine.PROJECTION_MIN:
        return None
    pts = ability_points(hist, today)
    theta, _ = fit([(r, ok, w) for r, ok, w, _ in pts])
    score = _expected(theta, level)
    return round(score, 1) if level == 'AIME' else round(score * 2) / 2


def _simulate(theta, se, level, target, runs=2000, seed=7):
    """(low, high) 80% range and P(score >= target), by simulation."""
    rng = random.Random(seed)
    table = SCALE_BY_NUMBER[level]
    scores = []
    for _ in range(runs):
        t = rng.gauss(theta, se)
        total = 0.0
        for r in table:
            p = chance(t, r)
            if level == 'AIME':
                total += 1 if rng.random() < p else 0
            elif 6 * p > 1.5:
                total += 6 if rng.random() < p else 0
            else:
                total += 1.5
        scores.append(total)
    scores.sort()
    hit = sum(1 for s in scores if s >= target) / runs if target is not None else None
    return scores[int(runs * 0.1)], scores[int(runs * 0.9)], hit


def _reach(theta, level):
    """The last problem number solved more often than not."""
    last = 0
    for n, r in enumerate(SCALE_BY_NUMBER[level], start=1):
        if chance(theta, r) >= 0.5:
            last = n
    return last


# ---------------------------------------------------------------------------
# Pace
# ---------------------------------------------------------------------------
def pace_model(hist, theta):
    """How long the student takes on a first try, as a function of how hard the
    problem is *for them* (rating minus theta).

    A least-squares line through log(seconds) against (rating - theta), from
    timed first attempts that were not reveals, shrunk toward contest pace
    (the AMC's 3 minutes at their own level) when there are few of them.
    Returns (intercept, slope, n): seconds = exp(intercept + slope * gap).
    """
    xs, ys = [], []
    for pid, h in hist.items():
        secs = h.get('first_seconds') or 0
        p = pb.get(pid)
        if not p or secs < 10 or secs > 3600 or h.get('first_source') == 'reveal':
            continue
        xs.append(p['rating'] - theta)
        ys.append(math.log(secs))
    prior_a, prior_b, k = math.log(PACE['AMC 10']), 0.21, 6.0
    n = len(xs)
    if n < 3:
        return prior_a, prior_b, n
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx) if sxx > 1e-9 else prior_b
    b = max(0.0, min(0.67, b))
    a = my - b * mx
    # Shrink toward the prior: k pseudo-answers at contest pace.
    a = (n * a + k * prior_a) / (n + k)
    b = (n * b + k * prior_b) / (n + k)
    return a, b, n


def seconds_for(model, theta, rating, level):
    a, b, _ = model
    secs = math.exp(a + b * (rating - theta))
    # The AIME's problems take longer for everyone; scale by the contests' pace.
    return secs * PACE[level] / PACE['AMC 10']


def _timed(theta, level, model):
    """(expected score, last problem reached) working through a paper in order
    against the clock, answering where it pays and skipping where it does not."""
    table = SCALE_BY_NUMBER[level]
    left = TIME_LIMIT[level]
    total, reached = 0.0, 0
    for n, r in enumerate(table, start=1):
        p = chance(theta, r)
        answer = level == 'AIME' or 6 * p > 1.5
        cost = seconds_for(model, theta, r, level) if answer else SKIP_COST[level]
        if cost > left:
            # Out of time: everything from here on is blank.
            if level != 'AIME':
                total += 1.5 * (len(table) - n + 1)
            break
        left -= cost
        reached = n
        total += (p if level == 'AIME' else 6 * p) if answer else 1.5
    return total, reached


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------
def _topic_points(level, theta, topic_theta, weight, total_weight):
    """Points on a `level` paper from raising one topic's ability from
    `topic_theta` to the overall level (or 1.2 points above, if it is already
    there). A topic of weight w is about w / total_weight of the paper, spread
    over its positions in proportion."""
    target = max(theta, topic_theta + 1.2) if topic_theta is not None else theta
    current = topic_theta if topic_theta is not None else theta - 0.6
    table = SCALE_BY_NUMBER[level]
    share = weight / total_weight
    worth = 1 if level == 'AIME' else 6
    gain = 0.0
    for r in table:
        before, after = chance(current, r), chance(target, r)
        if level == 'AIME':
            gain += share * (after - before)
        else:
            gain += share * (max(worth * after, 1.5) - max(worth * before, 1.5))
    return round(gain, 1)


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
def _patterns(attempts, hist, theta, level, mock_check):
    pace = PACE.get(level, 180)
    first_rows = {}
    for a in attempts:
        if a['problem_id'] not in first_rows:
            first_rows[a['problem_id']] = a
    careless, slow, rushed = [], [], []
    for pid, a in first_rows.items():
        p = pb.get(pid)
        if not p or a['source'] == 'reveal':
            continue
        secs = int(a.get('seconds') or 0)
        pace_here = 720 if p['level'] == 'AIME' else 180
        if not a['correct'] and p['rating'] <= theta - 1.9:
            careless.append(pid)
        if secs > 2 * pace_here:
            slow.append(pid)
        if not a['correct'] and 0 < secs < 0.25 * pace_here:
            rushed.append(pid)
    reveals = [pid for pid, a in first_rows.items() if a['source'] == 'reveal']

    def brief(ids):
        return [{'id': pid, 'short': catalog.short_label(pid), 'topic': pb.get(pid)['topic'],
                 'rating': pb.get(pid)['rating']} for pid in ids[:8]]
    out = []
    if careless:
        out.append({'kind': 'careless', 'count': len(careless), 'problems': brief(careless),
                    'text': '{} first-try miss{} on problems well below your level. '
                            'These are points you already know how to get.'.format(len(careless), '' if len(careless) == 1 else 'es')})
    if slow:
        out.append({'kind': 'slow', 'count': len(slow), 'problems': brief(slow),
                    'text': '{} problem{} took more than twice contest pace ({} min each).'.format(
                        len(slow), '' if len(slow) == 1 else 's', pace // 60)})
    if rushed:
        out.append({'kind': 'rushed', 'count': len(rushed), 'problems': brief(rushed),
                    'text': '{} wrong answer{} came in under a quarter of contest pace. Slow down and check.'.format(
                        len(rushed), '' if len(rushed) == 1 else 's')})
    if reveals:
        out.append({'kind': 'revealed', 'count': len(reveals), 'problems': brief(reveals),
                    'text': '{} solution{} opened before trying. Try for five minutes first.'.format(
                        len(reveals), '' if len(reveals) == 1 else 's')})
    if mock_check and mock_check['taken'] >= 1 and mock_check['gap'] <= -6:
        out.append({'kind': 'pressure', 'count': mock_check['taken'], 'problems': [],
                    'text': 'Timed mocks come in {:g} points below what your practice predicts. The ideas are '
                            'there; the clock is costing you. Sit more timed papers and skip sooner.'.format(
                                -mock_check['gap'])})
    return out


def _scored(m):
    """One sitting for the brief: the score, and read against that paper's real results."""
    st = results.of_row(m)
    out = {'contest': m['contest_id'], 'score': m['score'], 'at': m['at'][:10]}
    if st:
        out.update(adjusted=st['adjusted'], top=st['top'], vs_floor=st['vs_floor'], award=st['award'])
    return out


def _mock_summary(mocks):
    graded = [m for m in mocks if m['kind'] == 'mock']
    if not graded:
        return None
    by_fifth = [[0, 0] for _ in range(5)]
    blanks = 0
    asked = 0
    for m in graded:
        ids = (m.get('answers') or {}).get('_ids') or []
        for n, pid in enumerate(ids, start=1):
            given = (m['answers'] or {}).get(str(n), '')
            p = pb.get(pid)
            if not p:
                continue
            asked += 1
            fifth = min(4, (n - 1) * 5 // len(ids))
            by_fifth[fifth][1] += 1
            if given == '':
                blanks += 1
            elif engine.normalize_answer(p, given) == str(p['answer']):
                by_fifth[fifth][0] += 1
    return {
        'taken': len(graded),
        'scores': [_scored(m) for m in reversed(graded[:8])],
        'blank_rate': round(blanks / asked, 3) if asked else None,
        'by_fifth': [round(r / n, 3) if n else None for r, n in by_fifth],
    }


def _mock_check(mocks, theta):
    """Timed mock scores against what the model expects for those exact papers."""
    rows = []
    for m in mocks:
        if m['kind'] != 'mock':
            continue
        ids = (m.get('answers') or {}).get('_ids') or []
        problems = [pb.get(pid) for pid in ids]
        if not problems or any(p is None for p in problems):
            continue
        aime = problems[0]['level'] == 'AIME'
        expected = sum(chance(theta, p['rating']) if aime else max(6 * chance(theta, p['rating']), 1.5)
                       for p in problems)
        rows.append({'contest': m['contest_id'], 'score': m['score'], 'expected': round(expected, 1)})
    if not rows:
        return None
    gap = sum(r['score'] - r['expected'] for r in rows) / len(rows)
    return {'taken': len(rows), 'gap': round(gap, 1), 'recent': rows[:5]}


def _trend(attempts, today, weeks=6):
    out = []
    for back in range(weeks - 1, -1, -1):
        end_day = today - timedelta(days=7 * back)
        end = end_day.isoformat()
        firsts = {}
        for a in attempts:
            if a['at'][:10] <= end and a['source'] != 'reveal' and a['problem_id'] not in firsts:
                firsts[a['problem_id']] = (bool(a['correct']), a['at'])
        pts = [(pb.get(pid)['rating'], ok, _weight(at, end_day)) for pid, (ok, at) in firsts.items() if pb.get(pid)]
        out.append({'week_end': end, 'answered': len(pts), 'theta': fit(pts)[0] if pts else None})
    return out


def _next_problems(hist, level, theta, focus):
    """Unsolved problems in the focus topics that the student gets right between
    half and three-quarters of the time, closest to two-thirds first, at most
    two from one topic, unattempted ones before ones already missed."""
    focus_ids = [t['id'] for t in focus]
    lo, hi = LEARN_BAND
    sweet = (lo + hi) / 2
    candidates = []
    for p in pb.all_problems():
        if p['level'] != level and not (level == 'AMC 12' and p['level'] == 'AMC 10'):
            continue
        h = hist.get(p['id'])
        if h and h['solved']:
            continue
        topic = next((t for t in [p['topic']] + p['also'] if t in focus_ids), None)
        if topic is None:
            continue
        c = chance(theta, p['rating'])
        miss = 0.15 if not (lo <= c <= hi) else 0
        candidates.append((abs(c - sweet) + miss + (0.05 if h else 0), catalog.short_label(p['id']), topic, p, c))
    candidates.sort(key=lambda row: (row[0], row[1]))
    picked, per_topic = [], {}
    for _, short, topic, p, c in candidates:
        if per_topic.get(topic, 0) >= 2:
            continue
        per_topic[topic] = per_topic.get(topic, 0) + 1
        picked.append({'id': p['id'], 'short': short, 'topic': p['topic'],
                       'topic_name': catalog.TOPIC_BY_ID[p['topic']]['name'], 'rating': p['rating'],
                       'chance': round(c, 2)})
        if len(picked) == 8:
            break
    return picked


def analyze(attempts, hist, review_by_id, mocks, plan, today=None):
    """Everything the Insights page and the AI diagnosis read."""
    today = today or date.today()
    level = plan['target'] if plan else 'AMC 10'
    goal = plan['goal_score'] if plan else engine.DEFAULT_GOALS[level]
    points = _first_points(hist, today)
    theta, se = fit([(r, ok, w) for r, ok, w, _ in ability_points(hist, today)])
    n = len(points)
    pace = pace_model(hist, theta)

    contests = {}
    for lvl in ('AMC 10', 'AMC 12', 'AIME'):
        target = goal if lvl == level else CUTOFFS.get(lvl, 7 if lvl == 'AIME' else None)
        low, high, hit = _simulate(theta, se, lvl, target)
        timed, reached = _timed(theta, lvl, pace)
        expected = _expected(theta, lvl)
        contests[lvl] = {
            'expected': round(expected, 1), 'low': round(low, 1), 'high': round(high, 1),
            'target': target, 'chance': round(hit, 3) if hit is not None else None,
            'reach': _reach(theta, lvl), 'count': len(SCALE_BY_NUMBER[lvl]),
            'timed': round(timed, 1), 'reached': reached,
            'speed_cost': round(max(0.0, expected - timed), 1),
        }

    # Per topic and per technique, shrunk toward the overall theta: fitted
    # from first tries and retests, counted from first tries.
    by_topic, by_tech, firsts = {}, {}, {}
    for rating, ok, w, p in ability_points(hist, today):
        for tid in [p['topic']] + p['also']:
            by_topic.setdefault(tid, []).append((rating, ok, w))
        by_tech.setdefault(p['technique'], []).append((rating, ok, w))
    for rating, ok, w, p in points:
        for tid in [p['topic']] + p['also']:
            firsts.setdefault(tid, []).append(ok)
    level_topics = [t for t in catalog.TOPICS if level in t['levels']]
    total_weight = sum(t['weight'] for t in level_topics) or 1
    topics = []
    for t in catalog.TOPICS:
        pts = by_topic.get(t['id'], [])
        th, tse = fit(pts, mean=theta, sd=TOPIC_SD) if pts else (None, None)
        relevant = level in t['levels']
        points_at_stake = _topic_points(level, theta, th, t['weight'], total_weight) if relevant else 0
        topics.append({'id': t['id'], 'name': t['name'], 'category': t['category'], 'weight': t['weight'],
                       'answered': len(firsts.get(t['id'], [])), 'right': sum(firsts.get(t['id'], [])),
                       'theta': th, 'se': tse, 'relevant': relevant,
                       # Points on the student's contest from bringing this topic up.
                       'points': points_at_stake,
                       'priority': points_at_stake})
    techniques = []
    for tid, pts in by_tech.items():
        if tid == 'official' or len(pts) < 2:
            continue
        th, tse = fit(pts, mean=theta, sd=TOPIC_SD)
        if th < theta:              # only the ones holding the student back
            techniques.append({'id': tid, 'name': catalog.technique_name(tid), 'answered': len(pts), 'theta': th})
    techniques.sort(key=lambda r: r['theta'])

    # Weak topics are ones the student has touched and does worse in than overall.
    focus = sorted([t for t in topics if t['relevant'] and t['answered'] and t['theta'] < theta + 0.6],
                   key=lambda t: (-t['points'], t['name']))[:5]
    strong = sorted([t for t in topics if t['theta'] is not None and t['answered'] >= 2 and t['theta'] >= theta],
                    key=lambda t: -t['theta'])[:4]

    mock_check = _mock_check(mocks, theta)
    due = sum(1 for r in review_by_id.values() if r['status'] == 'active' and r['due'] <= today.isoformat())
    a, b, timed_n = pace
    return {
        'level': level, 'goal': goal, 'answered': n,
        'confident': n >= 15,
        'theta': theta, 'se': se,
        'band': '{:g}–{:g}'.format(max(1, round((theta - se) * 2) / 2), min(12, round((theta + se) * 2) / 2)),
        'contests': contests,
        'pace': {'timed_answers': timed_n,
                 'at_level': round(seconds_for(pace, theta, theta, level)),
                 'easy': round(seconds_for(pace, theta, theta - 2.4, level)),
                 'hard': round(seconds_for(pace, theta, theta + 2.4, level)),
                 'contest': PACE[level]},
        'topics': [t for t in topics if t['answered'] or t['relevant']],
        'techniques': techniques[:12],
        'focus': focus, 'strong': strong,
        'patterns': _patterns(attempts, hist, theta, level, mock_check),
        'trend': _trend(attempts, today),
        'mocks': _mock_summary(mocks),
        'mock_check': mock_check,
        'next_problems': _next_problems(hist, level, theta, focus),
        'review_due': due,
    }


def ai_brief(stats, plan):
    """The compact, factual brief the AI diagnosis is written from."""
    c = stats['contests'][stats['level']]
    pace = stats['pace']
    lines = [
        'Contest: {}. Goal: {}.'.format(stats['level'], stats['goal']),
        'First-try answers so far: {}.'.format(stats['answered']),
        'Ability estimate on AMC Guide\'s 1-12 scale (the AoPS rating times 2: an AMC 10 #1 is 2, 12 = hardest AIME problem; the rating solved '
        'half the time, recent answers weighted more): {} ± {}.'.format(stats['theta'], stats['se']),
        'Predicted score: {} untimed (80% range {}-{}); {} with their own pace in the time limit (reaching #{} of {}); '
        'chance of reaching {}: {}%. More likely right than wrong up to #{}.'.format(
            c['expected'], c['low'], c['high'], c['timed'], c['reached'], c['count'], c['target'],
            round(100 * (c['chance'] or 0)), c['reach']),
        'Pace: about {}s on a problem at their level, {}s 2.4 points easier, {}s 2.4 points harder (contest pace {}s; '
        'from {} timed answers).'.format(pace['at_level'], pace['easy'], pace['hard'], pace['contest'],
                                         pace['timed_answers']),
        'Weekly ability trend (oldest first): {}.'.format(', '.join(str(w['theta']) for w in stats['trend'] if w['theta'] is not None) or 'none yet'),
        'Weakest topics they have answered, worth the most points (id, name, ability, answered, points it would '
        'add); topics they have not tried are not weaknesses: {}.'.format(
            '; '.join('{} ({}, {}, {}, +{})'.format(t['id'], t['name'], t['theta'], t['answered'], t['points'])
                      for t in stats['focus']) or 'none yet'),
        'Strongest topics: {}.'.format('; '.join('{} ({})'.format(t['name'], t['theta']) for t in stats['strong']) or 'none yet'),
        'Weakest techniques: {}.'.format('; '.join('{} ({})'.format(t['name'], t['theta']) for t in stats['techniques'][:4]) or 'none yet'),
        'Patterns: {}'.format(' '.join(p['text'] for p in stats['patterns']) or 'none flagged.'),
        'Reviews due: {}.'.format(stats['review_due']),
    ]
    if stats['mocks']:
        m = stats['mocks']
        lines.append('Mocks taken: {}; blank rate {}; accuracy by fifth of the paper {}.'.format(
            m['taken'], m['blank_rate'], m['by_fifth']))
        lines.append('Recent sittings, oldest first, each read against that paper\'s real results (official papers '
                     'differ in difficulty, so compare the adjusted score, which puts every paper on a typical recent '
                     'one where 100 on the AMC 10 / 85 on the AMC 12 qualifies): {}.'.format('; '.join(
                         '{} {}{}'.format(s['contest'], s['score'], ' (adjusted {}, about top {}%, {:+g} vs that year\'s '
                                          'AIME floor{})'.format(s['adjusted'], s['top'], s['vs_floor'],
                                                                 ', ' + s['award'] if s['award'] else '')
                                          if s.get('vs_floor') is not None and s.get('top') is not None else
                                          (' (adjusted {})'.format(s['adjusted']) if s.get('adjusted') is not None else ''))
                         for s in m['scores'])))
    if stats.get('mock_check'):
        lines.append('Timed mocks against the model\'s expectation for those papers: {:+g} points on average.'.format(
            stats['mock_check']['gap']))
    if plan:
        lines.append('Exam date: {}; hours per week: {}.'.format(plan.get('exam_date'), plan.get('hours')))
    lines.append('Valid topic ids: {}.'.format(', '.join(t['id'] for t in catalog.TOPICS if stats['level'] in t['levels'])))
    return '\n'.join(lines)
