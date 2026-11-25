"""The bell: what it raises, what it will not raise twice, and what a delete means.

The contract this file protects, in the order the notifications feature would
break if any of it stopped holding:

  1. The sweep is idempotent. It runs on every read of the list (there is no
     job runner, backend/tracking/notify.py), so a bell that grew by one row
     per poll would be unusable within a minute.
  2. A deleted notification stays deleted. The situation behind it is usually
     still true, so a hard delete would let the next poll write it straight back.
  3. A day-scoped count is reworded in place rather than re-raised, so
     answering a review does not produce a second "problems to review".
  4. A channel that is off writes nothing and shows nothing.
  5. The first sweep an account ever gets says nothing about its backlog.
  6. One account's notifications are not another's.

And what it says is this site's (backend/amc/alerts.py): today's study plan
and the contest coming up, problems due for review, the week's mock and a new
best on one, and the practice streak.
"""
import uuid
from datetime import date, timedelta

import pytest

from backend.amc import catalog, store
from backend.database import connection as db
from backend.tracking import notify

from tests.conftest import make_account, sign_in

DAY = '2026-09-01'                       # a Tuesday
TOMORROW = '2026-09-02'
YESTERDAY = '2026-08-31'
PROBLEMS = catalog.MOCK_BY_ID['step-mock-10']['problems']


def _due(username, n, due='2026-08-30', start=0):
    """`n` review rows due on `due`."""
    statements = []
    for pid in PROBLEMS[start:start + n]:
        statements += store.review_upsert(username, {'problem_id': pid, 'stage': 1, 'due': due, 'status': 'active'})
    store.write(statements)


