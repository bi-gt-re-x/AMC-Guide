"""The projected score, and where mock sittings lose points.

## Projected score: what the sittings say, not what practice suggests

A projected score has to be one the student would actually get, and the best
evidence of that is what they have actually got: timed sittings here and real
contest scores they logged. Practice flatters: the problems come labelled with
their topic, there is no clock running across 25 of them, and a problem tried
twice counts its better try. A projection from practice alone ran well above
what the same students then scored in a sitting.

So `projection` is

    95%  the recent sittings at that level (newest weighing most, each
         official paper's score adjusted to a typical paper's difficulty,
         backend/amc/results.py)
     5%  the practice model (backend/amc/smart.py: problems solved, at the
         difficulty they were solved at)

and with no sitting at that level there is no projected score at all: the
page asks for a timed mock or a logged score instead of showing a practice
number as if it were one. `MODEL_SHARE` is the 5%.

## Mock mistakes: points lost in sittings, by topic

`mistakes` goes through every recent timed sitting answer by answer and counts,
per topic, the problems got wrong or left blank and the points they cost (6 a
wrong answer and 4.5 a blank against a right one on the AMC; 1 on the AIME).
Analytics lists them under Weaknesses, and the study plan's priorities weigh
them (backend/amc/planning.py `analyze`): a topic that costs points in
sittings gets studied, whatever practice says about it.
"""
from datetime import date, timedelta

from backend.amc import catalog, engine, results

#: The practice model's share of a projected score; the sittings have the rest.
MODEL_SHARE = 0.05
#: How far back a sitting still counts, and how many of the newest count.
RECENT_DAYS = 180
MAX_SITTINGS = 5
#: Each older sitting weighs this much of the one after it.
DECAY = 0.8


def contest_level(contest_id):
    """'AMC 10', 'AMC 12' or 'AIME' for a past paper or a mock set, else None."""
    found = catalog.PAST_BY_ID.get(contest_id) or catalog.MOCK_BY_ID.get(contest_id)
    return found['level'] if found else None


def sittings(mocks, level, today):
    """The recent timed sittings and logged scores at `level`, newest first,
    each as {'id', 'contest_id', 'kind', 'at', 'score'}, the score on a typical
    paper's scale where the paper's statistics are known."""
    since = (today - timedelta(days=RECENT_DAYS)).isoformat()
    out = []
    for m in sorted(mocks, key=lambda m: m['at'], reverse=True):
        if m['kind'] not in ('mock', 'logged') or m['at'][:10] < since:
            continue
        if contest_level(m['contest_id']) != level:
            continue
        st = results.of_row(m)
        out.append({'id': m.get('id'), 'contest_id': m['contest_id'], 'kind': m['kind'], 'at': m['at'],
                    'score': st['adjusted'] if st else m['score']})
        if len(out) == MAX_SITTINGS:
            break
    return out


def blend(model, recent):
    """A projected score from the practice model's number and the sittings
    (newest first): None with no sittings, whatever the model says."""
    if not recent:
        return None
    weights = [DECAY ** i for i in range(len(recent))]
    sat = sum(s['score'] * w for s, w in zip(recent, weights)) / sum(weights)
    score = sat if model is None else (1 - MODEL_SHARE) * sat + MODEL_SHARE * model
    return round(score * 2) / 2


def projection(hist, level, mocks, today=None):
    """{'score', 'sittings', 'mock', 'model', 'model_share'} for `level`.
    `score` is None until there is a sitting at that level."""
    today = today or date.today()
    model = engine.projected(hist, level, today) if len(hist) >= engine.PROJECTION_MIN else None
    recent = sittings(mocks, level, today)
    mock_avg = blend(None, recent)
    return {'score': blend(model, recent), 'sittings': len(recent), 'mock': mock_avg, 'model': model,
            'model_share': MODEL_SHARE if recent and model is not None else 0.0}


def projected_score(hist, level, mocks, today=None):
    return projection(hist, level, mocks, today)['score']


def _graded(m):
    """A timed sitting answer by answer: engine.score_mock's rows, or None
    when the sitting did not keep which problems it asked."""
    ids = (m.get('answers') or {}).get('_ids')
    level = contest_level(m['contest_id'])
    if not ids or not level:
        return None
    from backend.amc import problems as pb
    if not all(pb.get(pid) for pid in ids):
        return None
    return engine.score_mock({'level': level, 'problems': ids},
                             {k: v for k, v in m['answers'].items() if not k.startswith('_')})


def mistakes(mocks, level=None, today=None):
    """Points lost in recent timed sittings, by topic, most lost first.

    {'sittings': n, 'lost': total points lost, 'topics': [{'id', 'name',
    'category', 'wrong', 'blank', 'missed', 'asked', 'lost', 'per_sitting',
    'problems': [ids]}]}. `level` keeps only sittings at that contest."""
    today = today or date.today()
    since = (today - timedelta(days=RECENT_DAYS)).isoformat()
    by_topic, count = {}, 0
    for m in sorted(mocks, key=lambda m: m['at'], reverse=True):
        if m['kind'] != 'mock' or m['at'][:10] < since:
            continue
        lvl = contest_level(m['contest_id'])
        if level and lvl != level:
            continue
        graded = _graded(m)
        if not graded:
            continue
        count += 1
        full, blank_pts = (1, 0) if lvl == 'AIME' else (6, 1.5)
        for row in graded['rows']:
            t = by_topic.setdefault(row['topic'], {'wrong': 0, 'blank': 0, 'asked': 0, 'lost': 0.0, 'problems': []})
            t['asked'] += 1
            if row['result'] == 'correct':
                continue
            t[row['result']] += 1
            t['lost'] += full - (blank_pts if row['result'] == 'blank' else 0)
            if row['problem_id'] not in t['problems']:
                t['problems'].append(row['problem_id'])
        if count == MAX_SITTINGS * 2:
            break
    topics = []
    for tid, t in by_topic.items():
        if not t['lost']:
            continue
        info = catalog.TOPIC_BY_ID[tid]
        topics.append({'id': tid, 'name': info['name'], 'category': info['category'],
                       'wrong': t['wrong'], 'blank': t['blank'], 'missed': t['wrong'] + t['blank'],
                       'asked': t['asked'], 'lost': round(t['lost'], 1),
                       'per_sitting': round(t['lost'] / count, 1), 'problems': t['problems'][:12]})
    topics.sort(key=lambda t: (-t['lost'], -t['wrong'], t['name']))
    return {'sittings': count, 'lost': round(sum(t['lost'] for t in topics), 1), 'topics': topics}
