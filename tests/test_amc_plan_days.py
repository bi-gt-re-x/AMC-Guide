"""Marking a study day complete, unticking, and sizing the plan to how often it is kept.

Today's checklist ticks and unticks by hand, even an item whose progress is
already met; once every item is ticked the day can be marked complete
(confirmed on the page), which is stored in amc_plan_days and undone by
unticking anything. backend/amc/consistency.py reads those days to size the
days ahead.
"""
from datetime import date, timedelta

import pytest

from backend.amc import consistency, engine

# A Thursday: a study day on a five-hour plan (Mon, Tue, Thu, Sat, Sun).
DAY = date(2026, 11, 12)


@pytest.fixture
def today(monkeypatch):
    state = {'day': DAY}
    monkeypatch.setattr('backend.api.amc._today', lambda: state['day'])
    return state


@pytest.fixture
def planned(client, today):
    reply = client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': (DAY + timedelta(days=60)).isoformat(),
                                              'goal_score': 100, 'hours': 5}).json()
    assert reply['success'] and reply['today'], reply
    return client


def _plan(client):
    return client.get('/api/amc/plan').json()


def test_an_item_ticks_and_unticks_by_hand():
    items = [{'key': 'practice', 'progress': 8, 'goal': 8}, {'key': 'read'}]
    engine._mark_done(items, set())
    assert [i['done'] for i in items] == [True, False]   # progress met, not ticked
    keys = engine.tick([], 'practice', False)
    engine._mark_done(items, set(keys))
    assert items[0]['done'] is False                     # unticked by hand holds
    keys = engine.tick(keys, 'practice', True)
    keys = engine.tick(keys, 'read', True)
    engine._mark_done(items, set(keys))
    assert [i['done'] for i in items] == [True, True]
    assert keys == ['practice', 'read']


def test_the_day_is_marked_complete_only_once_everything_is_ticked(planned):
    body = _plan(planned)
    assert body['day'] == {'date': DAY.isoformat(), 'complete': False, 'completed_at': None, 'ready': False}
    refused = planned.post('/api/amc/plan/day', json={'done': True}).json()
    assert not refused['success'] and 'first' in refused['message']
    for item in body['today']:
        body = planned.post('/api/amc/plan/check', json={'key': item['key'], 'done': True}).json()
    assert body['day']['ready'] and not body['day']['complete']
    body = planned.post('/api/amc/plan/day', json={'done': True}).json()
    assert body['success'] and body['day']['complete'] and body['day']['completed_at']
    # The dashboard says the same.
    assert planned.get('/api/amc/dashboard').json()['plan']['day']['complete']


def test_unticking_reopens_a_completed_day(planned):
    body = _plan(planned)
    for item in body['today']:
        planned.post('/api/amc/plan/check', json={'key': item['key'], 'done': True})
    planned.post('/api/amc/plan/day', json={'done': True})
    first = body['today'][0]['key']
    body = planned.post('/api/amc/plan/check', json={'key': first, 'done': False}).json()
    assert not body['day']['complete'] and not body['day']['ready']
    assert not next(i for i in body['today'] if i['key'] == first)['done']
    # Ticked again, it can be completed again; and reopened by hand.
    planned.post('/api/amc/plan/check', json={'key': first, 'done': True})
    assert planned.post('/api/amc/plan/day', json={'done': True}).json()['day']['complete']
    assert not planned.post('/api/amc/plan/day', json={'done': False}).json()['day']['complete']


def test_a_completed_day_counts_toward_consistency(planned, today):
    body = _plan(planned)
    for item in body['today']:
        planned.post('/api/amc/plan/check', json={'key': item['key'], 'done': True})
    planned.post('/api/amc/plan/day', json={'done': True})
    today['day'] = DAY + timedelta(days=1)
    c = _plan(planned)['consistency']
    assert c['complete'] == 1 and c['study_days'] == 1 and c['status'] == 'new'
    assert c['days'][-1] == {'date': DAY.isoformat(), 'study': True, 'status': 'complete', 'minutes': 0}


# -- consistency.read ---------------------------------------------------------
TODAY = date(2026, 11, 26)          # a Thursday


def _settings(done=(), created=TODAY - timedelta(days=30)):
    return {'target': 'AMC 10', 'hours': 5, 'details': {}, 'created_at': created.isoformat() + 'T09:00:00',
            'days_done': {d.isoformat(): {'items': 3, 'minutes': 60, 'completed_at': d.isoformat()} for d in done}}


