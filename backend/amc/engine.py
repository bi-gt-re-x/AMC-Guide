"""The rules: grading, the review schedule, scores, projections, the study
plan and search. Pure functions over catalog content and an account's rows
(store.py), so every rule can be tested without a database.
"""
import re
from datetime import date, timedelta

from backend.amc import catalog
from backend.amc import problems as bank_of

LETTERS = 'ABCDE'

#: Days until a missed problem comes back, by stage. Passing the last one
#: marks it mastered.
INTERVALS = [3, 10, 21]

#: Default goals: the AIME qualifying score, which from the 2026-27 contests
#: is fixed at 100 on the AMC 10 and 85 on the AMC 12 (it used to move every
#: year with the score distribution), and a solid AIME score.
DEFAULT_GOALS = {'AMC 10': 100, 'AMC 12': 85, 'AIME': 7}

#: Problems answered before a projected score is shown at all.
PROJECTION_MIN = 5


# ---------------------------------------------------------------------------
# Grading and presenting problems
# ---------------------------------------------------------------------------
def normalize_answer(problem, answer):
    """The canonical form of a submitted answer, or '' for a blank."""
    text = str(answer if answer is not None else '').strip()
    if not text:
        return ''
    if problem['choices']:
        letter = text[:1].upper()
        return letter if letter in LETTERS else ''
    digits = re.sub(r'[^0-9]', '', text)
    return str(int(digits)) if digits else ''


def is_correct(problem, answer):
    given = normalize_answer(problem, answer)
    return given != '' and given == str(problem['answer'])


_SYMBOLS = {
    'le': '≤', 'leq': '≤', 'ge': '≥', 'geq': '≥', 'ne': '≠', 'neq': '≠', 'cdot': '·', 'times': '×',
    'pi': 'π', 'theta': 'θ', 'omega': 'ω', 'varphi': 'φ', 'ldots': '…', 'dots': '…', 'cdots': '⋯',
    'infty': '∞', 'circ': '°', 'sum': 'Σ', 'displaystyle': '', 'left': '', 'right': '', 'lfloor': '⌊', 'rfloor': '⌋', 'pm': '±', 'equiv': '≡', 'angle': '∠', 'triangle': '△',
}
_SUPERSCRIPT = str.maketrans('0123456789+-n', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ')
_SUBSCRIPT = str.maketrans('0123456789+-nk', '₀₁₂₃₄₅₆₇₈₉₊₋ₙₖ')
_DIGITS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉₊₋ₙₖ', '0123456789+-n0123456789+-nk')


_OPERATORS = {'sin', 'cos', 'tan', 'log', 'ln', 'gcd', 'lcm', 'max', 'min', 'operatorname', 'mathrm', 'bmod', 'pmod'}


def plain(text):
    """Statement text with the TeX turned into readable plain text, for search
    and one-line previews: `$n \\le 100$` reads "n ≤ 100", `x^2` reads "x²",
    `a_{10}` reads "a₁₀" and `150^{\\circ}` reads "150°"."""
    text = text.replace('\\$', '\x00').replace('\\%', '%').replace('\\{', '\x01').replace('\\}', '\x02')
    text = re.sub(r'\\[,;:! ]', '', text)
    text = re.sub(r'\^\{?\\circ\}?', '°', text)
    text = re.sub(r'_\{([0-9nk+-]{1,4})\}', lambda m: m.group(1).translate(_SUBSCRIPT), text)
    text = re.sub(r'_([0-9nk])', lambda m: m.group(1).translate(_SUBSCRIPT), text)
    text = re.sub(r'\^\{(-?[0-9n]{1,4})\}', lambda m: m.group(1).translate(_SUPERSCRIPT), text)
    text = re.sub(r'\^([0-9n])', lambda m: m.group(1).translate(_SUPERSCRIPT), text)
    for _ in range(2):  # a fraction inside a fraction
        text = re.sub(r'\\(?:dfrac|frac|tfrac)\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', text)
    text = re.sub(r'\(([A-Za-z0-9.]+)\)/', r'\1/', text)
    text = re.sub(r'/\(([A-Za-z0-9.]+)\)', r'/\1', text)
    text = re.sub(r'\\sqrt\{([^{}]*)\}', r'√\1', text)
    text = re.sub(r'\\([a-zA-Z]+)',
                  lambda m: _SYMBOLS.get(m.group(1)) or (m.group(1) + ' ' if m.group(1) in _OPERATORS else ' '),
                  text)
    text = re.sub(r'[{}\\_$]', '', text)
    text = text.replace('\x00', '$').replace('\x01', '{').replace('\x02', '}')
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'\s([,.?])', r'\1', text)


def public(problem, reveal=False):
    """A problem as the client sees it. The answer and write-up only once the
    account has answered it (or asked to see it)."""
    topic = catalog.TOPIC_BY_ID[problem['topic']]
    out = {
        'id': problem['id'],
        'level': problem['level'],
        'topic': topic['id'],
        'topic_name': topic['name'],
        'category': topic['category'],
        'category_name': catalog.CATEGORY_BY_ID[topic['category']]['name'],
        'also': [{'id': t, 'name': catalog.TOPIC_BY_ID[t]['name']} for t in problem['also']],
        'technique': problem['technique'],
        'technique_name': catalog.technique_name(problem['technique']),
        'difficulty': problem['difficulty'],
        'rating': problem.get('rating'),
        'aops': problem.get('aops'),
        'statement': problem['statement'],
        'choices': problem['choices'],
        'format': 'choice' if problem['choices'] else 'integer',
        'sources': catalog.sources(problem['id']),
        'official': bool(problem.get('official')),
        'diagram': problem.get('diagram') or '',
        'aops_url': problem.get('aops_url'),
        'ai': bool(problem.get('ai')),
        'has_solution': bool(problem.get('solution')),
    }
    if reveal:
        out.update(answer=problem['answer'], solution=problem['solution'],
                   insight=problem['insight'], trap=problem['trap'])
    return out


