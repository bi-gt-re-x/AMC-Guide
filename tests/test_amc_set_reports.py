"""A set's report: what was right, what was missed, read from the set itself.

The report used to be worked out on the practice set's page from each
problem's lifetime status, over a set the picker dealt again after the
answers were in, so it could count problems that were never in the set and
call a problem solved last month "solved" when it was missed today. These pin
that a set is stored as dealt (`amc_set_runs`), its answers carry its id, and
its report reads only those.
"""
from datetime import date, timedelta

import pytest

from backend.amc import engine, planning, practice, setreport, smart, store
from backend.amc.bank import BY_ID


@pytest.fixture
def today(monkeypatch):
    state = {'day': date(2026, 11, 12)}
    monkeypatch.setattr('backend.api.amc._today', lambda: state['day'])
    return state


def _wrong(pid):
    right = str(BY_ID[pid]['answer'])
    return 'A' if right != 'A' else 'B'


def _deal(client, ids, mode='practice', topic=None, kind='practice', seconds=None):
    reply = client.post('/api/amc/sets', json={'kind': kind, 'topic': topic or BY_ID[ids[0]]['topic'],
                                               'mode': mode, 'problems': ids, 'seconds': seconds}).json()
    assert reply['success'], reply
    return reply['id']


def _answer(client, pid, answer, set_id, seconds=60):
    return client.post('/api/amc/problems/{}/attempt'.format(pid),
                       json={'answer': answer, 'seconds': seconds, 'set_id': set_id}).json()


def _topic_ids(n=4):
    topic = BY_ID['step-10-01']['topic']
    ids = [pid for pid, p in BY_ID.items() if p['topic'] == topic and p['choices']][:n]
    assert len(ids) == n
    return topic, ids


def test_the_report_is_about_the_problems_dealt_and_this_sets_answers(client, today):
    topic, ids = _topic_ids(4)
    # Solved before the set: still a miss when it is missed in the set.
    client.post('/api/amc/problems/{}/attempt'.format(ids[0]), json={'answer': BY_ID[ids[0]]['answer']})
    set_id = _deal(client, ids, topic=topic)
    assert _answer(client, ids[0], _wrong(ids[0]), set_id)['set_id'] == set_id
    _answer(client, ids[1], BY_ID[ids[1]]['answer'], set_id)
    client.post('/api/amc/problems/{}/reveal'.format(ids[2]), json={'set_id': set_id})
    # ids[3] is left: skipped.
    report = client.post('/api/amc/sets/{}/finish'.format(set_id), json={}).json()['report']
    assert [r['id'] for r in report['problems']] == ids
    assert [r['result'] for r in report['problems']] == ['wrong', 'right', 'revealed', 'skipped']
    assert (report['right'], report['wrong'], report['revealed'], report['skipped']) == (1, 1, 1, 1)
    # Expected over the three answered, not the skipped one.
    answered_chance = sum(r['chance'] for r in report['problems'] if r['result'] != 'skipped')
    assert abs(report['expected'] - answered_chance) < 0.1 and '1 right of 3 answered' in report['verdict']
    assert report['total'] == 4 and report['answered'] == 3
    assert report['right_ids'] == [ids[1]] and report['missed_ids'] == [ids[0], ids[2]]
    assert report['skipped_ids'] == [ids[3]]
    first = report['problems'][0]
    assert first['given'] == '({})'.format(_wrong(ids[0])) and first['answer'] == '({})'.format(BY_ID[ids[0]]['answer'])
    assert first['seen_before'] and first['before'] == 'right'
    assert first['review'] is not None          # the miss is back in the review log
    # A skipped problem is still open: its answer is not given away.
    assert report['problems'][3]['answer'] == '' and report['problems'][3]['given'] == ''
    assert report['finished'] and report['next'] and report['next'][0]['topic'] == topic
    assert report['next'][0]['href'].startswith('/practice/{}?mode='.format(topic))


