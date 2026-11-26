"""What the bell can say on this site: the study plan, reviews, mocks and streak milestones.

Each function returns candidates for backend/tracking/notify.py, which decides
what is new, keeps what was deleted deleted, and retires the day-scoped ones
when their day has gone. A candidate is

    {'fingerprint', 'channel', 'tone', 'title', 'body', 'link', 'for_day'?}

and its fingerprint names the situation, not the moment: 'review-due:<day>' is
one row a day however the count moves (its words are brought up to date in
place, notify.REFRESHABLE), and 'exam-soon:<date>:7' is raised once.

Everything is read off what the student has done here: their answers, their
review log, their sittings and their plan, through the same builder the plan
page uses (backend/amc/plan_view.py), so the bell and the page never disagree
about what today is for.
"""
from datetime import date, timedelta

from backend.amc import catalog, engine, plan_view, store

#: Days before the contest worth a word, and what the word is.
EXAM_SOON = {
    30: 'A timed mock every week from here.',
    14: 'Two weeks: mocks and the topics they show you missed.',
    7: 'Light review this week. Nothing new.',
    3: 'Rest counts now. A short review a day.',
    1: 'Sleep early. Bring pencils, an eraser and a watch.',
}

#: Streak lengths worth saying something about.
STREAK_MILESTONES = (3, 7, 14, 30, 50, 100, 150, 200, 365)


def _plural(n, word):
    return '{} {}{}'.format(n, word, '' if n == 1 else 's')


def _minutes(m):
    return '{} h {} min'.format(m // 60, m % 60) if m >= 60 and m % 60 else (
        '{} h'.format(m // 60) if m >= 60 else '{} min'.format(m))


def candidates(username, today, channels):
    """Every candidate for this account today, from the channels asked for."""
    attempts = store.attempts(username)
    reviews = store.reviews(username)
    plan = store.plan(username)
    out = []
    built = None
    if plan and ({'plan', 'mocks'} & set(channels)):
        hist = engine.history(attempts)
        review_by_id = {r['problem_id']: r for r in reviews}
        tstats = engine.topic_stats(hist, review_by_id)
        built = plan_view.build(plan, today, attempts, reviews, hist, tstats, store.mocks(username))
    if 'plan' in channels and built:
        out += _plan(plan, built, today)
    if 'review' in channels:
        out += _review(reviews, attempts, today)
    if 'mocks' in channels:
        out += _mocks(username, plan, built, today)
    if 'streak' in channels:
        out += _streak(attempts, today)
    return out


def _plan(plan, built, today):
    day = today.isoformat()
    out = []
    items = built['today']
    left = [i for i in items if not i['done']]
    if items and left:
        minutes = sum(i.get('minutes') or 0 for i in left)
        names = [i['label'] for i in left]
        body = '; '.join(names[:2]) + ('; and {} more.'.format(len(names) - 2) if len(names) > 2 else '.')
        out.append({'fingerprint': 'plan-today:' + day, 'channel': 'plan', 'tone': 'info', 'for_day': day,
                    'title': "Today's plan: {}".format(_minutes(minutes)), 'body': body, 'link': '/study-plan'})
    elif items:
        out.append({'fingerprint': 'plan-done:' + day, 'channel': 'plan', 'tone': 'good', 'for_day': day,
                    'title': "Today's plan is done",
                    'body': 'Everything on it is ticked off.', 'link': '/study-plan'})
    exam = date.fromisoformat(plan['exam_date'])
    left_days = (exam - today).days
    ahead = [n for n in EXAM_SOON if n >= left_days]
    if 0 < left_days <= max(EXAM_SOON) and ahead:
        mark = min(ahead)
        out.append({'fingerprint': 'exam-soon:{}:{}'.format(exam.isoformat(), mark), 'channel': 'plan',
                    'tone': 'warn' if left_days <= 7 else 'info',
                    'title': 'The {} is {}'.format(plan['target'], 'tomorrow' if left_days == 1
                                                   else 'in {}'.format(_plural(left_days, 'day'))),
                    'body': EXAM_SOON[mark], 'link': '/study-plan'})
    return out


def _review(reviews, attempts, today):
    day = today.isoformat()
    due = sum(1 for r in reviews if r['status'] == 'active' and r['due'] <= day)
    if not due:
        return []
    # Today's set, never the backlog: a count of every miss waiting is pressure
    # to clear them all, and reviews come a set at a time.
    size = min(due, engine.REVIEW_SET)
    return [{'fingerprint': 'review-due:' + day, 'channel': 'review', 'tone': 'info', 'for_day': day,
             'title': "Today's review set: {}".format(_plural(size, 'problem')),
             'body': 'Weakest topics first. One set a day is enough.', 'link': '/review?start=1'}]


def _mocks(username, plan, built, today):
    out = []
    # This week's mock, once its day has come and it is still not sat.
    if built:
        week = next((w for w in built['weeks'] if w['current']), None)
        if week and week.get('mock') and not week.get('mock_done'):
            mock_day = next((d['date'] for d in week.get('days') or []
                             if any(b['kind'] == 'mock' for b in d['blocks'])), None)
            if mock_day and mock_day <= today.isoformat():
                minutes = engine.MOCK_MINUTES.get(plan['target'], 75)
                out.append({'fingerprint': 'mock-week:' + week['start'], 'channel': 'mocks', 'tone': 'info',
                            'for_day': week['end'], 'title': "This week's mock is still to sit",
                            'body': 'A full {}, {} minutes on the clock.'.format(plan['target'], minutes),
                            'link': '/mock-contests'})
    # A new best on a mock sat more than once.
    sittings = [m for m in store.mocks(username) if m['kind'] == 'mock']     # newest first
    by_contest = {}
    for m in sittings:
        by_contest.setdefault(m['contest_id'], []).append(m)
    for contest_id, rows in by_contest.items():
        latest, earlier = rows[0], rows[1:]
        if earlier and latest['score'] > max(r['score'] for r in earlier):
            found = catalog.contest(contest_id)
            name = found['name'] if found else contest_id
            out.append({'fingerprint': 'mock-best:' + latest['id'], 'channel': 'mocks', 'tone': 'good',
                        'title': 'New best on {}: {:g}'.format(name, latest['score']),
                        'body': 'Up from {:g}.'.format(max(r['score'] for r in earlier)),
                        'link': '/mocks/' + latest['id']})
    return out


def _streak(attempts, today):
    """Only a streak's milestones (3, 7, 14, 30 days...), each once.

    There is no daily "your streak needs a problem today": a reminder every
    day is pressure to answer something for the count rather than to study,
    and it turned the bell into a nag. A reminder already up from an older
    build is withdrawn by the next sweep (backend/tracking/notify.py), since
    nothing raises it any more."""
    day = today.isoformat()
    streak = engine.streak(attempts, today)
    answered_today = any(a['at'][:10] == day for a in attempts)
    out = []
    if streak in STREAK_MILESTONES:
        began = (today - timedelta(days=streak - (1 if answered_today else 0))).isoformat()
        out.append({'fingerprint': 'streak-milestone:{}:{}'.format(streak, began), 'channel': 'streak',
                    'tone': 'good', 'title': '{} days in a row'.format(streak),
                    'body': 'A problem a day, {} days running.'.format(streak), 'link': '/analytics'})
    return out
