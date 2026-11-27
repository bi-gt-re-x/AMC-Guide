""""Too challenging?": a problem out of reach of the account's level goes on
hold in the review log, is never due, and comes back by itself once the level
is near its rating (backend/amc/reach.py)."""
from datetime import date

import pytest

from backend.amc import reach, store
from backend.amc.bank import BY_ID

HARD = 'step-aime-17'      # rated 9: far above a new account's level (4)
EASY = 'step-10-04'        # rated 2: well within it


@pytest.fixture
def today(monkeypatch):
    state = {'day': date(2026, 11, 12)}
    monkeypatch.setattr('backend.api.amc._today', lambda: state['day'])
    return state


@pytest.fixture
def level(monkeypatch):
    """Set the account's level, as if its answers had moved it."""
    real = reach.levels
    state = {'theta': None}

    def fake(hist, today):
        if state['theta'] is None:
            return real(hist, today)
        return state['theta'], {}
    monkeypatch.setattr(reach, 'levels', fake)
    return state


def _miss(client, pid):
    wrong = '0' if str(BY_ID[pid]['answer']) != '0' else '1'
    client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': wrong})


def test_the_problem_page_says_whether_it_is_out_of_reach(client, today):
    hard = client.get('/api/amc/problems/' + HARD).json()['reach']
    assert hard['out_of_reach'] and hard['rating'] == 9.0 and hard['returns_at'] == 8.0
    assert not client.get('/api/amc/problems/' + EASY).json()['reach']['out_of_reach']


def test_too_challenging_puts_it_on_hold_in_the_review_log(client, today):
    _miss(client, HARD)
    assert client.get('/api/amc/review').json()['upcoming'][0]['id'] == HARD
    reply = client.post('/api/amc/review/{}/park'.format(HARD)).json()
    assert reply['success'] and reply['review']['review_status'] == 'parked'
    queue = client.get('/api/amc/review').json()
    # In the log, on hold: not due, not upcoming, not in the forecast.
    assert [v['id'] for v in queue['parked']] == [HARD]
    assert queue['parked'][0]['reach']['returns_at'] == 8.0
    assert queue['due'] == [] and queue['upcoming'] == []
    assert all(f['count'] == 0 for f in queue['forecast'])
    # Even on the day it would have been due.
    today['day'] = date(2026, 11, 20)
    assert client.get('/api/amc/review').json()['due'] == []
    assert client.get('/api/amc/dashboard').json()['stats']['due'] == 0
    # Its note and misses are kept; the page shows it as in the log.
    body = client.get('/api/amc/problems/' + HARD).json()
    assert body['status'] == 'review' and body['review']['misses'] == 1


def test_a_problem_never_missed_can_be_put_on_hold_too(client, today):
    assert client.post('/api/amc/review/{}/park'.format(HARD)).json()['success']
    assert [v['id'] for v in client.get('/api/amc/review').json()['parked']] == [HARD]


def test_a_problem_the_model_calls_within_reach_can_be_held_and_waits_for_growth(client, today, level):
    # Rated 2 against a level of 4: the model says easy, the student says too
    # hard. It is held, and comes back once the level grows by STEP, not on
    # the next page load.
    level['theta'] = 4.0
    _miss(client, EASY)
    reply = client.post('/api/amc/review/{}/park'.format(EASY)).json()
    assert reply['success'] and reply['reach']['returns_at'] == 4.5
    assert store.review('tester', EASY)['parked_level'] == 4.0
    assert [v['id'] for v in client.get('/api/amc/review').json()['parked']] == [EASY]
    level['theta'] = 4.4
    assert [v['id'] for v in client.get('/api/amc/review').json()['parked']] == [EASY]
    level['theta'] = 4.5
    queue = client.get('/api/amc/review').json()
    assert queue['parked'] == [] and [v['id'] for v in queue['due']] == [EASY]


def test_it_comes_back_at_the_later_of_near_the_rating_and_grown(client, today, level):
    # Rated 6.5 against 5.9 (the case that hid the button): near the rating
    # would be 5.5, already passed, so it waits for 5.9 + 0.5.
    p = {'rating': 6.5}
    assert reach.returns_at(p, 5.9) == 6.4
    assert reach.returns_at(p, 4.0) == 5.5
    assert reach.returns_at({'rating': None}, 3.0) == 3.5


def test_it_comes_back_once_the_level_is_near(client, today, level):
    _miss(client, HARD)
    client.post('/api/amc/review/{}/park'.format(HARD))
    level['theta'] = 7.5          # closer, still more than a point short of 9
    assert client.get('/api/amc/review').json()['parked'][0]['id'] == HARD
    level['theta'] = 8.0          # within a point: released, due today
    queue = client.get('/api/amc/review').json()
    assert queue['parked'] == [] and [v['id'] for v in queue['due']] == [HARD]
    assert store.review('tester', HARD)['status'] == 'active'
    assert store.review('tester', HARD)['parked_at'] is None
    # Released for good: the level dipping again does not put it back.
    level['theta'] = 4.0
    assert [v['id'] for v in client.get('/api/amc/review').json()['due']] == [HARD]


def test_answering_it_while_on_hold_keeps_the_hold(client, today):
    _miss(client, HARD)
    client.post('/api/amc/review/{}/park'.format(HARD))
    _miss(client, HARD)
    row = store.review('tester', HARD)
    assert row['status'] == 'parked' and row['misses'] == 2
    reply = client.post('/api/amc/problems/{}/attempt'.format(HARD), json={'answer': str(BY_ID[HARD]['answer'])}).json()
    assert reply['correct'] and store.review('tester', HARD)['status'] == 'parked'


def test_bring_it_back_now_releases_it(client, today):
    client.post('/api/amc/review/{}/park'.format(HARD))
    assert client.post('/api/amc/review/' + HARD).json()['success']
    queue = client.get('/api/amc/review').json()
    assert queue['parked'] == [] and [v['id'] for v in queue['due']] == [HARD]


def test_a_problem_on_hold_is_not_drawn_into_the_weak_topics_set(client, today):
    hard_10 = 'step-10-27'      # an AMC 10 problem rated 7: in the pool, out of reach
    before = client.get('/api/amc/review/weak', params={'mocks': 1}).json()['pool']['mock']
    assert client.post('/api/amc/review/{}/park'.format(hard_10)).json()['success']
    body = client.get('/api/amc/review/weak', params={'mocks': 1}).json()
    assert body['pool']['mock'] == before - 1
    assert hard_10 not in [p['id'] for p in body['problems']]


def test_on_hold_is_per_account(client, stranger, today):
    client.post('/api/amc/review/{}/park'.format(HARD))
    assert stranger.get('/api/amc/review').json()['parked'] == []


def test_signed_out_cannot_put_anything_on_hold(anon):
    assert anon.post('/api/amc/review/{}/park'.format(HARD)).status_code == 401