def test_only_the_first_answer_in_a_set_counts(client, today):
    topic, ids = _topic_ids(2)
    set_id = _deal(client, ids, topic=topic)
    _answer(client, ids[0], _wrong(ids[0]), set_id)
    _answer(client, ids[0], BY_ID[ids[0]]['answer'], set_id)
    report = client.get('/api/amc/sets/' + set_id).json()['report']
    assert report['problems'][0]['result'] == 'wrong'


def test_answers_outside_the_set_are_kept_out_of_it(client, stranger, today):
    topic, ids = _topic_ids(3)
    set_id = _deal(client, ids[:2], topic=topic)
    # A problem the set did not deal, and a set that is not this account's.
    assert _answer(client, ids[2], BY_ID[ids[2]]['answer'], set_id)['set_id'] == ''
    assert stranger.post('/api/amc/problems/{}/attempt'.format(ids[0]),
                         json={'answer': BY_ID[ids[0]]['answer'], 'set_id': set_id}).json()['set_id'] == ''
    assert not stranger.get('/api/amc/sets/' + set_id).json()['success']
    client.post('/api/amc/sets/{}/finish'.format(set_id), json={'time_up': True})
    # Finished: a late answer is not the set's.
    assert _answer(client, ids[0], BY_ID[ids[0]]['answer'], set_id)['set_id'] == ''
    report = client.get('/api/amc/sets/' + set_id).json()['report']
    assert report['time_up'] and report['skipped'] == 2 and report['right'] == 0
    assert any(n['kind'] == 'skipped' and 'clock ran out' in n['text'] for n in report['notes'])


def test_finishing_twice_keeps_the_first(client, today):
    topic, ids = _topic_ids(1)
    set_id = _deal(client, ids, topic=topic)
    client.post('/api/amc/sets/{}/finish'.format(set_id), json={'time_up': True})
    client.post('/api/amc/sets/{}/finish'.format(set_id), json={'time_up': False})
    assert client.get('/api/amc/sets/' + set_id).json()['report']['time_up']


def test_a_set_is_validated(client, today):
    assert not client.post('/api/amc/sets', json={'kind': 'practice', 'topic': 'nope', 'problems': ['step-10-01']}).json()['success']
    assert not client.post('/api/amc/sets', json={'kind': 'nope', 'problems': ['step-10-01']}).json()['success']
    assert not client.post('/api/amc/sets', json={'kind': 'review', 'problems': ['no-such']}).json()['success']
    reply = client.post('/api/amc/sets', json={'kind': 'review', 'problems': ['step-10-01', 'step-10-01', 'x']}).json()
    assert reply['success'] and reply['problems'] == ['step-10-01']


def test_review_answers_carry_the_set_and_the_list_counts_by_kind(client, today):
    client.post('/api/amc/problems/step-10-04/attempt', json={'answer': _wrong('step-10-04')})
    today['day'] += timedelta(days=3)
    set_id = _deal(client, ['step-10-04'], kind='review', topic='')
    reply = client.post('/api/amc/problems/step-10-04/attempt',
                        json={'answer': BY_ID['step-10-04']['answer'], 'source': 'review', 'set_id': set_id}).json()
    assert reply['set_id'] == set_id and reply['moved']
    body = client.get('/api/amc/sets').json()
    assert body['sets'][0]['id'] == set_id and body['sets'][0]['title'] == 'Review set'
    assert body['by_mode'][0]['id'] == 'review' and body['by_mode'][0]['accuracy'] == 1


