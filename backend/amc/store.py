"""Reads and writes for the AMC tables (data/sql/amc.sql).

Plain SQL with `?` placeholders, which both backends speak: SQLite natively
and Postgres through backend/database/pg.py. Every function is scoped to one
account, and the account is always the signed-in one (backend/api/guard.py).
"""
import json
import uuid
from datetime import datetime

from backend.database.connection import connect


def _now():
    return datetime.now().isoformat(timespec='seconds')


def _rows(cursor):
    return [dict(zip(row.keys(), tuple(row))) for row in cursor.fetchall()]


def _read(sql, params=()):
    con = connect()
    try:
        return _rows(con.execute(sql, params))
    finally:
        con.close()


def _write(statements):
    """Run (sql, params) pairs in one transaction."""
    con = connect()
    try:
        with con:
            for sql, params in statements:
                con.execute(sql, params)
    finally:
        con.close()


# -- Attempts ---------------------------------------------------------------
def attempts(user):
    """Every answer, oldest first, with the kind and mode of the set it was
    given in ('' for a problem answered on its own): a mixed set hides the
    topic and a timed one runs on a clock, which the analysis reads."""
    rows = _read('SELECT a.id, a.problem_id, a.answer, a.correct, a.seconds, a.source, a.at, a.set_id, '
                 'r.kind AS set_kind, r.mode AS set_mode, m.reason AS miss_reason '
                 'FROM amc_attempts a LEFT JOIN amc_set_runs r ON r.id = a.set_id AND r.user_id = a.user_id '
                 'LEFT JOIN amc_miss_reasons m ON m.user_id = a.user_id AND m.ref = a.id AND m.problem_id = a.problem_id '
                 'WHERE a.user_id = ? ORDER BY a.at, a.rowid', (user,))
    for row in rows:
        row['set_id'] = row.get('set_id') or ''
        row['set_kind'] = row.get('set_kind') or ''
        row['set_mode'] = row.get('set_mode') or ''
        row['miss_reason'] = row.get('miss_reason') or ''
    return rows


def attempt(user, attempt_id):
    """One of the account's answers by id, or None."""
    rows = _read('SELECT id, problem_id, answer, correct, seconds, source, at, set_id FROM amc_attempts '
                 'WHERE user_id = ? AND id = ?', (user, attempt_id))
    return rows[0] if rows else None


def new_id():
    return uuid.uuid4().hex


def attempt_rows(user, problem_id, answer, correct, seconds, source, set_id='', attempt_id=None):
    """The INSERT for one answer. Pass `attempt_id` (from `new_id`) to know the
    row's id before it is written."""
    return ('INSERT INTO amc_attempts (id, user_id, problem_id, answer, correct, seconds, source, at, set_id) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (attempt_id or uuid.uuid4().hex, user, problem_id, str(answer), 1 if correct else 0,
             int(seconds or 0), source, _now(), set_id or ''))


# -- The placement check ---------------------------------------------------
def placement(user):
    """The account's placement check (backend/amc/placement.py), or None."""
    rows = _read('SELECT level, answers, next_id, started_at, finished_at, theta FROM amc_placements '
                 'WHERE user_id = ?', (user,))
    if not rows:
        return None
    row = rows[0]
    answers = _json(row.get('answers'), [])
    row['answers'] = answers if isinstance(answers, list) else []
    row['next_id'] = row.get('next_id') or ''
    row['finished_at'] = row.get('finished_at') or ''
    return row


def placement_rows(user, level, answers, next_id, started_at, finished=False, theta=None):
    """Write the whole placement row (it is small)."""
    return [('DELETE FROM amc_placements WHERE user_id = ?', (user,)),
            ('INSERT INTO amc_placements (user_id, level, answers, next_id, started_at, finished_at, theta) '
             'VALUES (?, ?, ?, ?, ?, ?, ?)',
             (user, level, json.dumps(answers), next_id or '', started_at, _now() if finished else '', theta))]


def now():
    return _now()


