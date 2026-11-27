"""A problem solved in the last ten days is not dealt again while anything else
will do (engine.RECENT_SOLVE_DAYS): not in a topic set of any mode, and last in
the review queue."""
from datetime import date, timedelta

import pytest

from backend.amc import engine, planning, practice
from backend.amc import problems as pb

TODAY = date(2026, 11, 20)
TOPIC = 'probability'


def _attempt(pid, correct, days_ago, source='practice'):
    return {'problem_id': pid, 'answer': 'X', 'correct': 1 if correct else 0, 'seconds': 120,
            'source': source, 'at': (TODAY - timedelta(days=days_ago)).isoformat() + 'T17:00:00'}


def _pool():
    return [p for p in pb.all_problems() if p['level'] == 'AMC 10' and (p['topic'] == TOPIC or TOPIC in p['also'])]


def test_history_keeps_when_a_problem_was_last_solved():
    h = engine.history([_attempt('x', True, 20), _attempt('x', False, 12), _attempt('x', True, 5),
                        _attempt('x', False, 1)])['x']
    assert h['solved_at'].startswith((TODAY - timedelta(days=5)).isoformat())
    assert engine.history([_attempt('y', False, 3)])['y']['solved_at'] == ''


def test_recently_is_fewer_than_ten_days():
    solved = lambda days: engine.history([_attempt('x', True, days)])['x']
    assert engine.solved_recently(solved(0), TODAY) and engine.solved_recently(solved(9), TODAY)
    # Ten days is the review schedule's own second step: not held back.
    assert not engine.solved_recently(solved(10), TODAY)
    assert not engine.solved_recently(None, TODAY)
    assert not engine.solved_recently(engine.history([_attempt('x', False, 2)])['x'], TODAY)


@pytest.mark.parametrize('mode', practice.MODES)
def test_no_topic_set_deals_a_problem_solved_this_week_while_others_are_left(client, mode):
    pool = sorted(_pool(), key=lambda p: (p['rating'], p['id']))
    # The easiest four solved three days ago: exactly what most modes reach for first.
    recent = [p['id'] for p in pool[:4]]
    rows = [_attempt(pid, True, 3) for pid in recent]
    hist = engine.history(rows)
    s = practice.build(TOPIC, mode, 'AMC 10', 4.2, 4.2, planning.difficulty_mix(4.2, 2), hist, {}, 'u', TODAY)
    others = len(pool) - len(recent)
    if others >= len(s['problems']):
        assert not set(recent) & set(s['problems']), mode


def test_a_spaced_set_takes_problems_met_long_enough_ago(client):
    pool = sorted(_pool(), key=lambda p: (p['rating'], p['id']))
    recent, older = [p['id'] for p in pool[:3]], [p['id'] for p in pool[3:6]]
    rows = [_attempt(pid, True, 2) for pid in recent] + [_attempt(pid, True, 30) for pid in older]
    s = practice.build(TOPIC, 'spaced', 'AMC 10', 4.2, 4.2, None, engine.history(rows), {}, 'u', TODAY)
    assert set(older) <= set(s['problems']) and not set(recent) & set(s['problems'])


def test_a_small_topic_still_fills_its_set(client, monkeypatch):
    pool = _pool()[:8]
    monkeypatch.setattr(pb, 'all_problems', lambda: pool)
    rows = [_attempt(p['id'], True, 1) for p in pool]
    s = practice.build(TOPIC, 'practice', 'AMC 10', 4.2, 4.2, planning.difficulty_mix(4.2, 2),
                       engine.history(rows), {}, 'u', TODAY)
    # Nothing else to deal: the recent ones are dealt rather than an empty set.
    assert len(s['problems']) == len(pool)


@pytest.fixture
def today(monkeypatch):
    state = {'day': TODAY}
    monkeypatch.setattr('backend.api.amc._today', lambda: state['day'])
    return state


def test_a_review_solved_this_week_goes_last_in_the_queue(client, today):
    from backend.amc import store
    # The answer below is stamped with the real clock, so the queue's today is the real one too.
    today['day'] = date.today()
    ids = [p['id'] for p in _pool()[:3]]
    for pid in ids:
        store.write(store.review_upsert('tester', {'problem_id': pid, 'stage': 0, 'due': date.today().isoformat(),
                                                   'status': 'active', 'note': '', 'misses': 3}))
    # The first one put right in practice just now.
    store.write([store.attempt_rows('tester', ids[0], 'X', True, 60, 'practice', '')])
    due = client.get('/api/amc/review').json()['due']
    assert [v['id'] for v in due][-1] == ids[0] and due[-1]['solved_recently']
    assert not any(v['solved_recently'] for v in due[:-1])
