"""The Review page's weak-topics bank (backend/amc/weak.py): which topics count
as weak, how the twelve slots are shared out, which problems fill them, and
that the set holds still for a day and changes on "New set"."""
from datetime import date

import pytest

from backend.amc import catalog, engine, weak
from backend.amc import problems as pb

TODAY = date(2026, 11, 12)


def _hist(rows):
    return engine.history([{'problem_id': pid, 'correct': int(ok), 'at': '2026-11-10T10:00:00', 'seconds': 60}
                           for pid, ok in rows])


def _mock_problems(level, topic=None):
    return [p for p in pb.all_problems()
            if p['level'] == level and not p.get('official') and not p.get('ai')
            and (topic is None or p['topic'] == topic)]


def _single_topic(level):
    """Mock problems that count toward one topic only (no `also`)."""
    return [p for p in _mock_problems(level) if not p.get('also')]


# -- quotas -------------------------------------------------------------------
@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_quotas_fill_the_set_and_give_each_topic_its_minimum(n):
    topics = [{'missed': i + 1, 'attempted': i + 3, 'weakness': 0.5 + i / 10} for i in range(n)]
    out = weak.quotas(topics)
    assert sum(out) == weak.SIZE
    assert all(q >= weak.MIN_EACH for q in out)


def test_quotas_give_more_to_the_topic_missed_most():
    heavy = {'missed': 4, 'attempted': 4, 'weakness': 5 / 6}
    light = {'missed': 1, 'attempted': 4, 'weakness': 2 / 6}
    big, small = weak.quotas([heavy, light])
    assert big > small


def test_quotas_split_evenly_when_minimums_use_the_whole_set():
    topics = [{'missed': 0, 'attempted': 0}] * 5
    out = weak.quotas(topics, size=8, least=2)
    assert sum(out) == 8 and max(out) - min(out) <= 1


def test_quotas_of_nothing_is_nothing():
    assert weak.quotas([]) == []


# -- weak_topics ----------------------------------------------------------------
def test_a_missed_topic_ranks_above_untried_and_untried_above_perfect():
    missed = _single_topic('AMC 10')[0]
    solved = next(p for p in _single_topic('AMC 10') if p['topic'] != missed['topic'])
    rows = weak.weak_topics(_hist([(missed['id'], False), (solved['id'], True)]), {}, 'AMC 10')
    ids = [r['id'] for r in rows]
    assert ids[0] == missed['topic']
    assert ids.index(solved['topic']) == len(ids) - 1 or rows[ids.index(solved['topic'])]['missed'] == 0
    perfect = rows[ids.index(solved['topic'])]
    assert perfect['missed'] == 0 and perfect['attempted'] >= 1
    # Every untried topic sits between the missed one and the perfect one.
    assert all(r['attempted'] == 0 for r in rows[1:ids.index(solved['topic'])])


def test_weak_topics_only_cover_the_target_contest():
    for target in ('AMC 10', 'AMC 12', 'AIME'):
        rows = weak.weak_topics({}, {}, target)
        assert rows and all(target in catalog.TOPIC_BY_ID[r['id']]['levels'] for r in rows)


def test_weakness_is_shrunk_toward_the_middle():
    p = _single_topic('AMC 10')[0]
    row = next(r for r in weak.weak_topics(_hist([(p['id'], False)]), {}, 'AMC 10') if r['id'] == p['topic'])
    # One miss out of one is (1 + 1) / (1 + 2), not 100%.
    assert row['weakness'] == pytest.approx(2 / 3, abs=0.001)


# -- bank -----------------------------------------------------------------------
def test_a_new_account_gets_a_full_set_from_the_mocks():
    out = weak.bank({}, {}, 'AMC 10', True, 'tester', today=TODAY)
    assert len(out['problems']) == weak.SIZE
    ids = [p['id'] for p, _, _ in out['problems']]
    assert len(set(ids)) == len(ids)
    assert out['pool']['mock'] > 0
    assert all(p['level'] == 'AMC 10' for p, _, _ in out['problems'])
    # Easiest first.
    ratings = [p['rating'] for p, _, _ in out['problems']]
    assert ratings == sorted(ratings)


def test_without_mocks_and_no_imported_papers_the_bank_is_empty():
    out = weak.bank({}, {}, 'AMC 10', False, 'tester', today=TODAY)
    if out['pool']['official'] == 0:
        assert out['problems'] == []


def test_an_amc_12_student_also_draws_amc_10_problems():
    out = weak.bank({}, {}, 'AMC 12', True, 'tester', today=TODAY)
    assert {p['level'] for p, _, _ in out['problems']} <= {'AMC 10', 'AMC 12'}
    assert all(p['level'] != 'AIME' for p, _, _ in out['problems'])


def test_solved_and_logged_problems_are_left_out():
    topic = weak.weak_topics({}, {}, 'AMC 10')[0]['id']
    pool = _mock_problems('AMC 10', topic)
    solved, logged = pool[0], pool[1]
    hist = _hist([(solved['id'], True)])
    review = {logged['id']: {'problem_id': logged['id'], 'status': 'active'}}
    out = weak.bank(hist, review, 'AMC 10', True, 'tester', today=TODAY)
    ids = {p['id'] for p, _, _ in out['problems']}
    assert solved['id'] not in ids and logged['id'] not in ids


def test_the_missed_topic_leads_the_set():
    missed = _single_topic('AMC 10')[0]
    hist = _hist([(missed['id'], False)])
    out = weak.bank(hist, {}, 'AMC 10', True, 'tester', today=TODAY)
    assert out['topics'][0]['id'] == missed['topic']
    assert out['topics'][0]['picked'] >= weak.MIN_EACH


def test_the_set_holds_for_a_day_and_changes_on_a_new_draw():
    first = weak.bank({}, {}, 'AMC 10', True, 'tester', today=TODAY)
    again = weak.bank({}, {}, 'AMC 10', True, 'tester', today=TODAY)
    other = weak.bank({}, {}, 'AMC 10', True, 'tester', today=TODAY, draw=1)
    ids = lambda out: [p['id'] for p, _, _ in out['problems']]  # noqa: E731
    assert ids(first) == ids(again)
    assert ids(first) != ids(other)


def test_chances_are_probabilities():
    out = weak.bank({}, {}, 'AMC 10', True, 'tester', today=TODAY)
    assert all(0 <= c <= 1 for _, _, c in out['problems'])


# -- through the API ------------------------------------------------------------
def test_the_review_page_serves_the_weak_bank(client):
    body = client.get('/api/amc/review/weak', params={'mocks': 1}).json()
    assert body['success']
    assert len(body['problems']) == weak.SIZE
    assert body['topics']


def test_the_weak_bank_needs_a_session(anon):
    assert anon.get('/api/amc/review/weak').status_code == 401
