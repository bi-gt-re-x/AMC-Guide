"""Every set within the student's reach with one or two challenges
(backend/amc/pitch.py); accuracy drills aimed where accuracy per problem
answered is lowest; timed sets of sprint and heavy problems
(backend/amc/practice.py)."""
from datetime import date, timedelta

import pytest

from backend.amc import engine, pitch, planning, practice, smart, weak
from backend.amc import problems as pb

TODAY = date(2026, 11, 20)
TOPIC = 'probability'


def _attempt(pid, correct, days_ago=10):
    return {'problem_id': pid, 'answer': 'X', 'correct': 1 if correct else 0, 'seconds': 150,
            'source': 'practice', 'at': (TODAY - timedelta(days=days_ago)).isoformat() + 'T17:00:00'}


def _pool(topic=TOPIC):
    return [p for p in pb.all_problems() if p['level'] == 'AMC 10' and (p['topic'] == topic or topic in p['also'])]


def _bands(ids, th):
    return [pitch.band(smart.chance(th, pb.get(i)['rating'])) for i in ids]


# -- The bands --------------------------------------------------------------
def test_the_bands_follow_the_same_limit_as_too_challenging():
    assert pitch.band(0.5) == 'in' and pitch.band(0.49) == 'stretch'
    # A problem NEAR above the student is the hardest a set may go.
    assert pitch.band(smart.chance(4, 4 + 1.0)) == 'stretch'
    assert pitch.band(smart.chance(4, 4 + 1.2)) == 'beyond'
    assert pitch.challenges_for(3) == 1 and pitch.challenges_for(5) == 1
    assert pitch.challenges_for(6) == 2 and pitch.challenges_for(12) == 2


def test_pitch_swaps_out_what_is_beyond_and_keeps_one_or_two_challenges():
    rows = [{'id': 'p{}'.format(i), 'c': c} for i, c in enumerate(
        [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.45, 0.4, 0.35, 0.2, 0.1])]
    chance = lambda p: p['c']
    # Four challenges and two beyond reach picked: down to two challenges, none beyond.
    picked = rows[:3] + rows[8:]
    out = pitch.pitch(picked, rows, chance, 8)
    bands = [pitch.band(p['c']) for p in out]
    assert len(out) == 8 and bands.count('beyond') == 0 and bands.count('stretch') == 2
    # No challenge picked: the hardest in-reach one makes way for one.
    out = pitch.pitch(rows[:8], rows, chance, 8)
    assert [pitch.band(p['c']) for p in out].count('stretch') == 2
    assert rows[0] in out and rows[7] not in out     # the easiest stay
    # The challenge set: all challenges while there are any (three here), then
    # in reach, never beyond.
    out = pitch.pitch(rows[:3], rows, chance, 3, all_stretch=True)
    assert all(pitch.band(p['c']) == 'stretch' for p in out)
    out = pitch.pitch(rows[:2] + rows[11:], rows, chance, 4, all_stretch=True)
    assert [pitch.band(p['c']) for p in out].count('stretch') == 3 and 'beyond' not in [pitch.band(p['c']) for p in out]


def test_strict_keeps_a_like_problem_or_nothing():
    rows = [{'id': 'a', 'c': 0.9, 'k': 1}, {'id': 'b', 'c': 0.8, 'k': 1}, {'id': 'x', 'c': 0.4, 'k': 2}]
    out = pitch.pitch(rows[:2], rows, lambda p: p['c'], 3, like=lambda a, b: a['k'] == b['k'], strict=True)
    assert [p['id'] for p in out] == ['a', 'b']


# -- Every topic set --------------------------------------------------------
@pytest.mark.parametrize('th', [3.0, 4.2, 5.5])
def test_every_topic_set_is_in_reach_with_one_or_two_challenges(client, th):
    pool = _pool()
    reachable = [p for p in pool if pitch.band(smart.chance(th, p['rating'])) != 'beyond']
    stretchable = [p for p in pool if pitch.band(smart.chance(th, p['rating'])) == 'stretch']
    for mode in practice.MODES:
        s = practice.build(TOPIC, mode, 'AMC 10', th, th, planning.difficulty_mix(th, 2), {}, {}, 'u', TODAY)
        bands = _bands(s['problems'], th)
        if len(reachable) >= len(s['problems']):
            assert 'beyond' not in bands, (mode, th)
        if mode == 'challenge':
            if len(stretchable) >= len(s['problems']):
                assert set(bands) == {'stretch'}, th
            continue
        assert bands.count('stretch') <= 2, (mode, th)
        if stretchable and mode != 'spaced':
            assert bands.count('stretch') >= 1, (mode, th)
        assert s['challenges'] == [i for i, b in zip(s['problems'], bands) if b == 'stretch']
        if s['challenges']:
            assert 'stretch' in s['instructions']


