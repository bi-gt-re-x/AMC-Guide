"""What to study, in what order, and how: the study plan's arithmetic.

## Topic priority: expected score improvement

A topic is worth studying for how many points it would add to the student's
contest, not for how weak it is. Six things go into it, each shown on the
page with the number behind it:

* **Contest frequency**: the topic's weight, its share of a typical paper.
* **Mastery**: first-try accuracy and the topic's ability estimate (the
  topic's own theta, from backend/amc/smart.py, shrunk toward the overall).
* **Improvement potential**: the points the paper would give back if the
  topic came up to the student's overall level (or 1.2 above it, for one
  already there): `smart._topic_points`, which is frequency x the gap x where
  on the paper the topic's problems sit. Frequency and mastery work through
  this, so a 40% topic that appears on every paper outranks a 20% one that
  appears once in three.
* **Difficulty / feasibility**: how much of the topic's real problems are
  within reach a little above the student's level. Probability at the AIME
  level is worth little to someone at AMC 10 #10: the points are there but
  out of reach for now.
* **Recency**: days since the topic was last practised; a topic left alone
  fades, and one never tried is an open question.
* **Importance**: how many other topics on the contest build on it
  (`BUILDS_ON`), so fixing it lifts them too.

`priority = gain x feasibility x recency x importance`, in points.

## Five kinds of weakness

A topic is weak in different ways, and each wants different training. Each
is read from the student's own answers, with the evidence counted, and only
called when there is enough of it:

* **Conceptual**: misses that stay unsolved and solutions revealed, in a topic
  below the student's level. Study the theory, then introductory problems.
* **Execution**: misses on problems they usually get (rated at or below their
  level) or put right at the very next try. Practise accuracy and checking.
* **Speed**: right answers that took far longer than contest pace for that
  difficulty. Timed sets.
* **Recognition**: right in topic-by-topic practice, wrong when the same kind
  of problem comes unlabelled in a sitting. Mixed-topic sets.
* **Retention**: solved once, missed again later. Spaced repetition.

## Five difficulty levels, mixed to the student

`LEVELS` cuts AMC Guide's 1-12 rating into five: fundamental (an AMC 10's
#1-4), standard (#5-14), challenging (#15-22 and an AIME's opening), extremely
difficult AMC / AIME entry, and advanced AIME. `difficulty_mix` says what share
of a topic's practice to take from each: weighted by how likely the student is
to get a problem at that level right (their topic ability, through the same
model as everything else), aiming at the productive zone: about 70% right,
or 60% when their goal needs harder problems than they can do now. Problems
that are too easy fall away faster than ones a little too hard, and levels
more than one beyond what the goal needs are cut back. As a topic improves
the mix moves up: 40% gets mostly levels 1-2 with some 3; 80% mostly 2-3 with
some 4. Someone aiming to qualify and someone aiming at 120+ get different
mixes from the same answers.
"""
import math
from datetime import date

from backend.amc import catalog, smart
from backend.amc import problems as pb

