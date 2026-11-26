"""What a finished set says: each problem as it went, and what follows.

A set (a topic's practice set, a review set, the weak-topics set) is a row in
`amc_set_runs` holding the problems as they were dealt, and its answers are
the `amc_attempts` rows carrying its id. The report is read from those two
alone, never from a problem's status: a problem solved last month and missed
today is a miss in today's set, and the practice picker would deal different
problems once these are answered, so asking it again is not this set.

For each problem, in the order dealt:

* **result**: 'right', 'wrong', 'revealed' (the solution shown before an
  answer, which counts as a miss) or 'skipped' (not answered: passed over, or
  the clock ran out first). Only the first answer in the set counts.
* what was given and, unless it was skipped (still open, so not spoiled), the
  answer;
* the chance the model gave the student on it before the set
  (backend/amc/smart.py), so a miss on a problem they usually get is told
  apart from a miss on a stretch;
* time against the pace for its difficulty, and when a miss comes back for
  review.

Then the whole set: right of dealt, accuracy on what was answered, against
how many the model expected, the time used, and the student's level in each
topic before the set and after it (the same fit as Analytics and the study
plan, so the move shown here is the move they make). Last, what to do next,
from the study plan's own reading of the topic as it stands after the set
(backend/amc/planning.py): which kind of set, and why.
"""
from datetime import date

from backend.amc import catalog, engine, planning, practice, smart
from backend.amc import problems as pb

#: A miss on a problem the model gave at least this chance is a slip.
CARELESS = 0.7
#: A right answer at or below this chance is a stretch landed.
STRETCH = 0.4
#: Right, but this many times the pace for its difficulty: slow.
SLOW = 2.0

KIND_TITLE = {'review': 'Review set', 'weak': 'Weak topics set'}


def _levels(hist, today):
    """(overall theta, {topic: theta}) from first tries and retests: the fit every page reads."""
    pts = smart.ability_points(hist, today)
    theta = smart.fit([pt[:3] for pt in pts])[0] if pts else smart.PRIOR_MEAN
    by_topic = {}
    for rating, ok, w, p in pts:
        for tid in [p['topic']] + list(p.get('also') or []):
            by_topic.setdefault(tid, []).append((rating, ok, w))
    return theta, {tid: smart.fit(rows, mean=theta, sd=smart.TOPIC_SD)[0] for tid, rows in by_topic.items()}


def _answer_text(p, value):
    if value in (None, ''):
        return ''
    return '({})'.format(value) if p.get('choices') else str(value)


def _source(pid):
    found = catalog.sources(pid)
    if found:
        return '{} #{}'.format(found[0]['name'], found[0]['number'])
    return 'AI practice' if pid.startswith('ai-') else 'Drill'


def split(run, attempts):
    """(answers in this set, answers before it), each oldest first."""
    mine = [a for a in attempts if a.get('set_id') == run['id']]
    before = [a for a in attempts if a.get('set_id') != run['id'] and a['at'] <= run['started_at']]
    return mine, before


def tally(run, mine):
    """Right, wrong, revealed and skipped, from the first answer to each problem in the set."""
    first = {}
    for a in mine:
        first.setdefault(a['problem_id'], a)
    out = {'right': 0, 'wrong': 0, 'revealed': 0, 'skipped': 0}
    for pid in run['problems']:
        a = first.get(pid)
        if a is None:
            out['skipped'] += 1
        elif a.get('source') == 'reveal':
            out['revealed'] += 1
        elif a['correct']:
            out['right'] += 1
        else:
            out['wrong'] += 1
    return out


def title_of(run):
    if run['kind'] == 'practice':
        return run.get('title') or practice.TITLES.get(run['mode'], 'Practice set')
    return KIND_TITLE.get(run['kind'], 'Set')


def brief(run, mine):
    """One line of a set for a list: what it was and how it went."""
    t = tally(run, mine)
    n = len(run['problems'])
    answered = t['right'] + t['wrong'] + t['revealed']
    topic = catalog.TOPIC_BY_ID.get(run['topic'])
    return {'id': run['id'], 'kind': run['kind'], 'mode': run['mode'], 'title': title_of(run),
            'topic': run['topic'], 'topic_name': topic['name'] if topic else '',
            'started_at': run['started_at'], 'finished_at': run['finished_at'], 'time_up': run['time_up'],
            'total': n, **t, 'answered': answered,
            'accuracy': round(t['right'] / answered, 3) if answered else None,
            'finished': bool(run['finished_at']) or answered == n}