def _study_days(back=14):
    weekdays, _ = engine.study_schedule({'hours': 5, 'details': {}})
    return [TODAY - timedelta(days=k) for k in range(back, 0, -1)
            if (TODAY - timedelta(days=k)).weekday() in weekdays]


def _answer(day, seconds=600):
    return {'problem_id': 'step-10-01', 'correct': 1, 'seconds': seconds, 'source': 'practice',
            'at': day.isoformat() + 'T18:00:00'}


def test_a_plan_kept_stays_full():
    days = _study_days()
    c = consistency.read(_settings(days), [], TODAY)
    assert c['rate'] == 1.0 and c['load'] == 1.0 and c['status'] == 'on-track'
    assert c['complete'] == len(days) == c['study_days']
    assert 'full' in c['text']


def test_days_before_the_first_one_marked_are_not_held_against_the_plan():
    # Weeks of activity, no day ever marked complete: nothing is trimmed.
    days = _study_days()
    c = consistency.read(_settings(), [_answer(d) for d in days], TODAY)
    assert c['status'] == 'new' and c['load'] == 1.0 and c['study_days'] == 0
    assert len(c['days']) == 14 and {d['status'] for d in c['days'] if d['study']} == {'partial'}
    assert c['text'].startswith('Mark each study day complete')
    # Counting starts at the first day marked.
    c = consistency.read(_settings(days[-2:]), [], TODAY)
    assert c['study_days'] == 2 and c['complete'] == 2 and c['status'] == 'new'
    assert c['text'].startswith('2 of 2 study days marked complete so far')


def test_a_plan_left_untouched_is_trimmed_and_says_how_to_get_back():
    days = _study_days()
    c = consistency.read(_settings(days[:2]), [], TODAY)
    assert c['rate'] < 0.25 and c['load'] == 0.6 and c['status'] == 'lighter'
    assert c['adjusted'] < c['minutes']
    assert 'trimmed to about {} minutes (from {})'.format(c['adjusted'], c['minutes']) in c['text']
    assert 'Complete 3 study days in a row' in c['text']


def test_partial_days_count_half():
    days = _study_days()
    c = consistency.read(_settings(days[::2]), [_answer(d) for d in days[1::2]], TODAY)
    assert c['partial'] == len(days[1::2]) and 0.5 < c['rate'] < 1
    assert c['load'] in (0.85, 1.0)


def test_three_in_a_row_puts_the_full_plan_back():
    days = _study_days()
    # Marked from the start of the fortnight, mostly missed, then three in a row.
    c = consistency.read(_settings([days[0]] + days[-3:]), [], TODAY)
    assert c['rate'] < 0.5 and c['run'] == 3 and c['load'] == 1.0


def test_more_time_than_planned_moves_the_days_up():
    days = _study_days()
    c = consistency.read(_settings(days), [_answer(d, seconds=90 * 60) for d in days], TODAY)
    assert c['status'] == 'ahead' and c['load'] == consistency.UP[2] and c['adjusted'] > c['minutes']


def test_too_little_to_go_on_changes_nothing():
    c = consistency.read(_settings(created=TODAY - timedelta(days=3)), [], TODAY)
    assert c['status'] == 'new' and c['load'] == 1.0


def test_a_lighter_load_makes_the_days_smaller():
    plan = {'target': 'AMC 10', 'exam_date': (TODAY + timedelta(days=70)).isoformat(), 'goal_score': 100,
            'hours': 5, 'details': {}, 'created_at': (TODAY - timedelta(days=30)).isoformat()}
    tstats = engine.topic_stats({}, {})
    full = engine.plan_weeks(plan, tstats, [], TODAY)
    light = engine.plan_weeks({**plan, 'load': 0.6}, tstats, [], TODAY)
    now = lambda weeks: next(w for w in weeks if w['current'])
    minutes = lambda w: [d['minutes'] for d in w['days'] if not d['rest'] and not d['past']]
    assert sum(minutes(now(light))) < sum(minutes(now(full)))
    # Weeks already gone keep the days they had.
    past = lambda weeks: [d['minutes'] for w in weeks if w['past'] for d in w['days']]
    assert past(light) == past(full)