#: topic -> the topics it is built on (direct prerequisites on these contests).
BUILDS_ON = {
    'quadratics': ['linear-equations', 'exponents'], 'polynomials': ['quadratics'],
    'functions': ['linear-equations'], 'sequences-series': ['arithmetic', 'linear-equations'],
    'logarithms': ['exponents'], 'complex-numbers': ['quadratics', 'trigonometry'],
    'nonlinear-systems': ['linear-equations', 'quadratics'],
    'graphs-transformations': ['functions', 'coordinate-geometry'],
    'binomial-theorem': ['binomial-coefficients', 'polynomials'], 'inequalities': ['quadratics'],
    'floor-ceiling': ['arithmetic'], 'absolute-value': ['linear-equations'],
    'word-problems': ['arithmetic', 'linear-equations'],
    'factors-divisors': ['divisibility'], 'modular-arithmetic': ['divisibility'],
    'gcd-lcm': ['factors-divisors'], 'diophantine': ['modular-arithmetic', 'gcd-lcm'],
    'factorials': ['factors-divisors'], 'perfect-powers': ['factors-divisors', 'exponents'],
    'digits-bases': ['divisibility'], 'parity': ['divisibility'], 'decimals-fractions': ['arithmetic'],
    'permutations': ['basic-counting'], 'combinations': ['basic-counting'], 'casework': ['basic-counting'],
    'probability': ['combinations', 'casework'], 'expected-value': ['probability'],
    'conditional-probability': ['probability'], 'geometric-probability': ['probability', 'area'],
    'recursion': ['basic-counting'], 'binomial-coefficients': ['combinations'],
    'lattice-paths': ['combinations'], 'pigeonhole': ['basic-counting'], 'graph-theory': ['basic-counting'],
    'symmetry-counting': ['permutations'],
    'right-triangles': ['triangles'], 'similar-triangles': ['triangles'],
    'circles': ['triangles', 'right-triangles'], 'area': ['triangles'],
    'polygons': ['triangles', 'angle-chasing'], 'coordinate-geometry': ['linear-equations', 'right-triangles'],
    'solid-geometry': ['area', 'right-triangles'], 'trigonometry': ['right-triangles'],
    'angle-chasing': ['triangles'], 'quadrilaterals': ['triangles', 'area'],
    'triangle-centers': ['triangles', 'similar-triangles'], 'area-ratios': ['area', 'similar-triangles'],
    'cyclic-quadrilaterals': ['circles', 'angle-chasing'], 'conics': ['coordinate-geometry', 'quadratics'],
    'transformations': ['coordinate-geometry'], 'statistics': ['arithmetic'], 'data-graphs': ['statistics'],
}

KINDS = {
    'conceptual': {'name': 'Conceptual', 'mode': 'learn',
                   'means': "Doesn't yet understand the mathematics underneath.",
                   'approach': 'Study the theory, then introductory problems, untimed.'},
    'execution': {'name': 'Execution', 'mode': 'accuracy',
                  'means': 'Knows the idea but makes mistakes carrying it out.',
                  'approach': 'Accuracy practice: untimed, write each step, check every answer before submitting.'},
    'speed': {'name': 'Speed', 'mode': 'timed',
              'means': 'Gets there, but too slowly for the contest.',
              'approach': 'Timed sets at contest pace, three minutes a problem.'},
    'recognition': {'name': 'Recognition', 'mode': 'mixed',
                    'means': "Solves it when told the topic, misses which technique applies when it isn't.",
                    'approach': 'Mixed-topic sets and full mocks: name the technique before solving.'},
    'retention': {'name': 'Retention', 'mode': 'spaced',
                  'means': 'Understands it on the day, forgets it later.',
                  'approach': 'Spaced repetition: clear due reviews, revisit after 3, 7 and 21 days.'},
}
MODE_LABEL = {'learn': 'learn the ideas', 'accuracy': 'accuracy drill', 'timed': 'timed set',
              'mixed': 'mixed set', 'spaced': 'spaced review', 'practice': 'practice'}

#: The five difficulty levels on AMC Guide's 1-12 scale: the whole ratings each
#: covers (a half step goes with the whole below it, as the Problems filter
#: reads them) and a typical rating, to weigh a level by.
LEVELS = [
    {'level': 1, 'name': 'Fundamental', 'means': 'Fundamental concepts and straightforward applications',
     'ratings': [1, 2], 'top': 2.5, 'typical': 2.0},
    {'level': 2, 'name': 'Standard', 'means': 'Standard AMC problems', 'ratings': [3, 4], 'top': 4.5, 'typical': 3.75},
    {'level': 3, 'name': 'Challenging', 'means': 'Challenging AMC problems', 'ratings': [5, 6], 'top': 6.5,
     'typical': 5.75},
    {'level': 4, 'name': 'Very hard', 'means': 'Extremely difficult AMC problems, AIME entry level',
     'ratings': [7, 8], 'top': 8.5, 'typical': 7.75},
    {'level': 5, 'name': 'Advanced', 'means': 'Advanced AIME problems', 'ratings': [9, 10, 11, 12], 'top': 12,
     'typical': 10.0},
]
#: Share of right answers the practice should aim at: the productive zone.
AIM, AIM_STRETCH = 0.7, 0.6


