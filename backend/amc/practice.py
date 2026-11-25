"""A topic's practice set: eight problems, all in that one topic, picked for a
way of training it (backend/amc/planning.py `KINDS`).

* learn    — problems comfortably within reach for this student in this
             topic, worked solutions first: theory, then introductory
             problems, untimed.
* accuracy — problems within the student's reach (about 60% or better for
             them), ones they missed before first: untimed, check every answer.
* timed    — problems they can usually do, untried first, at contest pace
             (3 minutes each; 12 on the AIME).
* mixed    — the widest spread of difficulty the student can use, shown
             without the topic's name, to practise recognising it.
* spaced   — problems they have answered before, the longest ago and the ones
             due for review first.
* practice — the topic's difficulty mix (planning.difficulty_mix), level by level.

## Pitched to the student, and harder as it goes

Every set is picked from how this student does *in this topic*: the topic's
ability estimate (planning.analyze, from their answers in it, shrunk toward
their overall level so a few answers cannot swing it), or a little under their
overall level for a topic not tried yet. So a set moves up as the topic does,
and a strong student starting a new topic does not start at level 1.

Within a set the problems step up: `RAMPS` gives each mode the chance of a
right answer its first problem should have and the one its last should, and
the problems between are picked on the way down, so a set opens on something
they can do and ends on a stretch. Every set is then shown easiest first.

A set is the same all day (seeded by account, topic, mode and date), so
reloading the page does not reshuffle it.
"""
import random
from datetime import date

from backend.amc import catalog, engine, planning, smart
from backend.amc import problems as pb

SIZE = 8
MODES = ('learn', 'accuracy', 'timed', 'mixed', 'spaced', 'practice')
SECONDS = {'AMC 10': 180, 'AMC 12': 180, 'AIME': 720}
INSTRUCTIONS = {
    'learn': 'Read the ideas first, then work these easiest-first. No clock; check the solution after each.',
    'accuracy': 'No clock. Write each step and check your answer before you submit.',
    'timed': 'Contest pace: {} a problem. Skip what you cannot start.',
    'mixed': "The topic's name is hidden: decide which idea each one needs before you start.",
    'spaced': "Problems you have met before, the longest ago first. Solve them fresh.",
    'practice': 'A mix of difficulty levels for where you are in this topic.',
}
TITLES = {'learn': 'Learn the ideas', 'accuracy': 'Accuracy drill', 'timed': 'Timed set', 'mixed': 'Mixed set',
          'spaced': 'Spaced review', 'practice': 'Practice set'}


#: The fewest of each kind, real contest problems and mock ones, a set holds
#: when the topic has both: practice is on the papers it is for, and the mocks
#: (with their worked solutions) alongside them, never one kind alone.
MIN_EACH = 2


def _balance(picked, candidates):
    """`picked` with at least MIN_EACH real and MIN_EACH mock problems where
    `candidates` (best first) has them, swapping out the least wanted picks
    of the kind there are more of."""
    picked = list(picked)
    for want in (True, False):
        have = sum(1 for p in picked if pb.is_official(p['id']) == want)
        if have >= MIN_EACH:
            continue
        ids = {p['id'] for p in picked}
        extra = [p for p in candidates if pb.is_official(p['id']) == want and p['id'] not in ids]
        extra = extra[:MIN_EACH - have]
        spare = [p for p in picked if pb.is_official(p['id']) != want]
        drop = spare[len(spare) - len(extra):] if len(picked) + len(extra) > SIZE else []
        if len(spare) - len(drop) < MIN_EACH and spare:
            drop = drop[:max(0, len(spare) - MIN_EACH)]
            extra = extra[:len(drop) + max(0, SIZE - len(picked))]
        dropped = {p['id'] for p in drop}
        picked = [p for p in picked if p['id'] not in dropped] + extra
    return picked


#: (first, last): the chance of a right answer for this student that a set's
#: first and last problem aim at, the rest stepped evenly between. Learning
#: starts easy and stays in reach; a timed set ends nearer a coin flip.
RAMPS = {'learn': (0.92, 0.65), 'accuracy': (0.9, 0.6), 'timed': (0.85, 0.55),
         # The widest spread, for recognising the topic at every difficulty, but
         # still from where the student is, not the topic's hardest.
         'mixed': (0.92, 0.35)}


def _ramp(rows, chance, first, last, n, cost):
    """`n` of `rows` getting harder: for each of `n` targets stepped from
    `first` down to `last`, the free row whose chance is nearest, plus
    `cost` (untried and the topic's own problems first)."""
    targets = [first - (first - last) * k / max(1, n - 1) for k in range(n)]
    left, out = list(rows), []
    for target in targets:
        if not left:
            break
        best = min(left, key=lambda p: (abs(chance(p) - target) + cost(p), p['id']))
        out.append(best)
        left.remove(best)
    return out


def _in_topic(p, topic_id):
    return p['topic'] == topic_id or topic_id in p['also']


