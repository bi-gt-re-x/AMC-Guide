"""backend/amc/planning.py: topics ranked by the points studying them would add,
five kinds of weakness told apart from the student's own answers, and the
weekly plan built from both. The students here are made up, on the bank's
AMC 10 problems."""
from datetime import date, timedelta

from backend.amc import engine, planning
from backend.amc.bank import PROBLEMS

TODAY = date(2026, 11, 20)


def _pick(topic, n, used, avoid=(), key=lambda p: p['rating']):
    """`n` of the topic's own problems, easiest first, none also tagged with a
    topic in `avoid` (whose evidence a test reads: it would leak into it)."""
    found = [p for p in sorted(PROBLEMS, key=key) if p['level'] == 'AMC 10' and p['topic'] == topic
             and p['id'] not in used and not set(p['also']) & set(avoid)][:n]
    assert len(found) == n, (topic, len(found))
    used.update(p['id'] for p in found)
    return found


class Student:
    def __init__(self):
        self.rows, self.clock = [], 0

    def answer(self, p, correct, source='practice', seconds=120, days_ago=10):
        self.clock += 1
        at = (TODAY - timedelta(days=days_ago)).isoformat() + 'T17:{:02d}:{:02d}'.format(self.clock // 60 % 60,
                                                                                      self.clock % 60)
        self.rows.append({'problem_id': p['id'], 'answer': str(p['answer']) if correct else 'X',
                          'correct': 1 if correct else 0, 'seconds': seconds, 'source': source, 'at': at})

    def baseline(self, used, avoid=(), n=24):
        """A steady student: right on the easier half, wrong on the harder."""
        pool = [p for p in PROBLEMS if p['level'] == 'AMC 10' and p['id'] not in used
                and p['topic'] in ('word-problems', 'linear-equations', 'arithmetic', 'right-triangles',
                                   'sequences-series', 'exponents', 'coordinate-geometry', 'statistics')
                and not set(p['also']) & set(avoid)][:n]
        used.update(p['id'] for p in pool)
        for p in pool:
            self.answer(p, p['rating'] <= 4, seconds=150)

    def analyze(self):
        return planning.analyze(self.rows, engine.history(self.rows), 'AMC 10', TODAY)


def _row(study, tid):
    return next(r for r in study['topics'] if r['id'] == tid)


def test_a_frequent_topic_outranks_a_rare_weaker_one(client):
    # Divisibility, on every paper, at 40%; expected value, rare, at 0%.
    used, s = set(), Student()
    avoid = ('divisibility', 'expected-value')
    s.baseline(used, avoid)
    for i, p in enumerate(_pick('divisibility', 5, used, avoid)):
        s.answer(p, i in (0, 2))
    for p in _pick('expected-value', 3, used, avoid):
        s.answer(p, False)
    study = s.analyze()
    div, ev = _row(study, 'divisibility'), _row(study, 'expected-value')
    assert div['factors']['mastery'] == 0.4 and ev['factors']['mastery'] == 0.0
    assert div['priority'] > ev['priority'] and div['gain'] > ev['gain']
    # Every factor is there and in range, and the order is by priority.
    pri = [r['priority'] for r in study['topics']]
    assert pri == sorted(pri, reverse=True)
    for r in study['topics']:
        f = r['factors']
        assert 0.5 <= f['feasibility'] <= 1 and 1 <= f['recency'] <= 1.3 and 1 <= f['importance'] <= 1.25
        assert r['why']


def test_recency_and_importance_lift_a_topic(client):
    used, s = set(), Student()
    avoid = ('circles', 'modular-arithmetic')
    s.baseline(used, avoid)
    stale, fresh = _pick('circles', 4, used, avoid), _pick('modular-arithmetic', 4, used, avoid)
    for p in stale:
        s.answer(p, p is stale[0], days_ago=60)
    for p in fresh:
        s.answer(p, p is fresh[0], days_ago=1)
    study = s.analyze()
    assert _row(study, 'circles')['factors']['recency'] > _row(study, 'modular-arithmetic')['factors']['recency']
    # Triangles underpin right triangles, circles, area... more than polygons do.
    assert _row(study, 'triangles')['factors']['importance'] > _row(study, 'polygons')['factors']['importance']


