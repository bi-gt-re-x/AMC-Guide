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


def analyze(attempts, hist, level, today=None):
    """Priorities and weaknesses for a `level` student.

    Returns {'theta', 'topics': [priority rows, highest first], 'kinds': [per kind]}."""
    today = today or date.today()
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

    out = []
    for t in relevant:
        pts = by_topic.get(t['id'], [])
        th = smart.fit(pts, mean=theta, sd=smart.TOPIC_SD)[0] if pts else None
        answered = len(pts)
        right = sum(1 for _, ok, _w in pts if ok)
        gain = study_gain(level, theta, th, t['weight'] / total_weight)
        ratings = on_level.get(t['id'], [])
        reach = sum(smart.chance(theta + 1.0, r) for r in ratings) / len(ratings) if ratings else 0.6
        feasibility = round(0.5 + 0.5 * reach, 2)
        last = rows.get(t['id'], {}).get('last') or ''
        days = _days(today.isoformat(), last) if last else None
        recency = round(1.15 if days is None else 1 + 0.3 * min(1.0, days / STALE_DAYS), 2)
        importance = round(min(1.25, 1 + 0.05 * builds.get(t['id'], 0)), 2)
        priority = round(gain * feasibility * recency * importance, 2)
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
                        'importance': importance, 'builds': builds.get(t['id'], 0)},
            'kinds': kinds, 'kind': main, 'mode': mode, 'mode_label': MODE_LABEL[mode],
            'why': _why(t, gain, answered, right, feasibility, days, builds.get(t['id'], 0), main),
        })
    out.sort(key=lambda r: (-r['priority'], r['name']))

    kinds = []
    for key, info in KINDS.items():
        hit = sorted((r for r in out if key in r['kinds']), key=lambda r: -r['kinds'][key]['score'])
        kinds.append({'id': key, **info, 'topics': [
            {'id': r['id'], 'name': r['name'], 'category': r['category'], 'evidence': r['kinds'][key]['evidence'],
             'score': round(r['kinds'][key]['score'], 2)} for r in hit],
            'count': sum(r['kinds'][key]['count'] for r in hit)})
    return {'theta': round(theta, 2), 'topics': out, 'kinds': kinds}


def _why(t, gain, answered, right, feasibility, days, builds, kind):
    bits = []
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


def schedule(priorities, weeks, per_week=2, decay=0.55, coached=()):
    """[[topic rows] per week]: each week the highest remaining priorities, a
    topic's remaining value cut by `decay` once scheduled, so the most valuable
    come back spaced out, and not two weeks running while another is close.

    The AI coach's topic order (`coached`, a list), when there is one, fills
    the opening weeks as it asked: it has heard what the arithmetic cannot
    (backend/amc/coach.py). Then the arithmetic takes over."""
    by_id = {r['id']: r for r in priorities}
    remaining = {r['id']: max(r['priority'], 0.01) for r in priorities}
    order = [tid for tid in dict.fromkeys(coached) if tid in by_id]
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


def brief(study, top=6):
    """The priorities and kinds of weakness in a few lines, for an AI coach's brief."""
    lines = ['Study priorities by expected score gain (topic id: about +points from a few weeks on it; '
             'first-try right; kind of weakness and how to train it):']
    for r in study['topics'][:top]:
        f = r['factors']
        lines.append('- {} ({}): +{} pts; {}; {}'.format(
            r['id'], r['name'], r['gain'],
            '{}/{} right'.format(f['right'], f['answered']) if f['answered'] else 'not tried yet',
            '{} weakness, train by {}'.format(KINDS[r['kind']]['name'].lower(), r['mode_label'])
            if r['kind'] else 'train by ' + r['mode_label']))
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
