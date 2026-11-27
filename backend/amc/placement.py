"""The placement check: twelve problems at sign-up, so the level, the study
plan and the first practice sets are the student's own from the first day
instead of starting from nothing.

It is short and quiet on purpose. Twelve problems, each one picked where the
student's estimated level is after the answers so far (a small adaptive
test, on the same 1-12 scale and the same ability model as the rest of the
site, backend/amc/smart.py), turning through algebra, counting, number theory
and geometry so every subject gets a look. Only short problems with no
diagram are used, nothing is timed, nothing is marked right or wrong as it
goes, and "Not sure" is always an answer: a blank, which says as much about
the level as a wrong answer does. It can be stopped at any point; what was
answered still counts.

The answers are written as ordinary attempts (source 'practice', a blank as
an empty answer), so the level, the projected score, the topic estimates and
the study plan all read them with everything else. They are not put in the
review log: a placement problem above the level is a measurement, not a
mistake to go back over. The check itself (which problems were dealt, the
answers, the estimate) is one row in amc_placements (data/sql/amc.sql).
"""
import hashlib

from backend.amc import catalog, engine, smart
from backend.amc.bank import PROBLEMS as BANK
from backend.amc.scale import RATING_BY_NUMBER, to_scale

SIZE = 12
#: Below this many answers a check stopped early says nothing about the level.
MIN_FOR_RESULT = 4
#: Where the first problem is pitched, by contest, on the 1-12 scale: a typical
#: student starting out on that contest. Also the prior's centre.
START = {'AMC 10': 4.0, 'AMC 12': 4.5, 'AIME': 6.5}
#: The ratings a check may deal, by contest.
SPAN = {'AMC 10': (2.0, 8.0), 'AMC 12': (2.0, 9.0), 'AIME': (3.0, 11.0)}
#: Problems from these contests, the first preferred.
FROM = {'AMC 10': ('AMC 10',), 'AMC 12': ('AMC 12', 'AMC 10'), 'AIME': ('AIME', 'AMC 12')}
#: The subjects, in the order the problems turn through them.
SUBJECTS = ('algebra', 'counting', 'number-theory', 'geometry')
#: How wide the prior is: narrower than the site's (smart.PRIOR_SD), since the
#: start is already pitched at the contest, so twelve answers settle it.
PRIOR_SD = 2.0
#: Short problems only: a placement check is a quick look, not a contest.
MAX_CHARS = 380


def _short(p):
    return len(engine.plain(p['statement'])) <= MAX_CHARS


def pool(level):
    """The problems a `level` check can deal: rated, written out with a
    solution, no diagram, short, in the contest's range."""
    lo, hi = SPAN[level]
    return [p for p in BANK
            if p['level'] in FROM[level] and p.get('rating') is not None and lo <= p['rating'] <= hi
            and not p.get('diagram') and p.get('solution') and _short(p)]


def estimate(level, answers):
    """(theta, standard error) from the answers so far: [{'id', 'correct', ...}]."""
    points = []
    for a in answers:
        p = _problem(a['id'])
        if p:
            points.append((p['rating'], bool(a['correct'])))
    return smart.fit(points, mean=START[level], sd=PRIOR_SD)


def _problem(pid):
    from backend.amc import problems as pb
    return pb.get(pid)


def _subject(p):
    return catalog.TOPIC_BY_ID[p['topic']]['category']


def next_problem(level, answers, seen, seed=''):
    """The next problem's id, or None once the check is done.

    Pitched a little above the current estimate (a problem there says the
    most), in the subject whose turn it is, never one dealt already or one
    the account has answered before. Ties go the same way for the same
    account, so a refresh does not reshuffle the check."""
    if len(answers) >= SIZE:
        return None
    theta = estimate(level, answers)[0] if answers else START[level]
    lo, hi = SPAN[level]
    target = max(lo, min(hi, theta + 0.25))
    subject = SUBJECTS[len(answers) % len(SUBJECTS)]
    dealt = {a['id'] for a in answers}
    candidates = [p for p in pool(level) if p['id'] not in dealt and p['id'] not in seen]
    mine = [p for p in candidates if _subject(p) == subject] or candidates
    if not mine:
        return None

    def rank(p):
        tie = hashlib.sha1('{}:{}'.format(seed, p['id']).encode()).hexdigest()
        return (round(abs(p['rating'] - target) * 2) / 2, FROM[level].index(p['level']), tie)
    return min(mine, key=rank)['id']