def level_of(rating):
    """The difficulty level (1-5) of a 1-12 rating."""
    return next(L['level'] for L in LEVELS if rating <= L['top'])


def goal_level(level, goal):
    """The hardest difficulty level the goal needs solved reliably: the level
    of the last problem the goal needs right (with the rest left blank)."""
    from backend.amc import insights, official
    need = insights.needed_right(level, goal) if goal is not None else 0
    return level_of(official.rating_at(level, max(1, need))) if need else 1


def difficulty_mix(topic_theta, ceiling):
    """[{level, share}] summing to 1, in fives of a percent, for practice at
    `topic_theta` when the goal needs up to level `ceiling`."""
    working = max(LEVELS, key=lambda L: -abs(smart.chance(topic_theta, L['typical']) - 0.65))['level']
    aim = AIM_STRETCH if ceiling > working else AIM
    weights = {}
    for L in LEVELS:
        p = smart.chance(topic_theta, L['typical'])
        sd = 0.13 if p > aim else 0.3            # too easy falls away faster than a little too hard
        w = math.exp(-((p - aim) ** 2) / (2 * sd * sd))
        if L['level'] > ceiling + 1:
            w *= 0.25                            # beyond what the goal needs
        weights[L['level']] = w
    total = sum(weights.values()) or 1
    twentieths = _largest_remainder({k: v / total * 20 for k, v in weights.items()}, 20)
    return [{'level': k, 'share': round(n / 20, 2)} for k, n in sorted(twentieths.items()) if n]


def _largest_remainder(values, total):
    """Whole numbers summing to `total`, nearest to `values` (which sum to it)."""
    floors = {k: int(v) for k, v in values.items()}
    left = total - sum(floors.values())
    for k in sorted(values, key=lambda k: -(values[k] - floors[k]))[:left]:
        floors[k] += 1
    return floors


def split_count(mix, n):
    """`n` problems split by a mix: [{level, count}] for the levels that get any."""
    counts = _largest_remainder({m['level']: m['share'] * n for m in mix}, n)
    return [{'level': k, 'count': c} for k, c in sorted(counts.items()) if c]


def level_ratings(level):
    return next(L['ratings'] for L in LEVELS if L['level'] == level)


#: Least evidence before a kind of weakness is called.
MIN_ANSWERED = 3
#: A right answer slower than this many times contest pace (for its difficulty) is slow.
SLOW_FACTOR = 1.6
#: A topic not practised for this many days gets the full recency boost.
STALE_DAYS = 30


def dependents(level):
    """{topic: how many of the contest's topics build on it directly}."""
    relevant = {t['id'] for t in catalog.TOPICS if level in t['levels']}
    out = {tid: 0 for tid in relevant}
    for tid, needs in BUILDS_ON.items():
        if tid not in relevant:
            continue
        for need in needs:
            if need in out:
                out[need] += 1
    return out


def _par(level, theta, rating):
    """Seconds a problem of `rating` should take at contest pace for this student."""
    pace = smart.PACE[level]
    return min(3 * pace, max(45, pace * math.exp(0.3 * (rating - theta))))


def _days(a, b):
    return (date.fromisoformat(a[:10]) - date.fromisoformat(b[:10])).days


#: How far a topic's ability moves with a few weeks' work: a base step, and
#: more for a topic below the student's level (catching up is quicker than
#: going beyond), up to two points' worth of catch-up.
STEP, CATCH_UP = 0.6, 0.6


def study_gain(level, theta, topic_theta, share):
    """Expected points on a `level` paper from studying a topic: its ability
    rising by a realistic step, over the paper's positions in proportion to the
    topic's share. Improvement potential lives here: a topic far below the
    student's level has a bigger step, and one whose problems sit where the
    student's chances are changing (not hopeless, not certain) pays most."""
    current = topic_theta if topic_theta is not None else theta - 0.3
    step = STEP + CATCH_UP * max(0.0, min(2.0, theta - current))
    worth = 1 if level == 'AIME' else 6
    gain = 0.0
    for r in smart.SCALE_BY_NUMBER[level]:
        before, after = smart.chance(current, r), smart.chance(current + step, r)
        if level == 'AIME':
            gain += after - before
        else:
            gain += max(worth * after, 1.5) - max(worth * before, 1.5)
    return round(share * gain, 2)


