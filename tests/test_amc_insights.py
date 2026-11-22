"""Recent performance on the dashboard and the analytics page: the numbers
are computed from answers, the contest guide is complete, and the plan of
attack follows from the goal."""
from datetime import date, timedelta

from backend.amc import catalog, insights

TODAY = date(2026, 11, 13)


def _row(pid, correct, days_ago, seconds=60, source='practice'):
    day = TODAY - timedelta(days=days_ago)
    return {'problem_id': pid, 'answer': '', 'correct': 1 if correct else 0, 'seconds': seconds,
            'source': source, 'at': day.isoformat() + 'T17:00:00'}


def test_goal_breaks_into_right_answers():
    # 14 right and 11 blank is 100.5; 13 right is only 96.
    assert insights.needed_right('AMC 10', 100) == 14
    assert insights.needed_right('AMC 12', 85) == 11
    assert insights.needed_right('AMC 10', 30) == 0
    assert insights.needed_right('AMC 10', 150) == 25
    assert insights.needed_right('AIME', 7) == 7


def test_this_week_against_last_week():
    attempts = [
        _row('step-10-01', True, 10), _row('step-10-03', False, 9), _row('step-10-04', False, 8),
        _row('step-10-05', True, 3), _row('step-10-06', True, 2), _row('step-10-08', True, 1),
        _row('step-10-09', False, 0, source='reveal'),
    ]
    perf = insights.recent_performance(attempts, [], TODAY)
    assert perf['this_week']['answered'] == 3 and perf['this_week']['accuracy'] == 1.0
    assert perf['this_week']['revealed'] == 1
    assert perf['last_week']['answered'] == 3 and perf['last_week']['accuracy'] == 0.333
    assert len(perf['days']) == 14 and perf['days'][-1]['date'] == TODAY.isoformat()
    assert perf['notes'][0]['tone'] == 'up'
    assert perf['this_week']['hardest']['id'] in {'step-10-05', 'step-10-06', 'step-10-08'}


def test_every_contest_guide_is_complete():
    for level in ('AMC 10', 'AMC 12', 'AIME'):
        g = insights.contest_guide(level)
        assert sum(s['share'] for s in g['shares']) == 100
        assert g['sections'] and g['qualify'] and g['key_topics']
        assert g['bands'][-1]['last'] == catalog.FORMATS[level]['count']


def test_dashboard_reports_recent_performance(client):
    client.post('/api/amc/problems/step-10-01/attempt', json={'answer': 'D', 'seconds': 40})
    client.post('/api/amc/problems/step-10-03/attempt', json={'answer': 'A', 'seconds': 50})
    body = client.get('/api/amc/dashboard').json()
    assert 'recent' not in body
    week = body['performance']['this_week']
    assert week['answered'] == 2 and week['days'] == 1


def test_analytics_page(client):
    empty = client.get('/api/amc/analytics').json()
    assert empty['success'] and empty['performance']['attempted'] == 0
    assert empty['has_plan'] is False and empty['prepare']['goal'] == 100
    for pid in ('step-10-01', 'step-10-03', 'step-10-04', 'step-10-05', 'step-10-06'):
        client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': 'A', 'seconds': 90})
    client.put('/api/amc/plan', json={'target': 'AMC 12', 'exam_date': (date.today() + timedelta(days=60)).isoformat(),
                                      'goal_score': 85, 'hours': 5})
    body = client.get('/api/amc/analytics').json()
    perf = body['performance']
    assert perf['attempted'] == 5 and perf['projected']['AMC 12'] is not None
    assert sum(r['attempted'] for r in perf['ratings']) == 5
    assert set(body['contests']) == {'AMC 10', 'AMC 12', 'AIME'}
    prep = body['prepare']
    assert body['target'] == 'AMC 12' and prep['right_needed'] == 11
    assert prep['focus'] and prep['steps'] and prep['phase']['name'] == 'Build'
    assert round(sum(w['hours'] for w in prep['week'])) == 5


def test_analytics_is_signed_in_only(anon):
    assert anon.get('/api/amc/analytics').status_code == 401


def test_weeks_split_by_category_with_difficulty_and_test_score():
    # Two answers this week in different categories, one reveal (not counted),
    # and a mock scored this week: the chart's week carries all of it.
    a, b = 'step-10-01', 'step-10-04'
    attempts = [_row(a, True, 1), _row(b, False, 2), _row(a, False, 2, source='reveal')]
    contest_id = next(cid for cid, m in catalog.MOCK_BY_ID.items() if m['level'] == 'AMC 10')
    mock = {'id': 'm1', 'contest_id': contest_id, 'kind': 'mock', 'score': 75, 'at': TODAY.isoformat() + 'T10:00:00'}
    weeks = insights.weekly(attempts, TODAY, 12, [mock])
    assert len(weeks) == 12 and weeks[0]['answered'] == 0 and weeks[0]['by_category'] == {}
    now = weeks[-1]
    assert now['answered'] == 2 and now['correct'] == 1
    cats = [catalog.TOPIC_BY_ID[insights.pb.get(p)['topic']]['category'] for p in (a, b)]
    assert sum(now['by_category'].values()) == 2 and set(now['by_category']) == set(cats)
    ratings = [insights.pb.get(p)['rating'] for p in (a, b)]
    assert now['avg_rating'] == round(sum(ratings) / 2, 1)
    assert now['score_share'] == 0.5   # 75 of 150