def test_the_five_kinds_of_weakness_are_told_apart(client):
    used, s = set(), Student()
    avoid = ('circles', 'modular-arithmetic', 'digits-bases', 'probability', 'recursion')
    s.baseline(used, avoid)
    # Conceptual: wrong, and wrong again on another try; one solution shown.
    for i, p in enumerate(_pick('circles', 5, used, avoid)):
        s.answer(p, False, days_ago=12)
        s.answer(p, False, source='reveal' if i == 0 else 'review', days_ago=8)
    # Execution: the easiest problems missed, then right at the very next try.
    for p in _pick('modular-arithmetic', 5, used, avoid):
        s.answer(p, False, days_ago=12)
        s.answer(p, True, source='review', days_ago=8)
    # Speed: right, at twenty minutes a problem.
    for p in _pick('digits-bases', 5, used, avoid):
        s.answer(p, True, seconds=1200)
    # Recognition: right when practised by topic, wrong in a sitting.
    probs = _pick('probability', 10, used, avoid)
    for p in probs[:5]:
        s.answer(p, True, source='practice')
    for p in probs[5:]:
        s.answer(p, False, source='mock', seconds=0)
    # Retention: right once, wrong when it came back.
    for p in _pick('recursion', 4, used, avoid):
        s.answer(p, True, days_ago=30)
        s.answer(p, False, source='review', days_ago=5)
    study = s.analyze()
    assert 'conceptual' in _row(study, 'circles')['kinds']
    assert 'execution' in _row(study, 'modular-arithmetic')['kinds']
    assert 'speed' in _row(study, 'digits-bases')['kinds']
    assert 'recognition' in _row(study, 'probability')['kinds']
    assert 'retention' in _row(study, 'recursion')['kinds']
    # Each topic is trained the way its main kind wants.
    assert _row(study, 'circles')['mode'] == 'learn' and _row(study, 'digits-bases')['mode'] == 'timed'
    assert _row(study, 'recursion')['mode'] == 'spaced'
    kinds = {k['id']: k for k in study['kinds']}
    assert set(kinds) == {'conceptual', 'execution', 'speed', 'recognition', 'retention'}
    assert any(t['id'] == 'recursion' for t in kinds['retention']['topics'])
    assert all(t['evidence'] for k in kinds.values() for t in k['topics'])
    # The coach is told all of it.
    text = planning.brief(study)
    assert 'Retention' in text and 'Spaced repetition' in text


def test_too_few_answers_calls_nothing(client):
    used, s = set(), Student()
    for p in _pick('circles', 2, used):
        s.answer(p, False)
    study = s.analyze()
    assert all(not k['topics'] for k in study['kinds'])
    assert _row(study, 'circles')['mode'] == 'learn'
    assert 'Not enough answers yet' in planning.brief(study)


def test_the_schedule_spaces_the_best_topics_and_follows_the_coach():
    rows = [{'id': t, 'name': t, 'priority': p} for t, p in
            (('a', 3.0), ('b', 2.5), ('c', 1.0), ('d', 0.9), ('e', 0.2))]
    weeks = planning.schedule(rows, 6)
    ids = [[r['id'] for r in w] for w in weeks]
    assert ids[0] == ['a', 'b']
    assert ids[1] != ids[0]                                  # not the same two weeks running
    counts = {t: sum(t in w for w in ids) for t in 'abcde'}
    assert counts['a'] >= counts['c'] >= counts['e']         # the valuable come back more
    coached = planning.schedule(rows, 3, coached=['d', 'e', 'zz'])
    assert [r['id'] for r in coached[0]] == ['d', 'e']


def test_the_plan_is_built_from_it(client):
    client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 105, 'hours': 6,
                                      'details': {'days_per_week': 7}})
    for pid in [p['id'] for p in PROBLEMS if p['level'] == 'AMC 10' and p['topic'] == 'casework'][:5]:
        client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': 'A', 'seconds': 1500})
    body = client.get('/api/amc/plan').json()
    assert body['priorities'] and set(body['priorities'][0]) >= {'gain', 'factors', 'mode', 'why'}
    assert {k['id'] for k in body['kinds']} == {'conceptual', 'execution', 'speed', 'recognition', 'retention'}
    first = body['weeks'][0]['focus']
    assert [f['id'] for f in first] == [r['id'] for r in body['priorities'][:2]]
    assert all('mode' in f for f in first)
    practice = next(i for i in body['today'] if i['key'] == 'practice')
    # The week's two focus topics take turns down its days.
    assert any(f['name'] in practice['label'] for f in first)
    analytics = client.get('/api/amc/analytics').json()
    assert analytics['priorities'] and len(analytics['kinds']) == 5