def _topic_rows(attempts, hist, today):
    """Per topic: the first tries, every attempt in order, and the last day practised."""
    rows = {}
    by_problem = {}
    for a in sorted(attempts, key=lambda a: a['at']):
        by_problem.setdefault(a['problem_id'], []).append(a)
    for pid, tries in by_problem.items():
        p = pb.get(pid)
        if not p:
            continue
        for tid in [p['topic']] + p['also']:
            r = rows.setdefault(tid, {'problems': [], 'last': ''})
            r['problems'].append((p, tries, hist.get(pid)))
            r['last'] = max(r['last'], tries[-1]['at'])
    return rows


def classify(level, theta, problems, topic_theta=None):
    """The kinds of weakness in one topic, from [(problem, attempts in order, history)].

    Returns {kind: {'score': 0-1, 'evidence': sentence, 'count': n}} for each
    kind there is enough evidence of. `topic_theta` is the topic's ability
    estimate, to tell a topic that is below the student's level throughout
    (conceptual) from isolated slips in one that is not (execution)."""
    out = {}
    firsts = [(p, tries) for p, tries, _ in problems if tries]
    answered = [(p, t) for p, t in firsts if t[0].get('source') != 'reveal']
    if len(firsts) < MIN_ANSWERED:
        return out
    misses = [(p, t) for p, t in answered if not t[0]['correct']]
    reveals = sum(1 for p, t in firsts if any(a.get('source') == 'reveal' for a in t))
    # Tried again and still not right: not a slip.
    stuck = [(p, t) for p, t in misses if len(t) > 1 and not any(a['correct'] for a in t)]
    fixed_next = [(p, t) for p, t in misses if len(t) > 1 and t[1]['correct'] and t[1].get('source') != 'reveal']
    within_reach = [(p, t) for p, t in misses if smart.chance(theta, p['rating']) >= 0.6]
    below = topic_theta is not None and topic_theta < theta - 0.6

    # Conceptual: retries that still fail, solutions that had to be shown, or a
    # topic well below the student's level, missed even where they usually score.
    deep = len(stuck) + reveals + (len(within_reach) if below else 0)
    if deep >= 2 and (len(stuck) + reveals >= 2 or (below and len(within_reach) >= 3)):
        parts = []
        if stuck:
            parts.append('{} still wrong after another try'.format(len(stuck)))
        if reveals:
            parts.append('{} solution{} shown'.format(reveals, '' if reveals == 1 else 's'))
        if below:
            parts.append('{} missed at or below your level, the topic well under your overall level'.format(
                len(within_reach)))
        out['conceptual'] = {'count': deep, 'score': min(1.0, deep / max(4, len(firsts)) * 1.5),
                             'evidence': '; '.join(parts)}
    # Execution: misses within reach in a topic that is otherwise at level, or
    # put right at the very next try.
    slips = len({id(x) for x in fixed_next} | ({id(x) for x in within_reach} if not below else set()))
    if slips >= 2 and slips >= 0.4 * max(1, len(misses)):
        out['execution'] = {'count': slips, 'score': min(1.0, slips / max(4, len(answered)) * 2),
                            'evidence': '{} slips on problems within your reach, or put right at the next try'.format(slips)}
    # Speed: right, but well over contest pace for the difficulty.
    timed = [(p, t[0]) for p, t in answered if t[0]['correct'] and int(t[0].get('seconds') or 0) > 0]
    slow = [(p, a) for p, a in timed if int(a['seconds']) > SLOW_FACTOR * _par(level, theta, p['rating'])]
    if len(timed) >= MIN_ANSWERED and len(slow) >= 2 and len(slow) >= 0.5 * len(timed):
        out['speed'] = {'count': len(slow), 'score': min(1.0, len(slow) / len(timed)),
                        'evidence': '{} of {} right answers took over {:g}x contest pace'.format(
                            len(slow), len(timed), SLOW_FACTOR)}
    # Recognition: worse unlabelled (in a sitting) than labelled (practice), for the difficulty.
    def resid(rows):
        return sum((1 if t[0]['correct'] else 0) - smart.chance(theta, p['rating']) for p, t in rows) / len(rows)
    sat = [(p, t) for p, t in answered if t[0].get('source') == 'mock']
    drilled = [(p, t) for p, t in answered if t[0].get('source') == 'practice']
    if len(sat) >= MIN_ANSWERED and len(drilled) >= MIN_ANSWERED:
        gap = resid(drilled) - resid(sat)
        if gap >= 0.2:
            out['recognition'] = {'count': len(sat), 'score': min(1.0, gap),
                                  'evidence': '{:.0%} right in topic practice, {:.0%} in sittings, for the difficulty'.format(
                                      sum(1 for _, t in drilled if t[0]['correct']) / len(drilled),
                                      sum(1 for _, t in sat if t[0]['correct']) / len(sat))}
    # Retention: right once, wrong again later.
    relapses = 0
    for p, t in firsts:
        seen_right = False
        for a in t:
            if a['correct']:
                seen_right = True
            elif seen_right and a.get('source') != 'reveal':
                relapses += 1
                break
    if relapses >= 2:
        out['retention'] = {'count': relapses, 'score': min(1.0, relapses / max(3, len(firsts)) * 2),
                            'evidence': '{} solved once and missed again later'.format(relapses)}
    return out


