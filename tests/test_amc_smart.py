"""The student model in backend/amc/smart.py: ability on AMC Guide's 1-10 scale,
weighted toward recent answers, timed predictions from the student's own pace,
topics ranked by points, practice problems they can win, and timed mocks
checked against the model."""
from datetime import date

from backend.amc import engine, smart
from backend.amc.bank import BY_ID, PROBLEMS

TODAY = date(2026, 11, 14)


def _attempts(rows):
    """[(problem id, correct, day, seconds)] as attempt rows, oldest first."""
    return [{'problem_id': pid, 'correct': int(ok), 'at': '{}T10:00:00'.format(day), 'seconds': secs,
             'source': 'practice'} for pid, ok, day, secs in rows]


def _amc10(lo, hi):
    return [p for p in PROBLEMS if p['level'] == 'AMC 10' and lo <= p['rating'] <= hi]


def test_recent_answers_count_more_than_old_ones():
    easy, hard = _amc10(1, 2)[:12], _amc10(4.5, 6)[:12]
    # Missed the hard ones months ago, solves them now.
    rows = [(p['id'], False, '2026-07-01', 200) for p in hard] + [(p['id'], True, '2026-07-01', 90) for p in easy]
    old_hist = engine.history(_attempts(rows))
    fresh = [(p['id'], True, '2026-11-10', 200) for p in _amc10(4.5, 6)[12:24]]
    hist = engine.history(_attempts(rows + fresh))
    stale = engine.history(_attempts(rows + [(pid, ok, '2026-07-02', s) for pid, ok, _, s in fresh]))
    theta_now = smart.fit([(r, ok, w) for r, ok, w, _ in smart._first_points(hist, TODAY)])[0]
    theta_stale = smart.fit([(r, ok, w) for r, ok, w, _ in smart._first_points(stale, TODAY)])[0]
    assert theta_now > theta_stale                     # the same answers, given recently, move it more
    assert smart._weight('2026-11-14', TODAY) == 1 and smart._weight('2026-01-01', TODAY) == smart.MIN_WEIGHT
    assert len(old_hist) == 24


def test_a_slow_student_loses_points_to_the_clock():
    picks = _amc10(1, 4.5)[:30]
    quick = engine.history(_attempts([(p['id'], i % 3 != 0, '2026-11-10', 70) for i, p in enumerate(picks)]))
    slow = engine.history(_attempts([(p['id'], i % 3 != 0, '2026-11-10', 520) for i, p in enumerate(picks)]))
    fast_stats = smart.analyze([], quick, {}, [], None, TODAY)['contests']['AMC 10']
    slow_stats = smart.analyze([], slow, {}, [], None, TODAY)['contests']['AMC 10']
    assert fast_stats['expected'] == slow_stats['expected']        # same answers, same ability
    assert slow_stats['timed'] < fast_stats['timed'] <= fast_stats['expected'] + 0.05
    assert slow_stats['reached'] < 25 and slow_stats['speed_cost'] > fast_stats['speed_cost']


def test_next_problems_are_winnable_and_varied():
    picks = _amc10(1, 4.5)[:30]
    hist = engine.history(_attempts([(p['id'], i % 2 == 0, '2026-11-10', 150) for i, p in enumerate(picks)]))
    stats = smart.analyze([], hist, {}, [], None, TODAY)
    nxt = stats['next_problems']
    assert nxt and len(nxt) <= 8
    lo, hi = smart.LEARN_BAND
    assert sum(1 for p in nxt if lo - 0.1 <= p['chance'] <= hi + 0.1) >= len(nxt) - 2
    topics = [p['topic'] for p in nxt]
    assert max(topics.count(t) for t in topics) <= 2
    assert all(not hist.get(p['id'], {}).get('solved') for p in nxt)


def test_focus_topics_are_ranked_by_points():
    hist = engine.history(_attempts([(p['id'], p['topic'] != 'area', '2026-11-10', 150) for p in _amc10(1, 4.5)[:60]]))
    stats = smart.analyze([], hist, {}, [], None, TODAY)
    points = [t['points'] for t in stats['focus']]
    assert points == sorted(points, reverse=True) and points[0] > 0
    assert all(0 <= t['points'] <= 60 for t in stats['topics'])


def test_weak_topics_are_only_ones_the_student_has_touched():
    # Answers in a handful of topics only: every other topic is untouched, and
    # untouched is not weak (the focus list, the AI brief, "my weakest topic").
    picks = _amc10(1, 4.5)[:40]
    hist = engine.history(_attempts([(p['id'], i % 3 != 0, '2026-11-10', 150) for i, p in enumerate(picks)]))
    stats = smart.analyze([], hist, {}, [], None, TODAY)
    touched = {t['id'] for t in stats['topics'] if t['answered']}
    assert stats['focus'] and all(t['id'] in touched and t['answered'] for t in stats['focus'])
    assert 'untested' not in smart.ai_brief(stats, None)
    empty = smart.analyze([], {}, {}, [], None, TODAY)
    assert empty['focus'] == [] and 'none yet' in smart.ai_brief(empty, None)


def test_a_timed_mock_well_below_the_model_is_flagged():
    picks = _amc10(1, 4.5)[:30]
    hist = engine.history(_attempts([(p['id'], True, '2026-11-10', 100) for p in picks]))
    mock_ids = [pid for pid in sorted(BY_ID) if pid.startswith('mock10-1-')]
    mock = {'kind': 'mock', 'contest_id': 'mock-10-1', 'score': 40, 'at': '2026-11-12T10:00:00',
            'answers': {'_ids': mock_ids}}
    stats = smart.analyze([], hist, {}, [mock], None, TODAY)
    assert stats['mock_check']['taken'] == 1 and stats['mock_check']['gap'] < -6
    assert any(p['kind'] == 'pressure' for p in stats['patterns'])
    assert 'Timed mocks against the model' in smart.ai_brief(stats, None)