# -- Why a miss happened ----------------------------------------------------
def miss_reasons(user):
    """Every reason the account has given for a miss, oldest first."""
    rows = _read('SELECT ref, problem_id, reason, source, number, level, at FROM amc_miss_reasons '
                 'WHERE user_id = ? ORDER BY at', (user,))
    for row in rows:
        row['number'] = int(row.get('number') or 0)
        row['level'] = row.get('level') or ''
    return rows


def miss_reason_rows(user, ref, problem_id, reason, source, number, level):
    """Set (or, with `reason` falsy, clear) the reason for one miss."""
    statements = [('DELETE FROM amc_miss_reasons WHERE user_id = ? AND ref = ? AND problem_id = ?',
                   (user, ref, problem_id))]
    if reason:
        statements.append(('INSERT INTO amc_miss_reasons (user_id, ref, problem_id, reason, source, number, level, at) '
                           'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                           (user, ref, problem_id, reason, source, int(number or 0), level or '', _now())))
    return statements


# -- Sets walked one problem after another ------------------------------------
_RUN_COLUMNS = 'id, kind, topic, mode, title, problems, seconds, started_at, finished_at, time_up'


def _run(row):
    problems = _json(row.get('problems'), [])
    row['problems'] = [str(p) for p in problems] if isinstance(problems, list) else []
    row['seconds'] = int(row['seconds']) if row.get('seconds') not in (None, '') else None
    row['finished_at'] = row.get('finished_at') or ''
    row['time_up'] = bool(int(row.get('time_up') or 0))
    for key in ('topic', 'mode', 'title'):
        row[key] = row.get(key) or ''
    return row


def start_set_run(user, kind, topic, mode, title, problems, seconds=None):
    """Record a set as dealt, its problems in order. Returns the run's id."""
    run_id = uuid.uuid4().hex
    _write([('INSERT INTO amc_set_runs (id, user_id, kind, topic, mode, title, problems, seconds, started_at, '
             'finished_at, time_up) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
             (run_id, user, kind, topic or '', mode or '', title or '', json.dumps(list(problems)),
              int(seconds) if seconds else None, _now(), '', 0))])
    return run_id


def set_run(user, run_id):
    rows = _read('SELECT {} FROM amc_set_runs WHERE user_id = ? AND id = ?'.format(_RUN_COLUMNS), (user, run_id))
    return _run(rows[0]) if rows else None


def set_runs(user, limit=None):
    """The account's sets, newest first."""
    sql = 'SELECT {} FROM amc_set_runs WHERE user_id = ? ORDER BY started_at DESC, rowid DESC'.format(_RUN_COLUMNS)
    if limit:
        sql += ' LIMIT {:d}'.format(int(limit))
    return [_run(r) for r in _read(sql, (user,))]


def finish_set_run(user, run_id, time_up=False):
    """Mark a set over, once: the first finish (and whether its clock ended it) stands."""
    _write([('UPDATE amc_set_runs SET finished_at = ?, time_up = ? '
             "WHERE user_id = ? AND id = ? AND (finished_at IS NULL OR finished_at = '')",
             (_now(), 1 if time_up else 0, user, run_id))])


# -- Reviews ----------------------------------------------------------------
#: A review on hold ("Too challenging?", backend/amc/reach.py) is read back
#: with this status. Stored, it is 'active' with `parked_at` set, so the
#: table's status CHECK is untouched; everything that asks for 'active' (due
#: counts, the queue, the weak-topics pool) leaves it out without being told.
PARKED = 'parked'

_REVIEW_COLUMNS = 'problem_id, stage, due, status, note, misses, added_at, updated_at, parked_at, parked_level'


def _review_row(row):
    if row.get('parked_at'):
        row['status'] = PARKED
    return row


def reviews(user):
    return [_review_row(r) for r in _read('SELECT {} FROM amc_reviews WHERE user_id = ?'.format(_REVIEW_COLUMNS),
                                          (user,))]


def review(user, problem_id):
    rows = _read('SELECT {} FROM amc_reviews WHERE user_id = ? AND problem_id = ?'.format(_REVIEW_COLUMNS),
                 (user, problem_id))
    return _review_row(rows[0]) if rows else None


def review_upsert(user, row):
    """Insert or replace one account's review row (the full row is passed).
    A row with status PARKED is stored as on hold; any other clears the hold."""
    now = _now()
    parked = row['status'] == PARKED
    return [
        ('DELETE FROM amc_reviews WHERE user_id = ? AND problem_id = ?', (user, row['problem_id'])),
        ('INSERT INTO amc_reviews (user_id, problem_id, stage, due, status, note, misses, added_at, updated_at, '
         'parked_at, parked_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
         (user, row['problem_id'], int(row['stage']), row['due'], 'active' if parked else row['status'],
          row.get('note') or '', int(row.get('misses') or 0), row.get('added_at') or now, now,
          (row.get('parked_at') or now) if parked else None,
          row.get('parked_level') if parked else None)),
    ]


def review_delete(user, problem_id):
    _write([('DELETE FROM amc_reviews WHERE user_id = ? AND problem_id = ?', (user, problem_id))])


def review_note(user, problem_id, note):
    _write([('UPDATE amc_reviews SET note = ?, updated_at = ? WHERE user_id = ? AND problem_id = ?',
             (note, _now(), user, problem_id))])


# -- Mocks ------------------------------------------------------------------
def mocks(user):
    rows = _read('SELECT id, contest_id, kind, answers, score, correct, wrong, blank, seconds, note, at '
                 'FROM amc_mocks WHERE user_id = ? ORDER BY at DESC, rowid DESC', (user,))
    for row in rows:
        try:
            row['answers'] = json.loads(row.get('answers') or '{}')
        except ValueError:
            row['answers'] = {}
    return rows


def mock(user, mock_id):
    for row in mocks(user):
        if row['id'] == mock_id:
            return row
    return None


def mock_row(user, contest_id, kind, answers, score, correct, wrong, blank, seconds, note=''):
    mock_id = uuid.uuid4().hex
    return mock_id, (
        'INSERT INTO amc_mocks (id, user_id, contest_id, kind, answers, score, correct, wrong, blank, seconds, note, at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (mock_id, user, contest_id, kind, json.dumps(answers), float(score), int(correct), int(wrong),
         int(blank), int(seconds or 0), note, _now()))


def mock_delete(user, mock_id):
    # A blank's reason is keyed to the sitting, so it goes with it. (A wrong
    # answer's is keyed to its attempt, which stays, as the attempts do.)
    _write([('DELETE FROM amc_mocks WHERE user_id = ? AND id = ?', (user, mock_id)),
            ('DELETE FROM amc_miss_reasons WHERE user_id = ? AND ref LIKE ?', (user, 'mock:{}:%'.format(mock_id)))])


# -- Plan -------------------------------------------------------------------
def _json(value, fallback):
    try:
        return json.loads(value) if value else fallback
    except ValueError:
        return fallback


def plan(user):
    rows = _read('SELECT target, exam_date, goal_score, hours, checks, details, coach, coach_at, coach_by, '
                 'created_at, updated_at FROM amc_plans WHERE user_id = ?', (user,))
    if not rows:
        return None
    row = rows[0]
    row['checks'] = _json(row.get('checks'), {})
    row['details'] = _json(row.get('details'), {})
    row['coach'] = _json(row.get('coach'), None)
    row['coach_at'] = row.get('coach_at') or ''
    row['coach_by'] = row.get('coach_by') or ''
    # The days marked complete, by date: what backend/amc/consistency.py reads.
    row['days_done'] = plan_days(user)
    return row


def save_plan(user, target, exam_date, goal_score, hours, checks, details=None):
    """Write the plan's settings. The coach's plan is kept unless the contest
    changed, in which case it no longer fits and is dropped."""
    now = _now()
    existing = plan(user)
    created = existing['created_at'] if existing else now
    if details is None:
        details = existing['details'] if existing else {}
    keep = existing and existing['target'] == target
    coach = json.dumps(existing['coach']) if keep and existing['coach'] else ''
    _write([
        ('DELETE FROM amc_plans WHERE user_id = ?', (user,)),
        ('INSERT INTO amc_plans (user_id, target, exam_date, goal_score, hours, checks, details, coach, '
         'coach_at, coach_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
         (user, target, exam_date, float(goal_score), int(hours), json.dumps(checks), json.dumps(details),
          coach, existing['coach_at'] if keep else '', existing['coach_by'] if keep else '', created, now)),
    ])


def plan_days(user):
    """{date: {'items', 'minutes', 'completed_at'}} for every day marked complete."""
    return {r['day']: {'items': int(r['items'] or 0), 'minutes': int(r['minutes'] or 0),
                       'completed_at': r['completed_at']}
            for r in _read('SELECT day, items, minutes, completed_at FROM amc_plan_days WHERE user_id = ?', (user,))}


def complete_day(user, day, items, minutes):
    _write([('DELETE FROM amc_plan_days WHERE user_id = ? AND day = ?', (user, day)),
            ('INSERT INTO amc_plan_days (user_id, day, items, minutes, completed_at) VALUES (?, ?, ?, ?, ?)',
             (user, day, int(items), int(minutes), _now()))])


def reopen_day(user, day):
    _write([('DELETE FROM amc_plan_days WHERE user_id = ? AND day = ?', (user, day))])


def save_coach(user, coach, by):
    _write([('UPDATE amc_plans SET coach = ?, coach_at = ?, coach_by = ?, updated_at = ? WHERE user_id = ?',
             (json.dumps(coach), _now(), by, _now(), user))])


def delete_plan(user):
    _write([('DELETE FROM amc_plans WHERE user_id = ?', (user,))])


# -- Sittings in progress ---------------------------------------------------
def sitting(user, contest_id):
    """The account's timed contest in progress on this paper, or None."""
    rows = _read('SELECT used, answers, flags, started_at, updated_at FROM amc_sittings '
                 'WHERE user_id = ? AND contest_id = ?', (user, contest_id))
    if not rows:
        return None
    row = rows[0]
    answers = _json(row.get('answers'), {})
    flags = _json(row.get('flags'), [])
    return {
        'used': float(row.get('used') or 0),
        'answers': {str(k): str(v) for k, v in answers.items()} if isinstance(answers, dict) else {},
        'flags': sorted({int(n) for n in flags if isinstance(n, int) or str(n).isdigit()})
        if isinstance(flags, list) else [],
        'started_at': row.get('started_at') or '',
        'updated_at': row.get('updated_at') or '',
    }


def save_sitting(user, contest_id, used, answers, flags):
    """Write the sitting as it stands, keeping when it was first started."""
    now = _now()
    existing = sitting(user, contest_id)
    started = existing['started_at'] if existing and existing['started_at'] else now
    _write([
        ('DELETE FROM amc_sittings WHERE user_id = ? AND contest_id = ?', (user, contest_id)),
        ('INSERT INTO amc_sittings (user_id, contest_id, used, answers, flags, started_at, updated_at) '
         'VALUES (?, ?, ?, ?, ?, ?, ?)',
         (user, contest_id, max(0.0, float(used or 0)), json.dumps(answers), json.dumps(flags), started, now)),
    ])


def clear_sitting_sql(user, contest_id):
    return ('DELETE FROM amc_sittings WHERE user_id = ? AND contest_id = ?', (user, contest_id))


def clear_sitting(user, contest_id):
    _write([clear_sitting_sql(user, contest_id)])


# -- Papers unlocked before a sitting ----------------------------------------
def unlocked(user, contest_id):
    return bool(_read('SELECT 1 FROM amc_unlocks WHERE user_id = ? AND contest_id = ?', (user, contest_id)))


def set_unlocked(user, contest_id, on):
    statements = [('DELETE FROM amc_unlocks WHERE user_id = ? AND contest_id = ?', (user, contest_id))]
    if on:
        statements.append(('INSERT INTO amc_unlocks (user_id, contest_id, at) VALUES (?, ?, ?)',
                           (user, contest_id, _now())))
    _write(statements)


def write(statements):
    _write(statements)