#: The share of the points a topic lost in recent timed sittings (per sitting)
#: that a few weeks on it is taken to win back. Added to its practice gain, so
#: a topic that costs points under exam conditions is studied even when
#: practice says it is fine.
MOCK_RECOVERY = 0.25


def analyze(attempts, hist, level, today=None, goal=None, details=None, mocks=None):
    """Priorities, weaknesses and difficulty mixes for a `level` student aiming at `goal`.

    `mocks` (the account's amc_mocks rows) adds what the timed sittings say:
    the points each topic lost in them (backend/amc/mockscore.py `mistakes`)
    go into its gain and its reason.

    Returns {'theta', 'ceiling', 'mix', 'topics': [priority rows, highest first], 'kinds': [per kind],
    'mock': the mistakes}."""
    today = today or date.today()
    from backend.amc import mockscore
    lost = mockscore.mistakes(mocks or [], level, today)
    lost_by = {t['id']: t for t in lost['topics']}
    if goal is None:
        from backend.amc import engine
        goal = engine.DEFAULT_GOALS[level]
    ceiling = goal_level(level, goal)
    points = smart._first_points(hist, today)
    theta, _ = smart.fit([(r, ok, w) for r, ok, w, _ in points])
    by_topic = {}
    for rating, ok, w, p in points:
        for tid in [p['topic']] + p['also']:
            by_topic.setdefault(tid, []).append((rating, ok, w))
    relevant = [t for t in catalog.TOPICS if level in t['levels']]
    total_weight = sum(t['weight'] for t in relevant) or 1
    builds = dependents(level)
    rows = _topic_rows(attempts, hist, today)
    on_level = {}
    for p in pb.all_problems():
        if p['level'] == level:
            for tid in [p['topic']] + p['also']:
                on_level.setdefault(tid, []).append(p['rating'])

    leans = subject_lean(details, {tid: len(v) for tid, v in by_topic.items()})
    out = []
    for t in relevant:
        pts = by_topic.get(t['id'], [])
        th = smart.fit(pts, mean=theta, sd=smart.TOPIC_SD)[0] if pts else None
        answered = len(pts)
        right = sum(1 for _, ok, _w in pts if ok)
        gain = study_gain(level, theta, th, t['weight'] / total_weight)
        in_mocks = lost_by.get(t['id'])
        if in_mocks:
            gain = round(gain + MOCK_RECOVERY * in_mocks['per_sitting'], 2)
        ratings = on_level.get(t['id'], [])
        reach = sum(smart.chance(theta + 1.0, r) for r in ratings) / len(ratings) if ratings else 0.6
        feasibility = round(0.5 + 0.5 * reach, 2)
        last = rows.get(t['id'], {}).get('last') or ''
        days = _days(today.isoformat(), last) if last else None
        recency = round(1.15 if days is None else 1 + 0.3 * min(1.0, days / STALE_DAYS), 2)
        importance = round(min(1.25, 1 + 0.05 * builds.get(t['id'], 0)), 2)
        lean = leans.get(t['id'], 1.0)
        priority = round(gain * feasibility * recency * importance * lean, 2)
        kinds = classify(level, theta, rows.get(t['id'], {}).get('problems', []), th)
        main = max(kinds, key=lambda k: kinds[k]['score']) if kinds else None
        if main:
            mode = KINDS[main]['mode']
        elif answered < MIN_ANSWERED:
            mode = 'learn'
        else:
            mode = 'practice'
        out.append({
            'id': t['id'], 'name': t['name'], 'category': t['category'],
            'priority': priority, 'gain': gain,
            'factors': {'frequency': t['weight'], 'share': round(t['weight'] / total_weight, 3),
                        'mastery': round(right / answered, 3) if answered else None,
                        'answered': answered, 'right': right,
                        'level': round(th, 2) if th is not None else None,
                        'feasibility': feasibility, 'recency': recency, 'days_since': days,
                        'importance': importance, 'builds': builds.get(t['id'], 0),
                        'self_rated': ((details or {}).get('subjects') or {}).get(t['category']),
                        'mock_lost': in_mocks['lost'] if in_mocks else 0,
                        'mock_missed': in_mocks['missed'] if in_mocks else 0},
            'kinds': kinds, 'kind': main, 'mode': mode, 'mode_label': MODE_LABEL[mode],
            'why': _why(t, gain, answered, right, feasibility, days, builds.get(t['id'], 0), main,
                        in_mocks, lost['sittings']),
            # What difficulty to practise it at: from the topic's ability, or a
            # little below the overall level for a topic not tried yet.
            'mix': difficulty_mix(th if th is not None else theta - 0.3, ceiling),
        })
    out.sort(key=lambda r: (-r['priority'], r['name']))

    kinds = []
    for key, info in KINDS.items():
        hit = sorted((r for r in out if key in r['kinds']), key=lambda r: -r['kinds'][key]['score'])
        kinds.append({'id': key, **info, 'topics': [
            {'id': r['id'], 'name': r['name'], 'category': r['category'], 'evidence': r['kinds'][key]['evidence'],
             'score': round(r['kinds'][key]['score'], 2)} for r in hit],
            'count': sum(r['kinds'][key]['count'] for r in hit)})
    return {'theta': round(theta, 2), 'ceiling': ceiling, 'goal': goal,
            'mix': difficulty_mix(theta, ceiling), 'topics': out, 'kinds': kinds, 'mock': lost}