# ---------------------------------------------------------------------------
# An account's history
# ---------------------------------------------------------------------------
def history(attempts):
    """Per problem: attempts, first result, latest result, ever solved."""
    out = {}
    for row in attempts:
        pid = row['problem_id']
        h = out.setdefault(pid, {'attempts': 0, 'first_correct': bool(row['correct']),
                                 'first_at': row['at'], 'first_seconds': int(row.get('seconds') or 0),
                                 'first_source': row.get('source') or '',
                                 'solved': False, 'last_correct': False, 'last_at': '',
                                 'seconds': 0})
        h['attempts'] += 1
        h['solved'] = h['solved'] or bool(row['correct'])
        h['last_correct'] = bool(row['correct'])
        h['last_at'] = row['at']
        h['seconds'] += int(row.get('seconds') or 0)
    return out


def status_of(pid, hist, review_by_id):
    """'review' (in the error log), 'solved', 'missed' or 'new'."""
    rev = review_by_id.get(pid)
    if rev and rev['status'] == 'active':
        return 'review'
    h = hist.get(pid)
    if not h:
        return 'new'
    return 'solved' if h['solved'] else 'missed'


def streak(attempts, today):
    """Days in a row with at least one answer, ending today or yesterday."""
    days = {row['at'][:10] for row in attempts}
    cursor = today if today.isoformat() in days else today - timedelta(days=1)
    count = 0
    while cursor.isoformat() in days:
        count += 1
        cursor -= timedelta(days=1)
    return count


def projected(hist, level, today=None):
    """Expected score on a contest at `level`, from the ability model in
    backend/amc/smart.py, with the best answer-or-skip choice on each problem.

    The same number the Analytics page predicts: there is one model of the
    student, not one per page.
    """
    from backend.amc import smart
    return smart.projected(hist, level, today)


def topic_stats(hist, review_by_id):
    """Per topic: problems, attempted, solved, first-try accuracy, in review."""
    out = {t['id']: {'problems': 0, 'attempted': 0, 'solved': 0, 'first_right': 0, 'review': 0}
           for t in catalog.TOPICS}
    for p in bank_of.all_problems():
        for tid in [p['topic']] + p['also']:
            row = out[tid]
            row['problems'] += 1
            h = hist.get(p['id'])
            if h:
                row['attempted'] += 1
                row['solved'] += 1 if h['solved'] else 0
                row['first_right'] += 1 if h['first_correct'] else 0
            rev = review_by_id.get(p['id'])
            if rev and rev['status'] == 'active':
                row['review'] += 1
    for row in out.values():
        row['accuracy'] = round(row['first_right'] / row['attempted'], 3) if row['attempted'] else None
        # 0-1: the share of the topic's problems solved first time. Unseen
        # problems count as not yet in hand, so one lucky answer is not mastery.
        row['mastery'] = round(row['first_right'] / row['problems'], 3) if row['problems'] else 0
    return out


def category_stats(tstats):
    out = []
    for cat in catalog.CATEGORIES:
        rows = [tstats[t['id']] for t in catalog.TOPICS if t['category'] == cat['id']]
        attempted = sum(r['attempted'] for r in rows)
        right = sum(r['first_right'] for r in rows)
        out.append({**cat, 'problems': sum(r['problems'] for r in rows), 'attempted': attempted,
                    'solved': sum(r['solved'] for r in rows),
                    'accuracy': round(right / attempted, 3) if attempted else None})
    return out


# ---------------------------------------------------------------------------
# The review schedule
# ---------------------------------------------------------------------------
def after_answer(existing, problem_id, correct, today, manual=False):
    """The review row after an answer, or None when it does not change.

    Wrong: into the log (or back to the start of it), due in 3 days.
    Right on a due review: up a stage; past the last stage, mastered.
    Right any other time: no change — reviewing early does not count.
    """
    if manual:
        if existing and existing['status'] == 'active':
            return None
        return {'problem_id': problem_id, 'stage': 0, 'due': today.isoformat(), 'status': 'active',
                'note': (existing or {}).get('note', ''), 'misses': (existing or {}).get('misses', 0),
                'added_at': (existing or {}).get('added_at')}
    if not correct:
        return {'problem_id': problem_id, 'stage': 0,
                'due': (today + timedelta(days=INTERVALS[0])).isoformat(), 'status': 'active',
                'note': (existing or {}).get('note', ''),
                'misses': int((existing or {}).get('misses') or 0) + 1,
                'added_at': (existing or {}).get('added_at')}
    if not existing or existing['status'] != 'active' or existing['due'] > today.isoformat():
        return None
    stage = int(existing['stage']) + 1
    if stage >= len(INTERVALS):
        return {**existing, 'stage': len(INTERVALS), 'status': 'mastered'}
    return {**existing, 'stage': stage, 'due': (today + timedelta(days=INTERVALS[stage])).isoformat()}


