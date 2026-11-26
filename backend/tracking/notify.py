"""Notifications: the rules that decide the app has something to say.

What can be said is this site's own business: today's study plan, problems
due for review, the week's mock and a new best on one, the practice streak,
and the contest coming up. Those rules are in backend/amc/alerts.py; this
module is everything around them: what counts as new, what a delete means,
and when a notification ends.

## Derived, never scheduled

There is no job runner here, so nothing writes a notification at 3am about a
state that has since changed. `sweep` runs when somebody asks for the list,
reads the record as it stands, and writes down what is true *now*. An account
in good order comes back with nothing, which is the whole reason a badge on the
bell is worth looking at.

## The fingerprint is what makes a delete stick

Every candidate carries one, and it names the *situation* rather than the
moment: 'review-due:2026-09-01', 'exam-soon:2026-11-05:7', 'mock-best:<id>'.
The insert ignores a collision, so a sweep that finds the same situation on
every poll writes one row and then nothing. Deleting that row leaves a
tombstone under the same fingerprint (data/sql/notifications.sql), so the sweep
cannot put it back, and the bell stays empty until something genuinely new
turns up, which is exactly what the reader asked for by deleting it.

The day-scoped ones are the awkward case: "12 problems to review" is true all
day and the 12 moves. Putting the count in the fingerprint would mean a new
notification every time a review was answered, so the count is not in it and
the row's words are brought up to date in place instead
(`db.refresh_notification`). One a day, always current, and deletable for good.

They also end with their day. Each carries `for_day`, and the sweep retires the
live ones whose day has passed (`db.retire_notifications`). And one that stops
being true during its day (the plan finished, the reviews answered) is withdrawn by the next sweep rather than left saying it.

## The first sweep says nothing about the past

An account arriving with a streak already at 30 or a best already set is not
news. So the first sweep an account ever gets files the one-shot situations
straight to the tombstone state: remembered, never shown. The ongoing ones
(what is on today, what is due) are shown, because those are about now.

## Four channels, four switches

Each candidate declares a channel, with a switch per channel plus a master one
(FIELDS in backend/api/settings.py). A channel that is off is never swept, so
turning one off does not just hide its notifications; it stops writing them.
"""
from datetime import date, timedelta

from backend.amc import alerts
from backend.database import connection as db

#: The switchable groups. Mirrors the `notify_*` keys in
#: backend/api/settings.py and NotificationChannel in frontend/src/services/notifications.ts.
CHANNELS = ('plan', 'review', 'mocks', 'streak')

#: Situations that describe a moving count and so are reworded in place
#: rather than re-raised. Matched on the part of the fingerprint before the
#: first colon.
# 'streak-risk' is no longer raised (backend/amc/alerts.py `_streak`); it stays
# here so a row left from before is withdrawn on the next sweep.
REFRESHABLE = ('plan-today', 'review-due', 'streak-risk')

#: Where a fingerprint has no more chance of recurring, so its tombstone is
#: holding nothing back. Comfortably past the longest-lived day-scoped key.
TOMBSTONE_DAYS = 60

#: Which candidates are about a backlog rather than about now. The first sweep
#: files these without showing them; see the note at the top.
ONE_SHOT = ('streak-milestone', 'mock-best')


def _day(value, fallback=None):
    """A `YYYY-MM-DD` string as a date, or `fallback` if it is not one."""
    try:
        return date.fromisoformat(str(value or '')[:10])
    except ValueError:
        return fallback


def sweep(user, day, at=None, channels=CHANNELS):
    """Bring one account's notifications up to date. Returns the new rows.

    `day` is the reader's local ISO day, passed in because stored stamps carry
    no zone, so only the caller knows what today is. `at` (their 'HH:MM') is
    accepted for the endpoint's sake and not needed by any rule here.
    `channels` is the subset whose switch is on: a channel that is off is not
    swept at all, so it writes nothing rather than writing rows nobody sees.
    """
    username = user['username']
    today = _day(day, date.today())
    day = today.isoformat()
    wanted = [c for c in CHANNELS if c in set(channels or ())]
    if not wanted:
        return []

    candidates = alerts.candidates(username, today, wanted)

    known = db.live_fingerprints(username)
    settling = not known

    fresh = [c for c in candidates if c['fingerprint'] not in known]
    for candidate in candidates:
        head = candidate['fingerprint'].split(':', 1)[0]
        if candidate['fingerprint'] in known and head in REFRESHABLE:
            db.refresh_notification(username, candidate['fingerprint'],
                                    candidate['title'], candidate['body'])

    written = db.add_notifications(username, fresh)

    # Today's rows, withdrawn once they stop being true: the plan finished,
    # the reviews answered, a problem done to keep the streak. Left up, they
    # would go on saying it for the rest of a day on which it is not so.
    standing = {c['fingerprint'] for c in candidates}
    stale = [row['id'] for row in db.notifications_for(username, wanted)
             if row.get('for_day') == day and row['fingerprint'] not in standing
             and row['fingerprint'].split(':', 1)[0] in REFRESHABLE + ('plan-done',)]
    if stale:
        db.delete_notifications(username, stale)

    # The backlog, on the account's very first sweep: filed under its
    # fingerprint so it is never raised again, and never put on screen.
    if settling:
        backlog = [row['id'] for row in written
                   if row['fingerprint'].split(':', 1)[0] in ONE_SHOT]
        # And a mark that the first sweep has happened, filed the same way, so
        # an account that had nothing to say then is not "first" for ever:
        # without it, its first real news (a new best) would be filed unseen.
        backlog += [row['id'] for row in db.add_notifications(username, [{
            'fingerprint': 'settled', 'channel': wanted[0], 'tone': 'info',
            'title': 'Notifications on', 'body': '', 'link': '/dashboard'}])]
        if backlog:
            db.delete_notifications(username, backlog)
            written = [row for row in written if row['id'] not in backlog]

    # Yesterday's counts, retired now today's are written.
    db.retire_notifications(username, day)
    db.prune_notifications(
        username, (today - timedelta(days=TOMBSTONE_DAYS)).isoformat())
    return written