def _reach(level, theta):
    """The last problem number on a typical `level` paper the student is more
    likely than not to get right."""
    reach = 0
    for number, aops in enumerate(RATING_BY_NUMBER[level], start=1):
        if smart.chance(theta, to_scale(aops)) >= 0.5:
            reach = number
    return reach


def result(level, answers):
    """What the check found, or None when too little was answered to say."""
    tried = [a for a in answers if _problem(a['id'])]
    if len(tried) < MIN_FOR_RESULT:
        return None
    theta, se = estimate(level, tried)
    right = sum(1 for a in tried if a['correct'])
    by_subject = {}
    for a in tried:
        sub = _subject(_problem(a['id']))
        row = by_subject.setdefault(sub, {'id': sub, 'name': catalog.CATEGORY_BY_ID[sub]['name'], 'right': 0, 'total': 0})
        row['total'] += 1
        row['right'] += 1 if a['correct'] else 0
    reach = _reach(level, theta)
    level_shown = round(max(1.0, min(12.0, theta)) * 2) / 2
    if reach:
        where = 'most problems up to about #{} of an {}'.format(reach, level)
    else:
        where = 'the first problems of an {} are the place to start'.format(level)
    strong = [r for r in by_subject.values() if r['total'] >= 2 and r['right'] == r['total']]
    weak = sorted((r for r in by_subject.values() if r['total'] >= 2 and r['right'] * 2 < r['total']),
                  key=lambda r: r['right'] / r['total'])
    return {
        'theta': theta, 'se': se, 'level': level_shown, 'right': right, 'answered': len(tried),
        'blank': sum(1 for a in tried if not a.get('answer')),
        'reach': reach, 'contest': level,
        'subjects': sorted(by_subject.values(), key=lambda r: SUBJECTS.index(r['id']) if r['id'] in SUBJECTS else 9),
        # No score in the sentence: on this site a projected score comes from a
        # timed sitting (backend/amc/mockscore.py), never from practice alone.
        'summary': 'You’re at about {:g} on the 1–12 scale{}.'.format(
            level_shown, ': you’d get ' + where if reach else '. ' + where[0].upper() + where[1:]),
        'strongest': strong[0]['name'] if strong else None,
        'weakest': weak[0]['name'] if weak else None,
    }


def view(row, level=None):
    """The check as the page shows it: the problem to answer now (without its
    answer), how far along, and once done, what it found."""
    if not row:
        return None
    answers = row['answers']
    pid = row.get('next_id') or ''
    p = _problem(pid) if pid and not row.get('finished_at') else None
    return {
        'level': row['level'], 'answered': len(answers), 'total': SIZE,
        'problem': _public(p) if p else None,
        'done': bool(row.get('finished_at')),
        'result': result(row['level'], answers) if row.get('finished_at') else None,
    }


def _public(p):
    """A dealt problem without what would give it away: no answer, no
    solution, and not its paper or number either (a "#24" says "hard")."""
    out = engine.public(p, reveal=False)
    for key in ('sources', 'aops', 'aops_url', 'difficulty', 'rating', 'technique', 'technique_name', 'also'):
        out.pop(key, None)
    return out


def offer(row, attempts):
    """Whether to suggest the check: never taken, or begun and not finished,
    by an account that has not answered much yet."""
    if row and row.get('finished_at'):
        return False
    return len({a['problem_id'] for a in attempts}) < 20