# ---------------------------------------------------------------------------
# Contests
# ---------------------------------------------------------------------------
def score_mock(mock, answers):
    """Grade a mock. `answers` maps "1".."25" to a letter/integer or ''."""
    level = mock['level']
    rows = []
    correct = wrong = blank = 0
    for number, pid in enumerate(mock['problems'], start=1):
        problem = bank_of.get(pid)
        given = normalize_answer(problem, answers.get(str(number), ''))
        if given == '':
            result = 'blank'
            blank += 1
        elif given == str(problem['answer']):
            result = 'correct'
            correct += 1
        else:
            result = 'wrong'
            wrong += 1
        rows.append({'number': number, 'problem_id': pid, 'given': given,
                     'answer': problem['answer'], 'result': result,
                     'topic': problem['topic'], 'difficulty': problem['difficulty']})
    score = correct if level == 'AIME' else correct * 6 + blank * 1.5
    return {'score': score, 'correct': correct, 'wrong': wrong, 'blank': blank, 'rows': rows}


def mock_report(mock, graded):
    """Where the points went: by topic, and by fifth of the paper."""
    full = 1 if mock['level'] == 'AIME' else 6
    blank_pts = 0 if mock['level'] == 'AIME' else 1.5
    by_topic = {}
    for row in graded['rows']:
        t = by_topic.setdefault(row['topic'], {'topic': row['topic'],
                                               'name': catalog.TOPIC_BY_ID[row['topic']]['name'],
                                               'total': 0, 'correct': 0, 'lost': 0})
        t['total'] += 1
        if row['result'] == 'correct':
            t['correct'] += 1
        else:
            t['lost'] += full - (blank_pts if row['result'] == 'blank' else 0)
    size = 5 if mock['level'] != 'AIME' else 3
    bands = []
    for start in range(0, len(graded['rows']), size):
        chunk = graded['rows'][start:start + size]
        lost = sum(full - (blank_pts if r['result'] == 'blank' else 0) for r in chunk if r['result'] != 'correct')
        bands.append({'label': '#{}-{}'.format(start + 1, start + len(chunk)),
                      'correct': sum(1 for r in chunk if r['result'] == 'correct'),
                      'total': len(chunk), 'lost': lost})
    topics = sorted(by_topic.values(), key=lambda t: (-t['lost'], t['name']))
    return {'topics': topics, 'bands': bands}


# ---------------------------------------------------------------------------
# The study plan
# ---------------------------------------------------------------------------
def _monday(day):
    return day - timedelta(days=day.weekday())