def test_the_difficulty_mix_follows_ability_and_goal():
    levels = lambda mix: {m['level']: m['share'] for m in mix}
    qualify, high = planning.goal_level('AMC 10', 100), planning.goal_level('AMC 10', 125)
    assert qualify < high <= 5
    weak, strong = levels(planning.difficulty_mix(3.5, qualify)), levels(planning.difficulty_mix(5.5, qualify))
    for mix in (weak, strong):
        assert abs(sum(mix.values()) - 1) < 1e-9 and all(v * 20 == round(v * 20) for v in mix.values())
    mean = lambda mix: sum(k * v for k, v in mix.items())
    # Better at the topic: harder problems, less of the fundamentals.
    assert mean(strong) > mean(weak) and strong.get(1, 0) < weak.get(1, 0)
    assert weak.get(1, 0) + weak.get(2, 0) >= 0.6                  # 40%-ish: mostly levels 1-2
    assert strong.get(2, 0) + strong.get(3, 0) >= 0.7              # 80%-ish: mostly levels 2-3
    # A higher goal at the same ability: a harder mix.
    assert mean(levels(planning.difficulty_mix(5.5, high))) > mean(strong)
    # Levels well beyond the goal get little.
    assert levels(planning.difficulty_mix(4.0, 1)).get(5, 0) <= 0.05
    # Splitting a day's problems keeps the count.
    split = planning.split_count(planning.difficulty_mix(5.5, qualify), 7)
    assert sum(c['count'] for c in split) == 7
    assert [planning.level_of(r) for r in (2, 2.5, 3, 4.5, 5, 6.5, 7, 8.5, 9, 12)] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_todays_practice_and_analytics_carry_the_mix(client):
    client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 120, 'hours': 6,
                                      'details': {'days_per_week': 7}})
    body = client.get('/api/amc/plan').json()
    assert body['difficulty']['ceiling'] >= 2 and body['difficulty']['mix']
    practice = next(i for i in body['today'] if i['key'] == 'practice')
    focus = next(f for f in body['weeks'][0]['focus'] if f['name'] in practice['label'])
    assert focus['mix'] and abs(sum(m['share'] for m in focus['mix']) - 1) < 1e-9
    assert 'level' in practice['detail'] and focus['name'] in practice['label']
    # It opens the topic's own handpicked set, in the topic's mode, sized to today's time.
    assert practice['to'] == '/practice/{}?mode={}&n={}'.format(focus['id'], focus['mode'], practice['goal'])
    analytics = client.get('/api/amc/analytics').json()
    tiles = {t['id']: t for t in analytics['takeaways']}
    assert set(tiles) == {'projected', 'level', 'next', 'weakness'}
    assert tiles['level']['mix'] and tiles['level']['value'].startswith('Level')
    assert all(len(t['note']) <= 60 for t in tiles.values())     # short: a glance, not a paragraph


def test_a_topic_the_plan_comes_back_to_is_trained_further_along():
    untried = {'mode': 'learn', 'kind': None}
    practised = {'mode': 'practice', 'kind': None}
    # Met for the first time: learned, whatever the phase.
    assert planning.week_mode(untried, 'Contest mode', 0) == 'learn'
    # Each return climbs: learn, practise, timed, mixed.
    assert [planning.week_mode(untried, 'Foundations', v) for v in range(5)] == \
        ['learn', 'practice', 'timed', 'mixed', 'mixed']
    # The later phases train what has been met at contest pace.
    assert planning.week_mode(practised, 'Core', 0) == 'practice'
    assert planning.week_mode(practised, 'Contest mode', 0) == 'timed'
    assert planning.week_mode(untried, 'Contest mode', 1) == 'timed'
    # Accuracy and retention trouble keep the training they want.
    assert planning.week_mode({'mode': 'accuracy', 'kind': 'execution'}, 'Contest mode', 3) == 'accuracy'
    assert planning.week_mode({'mode': 'spaced', 'kind': 'retention'}, 'Core', 2) == 'spaced'