def test_the_challenges_come_last(client):
    s = practice.build(TOPIC, 'practice', 'AMC 10', 4.2, 4.2, planning.difficulty_mix(4.2, 2), {}, {}, 'u', TODAY)
    assert s['challenges'] and s['problems'][-len(s['challenges']):] == s['challenges']


# -- Accuracy drills ---------------------------------------------------------
def test_miss_rates_are_per_problem_answered_and_shrunk():
    pool = _pool()
    by_tech = {}
    for p in pool:
        by_tech.setdefault(p['technique'], []).append(p)
    weak_t, good_t = sorted(by_tech, key=lambda t: -len(by_tech[t]))[:2]
    rows = [_attempt(p['id'], False) for p in by_tech[weak_t][:2]] + \
           [_attempt(p['id'], True) for p in by_tech[good_t][:2]]
    rates = practice.miss_rates(pool, engine.history(rows))
    weak_p, good_p = by_tech[weak_t][-1], by_tech[good_t][-1]
    assert rates[weak_p['id']] > rates[good_p['id']]
    # Nothing answered: every problem at the same middling rate.
    assert len(set(practice.miss_rates(pool, {}).values())) == 1


def test_an_accuracy_drill_leans_to_the_technique_missed_most(client):
    pool = _pool()
    # Miss every casework problem answered, get everything else right.
    answered = sorted(pool, key=lambda p: p['rating'])[:6]
    rows = [_attempt(p['id'], p['technique'] != 'casework', days_ago=30 - i) for i, p in enumerate(answered)]
    assert any(p['technique'] == 'casework' for p in answered), 'the fixture needs a casework problem'
    hist = engine.history(rows)
    drill = practice.build(TOPIC, 'accuracy', 'AMC 10', 4.2, 4.2, None, hist, {}, 'u', TODAY)
    plain = practice.build(TOPIC, 'practice', 'AMC 10', 4.2, 4.2, planning.difficulty_mix(4.2, 2), hist, {}, 'u', TODAY)
    count = lambda s: sum(1 for i in s['problems'] if pb.get(i)['technique'] == 'casework')
    assert count(drill) >= count(plain) and count(drill) >= 2
    # The misses still open are in it.
    missed = {r['problem_id'] for r in rows if not r['correct']
              if pitch.band(smart.chance(4.2, pb.get(r['problem_id'])['rating'])) == 'in'}
    assert missed <= set(drill['problems'])


# -- Timed sets --------------------------------------------------------------
def test_work_rank_puts_long_computations_above_quick_ones():
    quick = {'id': 'q', 'solution': ['$2+2=4$.'], 'statement': ''}
    heavy = {'id': 'h', 'solution': ['$12 \\cdot 34 = 408$, then $408 - 17 = 391$ and $391 / 23 = 17$.'] * 4,
             'statement': ''}
    mid = {'id': 'm', 'solution': ['$12 \\cdot 3 = 36$, so $36 - 5 = 31$.'], 'statement': ''}
    rank = practice.work_rank([heavy, quick, mid])
    assert rank['q'] < rank['m'] < rank['h'] and rank['q'] == 0 and rank['h'] == 1
    # Ranked apart from problems scored only by their statement.
    bare = {'id': 'b', 'solution': [], 'statement': 'Find 1 + 1.'}
    assert practice.work_rank([quick, bare]) == {'q': 0, 'b': 0}


def test_a_timed_set_is_half_sprint_half_heavy(client):
    pool = _pool()
    heft = practice.work_rank([p for p in pool if p['level'] == 'AMC 10'])
    s = practice.build(TOPIC, 'timed', 'AMC 10', 4.5, 4.5, None, {}, {}, 'u', TODAY)
    ranks = [heft.get(i) for i in s['problems'] if i in heft]
    sprint = sum(1 for r in ranks if r <= 1 / 3)
    heavy = sum(1 for r in ranks if r >= 2 / 3)
    # Both kinds, and together most of the set (the reach pass may swap one or two).
    assert sprint >= 2 and heavy >= 2 and sprint + heavy >= len(s['problems']) - 3
    assert s['seconds'] == 180


# -- The weak-topics set ----------------------------------------------------
def test_the_weak_topics_set_is_in_reach_with_one_or_two_challenges(client):
    out = weak.bank({}, {}, 'AMC 10', True, 'u', TODAY)
    bands = [pitch.band(c) for _, _, c in out['problems']]
    assert len(out['problems']) == weak.SIZE
    assert 'beyond' not in bands and 1 <= bands.count('stretch') <= 2
