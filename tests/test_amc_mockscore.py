"""backend/amc/mockscore.py: the projected score is the sittings' (95%) with
practice a 5% nudge, and the points timed sittings lose, by topic, go into
Analytics' weaknesses and the study plan's priorities."""
from datetime import date

from backend.amc import catalog, mockscore
from backend.amc import problems as pb

TODAY = date(2026, 11, 24)


def _logged(contest, score, at):
    return {'id': contest, 'contest_id': contest, 'kind': 'logged', 'score': score, 'correct': 0, 'blank': 0,
            'at': at + 'T18:00:00', 'answers': {}}


def test_the_projection_is_the_sittings_with_practice_only_a_nudge():
    mocks = [_logged('2025-amc-10b', 99, '2026-11-01')]          # that year's floor: 100 on a typical paper
    recent = mockscore.sittings(mocks, 'AMC 10', TODAY)
    assert [s['score'] for s in recent] == [100]
    assert mockscore.blend(140, recent) == 102.0                  # 0.95 x 100 + 0.05 x 140
    assert mockscore.blend(None, recent) == 100
    assert mockscore.blend(140, []) is None                       # practice alone is not a projection
    # Newer sittings count more.
    two = mockscore.sittings([_logged('2025-amc-10b', 99, '2026-11-01'),
                              _logged('2024-amc-10a', 60, '2026-06-20')], 'AMC 10', TODAY)
    assert two[0]['score'] == 100 and mockscore.blend(None, two) > (two[0]['score'] + two[1]['score']) / 2
    # Another contest's sittings do not count, nor ones long ago.
    assert mockscore.sittings(mocks, 'AMC 12', TODAY) == []
    assert mockscore.sittings([_logged('2025-amc-10b', 99, '2025-01-01')], 'AMC 10', TODAY) == []


def _sit(client, wrong_topic):
    """Sit the AMC 10 Step mock: right on everything but `wrong_topic`, which is answered wrong."""
    mock = catalog.MOCK_BY_ID['step-mock-10']
    answers = {}
    for n, pid in enumerate(mock['problems'], start=1):
        p = pb.get(pid)
        answers[str(n)] = ('E' if str(p['answer']) != 'E' else 'A') if p['topic'] == wrong_topic else str(p['answer'])
    assert client.post('/api/amc/contests/step-mock-10/submit', json={'answers': answers}).json()['success']


def test_mock_mistakes_reach_analytics_and_the_plan(client):
    mock = catalog.MOCK_BY_ID['step-mock-10']
    topic = pb.get(mock['problems'][-1])['topic']
    asked = sum(1 for pid in mock['problems'] if pb.get(pid)['topic'] == topic)
    client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 120, 'hours': 6})
    before = {r['id']: r for r in client.get('/api/amc/plan').json()['priorities']}
    _sit(client, topic)

    body = client.get('/api/amc/analytics').json()
    lost = body['mock_mistakes']
    assert lost['sittings'] == 1 and lost['topics'][0]['id'] == topic
    assert lost['topics'][0]['wrong'] == asked and lost['topics'][0]['lost'] == 6 * asked
    # A sitting now exists: the projection is its score, give or take practice's 5%.
    score = 150 - 6 * asked
    assert abs(body['performance']['projected']['AMC 10'] - score) <= 0.05 * 150
    assert body['takeaways'][-1]['value'] == lost['topics'][0]['name']

    plan = client.get('/api/amc/plan').json()
    row = next(r for r in plan['priorities'] if r['id'] == topic)
    assert row['factors']['mock_lost'] == 6 * asked and 'in your last 1 mock' in row['why']
    assert plan['priorities'][0]['id'] == topic                      # the plan leads with it
    assert topic in [f['id'] for f in next(w for w in plan['weeks'] if w['current'])['focus']]
    assert row['gain'] > before.get(topic, {'gain': 0})['gain']