def _why(t, gain, answered, right, feasibility, days, builds, kind, in_mocks=None, sittings=0):
    bits = []
    if in_mocks:
        bits.append('lost {:g} pts in your last {} mock{} ({} missed)'.format(
            in_mocks['lost'], sittings, '' if sittings == 1 else 's', in_mocks['missed']))
    if t['weight'] >= 3:
        bits.append('on nearly every paper')
    elif t['weight'] == 1:
        bits.append('appears rarely')
    bits.append('{}/{} right first try'.format(right, answered) if answered else 'not tried yet')
    if feasibility < 0.6:
        bits.append('mostly above your level for now')
    if days is not None and days >= 14:
        bits.append('last practised {} days ago'.format(days))
    if builds >= 2:
        bits.append('{} topics build on it'.format(builds))
    if kind:
        bits.append('{} weakness'.format(KINDS[kind]['name'].lower()))
    return '; '.join(bits)


#: Answers in a topic before its accuracy can say it has been learned.
CLEARED_MIN = 5


def cleared(row):
    """Whether a priority row's answers say the topic is in hand: right first
    time 80% of the time over at least CLEARED_MIN answers."""
    f = row.get('factors') or {}
    return (f.get('answered') or 0) >= CLEARED_MIN and (f.get('mastery') or 0) >= 0.8