def test_the_weeks_move_on_from_learning_and_count_what_was_done(client):
    client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 100, 'hours': 6,
                                      'details': {'days_per_week': 3}})
    pid = next(p['id'] for p in PROBLEMS if p['level'] == 'AMC 10')
    client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': 'A', 'seconds': 60})
    body = client.get('/api/amc/plan').json()
    weeks = body['weeks']
    # Three days a week: the week's problems are what its three study days hold.
    assert sum(not d['rest'] for d in weeks[0]['days']) == 3
    assert weeks[0]['problems'] == sum(b.get('count', 0) for d in weeks[0]['days'] for b in d['blocks']
                                       if b['kind'] in ('practice', 'challenge'))
    current = next(w for w in weeks if w['current'])
    assert current['answered'] == 1
    assert 'answered' not in weeks[-1]
    # No topic is "learn the ideas" on a return visit, and Contest mode never is.
    seen = set()
    for w in weeks:
        for f in w['focus']:
            if f['id'] in seen:
                assert f['mode'] != 'learn', (w['number'], f)
            seen.add(f['id'])
    contest = [f['mode'] for w in weeks if w['phase'] == 'Contest mode' for f in w['focus'] if f['id'] in seen]
    assert contest and contest.count('learn') < len(contest)
    # The dashboard's Today list is the plan's.
    dash = client.get('/api/amc/dashboard').json()
    assert [i['label'] for i in dash['plan']['today']] == [i['label'] for i in body['today']]


def _settings(**extra):
    return {'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 100, 'hours': 6, 'details': {},
            'coach': None, **extra}


def test_the_weeks_run_from_when_the_plan_was_made_so_the_phases_move_on():
    tstats = engine.topic_stats({}, {})
    made = _settings(created_at='2026-11-20T10:00:00')
    first = engine.plan_weeks(made, tstats, [], date(2026, 11, 24))
    later = engine.plan_weeks(made, tstats, [], date(2027, 6, 1))
    assert len(first) == len(later)                                # one plan, not a new one each visit
    assert next(w for w in first if w['current'])['phase'] == 'Foundations'
    now = next(w for w in later if w['current'])
    assert now['number'] > 20 and now['phase'] != 'Foundations'   # seven months on, out of Foundations
    gone = [w for w in later if w['past']]
    assert gone and all(not w['focus'] for w in gone)
    assert all(w['focus'] for w in later if not w['past'] and w['phase'] != 'Taper')
    # Laid out from today instead (no created_at), the same day was still Foundations.
    fresh = engine.plan_weeks(_settings(), tstats, [], date(2027, 6, 1))
    assert next(w for w in fresh if w['current'])['phase'] == 'Foundations'


def test_the_coach_order_gives_way_to_a_topic_since_mastered():
    rows = [{'id': t, 'name': t, 'priority': p, 'factors': f} for t, p, f in (
        ('a', 3.0, {}), ('b', 2.5, {}), ('c', 1.0, {'answered': 8, 'mastery': 0.9}), ('d', 0.9, {}))]
    weeks = planning.schedule(rows, 2, coached=['c', 'd'])
    assert 'c' not in [r['id'] for r in weeks[0]] and 'd' in [r['id'] for r in weeks[0]]


def test_the_plan_says_what_level_it_is_built_from(client):
    client.put('/api/amc/plan', json={'target': 'AMC 10', 'exam_date': '2027-11-05', 'goal_score': 100, 'hours': 6})
    for p in [p for p in PROBLEMS if p['level'] == 'AMC 10'][:6]:
        client.post('/api/amc/problems/{}/attempt'.format(p['id']), json={'answer': str(p['answer']), 'seconds': 60})
    level = client.get('/api/amc/plan').json()['level']
    assert 1 <= level['level'] <= 5 and level['name'] and 1 <= level['goal_level'] <= 5
    assert level['recent']['answered'] == 6 and level['recent']['accuracy'] == 1.0 and level['mix']