def build(topic_id, mode, level, theta, topic_theta, mix, hist, review_by_id, user='', today=None):
    """{'topic', 'mode', 'title', 'instructions', 'seconds', 'hide_topic', 'problems': [ids]}."""
    today = today or date.today()
    mode = mode if mode in MODES else 'practice'
    th = topic_theta if topic_theta is not None else theta - 0.3
    rng = random.Random('{}|{}|{}|{}'.format(user, topic_id, mode, today.isoformat()))
    pool = [p for p in pb.all_problems() if _in_topic(p, topic_id)]
    # The student's own contest first; the topic's other problems only to fill.
    mine = [p for p in pool if p['level'] == level] or pool
    other = [p for p in pool if p not in mine]
    chance = lambda p: smart.chance(th, p['rating'])
    seen = lambda p: p['id'] in hist
    solved = lambda p: bool(hist.get(p['id'], {}).get('solved'))
    jitter = {p['id']: rng.random() for p in pool}

    def take(rows, key):
        # Problems whose main topic this is come first; one only tagged with it
        # (a probability problem that also uses circles) only fills a set.
        return sorted(rows, key=lambda p: (p['topic'] != topic_id, key(p), jitter[p['id']]))

    # What a pick costs besides its distance from the step it fills: a problem
    # met before, one only tagged with the topic, no worked solution to learn
    # from; and a little noise so equal problems are not always the same ones.
    def cost(p, solution=False):
        return (0.25 if seen(p) else 0) + (0.12 if p['topic'] != topic_id else 0) \
            + (0.06 if solution and not p.get('solution') else 0) + jitter[p['id']] * 0.02

    if mode == 'learn':
        order = _ramp(mine, chance, *RAMPS['learn'], SIZE, lambda p: cost(p, solution=True))
    elif mode == 'accuracy':
        # Missed and not yet put right first: those are the point. Then new
        # problems within reach, getting harder.
        missed = take([p for p in mine if seen(p) and not solved(p) and chance(p) >= 0.45],
                      lambda p: -chance(p))[:SIZE // 2]
        order = missed + _ramp([p for p in mine if p not in missed], chance, *RAMPS['accuracy'],
                               SIZE - len(missed), cost)
    elif mode == 'timed':
        order = _ramp(mine, chance, *RAMPS['timed'], SIZE, cost)
    elif mode == 'spaced':
        def due_rank(p):
            rev = review_by_id.get(p['id'])
            due = rev and rev['status'] == 'active' and rev['due'] <= today.isoformat()
            return (0 if due else 1, hist[p['id']]['last_at'])
        order = take([p for p in mine if seen(p)], due_rank)
        if len(order) < SIZE:                    # too few met before: the nearest new ones
            order += take([p for p in mine if not seen(p)], lambda p: abs(chance(p) - 0.7))
    elif mode == 'mixed':
        order = _ramp(mine, chance, *RAMPS['mixed'], SIZE, cost)
    else:
        counts = {c['level']: c['count'] for c in planning.split_count(mix, SIZE)} if mix else {}
        order = []
        for lvl, n in sorted(counts.items()):
            order += take([p for p in mine if planning.level_of(p['rating']) == lvl and p not in order],
                          lambda p: (seen(p), round(abs(chance(p) - 0.7), 1)))[:n]
        order += take([p for p in mine if p not in order], lambda p: (seen(p), abs(chance(p) - 0.65)))

    # Fill to eight: the mode's picks from the topic's own problems, then its
    # other own problems nearest the student's level, then problems only
    # tagged with the topic, then the topic's problems from other contests.
    own = lambda p: p['topic'] == topic_id
    near = lambda p: (seen(p), abs(chance(p) - 0.65))
    rest = take([p for p in mine if p not in order], near)
    ranked = ([p for p in order if own(p)] + [p for p in rest if own(p)]
              + [p for p in order if not own(p)] + [p for p in rest if not own(p)])
    candidates = ranked + take(other, near)
    picked = []
    for p in candidates:
        if p['id'] not in {q['id'] for q in picked}:
            picked.append(p)
        if len(picked) == SIZE:
            break
    if mode != 'spaced':
        picked = _balance(picked, candidates)
    # Every set easiest first, so it gets harder as it goes; real and mock
    # problems of the same rating mixed, not every mock first.
    picked = pb.mix_sources(sorted(picked, key=lambda p: (p['rating'], p['id'])), key=lambda p: p['rating'])
    seconds = SECONDS.get(level, 180) if mode == 'timed' else None
    text = INSTRUCTIONS[mode]
    if seconds:
        text = text.format('{} minutes'.format(seconds // 60))
    topic = catalog.TOPIC_BY_ID[topic_id]
    return {'topic': {'id': topic_id, 'name': topic['name'], 'category': topic['category']},
            'mode': mode, 'title': TITLES[mode], 'instructions': text, 'seconds': seconds,
            'hide_topic': mode == 'mixed', 'level': level,
            'problems': [p['id'] for p in picked]}


def for_user(topic_id, mode, attempts, hist, review_by_id, level, goal, user, today):
    """`build` from an account's own history and plan."""
    study = planning.analyze(attempts, hist, level, today, goal)
    row = next((r for r in study['topics'] if r['id'] == topic_id), None)
    topic_theta = row['factors']['level'] if row else None
    mix = row['mix'] if row else study['mix']
    out = build(topic_id, mode, level, study['theta'], topic_theta, mix, hist, review_by_id, user, today)
    out['mix'] = mix
    out['suggested'] = row['mode'] if row else 'practice'
    return out
