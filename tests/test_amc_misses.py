"""Why a miss happened (backend/amc/misses.py).

After a wrong answer, or a wrong answer or blank on a mock report, the student
says why: a careless slip, a method they didn't know, a misreading, running
out of time, or a guess. These pin that the reason is kept on the answer it
explains, that each reason leads to its own next step, that the reasons add
up to a profile, and that the study plan's weakness kinds read them.
"""
from datetime import date

import pytest

from backend.amc import catalog, engine, misses, planning, store
from backend.amc.bank import BY_ID, PROBLEMS


@pytest.fixture
def today(monkeypatch):
    state = {'day': date(2026, 11, 12)}
    monkeypatch.setattr('backend.api.amc._today', lambda: state['day'])
    return state


def _wrong(pid):
    right = str(BY_ID[pid]['answer'])
    return 'A' if right != 'A' else 'B'


def _miss(client, pid):
    reply = client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': _wrong(pid), 'seconds': 90}).json()
    assert reply['success'] and not reply['correct'], reply
    return reply


def _tag(client, attempt_id, reason):
    return client.post('/api/amc/attempts/{}/reason'.format(attempt_id), json={'reason': reason}).json()


PID = 'mock10-6-16'          # right triangles, angle bisector theorem, AMC 10 #16


def test_a_miss_is_asked_why_and_a_right_answer_is_not(client, today):
    reply = _miss(client, PID)
    assert reply['attempt_id'] and [c['id'] for c in reply['reasons']] == misses.IDS
    right = client.post('/api/amc/problems/mock10-6-01/attempt', json={'answer': BY_ID['mock10-6-01']['answer']}).json()
    assert right['correct'] and right['attempt_id'] and right['reasons'] is None
    refused = _tag(client, right['attempt_id'], 'careless')
    assert not refused['success']


@pytest.mark.parametrize('reason, mode', [('careless', 'accuracy'), ('time', 'timed'), ('guess', 'learn')])
def test_a_reason_leads_to_its_own_practice_set(client, today, reason, mode):
    reply = _tag(client, _miss(client, PID)['attempt_id'], reason)
    assert reply['success'] and reply['reason'] == reason
    step = reply['step']
    assert step['action']['to'] == '/practice/{}?mode={}'.format(BY_ID[PID]['topic'], mode)
    assert step['title'] and step['body']


def test_not_knowing_the_method_gives_the_idea_and_two_problems_using_it(client, today):
    pid = 'mock10-6-15'                                   # factoring trick: several others use it
    step = _tag(client, _miss(client, pid)['attempt_id'], 'method')['step']
    tech = BY_ID[pid]['technique']
    assert step['idea']['text'] == catalog.TECHNIQUE_IDEA[tech]
    assert len(step['problems']) == 2
    assert all(BY_ID[q['id']]['technique'] == tech and q['id'] != pid for q in step['problems'])
    assert all(q['why'] == "Uses Simon's factoring trick" for q in step['problems'])
    assert step['more']['to'].startswith('/problems?technique={}'.format(tech))


def test_a_rare_technique_is_filled_up_from_related_ideas_in_the_topic(client, today):
    # The angle bisector theorem is on two problems in the bank, and the other is out of reach.
    step = _tag(client, _miss(client, PID)['attempt_id'], 'method')['step']
    topic = BY_ID[PID]['topic']
    assert len(step['problems']) == 2 and 'rare' in step['body']
    assert all(topic in [BY_ID[q['id']]['topic']] + BY_ID[q['id']]['also'] and q['id'] != PID for q in step['problems'])
    assert all(q['why'] for q in step['problems'])


def test_suggestions_skip_problems_already_solved(client, today):
    pid = 'mock10-6-15'
    first = _tag(client, _miss(client, pid)['attempt_id'], 'method')['step']['problems'][0]['id']
    client.post('/api/amc/problems/{}/attempt'.format(first), json={'answer': str(BY_ID[first]['answer'])})
    again = client.get('/api/amc/problems/' + pid).json()['miss']['step']['problems']
    assert first not in [q['id'] for q in again]


