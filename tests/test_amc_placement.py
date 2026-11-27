"""The placement check at sign-up (backend/amc/placement.py).

Twelve problems, each pitched at the level the answers so far point to, so a
new account starts with a level, a projected score and a study plan of its
own. These pin that a dealt problem gives nothing away, that the check adapts
and turns through the subjects, that its answers are ordinary attempts kept
out of the review log, and that it can be stopped or declined.
"""
from datetime import date

import pytest

from backend.amc import catalog, placement, store
from backend.amc.bank import BY_ID


@pytest.fixture
def today(monkeypatch):
    monkeypatch.setattr('backend.api.amc._today', lambda: date(2026, 11, 12))


def _start(client, level='AMC 10'):
    reply = client.post('/api/amc/placement/start', json={'level': level}).json()
    assert reply['success'], reply
    return reply['placement']


def _answer(client, state, right):
    pid = state['problem']['id']
    key = str(BY_ID[pid]['answer'])
    reply = client.post('/api/amc/placement/answer',
                        json={'problem_id': pid, 'answer': key if right else '', 'seconds': 40}).json()
    assert reply['success'], reply
    return reply['placement']


def _run(client, right, level='AMC 10'):
    state, dealt = _start(client, level), []
    while not state['done']:
        dealt.append(state['problem']['id'])
        state = _answer(client, state, right(len(dealt)))
    return state, dealt


def test_a_dealt_problem_gives_nothing_away(client, today):
    state = _start(client)
    p = state['problem']
    assert state['answered'] == 0 and state['total'] == placement.SIZE == 12 and not state['done']
    for key in ('answer', 'solution', 'sources', 'rating', 'difficulty', 'technique'):
        assert key not in p, key
    assert p['statement'] and p['choices']


def test_twelve_answers_finish_it_with_a_level_and_they_count_as_practice(client, today):
    state, dealt = _run(client, lambda i: i % 2 == 0)
    assert state['done'] and state['problem'] is None and len(dealt) == 12 and len(set(dealt)) == 12
    found = state['result']
    assert found['answered'] == 12 and found['right'] == 6 and found['blank'] == 6
    assert 1 <= found['level'] <= 12 and found['summary'].startswith('You’re at about')
    attempts = store.attempts('tester')
    assert [a['problem_id'] for a in attempts] == dealt and all(a['source'] == 'practice' for a in attempts)
    # A measurement, not mistakes to go back over: nothing in the review log.
    assert not store.reviews('tester')
    dash = client.get('/api/amc/dashboard').json()
    assert dash['stats']['attempted'] == 12 and dash['placement']['offer'] is False
    # A projected score still waits for a timed sitting: practice alone is not a score.
    assert dash['projected']['AMC 10'] is None and 'projected' not in found['summary']


def test_it_adapts_up_for_a_strong_student_and_down_for_a_weak_one(client, stranger, today):
    _, strong = _run(client, lambda i: True)
    _, weak = _run(stranger, lambda i: False)
    rating = lambda ids: sum(BY_ID[i]['rating'] for i in ids) / len(ids)
    assert rating(strong[-4:]) > rating(strong[:2]) and rating(weak[-4:]) < rating(weak[:2])
    s = client.get('/api/amc/placement').json()['placement']['result']
    w = stranger.get('/api/amc/placement').json()['placement']['result']
    assert s['level'] > w['level'] + 2 and s['reach'] > w['reach']


def test_it_turns_through_the_subjects_and_keeps_to_short_problems(client, today):
    _, dealt = _run(client, lambda i: i % 3 != 0)
    subjects = [catalog.TOPIC_BY_ID[BY_ID[i]['topic']]['category'] for i in dealt]
    assert set(subjects[:4]) == set(placement.SUBJECTS)
    assert all(not BY_ID[i].get('diagram') and BY_ID[i]['level'] == 'AMC 10' for i in dealt)


def test_an_aime_check_deals_aime_and_amc_12_problems(client, today):
    _, dealt = _run(client, lambda i: i % 2 == 0, level='AIME')
    assert {BY_ID[i]['level'] for i in dealt} <= {'AIME', 'AMC 12'}


def test_an_answer_to_a_problem_not_dealt_changes_nothing(client, today):
    state = _start(client)
    other = next(p['id'] for p in placement.pool('AMC 10') if p['id'] != state['problem']['id'])
    reply = client.post('/api/amc/placement/answer', json={'problem_id': other, 'answer': 'A'}).json()
    assert reply['stale'] and reply['placement']['problem']['id'] == state['problem']['id']
    assert not store.attempts('tester')
    # Starting again carries on with the same check.
    assert _start(client)['problem']['id'] == state['problem']['id']


def test_stopping_early_keeps_what_was_answered(client, today):
    state = _start(client)
    for _ in range(5):
        state = _answer(client, state, True)
    stopped = client.post('/api/amc/placement/stop').json()['placement']
    assert stopped['done'] and stopped['result']['answered'] == 5 and len(store.attempts('tester')) == 5
    assert client.get('/api/amc/placement').json()['offer'] is False


def test_too_few_answers_say_nothing_about_the_level(client, today):
    state = _answer(client, _start(client), True)
    stopped = client.post('/api/amc/placement/stop').json()['placement']
    assert stopped['done'] and stopped['result'] is None


def test_declining_it_before_starting_means_it_is_not_offered_again(client, today):
    assert client.get('/api/amc/placement').json()['offer'] is True
    assert client.get('/api/amc/dashboard').json()['placement']['offer'] is True
    client.post('/api/amc/placement/stop')
    assert client.get('/api/amc/placement').json()['offer'] is False
    assert not store.attempts('tester')


def test_it_is_not_offered_to_an_account_with_a_history(client, today):
    for p in [q for q in BY_ID.values() if q['level'] == 'AMC 10' and q.get('choices')][:20]:
        client.post('/api/amc/problems/{}/attempt'.format(p['id']), json={'answer': 'A'})
    assert client.get('/api/amc/placement').json()['offer'] is False


def test_problems_answered_before_are_not_dealt(client, today):
    first = placement.next_problem('AMC 10', [], set(), seed='tester')
    client.post('/api/amc/problems/{}/attempt'.format(first), json={'answer': 'A'})
    assert _start(client)['problem']['id'] != first
