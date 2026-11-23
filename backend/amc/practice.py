"""A topic's practice set: eight problems, all in that one topic, picked for a
way of training it (backend/amc/planning.py `KINDS`).

* learn    — the topic's easiest problems, level by level, untried before
             tried and worked solutions first within a level: theory, then
             introductory problems, untimed.
* accuracy — problems within the student's reach (about 60% or better for
             them), ones they missed before first: untimed, check every answer.
* timed    — problems they can usually do, untried first, at contest pace
             (3 minutes each; 12 on the AIME).
* mixed    — the topic's whole range of difficulty and sources, shuffled, and
             shown without the topic's name, to practise recognising it.
* spaced   — problems they have answered before, the longest ago and the ones
             due for review first.
* practice — the topic's difficulty mix (planning.difficulty_mix), level by level.

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

    if mode == 'learn':
        order = take(mine, lambda p: (planning.level_of(p['rating']), seen(p), not p.get('solution'), p['rating']))
    elif mode == 'accuracy':
        within = [p for p in mine if chance(p) >= 0.6] or take(mine, lambda p: -chance(p))[:SIZE * 2]
        # Missed and not yet put right, then untried, then the rest.
        order = take(within, lambda p: (0 if seen(p) and not solved(p) else 1 if not seen(p) else 2,
                                        abs(chance(p) - 0.7)))
    elif mode == 'timed':
        fit = [p for p in mine if 0.5 <= chance(p) <= 0.9] or mine
        order = take(fit, lambda p: (seen(p), abs(chance(p) - 0.7)))
    elif mode == 'spaced':
        def due_rank(p):
            rev = review_by_id.get(p['id'])
            due = rev and rev['status'] == 'active' and rev['due'] <= today.isoformat()
            return (0 if due else 1, hist[p['id']]['last_at'])
        order = take([p for p in mine if seen(p)], due_rank)
        if len(order) < SIZE:                    # too few met before: the nearest new ones
            order += take([p for p in mine if not seen(p)], lambda p: abs(chance(p) - 0.7))
    elif mode == 'mixed':
        # Across every level and source the topic has, untried first.
        by_level = {}
        for p in take(mine, lambda p: seen(p)):
            by_level.setdefault(planning.level_of(p['rating']), []).append(p)
        order = []
        while any(by_level.values()):
            for lvl in sorted(by_level):
                if by_level[lvl]:
                    order.append(by_level[lvl].pop(0))
    else:
        counts = {c['level']: c['count'] for c in planning.split_count(mix, SIZE)} if mix else {}
        order = []
        for lvl, n in sorted(counts.items()):
            order += take([p for p in mine if planning.level_of(p['rating']) == lvl and p not in order],
                          lambda p: seen(p))[:n]
        order += take([p for p in mine if p not in order], lambda p: (seen(p), abs(chance(p) - 0.65)))

    # Fill to eight: the mode's picks from the topic's own problems, then its
    # other own problems nearest the student's level, then problems only
    # tagged with the topic, then the topic's problems from other contests.
    own = lambda p: p['topic'] == topic_id
    near = lambda p: (seen(p), abs(chance(p) - 0.65))
    rest = take([p for p in mine if p not in order], near)
    ranked = ([p for p in order if own(p)] + [p for p in rest if own(p)]
              + [p for p in order if not own(p)] + [p for p in rest if not own(p)])
    picked = []
    for p in ranked + take(other, near):
        if p['id'] not in {q['id'] for q in picked}:
            picked.append(p)
        if len(picked) == SIZE:
            break
    if mode == 'mixed':
        rng.shuffle(picked)
    elif mode != 'spaced':
        picked.sort(key=lambda p: p['rating'])
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