def report(run, attempts, review_by_id, level, goal, mocks=None, details=None, today=None):
    """The whole report of one set (see the module's note)."""
    today = today or date.today()
    mine, before = split(run, attempts)
    hist_before = engine.history(before)
    hist_after = engine.history(sorted(before + mine, key=lambda a: a['at']))
    theta0, topics0 = _levels(hist_before, today)
    theta1, topics1 = _levels(hist_after, today)
    per = run['seconds'] // max(1, len(run['problems'])) if run['seconds'] else None

    first = {}
    for a in mine:
        first.setdefault(a['problem_id'], a)
    rows, by_topic = [], {}
    expected = 0.0
    for i, pid in enumerate(run['problems']):
        p = pb.get(pid)
        if not p:
            continue
        a = first.get(pid)
        if a is None:
            result = 'skipped'
        elif a.get('source') == 'reveal':
            result = 'revealed'
        else:
            result = 'right' if a['correct'] else 'wrong'
        topic = catalog.TOPIC_BY_ID[p['topic']]
        # A topic not tried before the set sits a little under the overall
        # level, as the practice picker places it.
        chance = smart.chance(topics0.get(p['topic'], theta0 - 0.3), p['rating'])
        # Expected right on what was answered: a problem left unanswered is
        # reported as such, not as a shortfall against the model.
        if result != 'skipped':
            expected += chance
        seconds = int(a.get('seconds') or 0) if a and result != 'revealed' else 0
        par = planning._par(level, theta0, p['rating'])
        rev = review_by_id.get(pid)
        prior = hist_before.get(pid)
        rows.append({
            'n': i + 1, 'id': pid, 'source': _source(pid), 'topic': p['topic'], 'topic_name': topic['name'],
            'category': topic['category'], 'technique_name': catalog.technique_name(p['technique']),
            'rating': p['rating'], 'level_of': planning.level_of(p['rating']),
            'result': result,
            'given': _answer_text(p, a['answer']) if result in ('right', 'wrong') else '',
            # A skipped problem is still open: its answer is not given away.
            'answer': _answer_text(p, p['answer']) if result != 'skipped' else '',
            'seconds': seconds, 'par': round(par),
            'slow': result == 'right' and seconds > SLOW * par,
            'over_pace': bool(per and seconds > per),
            'chance': round(chance, 2),
            'careless': result == 'wrong' and chance >= CARELESS,
            'stretch': result == 'right' and chance <= STRETCH,
            'seen_before': prior is not None,
            'before': None if prior is None else ('right' if prior['last_correct'] else 'missed'),
            'review': {'due': rev['due'], 'stage': int(rev['stage']), 'status': rev['status']}
            if rev and result in ('wrong', 'revealed') else None,
        })
        t = by_topic.setdefault(p['topic'], {'id': p['topic'], 'name': topic['name'], 'category': topic['category'],
                                             'total': 0, 'right': 0})
        t['total'] += 1
        t['right'] += result == 'right'

    t = tally(run, mine)
    n = len(rows)
    answered = t['right'] + t['wrong'] + t['revealed']
    for tid, row in by_topic.items():
        row['before'] = topics0.get(tid)
        row['after'] = topics1.get(tid)
        row['moved'] = round(row['after'] - row['before'], 2) if row['before'] is not None and \
            row['after'] is not None else None
    notes = _notes(rows, t, run, expected)
    return {
        **brief(run, mine),
        'seconds': run['seconds'], 'per_problem': per,
        'used': sum(r['seconds'] for r in rows),
        'expected': round(expected, 1),
        'verdict': _verdict(t['right'], expected, answered),
        'notes': notes,
        'problems': rows,
        'right_ids': [r['id'] for r in rows if r['result'] == 'right'],
        'missed_ids': [r['id'] for r in rows if r['result'] in ('wrong', 'revealed')],
        'skipped_ids': [r['id'] for r in rows if r['result'] == 'skipped'],
        'level': {'before': theta0, 'after': theta1, 'moved': round(theta1 - theta0, 2)},
        'topics': sorted(by_topic.values(), key=lambda r: (r['right'] / r['total'], r['name'])),
        # From everything answered so far, so it is the plan as it stands now.
        'next': _next(run, attempts, engine.history(attempts), level, goal, mocks, details, today, by_topic),
    }


def _verdict(right, expected, answered):
    """One sentence: how the answered problems went against what the model
    expected of the student on those same problems."""
    if not answered:
        return 'Nothing answered in this set yet.'
    of = '{} right of {} answered'.format(right, answered)
    gap = right - expected
    if gap >= 1:
        return 'Better than expected: {}, where your level predicts about {:.1f}.'.format(of, expected)
    if gap <= -1:
        return 'Below what you usually do: {}, where your level predicts about {:.1f}.'.format(of, expected)
    return 'About where you are: {}, and your level predicts about {:.1f}.'.format(of, expected)