def test_a_misreading_gets_wordier_problems_from_the_topic():
    # A student with no history, so every problem at the level is within reach.
    step = misses.next_step('misread', BY_ID[PID], {}, {}, date(2026, 11, 12))
    topic = BY_ID[PID]['topic']
    assert step['problems'] and all(topic in [BY_ID[q['id']]['topic']] + BY_ID[q['id']]['also'] for q in step['problems'])
    pool = [q for q in PROBLEMS if q['id'] != PID and q['level'] == BY_ID[PID]['level']
            and (q['topic'] == topic or topic in q['also'])]
    median = sorted(len(engine.plain(q['statement'])) for q in pool)[len(pool) // 2]
    assert all(len(engine.plain(BY_ID[q['id']]['statement'])) >= median for q in step['problems'])


def test_the_reason_stays_with_the_answer_and_can_be_changed_or_taken_back(client, today):
    attempt_id = _miss(client, PID)['attempt_id']
    _tag(client, attempt_id, 'careless')
    page = client.get('/api/amc/problems/' + PID).json()
    assert page['miss']['attempt_id'] == attempt_id and page['miss']['reason'] == 'careless'
    assert page['miss']['step']['action']['to'].endswith('mode=accuracy')
    assert page['attempts'][-1]['miss_reason'] == 'careless'
    _tag(client, attempt_id, 'time')
    assert client.get('/api/amc/problems/' + PID).json()['miss']['reason'] == 'time'
    assert len(store.miss_reasons('tester')) == 1
    gone = _tag(client, attempt_id, '')
    assert gone['success'] and gone['reason'] is None
    page = client.get('/api/amc/problems/' + PID).json()
    assert page['miss']['reason'] is None and page['miss']['step'] is None
    assert not store.miss_reasons('tester')


def test_a_reason_must_be_one_of_the_five_and_the_answer_ones_own(client, stranger, today):
    attempt_id = _miss(client, PID)['attempt_id']
    assert not _tag(client, attempt_id, 'bad luck')['success']
    assert not _tag(stranger, attempt_id, 'careless')['success']
    assert not store.miss_reasons('stranger') and not store.miss_reasons('tester')


def _sit(client, contest_id, answers):
    reply = client.post('/api/amc/contests/{}/submit'.format(contest_id), json={'answers': answers, 'seconds': 600}).json()
    assert reply['success'], reply
    return reply['id']


def test_a_mock_report_asks_why_for_each_wrong_answer_and_blank(client, today):
    paper = catalog.MOCK_BY_ID['mock-10-6']['problems']
    answers = {'1': str(BY_ID[paper[0]]['answer']), '2': _wrong(paper[1])}           # right, wrong, rest blank
    mock_id = _sit(client, 'mock-10-6', answers)
    rows = {r['number']: r for r in client.get('/api/amc/mocks/' + mock_id).json()['rows']}
    assert rows[1]['reasons'] is None
    assert [c['id'] for c in rows[2]['reasons']] == misses.IDS
    assert [c['id'] for c in rows[3]['reasons']] == list(misses.BLANK_REASONS)

    tagged = client.post('/api/amc/mocks/{}/reason'.format(mock_id), json={'number': 2, 'reason': 'misread'}).json()
    assert tagged['success'] and tagged['step']['title']
    # A wrong answer's reason lands on its attempt, where the study plan reads it.
    mock_attempt = [a for a in store.attempts('tester') if a['problem_id'] == paper[1]][-1]
    assert mock_attempt['miss_reason'] == 'misread'
    assert not client.post('/api/amc/mocks/{}/reason'.format(mock_id), json={'number': 3, 'reason': 'careless'}).json()['success']
    assert not client.post('/api/amc/mocks/{}/reason'.format(mock_id), json={'number': 1, 'reason': 'time'}).json()['success']
    assert client.post('/api/amc/mocks/{}/reason'.format(mock_id), json={'number': 3, 'reason': 'time'}).json()['success']
    rows = {r['number']: r for r in client.get('/api/amc/mocks/' + mock_id).json()['rows']}
    assert rows[2]['miss_reason'] == 'misread' and rows[3]['miss_reason'] == 'time'
    # A blank's reason belongs to the sitting and goes with it.
    client.delete('/api/amc/mocks/' + mock_id)
    assert [r['reason'] for r in store.miss_reasons('tester')] == ['misread']


def test_the_profile_names_the_most_common_reason_and_where_on_the_paper(client, today):
    # Three careless slips on #1-10 of AMC 10 papers, one ran-out-of-time at #24.
    for pid in ('mock10-6-03', 'mock10-6-07', 'mock10-7-05'):
        _tag(client, _miss(client, pid)['attempt_id'], 'careless')
    _tag(client, _miss(client, 'mock10-7-24')['attempt_id'], 'time')
    _miss(client, 'mock10-7-09')                                     # not tagged
    body = client.get('/api/amc/analytics').json()['misses']
    assert body['total'] == 4 and body['untagged'] == 1 and body['top'] == 'careless'
    careless = body['reasons'][0]
    assert careless['count'] == 3 and careless['band'] == '#1–10' and careless['action']['to'].endswith('mode=accuracy')
    assert body['headline'] == 'Your most common reason is careless slips: 3 of your last 4 tagged misses, mostly on #1–10.'
    assert [r['id'] for r in body['reasons']] == ['careless', 'time']


def test_a_tie_names_no_leader(client, today):
    for pid, reason in (('mock10-6-03', 'careless'), ('mock10-6-07', 'method'), ('mock10-7-05', 'time')):
        _tag(client, _miss(client, pid)['attempt_id'], reason)
    body = client.get('/api/amc/analytics').json()['misses']
    assert body['top'] is None
    assert body['headline'] == ('No one reason leads yet: careless slips, not knowing the method and running out '
                                'of time are level at 1 each.')


def test_with_too_few_reasons_there_is_no_pattern_yet(client, today):
    _tag(client, _miss(client, PID)['attempt_id'], 'guess')
    body = client.get('/api/amc/analytics').json()['misses']
    assert body['total'] == 1 and body['headline'] is None


def test_paper_bands():
    assert misses.band('AMC 10', 3) == '#1–10' and misses.band('AMC 12', 17) == '#11–20'
    assert misses.band('AMC 10', 25) == '#21–25' and misses.band('AIME', 7) == '#6–10'
    assert misses.band('AIME', 15) == '#11–15' and misses.band('AMC 10', 0) is None


def _row(pid, correct, reason='', at='2026-11-01T10:00:00'):
    return {'id': pid + at, 'problem_id': pid, 'answer': 'A', 'correct': 1 if correct else 0, 'seconds': 60,
            'source': 'practice', 'at': at, 'set_id': '', 'set_kind': '', 'set_mode': '', 'miss_reason': reason}


def test_the_study_plan_reads_what_the_student_said():
    pool = [p for p in PROBLEMS if p['topic'] == 'probability' and p['level'] == 'AMC 10'][:5]
    problems = [(p, [_row(p['id'], i >= 3, 'careless' if i < 2 else '')], None) for i, p in enumerate(pool)]
    said = planning.classify('AMC 10', 9.0, problems)
    assert 'execution' in said and 'you put 2 misses down to a slip or misreading' in said['execution']['evidence']
    untold = planning.classify('AMC 10', 9.0, [(p, [dict(t[0], miss_reason='')], h) for p, t, h in problems])
    # Without the reasons, the same answers are read only from what they show.
    assert 'you put' not in (untold.get('execution') or {}).get('evidence', '')
    timed = [(p, [_row(p['id'], i >= 3, 'time' if i < 3 else '')], None) for i, p in enumerate(pool)]
    assert 'you ran out of time on 3 misses' in planning.classify('AMC 10', 9.0, timed)['speed']['evidence']