def _answered(username, day, pid=None):
    """One answer, on `day`."""
    store.write([('INSERT INTO amc_attempts (id, user_id, problem_id, answer, correct, seconds, source, at) '
                  'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (uuid.uuid4().hex, username, pid or PROBLEMS[20], 'A', 1, 60, 'practice', day + 'T10:00:00'))])


def _list(client, day=DAY, at='09:00'):
    reply = client.post('/api/notifications', params={'day': day, 'at': at}).json()
    assert reply['success'], reply
    return reply['notifications']


def _prints(rows):
    return {row['fingerprint'] for row in rows}


@pytest.fixture
def due(client):
    """`tester`, with three reviews due and a one-day streak with nothing on it yet today."""
    _due('tester', 3)
    _answered('tester', YESTERDAY)
    return client


# --------------------------------------------------------------------------
# The sweep
# --------------------------------------------------------------------------
def test_the_record_becomes_notifications(due):
    rows = _list(due)
    prints = _prints(rows)
    assert {'review-due:%s' % DAY, 'streak-risk:%s' % DAY} <= prints

    review = next(r for r in rows if r['fingerprint'] == 'review-due:%s' % DAY)
    assert review['channel'] == 'review' and review['tone'] == 'info'
    # The count is in the words, never in the fingerprint: see backend/tracking/notify.py.
    assert review['title'] == '3 problems to review'
    assert review['link'] == '/review?start=1'
    streak = next(r for r in rows if r['fingerprint'] == 'streak-risk:%s' % DAY)
    assert streak['title'] == 'Your 1-day streak needs a problem today'


def test_sweeping_again_writes_nothing(due):
    first = _list(due)
    assert first
    for _ in range(3):
        again = _list(due)
    assert _prints(again) == _prints(first)
    assert [r['id'] for r in again] == [r['id'] for r in first]


def test_a_moving_count_is_reworded_rather_than_re_raised(due):
    before = next(r for r in _list(due) if r['fingerprint'] == 'review-due:%s' % DAY)
    # Two more come due. The situation is the same situation; only its number moved.
    _due('tester', 2, start=3)
    after = [r for r in _list(due) if r['fingerprint'] == 'review-due:%s' % DAY]
    assert len(after) == 1 and after[0]['id'] == before['id']
    assert after[0]['title'] == '5 problems to review'


def test_a_new_day_retires_the_old_one_and_raises_its_own(due):
    """Yesterday's count is neither news nor today's number, so it goes."""
    assert 'review-due:%s' % DAY in _prints(_list(due))

    tomorrow = _prints(_list(due, day=TOMORROW))
    assert 'review-due:%s' % TOMORROW in tomorrow
    assert 'review-due:%s' % DAY not in tomorrow

    # Retired, not forgotten: the fingerprint stays as a tombstone, so going
    # back to yesterday does not resurrect it.
    assert 'review-due:%s' % DAY in db.live_fingerprints('tester')
    assert 'review-due:%s' % DAY not in _prints(_list(due))


def test_a_streak_kept_today_is_withdrawn_from_the_bell(due):
    assert 'streak-risk:%s' % DAY in _prints(_list(due))
    _answered('tester', DAY)
    assert 'streak-risk:%s' % DAY not in _prints(_list(due))


# --------------------------------------------------------------------------
# Deleting
# --------------------------------------------------------------------------
def test_deleting_one_keeps_it_gone(due):
    doomed = next(r for r in _list(due) if r['fingerprint'] == 'review-due:%s' % DAY)
    assert due.delete('/api/notifications/%s' % doomed['id']).json()['success']

    # The reviews are still due. The notification about them does not come back.
    for _ in range(3):
        rows = _list(due)
    assert 'review-due:%s' % DAY not in _prints(rows)
    assert 'streak-risk:%s' % DAY in _prints(rows)


def test_delete_all_empties_it_and_it_stays_empty(due):
    assert _list(due)
    removed = due.delete('/api/notifications').json()
    assert removed['success'] and removed['removed'] > 0

    assert _list(due) == []
    assert _list(due) == []

    # Until something genuinely new turns up, which a new day is.
    assert _list(due, day=TOMORROW)


def test_deleting_one_that_is_already_gone_is_a_failure_not_a_crash(due):
    doomed = _list(due)[0]
    assert due.delete('/api/notifications/%s' % doomed['id']).json()['success']
    assert not due.delete('/api/notifications/%s' % doomed['id']).json()['success']


def test_one_account_cannot_delete_anothers(due, stranger):
    mine = _list(due)[0]
    assert not stranger.delete('/api/notifications/%s' % mine['id']).json()['success']
    assert mine['id'] in {row['id'] for row in _list(due)}


def test_an_accounts_list_is_its_own(due, stranger):
    _due('stranger', 1)
    theirs = _list(stranger)
    assert theirs
    assert not {r['id'] for r in theirs} & {r['id'] for r in _list(due)}


# --------------------------------------------------------------------------
# Read, and shown
# --------------------------------------------------------------------------
def test_reading_is_not_deleting(due):
    rows = _list(due)
    assert due.post('/api/notifications/mark', json={'read': True}).json()['success']

    after = _list(due)
    assert len(after) == len(rows)
    assert all(row['read_at'] for row in after)


def test_shown_is_stamped_per_row(due):
    rows = _list(due)
    assert len(rows) >= 2
    first = rows[0]['id']
    due.post('/api/notifications/mark', json={'shown': [first]})

    after = {row['id']: row for row in _list(due)}
    assert after[first].get('shown_at')
    assert not any(row.get('shown_at') for key, row in after.items() if key != first)


# --------------------------------------------------------------------------
# The switches
# --------------------------------------------------------------------------
def test_the_master_switch_stops_everything(due):
    assert _list(due)
    due.post('/api/settings', json={'values': {'notifications_enabled': False}})

    reply = due.post('/api/notifications', params={'day': DAY}).json()
    assert reply['success'] and reply['enabled'] is False
    assert reply['notifications'] == []

    # Off is not a delete: what was there is there again when it comes back.
    due.post('/api/settings', json={'values': {'notifications_enabled': True}})
    assert _list(due)


def test_a_channel_that_is_off_is_neither_written_nor_shown(client):
    client.post('/api/settings', json={'values': {'notify_review': False}})
    _due('tester', 2)

    assert 'review-due:%s' % DAY not in _prints(_list(client))
    # Not written either, so turning it back on starts from what is true then
    # rather than replaying what was suppressed.
    assert not [row for row in db.notifications_for('tester') if row['channel'] == 'review']

    client.post('/api/settings', json={'values': {'notify_review': True}})
    assert 'review-due:%s' % DAY in _prints(_list(client))


def test_popups_are_reported_with_the_list(due):
    assert due.post('/api/notifications', params={'day': DAY}).json()['popups'] is True
    due.post('/api/settings', json={'values': {'notify_popups': False}})
    assert due.post('/api/notifications', params={'day': DAY}).json()['popups'] is False


def test_the_channels_are_this_sites():
    assert notify.CHANNELS == ('plan', 'review', 'mocks', 'streak')


# --------------------------------------------------------------------------
# The first sweep
# --------------------------------------------------------------------------
def test_the_first_sweep_says_nothing_about_the_backlog(app):
    """A week-long streak already run is not news, and is never raised. It is
    still filed, which is what stops it turning up as news on the second sweep."""
    make_account('veteran')
    for back in range(7):
        _answered('veteran', (date.fromisoformat(DAY) - timedelta(days=back)).isoformat())
    client = sign_in(app, 'veteran')

    rows = _list(client)
    assert not [r for r in rows if r['fingerprint'].startswith('streak-milestone:')]
    assert any(p.startswith('streak-milestone:7:') for p in db.live_fingerprints('veteran'))
    assert not [r for r in _list(client) if r['fingerprint'].startswith('streak-milestone:')]


def test_something_new_after_the_first_sweep_is_raised(client):
    _list(client)  # the settling sweep

    for score in (84, 96):
        _, statement = store.mock_row('tester', 'mock-10-1', 'mock', {}, score, 14, 6, 5, 4000)
        store.write([statement])
    rows = _list(client)
    fresh = [r for r in rows if r['fingerprint'].startswith('mock-best:')]
    assert len(fresh) == 1
    assert fresh[0]['title'] == 'New best on {}: 96'.format(catalog.MOCK_BY_ID['mock-10-1']['name'])
    assert fresh[0]['body'] == 'Up from 84.' and fresh[0]['tone'] == 'good'


# --------------------------------------------------------------------------
# The study plan
# --------------------------------------------------------------------------
def test_the_plan_says_what_today_holds_and_when_the_contest_is(client):
    store.save_plan('tester', 'AMC 10', '2026-09-08', 100, 6, {}, {})
    rows = _list(client)
    today = next(r for r in rows if r['fingerprint'] == 'plan-today:%s' % DAY)
    assert today['channel'] == 'plan' and today['title'].startswith("Today's plan: ")
    assert today['link'] == '/study-plan'
    soon = next(r for r in rows if r['fingerprint'] == 'exam-soon:2026-09-08:7')
    assert soon['title'] == 'The AMC 10 is in 7 days' and soon['tone'] == 'warn'
    # The day before, it says tomorrow, under the next mark.
    later = _list(client, day='2026-09-07')
    assert next(r for r in later if r['fingerprint'] == 'exam-soon:2026-09-08:1')['title'] == 'The AMC 10 is tomorrow'


def test_a_rest_day_has_no_plan_to_announce(client):
    store.save_plan('tester', 'AMC 10', '2026-12-08', 100, 6, {}, {})
    friday = '2026-09-04'                                 # six days a week: Friday off
    assert not [r for r in _list(client, day=friday) if r['fingerprint'].startswith('plan-')]


# --------------------------------------------------------------------------
# Tombstones
# --------------------------------------------------------------------------
def test_old_tombstones_are_pruned(due):
    """A tombstone stops being useful once its fingerprint cannot recur.

    `sweep` takes the day from the request, and the prune cutoff is computed
    from it, but `deleted_at` is stamped from the server's wall clock. So the
    far day is measured from `date.today()`, the clock that writes the value
    being tested: the offset is what matters, not the date.
    """
    doomed = _list(due)[0]
    due.delete('/api/notifications/%s' % doomed['id'])
    assert doomed['fingerprint'] in db.live_fingerprints('tester')

    far = (date.today() + timedelta(days=notify.TOMBSTONE_DAYS + 2)).isoformat()
    _list(due, day=far)
    assert doomed['fingerprint'] not in db.live_fingerprints('tester')


def test_a_tombstone_inside_the_window_is_kept(due):
    """What a tombstone is *for* is stopping a dismissed notification from being
    written again, so one inside the window has to survive a later sweep."""
    doomed = _list(due)[0]
    due.delete('/api/notifications/%s' % doomed['id'])

    near = (date.today() + timedelta(days=notify.TOMBSTONE_DAYS - 2)).isoformat()
    _list(due, day=near)
    assert doomed['fingerprint'] in db.live_fingerprints('tester')


def test_signed_out_is_a_401(anon):
    assert anon.get('/api/notifications').status_code == 401
    assert anon.delete('/api/notifications').status_code == 401