def plan_weeks(settings, tstats, mocks_taken, today, priorities=None, stage=None):
    """The week-by-week plan from the week it was made to the exam.

    Phases: Foundations (first ~40%), Core (~35%), Contest mode (the rest),
    and a taper in the exam's own week, with a mock every third week of Core
    and every week of Contest mode.

    The weeks run from the plan's own start (`created_at`), not from today:
    laid out from today, every visit made a new plan whose first 40% was
    Foundations, so a student never left Foundations until the last few weeks.
    Weeks already gone keep their place (and their progress, which the caller
    adds) with no focus of their own; the focus from this week on is worked
    out again from the latest results each time, as are the phase lengths
    (from how far the student now is from the goal, `stage`).

    With `priorities` (backend/amc/planning.py `analyze`), each week takes the
    two topics worth the most expected points still to be had, a topic's value
    shrinking once scheduled so the most valuable come back spaced out; each
    carries how to train it (`mode`, from its kind of weakness). Without, the
    older rule: how often a topic appears times how much is not yet in hand.
    """
    from backend.amc import planning as _planning
    exam = date.fromisoformat(settings['exam_date'])
    level = settings['target']
    start = _monday(today)
    try:
        made = _monday(date.fromisoformat(str(settings.get('created_at') or '')[:10]))
        start = min(start, made)
    except ValueError:
        pass
    last = _monday(exam)
    count = max(1, (last - start).days // 7 + 1)
    # The week this is: the plan's focus is laid out from here on.
    now = max(0, min(count - 1, (_monday(today) - start).days // 7))

    relevant = [t for t in catalog.TOPICS if level in t['levels']]

    def priority(t):
        s = tstats[t['id']]
        known = (s['first_right'] / s['problems']) if s['problems'] else 0
        return t['weight'] * (1.05 - known)

    ranked = sorted(relevant, key=lambda t: (-priority(t), t['name']))
    # The AI coach's order, when there is one, goes first: it has heard what
    # the arithmetic cannot (backend/amc/coach.py). Topics it left out follow
    # in the usual order.
    coached = (settings.get('coach') or {}).get('focus_order') or []
    # ...unless the answers since say the student has it: a topic the coach
    # put first that is now right first time 80% of the time stops leading.
    coached = [tid for tid in coached
               if not (tstats.get(tid, {}).get('attempted', 0) >= _planning.CLEARED_MIN
                       and tstats[tid]['first_right'] / tstats[tid]['attempted'] >= 0.8)]
    if coached:
        first = [t for tid in coached for t in relevant if t['id'] == tid]
        ranked = first + [t for t in ranked if t not in first]
    schedule = None
    if priorities:
        schedule = _planning.schedule(priorities, count - now, coached=coached)
    # How far the student is from the goal sets the plan's shape: far below it,
    # more weeks on skills; at it already, more under exam conditions
    # (backend/amc/planning.py SHAPES, from `starting_point`).
    shape = _planning.SHAPES.get(stage or 'unknown', _planning.SHAPES['unknown'])
    foundations = max(1, round(count * shape['foundations'])) if count >= 4 else 0
    core = max(1, round(count * shape['core'])) if count >= 3 else 0
    # About ten minutes a problem, but no more than a set of eight on each day
    # the student said they study: six hours over two days is not 36 problems.
    per_week = max(5, int(settings['hours']) * 6)
    days = (settings.get('details') or {}).get('days_per_week')
    if days:
        per_week = max(5, min(per_week, int(days) * 8))
    taken = {m['at'][:10] for m in mocks_taken}
    visits = {}

    weeks = []
    cursor = 0
    for i in range(count):
        week_start = start + timedelta(days=7 * i)
        if i == count - 1:
            phase = 'Taper'
        elif i < foundations:
            phase = 'Foundations'
        elif i < foundations + core:
            phase = 'Core'
        else:
            phase = 'Contest mode'
        if phase == 'Taper' or i < now:
            focus = []
        elif schedule is not None:
            focus = schedule[i - now]
        else:
            focus = [ranked[(cursor + k) % len(ranked)] for k in range(2)] if ranked else []
            cursor += 2
        # Each return to a topic trains it a step further along, and the later
        # phases at contest pace (planning.week_mode).
        modes = []
        for t in focus:
            modes.append(_planning.week_mode(t, phase, visits.get(t['id'], 0)))
            visits[t['id']] = visits.get(t['id'], 0) + 1
        every = shape['core_mock_every']
        mock = phase == 'Contest mode' or (phase == 'Core' and (i - foundations) % every == every - 1)
        week_end = week_start + timedelta(days=6)
        mock_done = any(week_start.isoformat() <= d <= week_end.isoformat() for d in taken)
        notes = {
            'Done': 'Gone by.',
            'Foundations': 'Learn each focus topic, then do its easier problems untimed.',
            'Core': 'Focus topics plus review. Aim for under 3 minutes on #1-15.',
            'Contest mode': 'One timed mock, then work on what you missed.',
            'Taper': 'Light review only. Nothing new. Sleep well.',
        }
        weeks.append({
            'number': i + 1, 'start': week_start.isoformat(), 'end': week_end.isoformat(),
            'phase': phase, 'note': notes['Done' if i < now else phase],
            'focus': [{'id': t['id'], 'name': t['name'], 'category': t['category'],
                       'mode': mode, 'mode_label': _planning.MODE_LABEL[mode],
                       'gain': t.get('gain'), 'mix': t.get('mix'), 'reason': _reason(t)}
                      for t, mode in zip(focus, modes)],
            'problems': 0 if phase == 'Taper' else per_week,
            'mock': mock, 'mock_done': mock and mock_done,
            'current': week_start <= today <= week_end,
            'past': week_end < today,
        })
    # Each week as seven days, sized to the time the student has a day; the
    # week's problem count is what its days hold.
    weekdays, minutes = study_schedule(settings)
    for w in weeks:
        w['days'] = week_days(w, weekdays, minutes, level, today)
        if w['phase'] != 'Taper':
            w['problems'] = sum(b.get('count', 0) for d in w['days'] for b in d['blocks']
                                if b['kind'] in ('practice', 'challenge'))
    return weeks


# ---------------------------------------------------------------------------
# Days: each week as seven, sized to the time the student has
# ---------------------------------------------------------------------------
#: Which weekdays a student studies, by how many days a week they study
#: (Monday is 0): Saturday, Tuesday and Thursday first, so the rest days fall
#: on Friday and midweek before they reach a weekend.
STUDY_ORDER = (5, 1, 3, 6, 0, 2, 4)
WEEKDAY = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

#: Minutes a problem takes in a plan: on the clock, and untimed (time to check).
PACE = {'AMC 10': 3, 'AMC 12': 3, 'AIME': 12}
UNTIMED_EXTRA = 2
#: A challenge problem gets half as long again (backend/amc/practice.py).
CHALLENGE_PACE = 1.5
MOCK_MINUTES = {'AMC 10': 75, 'AMC 12': 75, 'AIME': 180}
#: The fewest and most problems a day's set holds; a challenge set holds up to five.
SET_RANGE = (3, 8)
CHALLENGE_MAX = 5


def study_schedule(settings):
    """(the weekdays studied, minutes on each), from the plan's hours a week
    and, if given, days a week. Without days, about an hour a day: two to six."""
    hours = max(1, int(settings.get('hours') or 1))
    days = (settings.get('details') or {}).get('days_per_week')
    n = max(1, min(7, int(days) if days else min(6, max(2, hours))))
    minutes = max(15, int(round(hours * 60 / n / 5.0)) * 5)
    return tuple(sorted(STUDY_ORDER[:n])), minutes


def _fit(minutes, per, top):
    """How many problems at `per` minutes fit in `minutes`, within SET_RANGE and `top`."""
    return max(SET_RANGE[0], min(top, int(minutes // per)))


def _set_block(topic, mode, n, per, kind='practice'):
    tid, name = topic['id'], topic['name']
    timed = mode in ('timed', 'challenge')
    if kind == 'challenge':
        label, detail = 'Challenge set: ' + name, '{} harder problems, {:g} minutes each on the clock.'.format(n, per)
    else:
        label = '{}: {}'.format(SET_TITLE.get(mode, 'Practice set'), name)
        detail = '{} problems, {}.'.format(n, '{:g} minutes each, on one clock'.format(per) if timed else {
            'learn': 'easiest first, no clock', 'accuracy': 'no clock, check each answer',
            'mixed': 'topic hidden', 'spaced': 'ones you have seen before'}.get(mode, 'no clock'))
    levels = sorted({c['level'] for c in (topic.get('mix') or []) if c.get('share')})
    if levels and kind != 'challenge':
        detail = detail[:-1] + ', ' + ('level {}'.format(levels[0]) if len(levels) == 1
                                       else 'levels {}–{}'.format(levels[0], levels[-1])) + '.'
    if topic.get('reason'):
        detail += ' ' + topic['reason']
    return {'kind': kind, 'label': label, 'detail': detail, 'minutes': int(round(n * per)), 'count': n,
            'mode': mode, 'topic': tid, 'name': name, 'to': '/practice/{}?mode={}&n={}'.format(tid, mode, n)}


def _study_day(week, minutes, k, level, challenge, mock_here, read):
    """What one study day holds, in order, within `minutes`.

    A mock day is the mock and going over it. The taper is light reading and
    review. Otherwise: a short review set, then a set in one of the week's
    focus topics (the two take turns down the week), its key ideas first while
    it is still being learned, and a second set in the other topic if the
    time runs to it. One day a week the set is a challenge set: fewer, harder
    problems on a longer clock."""
    pace = PACE.get(level, 3)
    if mock_here:
        mock = MOCK_MINUTES.get(level, 75)
        blocks = [{'kind': 'mock', 'label': 'Timed mock: a full {}'.format(level),
                   'detail': 'One sitting, on the clock, as on the day.', 'minutes': mock, 'to': '/mock-contests'}]
        if minutes - mock >= 15:
            blocks.append({'kind': 'review', 'label': 'Go over the mock',
                           'detail': 'Each problem you missed or guessed, with its solution.',
                           'minutes': min(30, minutes - mock), 'to': '/review'})
        return blocks
    if week['phase'] == 'Taper':
        blocks = [{'kind': 'read', 'label': 'Skim the key ideas', 'detail': 'A quick read, nothing new.',
                   'minutes': min(20, minutes), 'to': '/topics'}]
        if minutes >= 30:
            blocks.append({'kind': 'review', 'label': 'Review set', 'detail': 'A few problems you missed, for a fresh try.',
                           'minutes': min(15, minutes - 20), 'count': max(2, min(15, minutes - 20) // pace),
                           'to': '/review?start=1'})
        return blocks
    blocks, left = [], minutes
    if minutes >= 30:
        review = max(5, min(15, minutes // 4) // 5 * 5)
        blocks.append({'kind': 'review', 'label': 'Review set', 'detail': 'Problems you missed, back for a fresh try.',
                       'minutes': review, 'count': max(2, review // pace), 'to': '/review?start=1'})
        left -= review
    focus = week['focus']
    if not focus:
        n = _fit(left, pace + UNTIMED_EXTRA, SET_RANGE[1])
        blocks.append({'kind': 'practice', 'label': 'Practice set', 'detail': '{} problems at your level.'.format(n),
                       'minutes': n * (pace + UNTIMED_EXTRA), 'count': n, 'to': '/problems'})
        return blocks
    topic = focus[k % len(focus)]
    if challenge:
        per = pace * CHALLENGE_PACE
        block = _set_block(topic, 'challenge', _fit(left, per, CHALLENGE_MAX), per, 'challenge')
    else:
        mode = topic.get('mode', 'practice')
        if read:
            blocks.append({'kind': 'read', 'label': 'Read the key ideas: ' + topic['name'],
                           'detail': 'The topic page: its ideas and worked examples.', 'minutes': 10,
                           'topic': topic['id'], 'name': topic['name'], 'to': '/topics/' + topic['id']})
            left -= 10
        per = pace if mode == 'timed' else pace + UNTIMED_EXTRA
        block = _set_block(topic, mode, _fit(left, per, SET_RANGE[1]), per)
    blocks.append(block)
    left -= block['minutes']
    if len(focus) > 1:
        other = focus[(k + 1) % len(focus)]
        mode = other.get('mode', 'practice')
        per = pace if mode == 'timed' else pace + UNTIMED_EXTRA
        if left >= SET_RANGE[0] * per:
            blocks.append(_set_block(other, mode, _fit(left, per, SET_RANGE[1]), per))
    return blocks


def week_days(week, weekdays, minutes, level, today):
    """The week's seven days: {'date', 'weekday', 'rest', 'minutes', 'blocks', 'today', 'past'}.

    The mock goes on the week's last weekend study day (else its last), the
    challenge set on the last study day before it."""
    start = date.fromisoformat(week['start'])
    studied = [d for d in range(7) if d in weekdays]
    mock_day = None
    if week['mock'] and studied:
        weekend = [d for d in studied if d >= 5]
        mock_day = (weekend or studied)[-1]
    rest_of = [d for d in studied if d != mock_day]
    challenge_day = rest_of[-1] if len(rest_of) >= 2 and week['phase'] != 'Taper' else None
    days, k, met = [], 0, set()
    for d in range(7):
        day = start + timedelta(days=d)
        entry = {'date': day.isoformat(), 'weekday': WEEKDAY[d], 'rest': d not in weekdays,
                 'today': day == today, 'past': day < today, 'blocks': []}
        if d in weekdays:
            topic = week['focus'][k % len(week['focus'])] if week['focus'] else None
            read = bool(topic) and topic.get('mode') == 'learn' and topic['id'] not in met
            entry['blocks'] = _study_day(week, minutes, k, level, d == challenge_day, d == mock_day, read)
            for b in entry['blocks']:
                if b['kind'] == 'mock':
                    b['done'] = bool(week.get('mock_done'))
            if topic and d != mock_day:
                met.add(topic['id'])
                k += 1
        entry['minutes'] = sum(b['minutes'] for b in entry['blocks'])
        days.append(entry)
    return days


def _practice_label(focus, daily):
    """Today's practice for a focus topic, trained the way its weakness wants,
    at the difficulty its mix prescribes (backend/amc/planning.py)."""
    label, to = _practice_kind(focus, daily)
    mix = focus.get('mix')
    if mix:
        from backend.amc import planning
        split = planning.split_count(mix, daily)
        label += ': ' + ', '.join('{} at level {}'.format(c['count'], c['level']) for c in split)
    # The day's practice is the topic's own handpicked set of eight, in this
    # mode, all from the one topic (backend/amc/practice.py).
    mode = focus.get('mode', 'practice')
    to = '/practice/{}?mode={}'.format(focus['id'], mode)
    return label, to


def _practice_kind(focus, daily):
    name, tid = focus['name'], focus['id']
    mode = focus.get('mode', 'practice')
    if mode == 'learn':
        return ('Solve {} introductory {} problems, untimed, easiest first'.format(daily, name),
                '/problems?topic={}&sort=difficulty'.format(tid))
    if mode == 'accuracy':
        return ('Accuracy drill: {} {} problems, untimed, check each answer before submitting'.format(daily, name),
                '/problems?topic=' + tid)
    if mode == 'timed':
        return ('Timed set: {} {} problems, 3 minutes each'.format(daily, name), '/problems?topic=' + tid)
    if mode == 'mixed':
        return ('Mixed set: {} {} problems of every kind, topic hidden; name the technique first'.format(
            daily, name), '/problems?topic=' + tid)
    if mode == 'spaced':
        return ('Revisit {} {} problems you have solved before'.format(daily, name), '/problems?topic={}&status=solved'.format(tid))
    return 'Solve {} problems in {}'.format(daily, name), '/problems?topic=' + tid


#: Reviews come in sets: one set of this many a day, weakest topics first.
#: A backlog of hundreds is worked down a set at a time, never all at once.
REVIEW_SET = 12

#: What each kind of practice set is called on the Today list.
SET_TITLE = {'learn': 'Learning set', 'accuracy': 'Accuracy set', 'timed': 'Timed set', 'mixed': 'Mixed set',
             'spaced': 'Revisit set', 'practice': 'Practice set'}


def _reason(t):
    """Why a focus topic is on the plan, in a few words, from its priority row."""
    f = t.get('factors') or {}
    if f.get('mock_lost'):
        return 'You lost {:g} points here in recent mocks.'.format(f['mock_lost'])
    if f.get('answered'):
        return '{} of {} right on the first try so far.'.format(f.get('right', 0), f['answered'])
    if t.get('id'):
        return 'Not tried yet, and it comes up on most papers.' if (t.get('weight') or 0) >= 3 else 'Not tried yet.'
    return ''


def _set_detail(focus, daily):
    """The practice set's size, pace and difficulty, in one line."""
    mode = focus.get('mode', 'practice')
    bits = ['{} problems'.format(daily)]
    bits.append({'timed': '3 minutes each', 'learn': 'easiest first, no clock', 'accuracy': 'no clock, check each answer',
                 'mixed': 'topic hidden', 'spaced': 'ones you have seen before'}.get(mode, 'no clock'))
    levels = sorted({c['level'] for c in (focus.get('mix') or []) if c.get('share')})
    if levels:
        bits.append('level {}'.format(levels[0]) if len(levels) == 1 else 'levels {}–{}'.format(levels[0], levels[-1]))
    return ', '.join(bits).capitalize() + '.'


def today_items(settings, weeks, due_count, today, checks, practiced_today, reviewed_today=0):
    """The checklist for today, from the current week of the plan.

    Each item is {'key', 'label', 'detail', 'minutes', 'to', 'done'} and, when
    it can be counted, 'progress' and 'goal'. `practiced_today` is the set of
    problem ids practised today; `reviewed_today` how many reviews were
    answered today. Reviews are one set of REVIEW_SET, not the whole backlog."""
    week = next((w for w in weeks if w['current']), weeks[0] if weeks else None)
    day = next((d for d in (week or {}).get('days') or [] if d['date'] == today.isoformat()), None)
    if day is not None:
        return _day_items(settings, week, day, due_count, today, checks, practiced_today, reviewed_today)
    level = settings['target']
    # One handpicked set of eight a day (backend/amc/practice.py SIZE).
    daily = 8 if week and week['problems'] else 0
    ticked = set(checks.get(today.isoformat(), []))
    pace = 12 if level == 'AIME' else 3
    items = []
    if due_count or reviewed_today:
        goal = min(REVIEW_SET, due_count + reviewed_today)
        left = due_count + reviewed_today - goal
        items.append({'key': 'review', 'label': 'Review set: {} problem{} you missed'.format(goal, '' if goal == 1 else 's'),
                      'detail': ('Weakest topics first. One set a day is enough; the rest wait for later sets.'
                                 if left else 'Each one back for a fresh try.'),
                      'minutes': goal * pace, 'to': '/review?start=1', 'auto': False,
                      'progress': min(reviewed_today, goal), 'goal': goal})
    if week and week['focus']:
        focus = week['focus'][0]
        mode = focus.get('mode', 'practice')
        # Theory first only for a topic still being learned.
        if mode == 'learn':
            items.append({'key': 'read', 'label': 'Read the key ideas: {}'.format(focus['name']),
                          'detail': 'The topic page has the ideas and worked examples. About 10 minutes.',
                          'minutes': 10, 'to': '/topics/' + focus['id'], 'auto': False})
        done = sum(1 for pid in practiced_today
                   if bank_of.get(pid) and focus['id'] in [bank_of.get(pid)['topic']] + bank_of.get(pid)['also'])
        _, to = _practice_label(focus, daily)
        reason = focus.get('reason') or ''
        items.append({'key': 'practice', 'label': '{}: {}'.format(SET_TITLE.get(mode, 'Practice set'), focus['name']),
                      'detail': _set_detail(focus, daily) + (' ' + reason if reason else ''),
                      'minutes': daily * (pace if mode == 'timed' else pace + 2), 'to': to, 'auto': False,
                      'mode': mode, 'progress': min(done, daily), 'goal': daily})
    if week and week['mock'] and not week['mock_done']:
        minutes = 180 if level == 'AIME' else 75
        items.append({'key': 'mock', 'label': 'Timed mock: this week’s {}'.format(level),
                      'detail': 'In one sitting, on the clock. Your projected score comes from mocks.',
                      'minutes': minutes, 'to': '/mock-contests', 'auto': False})
    if week and week['phase'] == 'Taper':
        items.append({'key': 'formulas', 'label': 'Skim the key ideas for each topic',
                      'detail': 'A quick read, nothing new. Rest counts this week.', 'minutes': 20,
                      'to': '/topics', 'auto': False})
    for item in items:
        item['done'] = item['key'] in ticked or (
            'goal' in item and item['goal'] > 0 and item['progress'] >= item['goal'])
    return items


def _day_items(settings, week, day, due_count, today, checks, practiced_today, reviewed_today):
    """Today's checklist from today's day of the plan (`week_days`): its blocks,
    with what has been done of each. A rest day has nothing on it but a
    review set when one is due; a mock not yet sat this week stays on."""
    level = settings['target']
    pace = PACE.get(level, 3)
    ticked = set(checks.get(today.isoformat(), []))
    items, keys = [], {}

    def key(kind):
        keys[kind] = keys.get(kind, 0) + 1
        return kind if keys[kind] == 1 else '{}-{}'.format(kind, keys[kind])

    def review_item(planned):
        goal = min(REVIEW_SET, due_count + reviewed_today)
        if not goal:
            return None
        left = due_count + reviewed_today - goal
        return {'key': key('review'), 'label': 'Review set: {} problem{} you missed'.format(goal, '' if goal == 1 else 's'),
                'detail': ('Weakest topics first. One set a day is enough; the rest wait for later sets.'
                           if left else 'Each one back for a fresh try.'),
                'minutes': planned or goal * pace, 'to': '/review?start=1', 'auto': False,
                'progress': min(reviewed_today, goal), 'goal': goal}

    blocks = day['blocks']
    if day['rest'] and due_count:
        item = review_item(None)
        if item:
            items.append(item)
    for b in blocks:
        if b['kind'] == 'review' and b['to'].startswith('/review?'):
            item = review_item(b['minutes'])
            if item:
                items.append(item)
        elif b['kind'] == 'review':
            items.append({'key': key('review'), 'label': b['label'], 'detail': b['detail'], 'minutes': b['minutes'],
                          'to': b['to'], 'auto': False})
        elif b['kind'] in ('practice', 'challenge'):
            topic = b.get('topic')
            done = sum(1 for pid in practiced_today
                       if topic and bank_of.get(pid) and topic in [bank_of.get(pid)['topic']] + bank_of.get(pid)['also'])
            items.append({'key': key(b['kind']), 'label': b['label'], 'detail': b['detail'], 'minutes': b['minutes'],
                          'to': b['to'], 'auto': False, 'mode': b.get('mode', 'practice'),
                          'progress': min(done, b['count']), 'goal': b['count']})
        elif b['kind'] == 'mock':
            items.append({'key': key('mock'), 'label': 'Timed mock: this week’s {}'.format(level),
                          'detail': b['detail'], 'minutes': b['minutes'], 'to': b['to'], 'auto': False})
        else:
            items.append({'key': key('read' if b['to'].startswith('/topics/') else 'formulas'), 'label': b['label'],
                          'detail': b['detail'], 'minutes': b['minutes'], 'to': b['to'], 'auto': False})
    # This week's mock, if its day has gone by unsat: still on, until it is.
    mock_days = [d for d in week.get('days') or [] if any(b['kind'] == 'mock' for b in d['blocks'])]
    if (week.get('mock') and not week.get('mock_done') and mock_days and mock_days[0]['date'] < day['date']
            and not any(i['key'].startswith('mock') for i in items)):
        items.append({'key': 'mock', 'label': 'Timed mock: this week’s {}'.format(level),
                      'detail': 'Still to sit this week. One sitting, on the clock.',
                      'minutes': MOCK_MINUTES.get(level, 75), 'to': '/mock-contests', 'auto': False})
    for item in items:
        item['done'] = item['key'] in ticked or (
            'goal' in item and item['goal'] > 0 and item['progress'] >= item['goal'])
        if item['key'].startswith('mock') and week.get('mock_done'):
            item['done'] = True
    return items


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
PAGES = [
    {'name': 'Dashboard', 'to': '/dashboard', 'words': 'home overview progress score'},
    {'name': 'Review', 'to': '/review', 'words': 'error log mistakes spaced repetition due'},
    {'name': 'Problems', 'to': '/problems', 'words': 'practice problem bank drill'},
    {'name': 'Topics', 'to': '/topics', 'words': 'topics algebra geometry number theory counting probability'},
    {'name': 'Mock Contests', 'to': '/mock-contests', 'words': 'mock contests practice test exam timed sets amc 10 amc 12 aime'},
    {'name': 'Past Contests', 'to': '/contests', 'words': 'contests past papers official exam amc aime'},
    {'name': 'Study Plan', 'to': '/study-plan', 'words': 'study plan schedule weeks calendar goal'},
    {'name': 'Analytics', 'to': '/analytics', 'words': 'analytics performance accuracy trend stats cutoff format prepare goal'},
    {'name': 'Settings', 'to': '/settings', 'words': 'settings account preferences theme'},
    {'name': 'Posts', 'to': '/posts', 'words': 'posts post write share problem test answer key'},
]


def _tokens(text):
    return [t for t in re.split(r'[^a-z0-9]+', text.lower()) if t]


def _score(query_tokens, haystack, title=''):
    """Points for a row matching every token: 3 a token in its title, 2 at the
    start of a word, 1 anywhere; 0 when any token is missing. `haystack` and
    `title` are lower case already when they come from the problem index."""
    hay = haystack.lower()
    head = title.lower()
    points = 0
    for tok in query_tokens:
        if tok in head:
            points += 3
        elif tok in hay:
            points += 2 if _word_start(tok).search(hay) else 1
        else:
            return 0
    return points


_WORD_START = {}


def _word_start(tok):
    """A pattern for `tok` at the start of a word, compiled once per token, not per problem."""
    pattern = _WORD_START.get(tok)
    if pattern is None:
        if len(_WORD_START) > 512:
            _WORD_START.clear()
        pattern = _WORD_START[tok] = re.compile(r'\b' + re.escape(tok))
    return pattern


#: The problems' search text, built once and kept until the problem lists
#: change. Building it means turning every statement's TeX into plain text,
#: which is nearly all of a search's time, so doing it per keystroke made the
#: top bar's search take a tenth of a second for every letter typed.
_INDEX = {'key': None, 'rows': []}
#: Each problem's row by id, with the statement it was built from: the imported
#: papers reload every minute as a new list of the same problems, and rebuilding
#: from these is a lookup each rather than a TeX conversion each.
_ROWS = {}


def _problem_index():
    """[(title, haystack, row)] for every problem, lower-cased, cached against
    the identity of the lists it was built from (the imported and AI problems
    are cached lists that are replaced, not changed, when they reload)."""
    key = (len(bank_of.bank.PROBLEMS), id(bank_of.official.all_problems()), id(bank_of.create.all_problems()))
    if _INDEX['key'] != key:
        rows = []
        for p in bank_of.all_problems():
            kept = _ROWS.get(p['id'])
            if kept and kept[0] == (p['statement'], p['topic'], tuple(p['also']), p['technique']):
                rows.append(kept[1])
                continue
            topic = catalog.TOPIC_BY_ID[p['topic']]
            sources = catalog.sources(p['id'])
            source = '{} #{}'.format(sources[0]['name'], sources[0]['number']) if sources else 'Drill'
            text = plain(p['statement'])
            # The subscripts and superscripts as plain digits too, so "a1" finds "a₁".
            hay = ' '.join([p['id'], p['level'], text, text.translate(_DIGITS), topic['name'], p['topic'],
                            catalog.technique_name(p['technique']),
                            ' '.join(catalog.TOPIC_BY_ID[t]['name'] for t in p['also']),
                            ' '.join('{} {}'.format(s['name'], s['number']) for s in sources)])
            # Its title is where it comes from and what it is about, so "circles"
            # puts a Circles problem above one that only mentions a circle, and
            # "2016 AMC 10A 12" puts that problem first.
            title = '{} {} {}'.format(source.replace('#', ''), topic['name'], p['id'])
            row = (title.lower(), hay.lower(), {
                'id': p['id'], 'level': p['level'], 'topic_name': topic['name'], 'difficulty': p['difficulty'],
                'rating': p.get('rating'), 'preview': text[:140], 'source': source})
            _ROWS[p['id']] = ((p['statement'], p['topic'], tuple(p['also']), p['technique']), row)
            rows.append(row)
        _INDEX.update(key=key, rows=rows)
    return _INDEX['rows']


def search(query, limit=20):
    """Problems, topics, contests and pages matching every word of `query`."""
    toks = _tokens(query)
    if not toks:
        return {'problems': [], 'topics': [], 'contests': [], 'pages': []}
    problems = []
    for title, hay, row in _problem_index():
        pts = _score(toks, hay, title)
        if pts:
            problems.append((pts, row))
    topics = []
    for t in catalog.TOPICS:
        pts = _score(toks, ' '.join([t['name'], t['summary'], ' '.join(t['ideas']), t['category'],
                                     catalog.CATEGORY_BY_ID[t['category']]['name']]), t['name'])
        if pts:
            topics.append((pts, {'id': t['id'], 'name': t['name'], 'summary': t['summary'],
                                 'category_name': catalog.CATEGORY_BY_ID[t['category']]['name']}))
    contests = []
    for c in catalog.MOCKS + catalog.PAST:
        name = c['name']
        pts = _score(toks, ' '.join([name, c['level'], c.get('blurb', ''), name.replace(' ', '')]), name)
        if pts:
            contests.append((pts, {'id': c['id'], 'name': name, 'level': c['level'],
                                   'kind': 'mock' if c['id'] in catalog.MOCK_BY_ID else 'past'}))
    pages = []
    for page in PAGES:
        pts = _score(toks, page['name'] + ' ' + page['words'], page['name'])
        if pts:
            pages.append((pts, {'name': page['name'], 'to': page['to']}))

    def top(rows, n):
        return [r for _, r in sorted(rows, key=lambda x: -x[0])[:n]]

    return {'problems': top(problems, limit), 'topics': top(topics, 8),
            'contests': top(contests, 8), 'pages': top(pages, 4)}