def schedule(priorities, weeks, per_week=2, decay=0.55, coached=()):
    """[[topic rows] per week]: each week the highest remaining priorities, a
    topic's remaining value cut by `decay` once scheduled, so the most valuable
    come back spaced out, and not two weeks running while another is close.

    The AI coach's topic order (`coached`, a list), when there is one, fills
    the opening weeks as it asked: it has heard what the arithmetic cannot
    (backend/amc/coach.py). Then the arithmetic takes over."""
    by_id = {r['id']: r for r in priorities}
    remaining = {r['id']: max(r['priority'], 0.01) for r in priorities}
    # The coach's order leads only for topics the answers have not since
    # shown the student has: it was written once, and a topic mastered since
    # should give its week to one that is not (`cleared`).
    order = [tid for tid in dict.fromkeys(coached) if tid in by_id and not cleared(by_id[tid])]
    out, last = [], set()
    for _ in range(weeks):
        if order:
            pick, order = order[:per_week], order[per_week:]
            if len(pick) < per_week:
                pick += [tid for tid in sorted(remaining, key=lambda t: (-remaining[t], by_id[t]['name']))
                         if tid not in pick][:per_week - len(pick)]
        else:
            pool = sorted(remaining, key=lambda t: (-remaining[t] * (0.6 if t in last else 1.0), by_id[t]['name']))
            pick = pool[:per_week]
        for tid in pick:
            remaining[tid] *= decay
        last = set(pick)
        out.append([by_id[tid] for tid in pick])
    return out


#: How a topic is trained as the plan comes back to it, when the answers have
#: not said what kind of weakness it has: learn the ideas, practise them, then
#: at contest pace, then unlabelled among other topics as on the day.
LADDER = ('learn', 'practice', 'timed', 'mixed')
#: The lowest rung each phase trains a topic it has met before at. A topic
#: seen for the first time is still learned first, whatever the phase.
PHASE_FLOOR = {'Foundations': 0, 'Core': 1, 'Contest mode': 2, 'Taper': 3}


def week_mode(row, phase, visits):
    """How to train topic `row` in a week of `phase`, the plan's `visits`-th
    return to it (0 the first time).

    A topic whose answers show accuracy or retention trouble keeps the
    training that wants (`KINDS`). Otherwise it climbs `LADDER` one rung per
    visit, and no lower than the phase asks once it has been met: a plan that
    said "learn the ideas" for the same topic in week 1 and week 41 was
    teaching it from scratch in the weeks meant for timed papers."""
    mode = row.get('mode') or 'practice'
    if mode not in LADDER:
        return mode
    rung = LADDER.index(mode) + visits
    if visits or mode != 'learn':
        rung = max(rung, PHASE_FLOOR.get(phase, 0))
    return LADDER[min(rung, len(LADDER) - 1)]


def mix_text(mix):
    """'50% level 1, 35% level 2, 15% level 3'."""
    return ', '.join('{:.0%} level {}'.format(m['share'], m['level']) for m in mix)


def brief(study, top=6):
    """The priorities and kinds of weakness in a few lines, for an AI coach's brief."""
    lines = ['Difficulty levels: 1 fundamental (AMC 10 #1-4), 2 standard AMC, 3 challenging AMC, 4 extremely '
             'difficult AMC / AIME entry, 5 advanced AIME. Their goal needs up to level {}; overall they should '
             'practise at {}.'.format(study.get('ceiling'), mix_text(study.get('mix') or []))] + ['Study priorities by expected score gain (topic id: about +points from a few weeks on it; '
             'first-try right; kind of weakness and how to train it):']
    for r in study['topics'][:top]:
        f = r['factors']
        lines.append('- {} ({}): +{} pts; {}; {}'.format(
            r['id'], r['name'], r['gain'],
            '{}/{} right'.format(f['right'], f['answered']) if f['answered'] else 'not tried yet',
            '{} weakness, train by {}'.format(KINDS[r['kind']]['name'].lower(), r['mode_label'])
            if r['kind'] else 'train by ' + r['mode_label']) + '; practise at ' + mix_text(r['mix']))
    lost = study.get('mock') or {}
    if lost.get('topics'):
        lines.append('Points lost in their last {} timed mock sitting(s), by topic (target these first): {}.'.format(
            lost['sittings'], '; '.join('{} ({}): -{:g} pts, {} wrong, {} blank'.format(
                t['id'], t['name'], t['lost'], t['wrong'], t['blank']) for t in lost['topics'][:6])))
    called = [k for k in study['kinds'] if k['topics']]
    if called:
        lines.append('Kinds of weakness found (with the topics and the evidence): ' + ' '.join(
            '{}: {}.'.format(k['name'], '; '.join('{} ({})'.format(t['name'], t['evidence']) for t in k['topics'][:3]))
            for k in called))
        lines.append('Train each kind its own way: ' + ' '.join(
            '{}: {}'.format(KINDS[k['id']]['name'], KINDS[k['id']]['approach']) for k in called))
    else:
        lines.append('Not enough answers yet to tell what kind of weakness any topic has.')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Where the student starts, and the plan's shape from the gap to the goal
