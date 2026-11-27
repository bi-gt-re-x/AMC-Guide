"""A topic's practice set: eight problems, all in that one topic, picked for a
way of training it (backend/amc/planning.py `KINDS`).

* learn    — problems comfortably within reach for this student in this
             topic, worked solutions first: theory, then introductory
             problems, untimed.
* accuracy — problems within the student's reach (about 60% or better for
             them), aimed at the techniques and difficulty levels of the
             topic where their accuracy per problem answered is lowest
             (`miss_rates`), ones they missed there first: untimed, check
             every answer.
* timed    — at contest pace (3 minutes each; 12 on the AIME): half sprint
             problems (quick to work and likely right), half heavy ones
             (long to compute), each half stepping up (`work_rank`).
* mixed    — the widest spread of difficulty the student can use, shown
             without the topic's name, to practise recognising it.
* spaced   — problems they have answered before, the longest ago and the ones
             due for review first.
* practice — the topic's difficulty mix (planning.difficulty_mix), level by level.
* challenge — five problems above where the student is in the topic, on a
             longer clock: the study plan's weekly stretch, never beyond reach.

Every set is within the student's reach with one or two challenges at the end
(backend/amc/pitch.py); the challenge set is all challenges.

A set is eight problems unless asked for fewer or more (`size`): the study
plan sizes each day's set to the minutes the student has that day.

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
import re
from datetime import date

from backend.amc import catalog, engine, pitch, planning, smart
from backend.amc import problems as pb

SIZE = 8
MODES = ('learn', 'accuracy', 'timed', 'mixed', 'spaced', 'practice', 'challenge')
#: The sets that run on a clock, and how long each problem gets.
TIMED = ('timed', 'challenge')
CHALLENGE_SIZE = 5
SIZES = (3, 12)
SECONDS = {'AMC 10': 180, 'AMC 12': 180, 'AIME': 720}
#: A challenge problem gets half as long again as a timed one.
CHALLENGE_STRETCH = 1.5
INSTRUCTIONS = {
    'learn': 'Read the ideas first, then work these easiest-first. No clock; check the solution after each.',
    'accuracy': 'No clock. Write each step and check your answer before you submit.',
    'timed': 'Contest pace: {} a problem. Skip what you cannot start.',
    'mixed': "The topic's name is hidden: decide which idea each one needs before you start.",
    'spaced': "Problems you have met before, the longest ago first. Solve them fresh.",
    'practice': 'A mix of difficulty levels for where you are in this topic.',
    'challenge': 'Harder than you usually solve, {} a problem on the clock. Two right is a good set.',
}
TITLES = {'learn': 'Learn the ideas', 'accuracy': 'Accuracy drill', 'timed': 'Timed set', 'mixed': 'Mixed set',
          'spaced': 'Spaced review', 'practice': 'Practice set', 'challenge': 'Challenge set'}


#: The fewest of each kind, real contest problems and mock ones, a set holds
#: when the topic has both: practice is on the papers it is for, and the mocks
#: (with their worked solutions) alongside them, never one kind alone.
MIN_EACH = 2


def _balance(picked, candidates, size=SIZE):
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
        drop = spare[len(spare) - len(extra):] if len(picked) + len(extra) > size else []
        if len(spare) - len(drop) < MIN_EACH and spare:
            drop = drop[:max(0, len(spare) - MIN_EACH)]
            extra = extra[:len(drop) + max(0, size - len(picked))]
        dropped = {p['id'] for p in drop}
        picked = [p for p in picked if p['id'] not in dropped] + extra
    return picked


#: (first, last): the chance of a right answer for this student that a set's
#: first and last problem aim at, the rest stepped evenly between. Learning
#: starts easy and stays in reach; a timed set ends nearer a coin flip.
RAMPS = {'learn': (0.92, 0.65), 'accuracy': (0.9, 0.6), 'timed': (0.85, 0.55),
         # The widest spread, for recognising the topic at every difficulty, but
         # still from where the student is, not the topic's hardest: in reach
         # (the set's challenges are added by backend/amc/pitch.py).
         'mixed': (0.92, 0.5),
         # A stretch: from even odds to the edge of reach, never past it.
         'challenge': (0.5, pitch.FLOOR)}

#: A timed set's two halves: sprint problems (quick to work, and likely right:
#: the points banked fast on a real paper) and heavy ones (long to compute:
#: where a clock is lost). Each ramps on its own.
SPRINT_RAMP = (0.9, 0.65)
HEAVY_RAMP = (0.8, 0.55)
#: How hard an accuracy drill leans toward a weak spot: a miss rate of 1
#: outweighs being a quarter of a chance away from the step it would fill.
WEAK_PULL = 0.25


def _work(p):
    """How much computing a problem takes, roughly: the numbers and length of
    its worked solution (or, without one, of its statement, which says less)."""
    steps = p.get('solution') or []
    text = ' '.join(steps) if isinstance(steps, list) else str(steps)
    if text:
        return 'solution', len(re.findall(r'\d+', text)) + len(text) / 40 + 2 * len(steps)
    statement = p.get('statement') or ''
    return 'statement', len(re.findall(r'\d+', statement)) + len(statement) / 40


def work_rank(rows):
    """{id: 0..1}, how heavy each problem is to compute next to the others:
    ranked within those scored from a solution and within those scored from a
    statement, which are not on the same footing."""
    groups = {}
    for p in rows:
        basis, score = _work(p)
        groups.setdefault(basis, []).append((score, p['id']))
    out = {}
    for scored in groups.values():
        scored.sort()
        for i, (_, pid) in enumerate(scored):
            out[pid] = i / max(1, len(scored) - 1)
    return out


def miss_rates(rows, hist):
    """{id: 0..1}, how often this student misses problems like each one, per
    problem answered: the first-try miss rate of its technique and of its
    difficulty level within these rows, whichever is worse. Each is shrunk
    toward the rows' own rate (two answers' worth), so one miss does not make
    a weakness, and a technique not yet answered sits at the average."""
    answered = [p for p in rows if p['id'] in hist and hist[p['id']].get('first_source') != 'reveal']
    misses = sum(1 for p in answered if not hist[p['id']]['first_correct'])
    base = (misses + 1) / (len(answered) + 2)
    counts = {}
    for p in answered:
        for key in (('t', p['technique']), ('l', planning.level_of(p['rating']))):
            seen, missed = counts.get(key, (0, 0))
            counts[key] = (seen + 1, missed + (0 if hist[p['id']]['first_correct'] else 1))

    def rate(key):
        seen, missed = counts.get(key, (0, 0))
        return (missed + 2 * base) / (seen + 2)
    return {p['id']: max(rate(('t', p['technique'])), rate(('l', planning.level_of(p['rating'])))) for p in rows}


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


def size_for(mode, size=None):
    """How many problems a set holds: `size` if given, within SIZES; else eight, or five for a challenge."""
    if size:
        return max(SIZES[0], min(SIZES[1], int(size)))
    return CHALLENGE_SIZE if mode == 'challenge' else SIZE


def seconds_for(mode, level):
    """Seconds a problem gets in a set that runs on a clock, else None."""
    if mode not in TIMED:
        return None
    base = SECONDS.get(level, 180)
    return int(base * CHALLENGE_STRETCH) if mode == 'challenge' else base


def build(topic_id, mode, level, theta, topic_theta, mix, hist, review_by_id, user='', today=None, size=None):
    """{'topic', 'mode', 'title', 'instructions', 'seconds', 'hide_topic', 'problems': [ids]}."""
    today = today or date.today()
    mode = mode if mode in MODES else 'practice'
    n = size_for(mode, size)
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
        order = _ramp(mine, chance, *RAMPS['learn'], n, lambda p: cost(p, solution=True))
    elif mode == 'accuracy':
        # Aimed where this student's accuracy per problem answered is lowest:
        # the techniques and difficulty levels of the topic they miss most
        # often (`miss_rates`). Missed and not yet put right first, worst
        # first: those are the point. Then new problems within reach, getting
        # harder, pulled toward the same weak spots.
        weak = miss_rates(mine, hist)
        open_ = take([p for p in mine if seen(p) and not solved(p) and pitch.band(chance(p)) != 'beyond'],
                     lambda p: (-round(weak[p['id']], 2), -chance(p)))
        # Those a little past reach count as the set's challenges, so no more of them.
        stretch = [p for p in open_ if pitch.band(chance(p)) == 'stretch'][:pitch.challenges_for(n)]
        missed = [p for p in open_ if pitch.band(chance(p)) == 'in' or p in stretch][:n // 2]
        order = missed + _ramp([p for p in mine if p not in missed], chance, *RAMPS['accuracy'],
                               n - len(missed), lambda p: cost(p) - WEAK_PULL * weak[p['id']])
    elif mode == 'timed':
        # Half sprint problems, half heavy ones (`work_rank`), each half
        # stepping up on its own; whatever the topic lacks of one, the other fills.
        heft = work_rank(mine)
        sprint = [p for p in mine if heft[p['id']] <= 1 / 3]
        heavy = [p for p in mine if heft[p['id']] >= 2 / 3]
        quick = _ramp(sprint, chance, *SPRINT_RAMP, (n + 1) // 2, cost)
        order = quick + _ramp([p for p in heavy if p not in quick], chance, *HEAVY_RAMP, n - len(quick), cost)
        if len(order) < n:
            order += _ramp([p for p in mine if p not in order], chance, *RAMPS['timed'], n - len(order), cost)
    elif mode == 'spaced':
        def due_rank(p):
            rev = review_by_id.get(p['id'])
            due = rev and rev['status'] == 'active' and rev['due'] <= today.isoformat()
            return (0 if due else 1, hist[p['id']]['last_at'])
        order = take([p for p in mine if seen(p)], due_rank)
        if len(order) < n:                    # too few met before: the nearest new ones
            order += take([p for p in mine if not seen(p)], lambda p: abs(chance(p) - 0.7))
    elif mode == 'mixed':
        order = _ramp(mine, chance, *RAMPS['mixed'], n, cost)
    elif mode == 'challenge':
        # Untried first: a stretch is no stretch if the answer is remembered.
        order = _ramp(mine, chance, *RAMPS['challenge'], n, lambda p: cost(p) + (0.3 if solved(p) else 0))
    else:
        counts = {c['level']: c['count'] for c in planning.split_count(mix, n)} if mix else {}
        order = []
        for lvl, k in sorted(counts.items()):
            order += take([p for p in mine if planning.level_of(p['rating']) == lvl and p not in order],
                          lambda p: (seen(p), round(abs(chance(p) - 0.7), 1)))[:k]
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
        if len(picked) == n:
            break
    if mode != 'spaced':
        # Never balanced in with something beyond reach.
        picked = _balance(picked, [p for p in candidates if pitch.band(chance(p)) != 'beyond'], n)
    # Within reach, with one or two challenges (backend/amc/pitch.py). A swap
    # keeps a real problem for a real one, and in a spaced set one met before
    # for one met before.
    if mode == 'spaced':
        like = lambda a, b: seen(a) == seen(b)
    else:
        like = lambda a, b: pb.is_official(a['id']) == pb.is_official(b['id'])
    tier = lambda p: (0 if own(p) else 1) + (2 if p in other else 0)
    picked = pitch.pitch(picked, candidates, chance, n, like, all_stretch=mode == 'challenge', tier=tier,
                         strict=mode == 'spaced')
    # Every set easiest first, so it gets harder as it goes; real and mock
    # problems of the same rating mixed, not every mock first.
    picked = pb.mix_sources(sorted(picked, key=lambda p: (p['rating'], p['id'])), key=lambda p: p['rating'])
    challenges = [p['id'] for p in picked if pitch.band(chance(p)) == 'stretch']
    seconds = seconds_for(mode, level)
    text = INSTRUCTIONS[mode]
    if seconds:
        text = text.format('{:g} minutes'.format(seconds / 60))
    if mode != 'challenge' and challenges:
        text += ' The last {} {} a stretch.'.format(
            'one' if len(challenges) == 1 else len(challenges), 'is' if len(challenges) == 1 else 'are')
    topic = catalog.TOPIC_BY_ID[topic_id]
    return {'topic': {'id': topic_id, 'name': topic['name'], 'category': topic['category']},
            'mode': mode, 'title': TITLES[mode], 'instructions': text, 'seconds': seconds,
            'hide_topic': mode == 'mixed', 'level': level, 'size': n,
            'total_seconds': seconds * len(picked) if seconds else None,
            'problems': [p['id'] for p in picked],
            # The ones a little past the student's reach (backend/amc/pitch.py),
            # and the level in this topic the set was pitched at.
            'challenges': challenges, 'pitched_at': round(th, 2)}


def for_user(topic_id, mode, attempts, hist, review_by_id, level, goal, user, today, size=None):
    """`build` from an account's own history and plan."""
    study = planning.analyze(attempts, hist, level, today, goal)
    row = next((r for r in study['topics'] if r['id'] == topic_id), None)
    topic_theta = row['factors']['level'] if row else None
    mix = row['mix'] if row else study['mix']
    out = build(topic_id, mode, level, study['theta'], topic_theta, mix, hist, review_by_id, user, today, size)
    out['mix'] = mix
    out['suggested'] = row['mode'] if row else 'practice'
    return out
