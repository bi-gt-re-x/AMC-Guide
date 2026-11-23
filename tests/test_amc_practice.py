"""Topic practice sets (backend/amc/practice.py), the plan's starting point and
shape from the goal and current scores (planning.starting_point / SHAPES), and
the student's own subject ratings (planning.subject_lean)."""
from datetime import date, timedelta

from backend.amc import engine, planning, practice
from backend.amc import problems as pb
from backend.amc.bank import PROBLEMS

TODAY = date(2026, 11, 20)


def _attempt(p, correct, days_ago=10, source='practice'):
    return {'problem_id': p['id'], 'answer': 'X', 'correct': 1 if correct else 0, 'seconds': 150,
            'source': source, 'at': (TODAY - timedelta(days=days_ago)).isoformat() + 'T17:00:00'}


def test_every_set_is_eight_from_the_one_topic_and_each_mode_picks_its_own(client):
    topic = 'probability'
    pool = [p for p in PROBLEMS if p['level'] == 'AMC 10' and (p['topic'] == topic or topic in p['also'])]
    # Some history: the easiest half right, a couple missed.
    rows = [_attempt(p, i % 3 != 0, days_ago=40 - i) for i, p in enumerate(sorted(pool, key=lambda p: p['rating'])[:8])]
    hist = engine.history(rows)
    sets = {}
    for mode in practice.MODES:
        s = practice.build(topic, mode, 'AMC 10', 4.5, 4.2, planning.difficulty_mix(4.2, 2), hist, {}, 'u', TODAY)
        ids = s['problems']
        assert len(ids) == practice.SIZE and len(set(ids)) == practice.SIZE, mode
        assert all(pb.get(i)['topic'] == topic or topic in pb.get(i)['also'] for i in ids), mode
        sets[mode] = s
    ratings = {m: [pb.get(i)['rating'] for i in s['problems']] for m, s in sets.items()}
    # Learn: the easiest; mixed: the widest spread; spaced: problems met before.
    assert sum(ratings['learn']) / 8 <= min(sum(ratings[m]) / 8 for m in ('timed', 'mixed', 'practice'))
    assert max(ratings['mixed']) - min(ratings['mixed']) >= max(ratings['timed']) - min(ratings['timed'])
    own_seen = {i for i in hist if pb.get(i)['topic'] == topic}
    assert own_seen <= set(sets['spaced']['problems'])
    # Accuracy puts the misses still open first in line.
    missed = {r['problem_id'] for r in rows if not r['correct'] and pb.get(r['problem_id'])['topic'] == topic}
    assert missed <= set(sets['accuracy']['problems'])
    # A timed set has a clock; a mixed set hides the topic; the same set all day.
    assert sets['timed']['seconds'] == 180 and sets['mixed']['hide_topic'] and not sets['learn']['hide_topic']
    again = practice.build(topic, 'mixed', 'AMC 10', 4.5, 4.2, planning.difficulty_mix(4.2, 2), hist, {}, 'u', TODAY)
    assert again['problems'] == sets['mixed']['problems']


def test_the_set_endpoint(client):
    body = client.get('/api/amc/topics/circles/set?mode=timed').json()
    assert body['success'] and body['mode'] == 'timed' and len(body['problems']) == 8
    assert all(p['topic'] == 'circles' or p['level_of'] for p in body['problems'])
    assert {m['id'] for m in body['modes']} == set(practice.MODES)
    assert not client.get('/api/amc/topics/nope/set').json()['success']
    # The topic's own problems first: none only tagged with it while there are enough of its own.
    own = [p for p in PROBLEMS if p['topic'] == 'circles']
    if len(own) >= 8:
        assert all(p['topic'] == 'circles' for p in body['problems'])


def test_the_starting_point_comes_from_scores_and_answers():
    sittings = [{'contest_id': '2025-amc-10b', 'kind': 'logged', 'score': 99, 'correct': 0, 'blank': 0,
                 'at': '2026-11-01T18:00:00'},
                {'contest_id': '2024-amc-10a', 'kind': 'logged', 'score': 94.5, 'correct': 0, 'blank': 0,
                 'at': '2026-10-20T18:00:00'}]
    details = {'_exam': '2027-11-05'}
    both = planning.starting_point('AMC 10', 120, 90, sittings, details, TODAY)
    # Both sittings were exactly that year's floor: 100 on a typical paper; the model says 90.
    assert 90 < both['current'] < 100 and 'recent sittings' in both['from'] and 'your answers' in both['from']
    assert both['gap'] == round(120 - both['current'], 1) and both['stage'] == 'far' and both['weeks'] > 40
    near = planning.starting_point('AMC 10', 105, 100, [], details, TODAY)
    assert near['stage'] == 'near' and near['current'] == 100
    there = planning.starting_point('AMC 10', 95, 100, [], details, TODAY)
    assert there['stage'] == 'there'
    told = planning.starting_point('AMC 10', 100, None, [], {**details, 'last_score': 84}, TODAY)
    assert told['current'] == 84 and 'you gave' in told['from']
    assert planning.starting_point('AMC 10', 100, None, [], details, TODAY)['stage'] == 'unknown'


def test_the_plans_shape_follows_the_gap():
    settings = {'target': 'AMC 10', 'exam_date': (TODAY + timedelta(weeks=20)).isoformat(), 'hours': 6}
    tstats = engine.topic_stats({}, {})
    def phases(stage):
        weeks = engine.plan_weeks(settings, tstats, [], TODAY, None, stage)
        return [w['phase'] for w in weeks], sum(1 for w in weeks if w['mock'])
    far, far_mocks = phases('far')
    there, there_mocks = phases('there')
    assert far.count('Foundations') > there.count('Foundations')
    assert there.count('Contest mode') > far.count('Contest mode') and there_mocks > far_mocks


def test_subject_ratings_are_kept_and_lean_on_priorities_until_answers_come(client):
    reply = client.put('/api/amc/plan', json={
        'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 110, 'hours': 6,
        'details': {'subjects': {'geometry': 'weak', 'algebra': 'strong', 'bogus': 'weak', 'counting': 'meh'},
                    'subject_notes': {'geometry': ' circles mostly ', 'misc': '', 'nope': 'x'}}}).json()
    details = reply['plan']['details']
    assert details['subjects'] == {'geometry': 'weak', 'algebra': 'strong'}
    assert details['subject_notes'] == {'geometry': 'circles mostly'}
    lean = planning.subject_lean(details, {})
    assert lean['circles'] > 1 > lean['quadratics'] and 'basic-counting' not in lean
    # With answers of its own, a topic leans on the rating less.
    assert planning.subject_lean(details, {'circles': 40})['circles'] < lean['circles']
    body = client.get('/api/amc/plan').json()
    assert body['start']['stage'] in ('far', 'near', 'there', 'unknown')