# ---------------------------------------------------------------------------
SUBJECT_LEAN = {'weak': 1.2, 'ok': 1.0, 'strong': 0.8}


def starting_point(level, goal, projected, mocks, details, today):
    """Where the student is now against the goal, from their data.

    The projected score (backend/amc/mockscore.py): 95% their recent timed
    sittings and logged scores at this level, each adjusted for that paper's
    difficulty, and 5% the practice model's number (`projected`). With no
    sitting, the last real score they gave; with neither, unknown: practice
    alone is not a score. Returns {'current', 'from', 'goal', 'gap', 'weeks',
    'per_week', 'stage', 'summary'}."""
    from backend.amc import mockscore
    recent = mockscore.sittings(mocks, level, today)
    current, sources = None, []
    if recent:
        current = mockscore.blend(projected, recent)
        sources.append('{} recent sitting{} (adjusted for difficulty)'.format(len(recent), '' if len(recent) == 1 else 's'))
        if projected is not None:
            sources.append('{:.0%} your answers'.format(mockscore.MODEL_SHARE))
    elif (details or {}).get('last_score') not in (None, ''):
        current = float(details['last_score'])
        sources.append('the last score you gave')
    return _shape_from(level, goal, current, sources, today, details)


def _shape_from(level, goal, current, sources, today, details):
    aime = level == 'AIME'
    exam = (details or {}).get('_exam')
    weeks = max(1, ((date.fromisoformat(exam) - today).days // 7) + 1) if exam else None
    if current is None:
        return {'current': None, 'from': '', 'goal': goal, 'gap': None, 'weeks': weeks, 'per_week': None,
                'stage': 'unknown', 'summary': 'Sit a timed mock or log a contest score to see where you start.'}
    gap = round(goal - current, 1)
    far, near = (3, 0) if aime else (20, 0)
    if gap >= far:
        stage = 'far'
        summary = '{:g} below your goal: skills first, timed papers later.'.format(gap)
    elif gap > near:
        stage = 'near'
        summary = '{:g} below your goal: skills and timed papers side by side.'.format(gap)
    else:
        stage = 'there'
        summary = 'At your goal already: hold it under exam conditions and push higher.'
    return {'current': current, 'from': ' and '.join(sources), 'goal': goal, 'gap': gap, 'weeks': weeks,
            'per_week': round(gap / weeks, 2) if weeks and gap > 0 else 0, 'stage': stage, 'summary': summary}


#: Share of the weeks in Foundations and Core, and how often Core has a mock,
#: by how far the student is from the goal.
SHAPES = {
    'far': {'foundations': 0.45, 'core': 0.35, 'core_mock_every': 3},
    'near': {'foundations': 0.25, 'core': 0.4, 'core_mock_every': 2},
    'there': {'foundations': 0.15, 'core': 0.35, 'core_mock_every': 2},
    'unknown': {'foundations': 0.4, 'core': 0.35, 'core_mock_every': 3},
}


def subject_lean(details, answered_by_topic):
    """{topic: multiplier} from the student's own rating of each subject, worth
    less as the topic gathers answers of its own (the data takes over)."""
    rated = (details or {}).get('subjects') or {}
    out = {}
    for t in catalog.TOPICS:
        lean = SUBJECT_LEAN.get(rated.get(t['category']), 1.0)
        if lean != 1.0:
            trust = 1 / (1 + answered_by_topic.get(t['id'], 0) / 8)
            out[t['id']] = 1 + (lean - 1) * trust
    return out