def test_reviews_come_one_set_at_a_time():
    """Two hundred due is one set of ten today, not two hundred."""
    week = {'current': True, 'focus': [], 'problems': 0, 'mock': False, 'mock_done': False, 'phase': 'Core'}
    today = date(2026, 11, 25)
    items = engine.today_items({'target': 'AMC 10'}, [week], 228, today, {}, set())
    review = next(i for i in items if i['key'] == 'review')
    assert review['goal'] == engine.REVIEW_SET == 10
    assert '218 more' in review['detail'] and review['to'] == '/review?start=1'
    # Ten answered as reviews today: the set is done, whatever is still due.
    done = engine.today_items({'target': 'AMC 10'}, [week], 218, today, {}, set(), reviewed_today=10)
    assert next(i for i in done if i['key'] == 'review')['done']
    # A short queue is a short set.
    few = engine.today_items({'target': 'AMC 10'}, [week], 3, today, {}, set())
    assert next(i for i in few if i['key'] == 'review')['goal'] == 3


def test_todays_set_says_how_big_how_fast_and_why():
    focus = {'id': 'probability', 'name': 'Probability', 'category': 'counting', 'mode': 'timed',
             'mix': [{'level': 2, 'share': 0.25}, {'level': 3, 'share': 0.5}, {'level': 4, 'share': 0.25}],
             'reason': 'You lost 9 points here in recent mocks.'}
    week = {'current': True, 'focus': [focus], 'problems': 40, 'mock': True, 'mock_done': False, 'phase': 'Core'}
    items = engine.today_items({'target': 'AMC 10'}, [week], 0, date(2026, 11, 25), {}, set())
    practice = next(i for i in items if i['key'] == 'practice')
    assert practice['label'] == 'Timed set: Probability'
    assert practice['detail'] == '8 problems, 3 minutes each, levels 2–4. You lost 9 points here in recent mocks.'
    assert practice['minutes'] == 24
    assert next(i for i in items if i['key'] == 'mock')['minutes'] == 75
    assert engine._reason({'factors': {'mock_lost': 9}}) == 'You lost 9 points here in recent mocks.'


def test_each_week_is_days_sized_to_the_time_a_day():
    """Hours a week over days a week: each study day fits its minutes, rest days are empty,
    one day a week is a challenge set, and the mock goes on the weekend."""
    tstats = engine.topic_stats({}, {})
    assert engine.study_schedule(_settings(hours=6)) == ((0, 1, 2, 3, 5, 6), 60)       # Friday off
    assert engine.study_schedule(_settings(hours=5, details={'days_per_week': 3})) == ((1, 3, 5), 100)
    weeks = engine.plan_weeks(_settings(exam_date='2027-01-20', created_at='2026-11-20'), tstats, [], date(2026, 11, 25))
    for w in weeks:
        assert [d['weekday'] for d in w['days']] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        assert w['days'][4]['rest'] and not w['days'][4]['blocks']
        for d in w['days']:
            mock = any(b['kind'] == 'mock' for b in d['blocks'])
            if not d['rest'] and not mock:
                assert 0 < d['minutes'] <= 60, (w['number'], d)
        if w['phase'] != 'Taper' and not w['past']:
            challenges = [b for d in w['days'] for b in d['blocks'] if b['kind'] == 'challenge']
            assert len(challenges) == 1 and challenges[0]['to'].startswith('/practice/')
            assert 'mode=challenge' in challenges[0]['to'] and challenges[0]['count'] <= 5
        if w['mock']:
            day = next(d for d in w['days'] if any(b['kind'] == 'mock' for b in d['blocks']))
            assert day['weekday'] in ('Sat', 'Sun')


def test_todays_list_is_todays_day_of_the_plan():
    tstats = engine.topic_stats({}, {})
    settings = _settings(created_at='2026-11-20')
    weeks = engine.plan_weeks(settings, tstats, [], date(2026, 11, 23))              # a Monday
    monday = next(w for w in weeks if w['current'])['days'][0]
    items = engine.today_items(settings, weeks, 4, date(2026, 11, 23), {}, set())
    sets = [b for b in monday['blocks'] if b['kind'] in ('practice', 'challenge')]
    assert [i['label'] for i in items if i['key'].startswith(('practice', 'challenge'))] == [b['label'] for b in sets]
    assert next(i for i in items if i['key'] == 'review')['goal'] == 4
    # Friday is a rest day: only a review set, when one is due.
    friday = engine.plan_weeks(settings, tstats, [], date(2026, 11, 27))
    assert [i['key'] for i in engine.today_items(settings, friday, 4, date(2026, 11, 27), {}, set())] == ['review']
    assert engine.today_items(settings, friday, 0, date(2026, 11, 27), {}, set()) == []
