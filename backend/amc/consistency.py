"""How often the study plan is kept, and how much the days ahead should hold.

The plan is written for the hours a week the student said they had. What they
actually do is in their record: the study days they marked complete
(`amc_plan_days`, the dashboard's "Mark the day complete"), the days they
answered something without finishing the list, and the days they did nothing.
A plan that asks for fifty minutes on days that keep going by untouched is a
plan that is not being followed, and a smaller day that gets done does more
than a full one that does not. So the days ahead are sized to how the last
two weeks went:

* Each study day in the last `WINDOW` days (today left out, because it is
  not over) is **complete**, **partial** (something answered, the list not
  finished) or **missed**. Only days from the first one the student ever
  marked complete are counted: before that there was no way to say a day was
  done (or they have not started saying so), and reading those days as
  missed would trim every plan at once. Until then nothing changes, and the
  strip still shows the fortnight's activity. A day answered on that the
  plan had as rest counts too, as extra.
* `rate` = (complete + half of partial) / study days.
* With fewer than `MIN_DAYS` study days to go on, nothing changes yet.
* Otherwise the minutes each day holds are scaled by `load`: the full plan at
  80% and over, then 85%, 70%, and at least 60% of it (never below the
  15-minute floor of engine.study_schedule).
* `RECOVER` complete study days in a row puts it back to the full plan,
  whatever the rate, so catching up is quick to reward.
* Keeping every day and spending well over the planned minutes on them moves
  it up a step (`UP`), since the plan is then smaller than the student.

The sets are smaller rather than fewer (engine._fit sizes them to the
minutes), so a lighter day still trains the same topics the same way.
`trend` compares this window's rate with the one before it.
"""
from datetime import date, timedelta

from backend.amc import engine

WINDOW = 14
MIN_DAYS = 4
RECOVER = 3
#: (rate at or above, load).
LOADS = ((0.8, 1.0), (0.5, 0.85), (0.25, 0.7), (0.0, 0.6))
#: Every day kept and this much more time than planned on them: a step up.
UP = (0.9, 1.25, 1.15)


def _day(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _window(plan, attempts, days_done, first, last, weekdays):
    """Each day from `first` to `last` (inclusive) with its status, and the counts."""
    active, seconds = set(), {}
    for a in attempts:
        if a.get('source') == 'reveal':
            continue
        d = a['at'][:10]
        active.add(d)
        seconds[d] = seconds.get(d, 0) + int(a.get('seconds') or 0)
    rows = []
    day = first
    while day <= last:
        iso = day.isoformat()
        study = day.weekday() in weekdays
        if iso in days_done:
            status = 'complete'
        elif iso in active:
            status = 'partial' if study else 'extra'
        else:
            status = 'missed' if study else 'rest'
        rows.append({'date': iso, 'study': study, 'status': status, 'minutes': round(seconds.get(iso, 0) / 60)})
        day += timedelta(days=1)
    studied = [r for r in rows if r['study']]
    complete = sum(1 for r in studied if r['status'] == 'complete')
    partial = sum(1 for r in studied if r['status'] == 'partial')
    rate = round((complete + 0.5 * partial) / len(studied), 2) if studied else None
    return rows, studied, complete, partial, rate


def read(plan, attempts, today):
    """{'rate', 'load', 'status', 'minutes', 'adjusted', 'days', 'text', ...} for this plan."""
    weekdays, minutes = engine.study_schedule(plan)
    days_done = plan.get('days_done') or {}
    marked = sorted(d for d in (_day(k) for k in days_done) if d)
    created = _day(plan.get('created_at')) or today
    last = today - timedelta(days=1)
    # What the strip shows: the fortnight, or since the plan was made.
    shown_from = max(min([created] + marked[:1]), today - timedelta(days=WINDOW))
    rows, _, _, _, _ = _window(plan, attempts, days_done, shown_from, last, weekdays)
    # What is counted: from the first day ever marked complete.
    started = marked[0] if marked else today
    first = max(started, today - timedelta(days=WINDOW))
    _, studied, complete, partial, rate = _window(plan, attempts, days_done, first, last, weekdays)
    # The two weeks before, for the trend.
    before_first = max(started, first - timedelta(days=WINDOW))
    _, before_studied, _, _, before_rate = _window(plan, attempts, days_done, before_first,
                                                   first - timedelta(days=1), weekdays) if before_first < first \
        else ([], [], 0, 0, None)
    run = 0
    for r in reversed(studied):
        if r['status'] != 'complete':
            break
        run += 1
    counted = [r for r in rows if r['date'] >= first.isoformat()]
    active_minutes = [r['minutes'] for r in counted if r['status'] in ('complete', 'partial', 'extra') and r['minutes']]
    avg = round(sum(active_minutes) / len(active_minutes)) if active_minutes else None
    extra = sum(1 for r in counted if r['status'] == 'extra')

    if len(studied) < MIN_DAYS:
        load, status = 1.0, 'new'
    elif run >= RECOVER:
        load, status = 1.0, 'on-track'
        if rate is not None and rate >= UP[0] and avg and avg >= UP[1] * minutes:
            load, status = UP[2], 'ahead'
    else:
        load = next(l for floor, l in LOADS if rate >= floor)
        status = 'on-track' if load == 1.0 else 'lighter'
        if load == 1.0 and rate >= UP[0] and avg and avg >= UP[1] * minutes:
            load, status = UP[2], 'ahead'
    adjusted = scaled(minutes, load)
    trend = None
    if rate is not None and before_rate is not None and len(before_studied) >= MIN_DAYS:
        trend = 'up' if rate >= before_rate + 0.15 else 'down' if rate <= before_rate - 0.15 else 'flat'
    out = {'window': WINDOW, 'rate': rate, 'load': load, 'status': status, 'minutes': minutes,
           'adjusted': adjusted, 'study_days': len(studied), 'complete': complete, 'partial': partial,
           'missed': len(studied) - complete - partial, 'extra': extra, 'run': run, 'avg_minutes': avg,
           'trend': trend, 'before_rate': before_rate, 'days': rows}
    out['text'] = _text(out)
    return out


def scaled(minutes, load):
    """A day's minutes at `load`, to the nearest five and never under the plan's 15-minute floor."""
    return max(15, int(round(minutes * load / 5.0)) * 5)


def _text(c):
    """One or two sentences: how the plan has been kept, and what that changes."""
    n, done = c['study_days'], c['complete']
    if c['status'] == 'new':
        if not c['study_days']:
            return ('Mark each study day complete when its list is done. After {} study days of that, the '
                    'plan sizes your days to how often you keep them.').format(MIN_DAYS)
        return ('{} of {} study days marked complete so far. After {}, the plan sizes your days to how often '
                'you keep them.').format(done, n, MIN_DAYS)
    kept = 'You completed {} of your last {} study days'.format(done, n)
    if c['partial']:
        kept += ' and did part of {} more'.format(c['partial'])
    kept += '.'
    if c['trend'] == 'up':
        kept += ' More than the two weeks before.'
    elif c['trend'] == 'down':
        kept += ' Fewer than the two weeks before.'
    if c['status'] == 'ahead':
        return kept + ' You are putting in more time than planned, so each day now holds about {} minutes ' \
                      '(from {}).'.format(c['adjusted'], c['minutes'])
    if c['status'] == 'on-track':
        return kept + ' Your days stay at the full {} minutes.'.format(c['minutes'])
    return kept + (' Each study day is trimmed to about {} minutes (from {}) so it fits. Complete {} study '
                   'days in a row to go back to the full plan.').format(c['adjusted'], c['minutes'], RECOVER)