def _notes(rows, t, run, expected):
    """What stands out in the set, each with what to do about it."""
    out = []
    careless = [r for r in rows if r['careless']]
    if careless:
        out.append({'kind': 'careless', 'ids': [r['id'] for r in careless],
                    'text': '{} missed that you usually get right ({}): slips, not gaps. Check each answer '
                            'before you submit.'.format(len(careless), ', '.join('#{}'.format(r['n']) for r in careless))})
    if t['revealed']:
        out.append({'kind': 'revealed', 'ids': [r['id'] for r in rows if r['result'] == 'revealed'],
                    'text': '{} solution{} shown before answering: counted as a miss and back in review. '
                            'Give each a real attempt first next time.'.format(
                                t['revealed'], '' if t['revealed'] == 1 else 's')})
    slow = [r for r in rows if r['slow']]
    if slow:
        out.append({'kind': 'slow', 'ids': [r['id'] for r in slow],
                    'text': '{} right but over twice the pace for their difficulty ({}). Timed sets build speed.'.format(
                        len(slow), ', '.join('#{}'.format(r['n']) for r in slow))})
    stretch = [r for r in rows if r['stretch']]
    if stretch:
        out.append({'kind': 'stretch', 'ids': [r['id'] for r in stretch],
                    'text': '{} right that your level gave under even odds ({}).'.format(
                        len(stretch), ', '.join('#{}'.format(r['n']) for r in stretch))})
    if t['skipped']:
        why = 'The clock ran out before' if run['time_up'] else 'Not answered:'
        out.append({'kind': 'skipped', 'ids': [r['id'] for r in rows if r['result'] == 'skipped'],
                    'text': '{} {} {}. They stay unanswered, with no answer shown, for another try.'.format(
                        why, t['skipped'], 'problem' if t['skipped'] == 1 else 'problems')})
    return out


def _next(run, attempts, hist, level, goal, mocks, details, today, by_topic):
    """What the study plan now says for the topics in this set: the kind of set each wants and why."""
    study = planning.analyze(attempts, hist, level, today, goal, details, mocks)
    rows = {r['id']: r for r in study['topics']}
    picks = []
    order = [run['topic']] if run['kind'] == 'practice' and run['topic'] else \
        [t['id'] for t in sorted(by_topic.values(), key=lambda r: (r['right'] / r['total'], -r['total']))]
    for tid in order[:3]:
        row = rows.get(tid)
        if not row:
            continue
        kind = planning.KINDS.get(row['kind']) if row['kind'] else None
        picks.append({
            'topic': tid, 'topic_name': row['name'], 'mode': row['mode'],
            'mode_title': practice.TITLES.get(row['mode'], 'Practice set'),
            'kind': row['kind'], 'kind_name': kind['name'] if kind else None,
            'approach': kind['approach'] if kind else None,
            'evidence': row['kinds'][row['kind']]['evidence'] if row['kind'] else None,
            'mastery': row['factors']['mastery'], 'answered': row['factors']['answered'],
            'mix': planning.mix_text(row['mix']),
            'rank': next(i for i, r in enumerate(study['topics'], 1) if r['id'] == tid),
            'of': len(study['topics']),
            'href': '/practice/{}?mode={}'.format(tid, row['mode']),
        })
    return picks


def by_mode(runs, attempts):
    """Accuracy by kind of set, over every set with an answer: which training
    is landing. Keys are a practice mode, or 'review' / 'weak'."""
    sets = {}
    for a in attempts:
        if a.get('set_id'):
            sets.setdefault(a['set_id'], []).append(a)
    out = {}
    for run in runs:
        mine = sets.get(run['id'])
        if not mine:
            continue
        t = tally(run, mine)
        key = run['mode'] if run['kind'] == 'practice' else run['kind']
        row = out.setdefault(key, {'id': key, 'title': title_of(run) if run['kind'] != 'practice'
                                   else practice.TITLES.get(key, 'Practice set'),
                                   'sets': 0, 'right': 0, 'answered': 0, 'dealt': 0})
        row['sets'] += 1
        row['right'] += t['right']
        row['answered'] += t['right'] + t['wrong'] + t['revealed']
        row['dealt'] += len(run['problems'])
    for row in out.values():
        row['accuracy'] = round(row['right'] / row['answered'], 3) if row['answered'] else None
    return sorted(out.values(), key=lambda r: -r['sets'])
