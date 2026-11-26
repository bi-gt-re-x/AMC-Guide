"""The study plan as the pages and the bell see it: its weeks and days, today's
checklist, and what they were built from.

One builder for the study plan page, the dashboard and the notifications
(backend/tracking/notify.py), so all three name the same focus topic and the
same set for the same day.
"""
from datetime import timedelta

from backend.amc import consistency, engine, mockscore, planning


def build(plan, today, attempts, reviews, hist, tstats, every_score):
    """The weeks, today's checklist and what they were built from.

    One builder for the study plan page and the dashboard: the dashboard used
    to lay the weeks out by an older rule of its own, so its Today list could
    name a different focus topic from the plan's for the same day."""
    mocks = [m for m in every_score if m['kind'] == 'mock']
    # Mock mistakes weigh in the priorities, so the weeks target them.
    study = planning.analyze(attempts, hist, plan['target'], today, plan['goal_score'], plan['details'],
                             mocks=every_score)
    model = engine.projected(hist, plan['target']) if len(hist) >= engine.PROJECTION_MIN else None
    # Where the student starts against the goal, from their scores and answers;
    # it sets the plan's shape (more skills when far, more papers when close).
    start = planning.starting_point(plan['target'], plan['goal_score'], model, every_score,
                                    {**plan['details'], '_exam': plan['exam_date']}, today)
    # How often the plan has been kept sizes the days ahead.
    kept = consistency.read(plan, attempts, today)
    weeks = engine.plan_weeks({**plan, 'load': kept['load']}, tstats, mocks, today, study['topics'], start['stage'])
    # How much of each week's practice has been done: distinct problems
    # answered (not solutions looked at) between its Monday and Sunday.
    answered = {}
    for a in attempts:
        if a.get('source') != 'reveal':
            answered.setdefault(a['at'][:10], set()).add(a['problem_id'])
    for w in weeks:
        if w['past'] or w['current']:
            done = set()
            for day, ids in answered.items():
                if w['start'] <= day <= w['end']:
                    done |= ids
            w['answered'] = len(done)
    due = sum(1 for r in reviews if r['status'] == 'active' and r['due'] <= today.isoformat())
    practiced = {a['problem_id'] for a in attempts
                 if a['at'][:10] == today.isoformat() and a['source'] == 'practice'}
    reviewed = len({a['problem_id'] for a in attempts
                    if a['at'][:10] == today.isoformat() and a['source'] == 'review'})
    items = engine.today_items(plan, weeks, due, today, plan['checks'], practiced, reviewed)
    projected_now = mockscore.projected_score(hist, plan['target'], every_score, today)
    done_today = (plan.get('days_done') or {}).get(today.isoformat())
    return {'study': study, 'projected': projected_now, 'start': start, 'weeks': weeks, 'today': items,
            'level': level_now(study, attempts, weeks, today), 'consistency': kept,
            'day': {'date': today.isoformat(), 'complete': bool(done_today),
                    'completed_at': done_today['completed_at'] if done_today else None,
                    # Every item ticked: the day can be marked complete.
                    'ready': bool(items) and all(i['done'] for i in items)}}


def level_now(study, attempts, weeks, today):
    """Where the student is working now, which the plan is built from: their
    level on the five-step difficulty scale (from every answer), what their goal
    needs, the last two weeks' answers against the two before, and their pace
    against the plan's weekly target."""
    def window(days_from, days_to):
        lo = (today - timedelta(days=days_to)).isoformat()
        hi = (today - timedelta(days=days_from)).isoformat()
        rows = [a for a in attempts if lo < a['at'][:10] <= hi]
        right = sum(1 for a in rows if a['correct'] and a.get('source') != 'reveal')
        return {'answered': len(rows), 'right': right,
                'accuracy': round(right / len(rows), 3) if rows else None}
    level = planning.level_of(study['theta'])
    info = planning.LEVELS[level - 1]
    goal = planning.LEVELS[max(1, min(5, study['ceiling'])) - 1]
    recent, before = window(0, 14), window(14, 28)
    done = [w for w in weeks if w['past'] and w['problems']][-2:]
    pace = {'per_week': round(sum(w.get('answered', 0) for w in done) / len(done), 1),
            'planned': done[-1]['problems']} if done else None
    return {'level': level, 'name': info['name'], 'means': info['means'], 'measured': len({a['problem_id'] for a in attempts}),
            'goal_level': goal['level'], 'goal_name': goal['name'], 'mix': study['mix'],
            'recent': recent, 'before': before, 'pace': pace}