def test_a_careless_miss_and_a_slow_answer_are_called_out():
    run = {'id': 's1', 'kind': 'practice', 'topic': BY_ID['step-10-01']['topic'], 'mode': 'accuracy',
           'title': '', 'problems': ['step-10-01', 'step-10-03'], 'seconds': None,
           'started_at': '2026-11-12T10:00:00', 'finished_at': '2026-11-12T10:30:00', 'time_up': False}
    # A strong history makes #1 and #2 near-certain for this student.
    history = [{'problem_id': pid, 'answer': str(p['answer']), 'correct': 1, 'seconds': 60, 'source': 'practice',
                'at': '2026-11-0{}T09:00:00'.format(1 + i % 9), 'set_id': ''}
               for i, (pid, p) in enumerate(BY_ID.items()) if p['level'] == 'AMC 10' and p['rating'] <= 6][:30]
    history = [a for a in history if a['problem_id'] not in run['problems']]
    mine = [{'problem_id': 'step-10-01', 'answer': _wrong('step-10-01'), 'correct': 0, 'seconds': 50,
             'source': 'practice', 'at': '2026-11-12T10:05:00', 'set_id': 's1'},
            {'problem_id': 'step-10-03', 'answer': str(BY_ID['step-10-03']['answer']), 'correct': 1,
             'seconds': 3000, 'source': 'practice', 'at': '2026-11-12T10:25:00', 'set_id': 's1'}]
    report = setreport.report(run, history + mine, {}, 'AMC 10', 100, today=date(2026, 11, 12))
    kinds = {n['kind'] for n in report['notes']}
    assert 'careless' in kinds and 'slow' in kinds
    assert report['problems'][0]['careless'] and report['problems'][1]['slow']
    assert report['expected'] > 1.5 and '1 right of 2 answered' in report['verdict']


def test_a_spaced_retest_moves_the_topic_level():
    # Missed first, right again a fortnight later: the fit rises, the first-try count does not.
    pids = [pid for pid, p in BY_ID.items() if p['level'] == 'AMC 10'][:6]
    first = [{'problem_id': pid, 'answer': '', 'correct': 0, 'seconds': 90, 'source': 'practice',
              'at': '2026-10-01T10:00:00'} for pid in pids]
    soon = [dict(a, correct=1, at='2026-10-03T10:00:00') for a in first]
    later = [dict(a, correct=1, at='2026-10-20T10:00:00') for a in first]
    today = date(2026, 10, 21)
    missed_only = engine.history(first + soon)
    retested = engine.history(first + later)
    assert all(h['retest'] is None for h in missed_only.values())
    assert all(h['retest'] == {'at': '2026-10-20T10:00:00', 'correct': True} for h in retested.values())
    fit = lambda hist: smart.fit([p[:3] for p in smart.ability_points(hist, today)])[0]
    assert fit(retested) > fit(missed_only)
    assert len(smart._first_points(retested, today)) == len(pids)


def test_a_mixed_set_counts_as_unlabelled_for_recognition():
    assert planning.unlabelled({'source': 'practice', 'set_mode': 'mixed'})
    assert planning.unlabelled({'source': 'mock'})
    assert not planning.unlabelled({'source': 'practice', 'set_mode': 'timed'})


def test_attempts_read_back_with_their_set(client, today):
    topic, ids = _topic_ids(1)
    set_id = _deal(client, ids, mode='mixed', topic=topic)
    _answer(client, ids[0], BY_ID[ids[0]]['answer'], set_id)
    rows = [a for a in store.attempts('tester') if a['set_id'] == set_id]
    assert len(rows) == 1 and rows[0]['set_kind'] == 'practice' and rows[0]['set_mode'] == 'mixed'
    assert client.get('/api/amc/sets').json()['sets'][0]['title'] == practice.TITLES['mixed']


def test_the_problem_page_says_which_set_each_answer_was_given_in(client, today):
    """So a set reopened, or a page refreshed, part way shows what was answered
    in that set (pages/amc/Problem.tsx), and a new set starts fresh."""
    _, ids = _topic_ids(2)
    first = _deal(client, ids)
    _answer(client, ids[0], _wrong(ids[0]), first, seconds=95)
    later = _deal(client, ids)
    _answer(client, ids[0], str(BY_ID[ids[0]]['answer']), later)
    client.post('/api/amc/problems/{}/reveal'.format(ids[1]), json={'set_id': later})
    client.post('/api/amc/problems/{}/attempt'.format(ids[1]), json={'answer': 'A'})
    seen = client.get('/api/amc/problems/' + ids[0]).json()['attempts']
    assert [(a['set_id'], a['correct'], a['seconds']) for a in seen] == [(first, False, 95), (later, True, 60)]
    other = client.get('/api/amc/problems/' + ids[1]).json()['attempts']
    assert [(a['set_id'], a['source']) for a in other] == [(later, 'reveal'), ('', 'practice')]
