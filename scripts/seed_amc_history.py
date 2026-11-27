"""Eight weeks of believable AMC 10 history on an existing account, for trying
the Review, Analytics and Dashboard pages with real-looking data.

    .venv-fastapi/bin/python scripts/seed_amc_history.py --user myles           # seed
    .venv-fastapi/bin/python scripts/seed_amc_history.py --user myles --replace # reseed
    .venv-fastapi/bin/python scripts/seed_amc_history.py --user myles --clear   # remove

Development only. Writes to whatever database the app is configured for, so
never point it at production. It refuses to touch an account that already has
AMC rows unless --replace (or --clear) says so.

The student is simulated, not scripted: a level on AMC Guide's 1-10 scale that
climbs from 3.0 to about 4.2 over the eight weeks, stronger in algebra and
weaker in geometry and counting, answering each problem with the chance
backend/amc/smart.py's model gives. On most days it practises a handful of
AMC Guide and Step mock problems and works whatever reviews are due (a review it
knows is a little easier than a first try). It sits the Step Mock and three
AMC Guide Mock AMC 10 sets, and three older official papers (the 2018 AMC 10A and
the 2019 AMC 10A and 10B), which unlocks those papers for the account. Every
miss goes through backend/amc/engine.py's review schedule on the day it
happened, so the error log is exactly what the app would have built. A study
plan for the 2027 AMC 10A finishes it off. The random draw is fixed, so a
reseed gives the same history.
"""
import argparse
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.config import settings  # noqa: E402

settings.load_dotenv()

from backend.amc import catalog, engine, official, smart, store  # noqa: E402
from backend.amc import problems as pb  # noqa: E402
from backend.database.connection import connect  # noqa: E402

TABLES = ('amc_attempts', 'amc_reviews', 'amc_mocks', 'amc_plans', 'amc_sittings', 'amc_unlocks', 'amc_set_runs', 'amc_plan_days',
          'amc_miss_reasons')
DAYS = 56
# The level on the 1-10 scale, start to finish, and how each category sits
# against it.
START, END = 3.0, 4.2
LEAN = {'algebra': 0.5, 'number-theory': 0.2, 'misc': 0.0, 'counting': -0.5, 'geometry': -0.7}
# (days ago, contest): the sittings.
SITTINGS = [(54, 'step-mock-10'), (47, '2018-amc-10a'), (40, 'mock-10-1'), (31, '2019-amc-10b'),
            (24, 'mock-10-2'), (13, '2019-amc-10a'), (5, 'mock-10-3')]


def account_exists(user):
    con = connect()
    try:
        return bool(con.execute('SELECT 1 FROM users WHERE username = ?', (user,)).fetchall())
    finally:
        con.close()


def row_count(user):
    con = connect()
    try:
        return sum(con.execute('SELECT COUNT(*) FROM {} WHERE user_id = ?'.format(t), (user,)).fetchall()[0][0]
                   for t in TABLES)
    finally:
        con.close()


def clear(user):
    store.write([('DELETE FROM {} WHERE user_id = ?'.format(t), (user,)) for t in TABLES])


def wrong_choice(p, rng):
    if p['level'] == 'AIME':
        return str((int(p['answer']) + rng.randint(1, 400)) % 1000)
    return rng.choice([c for c in 'ABCDE' if c != str(p['answer'])])


class Student:
    def __init__(self, user, today, rng):
        self.user, self.today, self.rng = user, today, rng
        self.rows, self.reviews, self.solved = [], {}, set()

    def level(self, day, p):
        progress = 1 - (self.today - day).days / DAYS
        cat = catalog.TOPIC_BY_ID[p['topic']]['category']
        return START + (END - START) * progress + LEAN.get(cat, 0)

    def stamp(self, day, minute):
        hour, minute = 16 + minute // 60, minute % 60
        return datetime(day.year, day.month, day.day, min(hour, 22), minute).isoformat(timespec='seconds')

    def answer(self, day, minute, p, source, boost=0.0):
        chance = min(0.97, smart.chance(self.level(day, p), p['rating']) + boost)
        right = self.rng.random() < chance
        seconds = int(max(25, self.rng.gauss(45 + 32 * p['rating'], 25)))
        given = str(p['answer']) if right else wrong_choice(p, self.rng)
        self.rows.append(store.attempt_rows(self.user, p['id'], given, right, seconds, source))
        self.rows[-1] = (self.rows[-1][0], self.rows[-1][1][:-1] + (self.stamp(day, minute),))
        self.schedule(day, p['id'], right)
        if right:
            self.solved.add(p['id'])
        return right, given, seconds

    def schedule(self, day, pid, right):
        row = engine.after_answer(self.reviews.get(pid), pid, right, day)
        if row:
            row['added_at'] = row.get('added_at') or self.stamp(day, 0)
            self.reviews[pid] = row

    def reveal(self, day, minute, p):
        self.rows.append(store.attempt_rows(self.user, p['id'], '', False, 0, 'reveal'))
        self.rows[-1] = (self.rows[-1][0], self.rows[-1][1][:-1] + (self.stamp(day, minute),))
        self.schedule(day, p['id'], False)

    def sit(self, day, contest_id, mock):
        answers, seconds_total = {}, 0
        for number, pid in enumerate(mock['problems'], start=1):
            p = pb.get(pid)
            chance = smart.chance(self.level(day, p), p['rating'])
            if chance < 0.28 and self.rng.random() < 0.8:
                answers[str(number)] = ''        # left blank: still goes to review
                self.schedule(day, pid, False)
                continue
            right = self.rng.random() < chance
            given = str(p['answer']) if right else wrong_choice(p, self.rng)
            answers[str(number)] = given
            self.rows.append(store.attempt_rows(self.user, pid, given, right, 0, 'mock'))
            self.rows[-1] = (self.rows[-1][0], self.rows[-1][1][:-1] + (self.stamp(day, 75),))
            self.schedule(day, pid, right)
            if right:
                self.solved.add(pid)
            seconds_total += 1
        graded = engine.score_mock(mock, answers)
        answers['_ids'] = list(mock['problems'])
        seconds = int(self.rng.uniform(0.86, 1.0) * mock.get('minutes', 75) * 60)
        _, insert = store.mock_row(self.user, contest_id, 'mock', answers, graded['score'], graded['correct'],
                                   graded['wrong'], graded['blank'], seconds)
        sql, params = insert
        self.rows.append((sql, params[:-1] + (self.stamp(day, 75),)))
        return graded


def gradable(contest_id):
    if contest_id in catalog.MOCK_BY_ID:
        return catalog.MOCK_BY_ID[contest_id]
    past = catalog.PAST_BY_ID[contest_id]
    ids = [official.problem_id(contest_id, n) for n in range(1, past['count'] + 1)]
    missing = [pid for pid in ids if not pb.get(pid)]
    if missing:
        raise SystemExit('{} is not fully imported ({} missing).'.format(contest_id, len(missing)))
    return {'id': contest_id, 'name': past['name'], 'level': past['level'], 'problems': ids, 'minutes': 75}


def seed(user):
    today = date.today()
    rng = random.Random('summit-amc-history-v1')
    s = Student(user, today, rng)
    sit_on = {today - timedelta(days=d): c for d, c in SITTINGS}
    # Practice comes from the AMC Guide and Step mocks (AMC 10, and the easier AMC
    # 12 problems), never from a paper before the day it is sat.
    practice = [p for p in pb.all_problems() if not p.get('official') and not p.get('ai')
                and (p['level'] == 'AMC 10' or (p['level'] == 'AMC 12' and p['rating'] <= 4.5))]
    rng.shuffle(practice)
    practice.sort(key=lambda p: p['rating'] + rng.uniform(-1.2, 1.2))
    queue = list(practice)
    sat_after = {}
    for d, contest in SITTINGS:
        for pid in gradable(contest)['problems']:
            sat_after[pid] = today - timedelta(days=d)
    checks = {}
    for back in range(DAYS, -1, -1):
        day = today - timedelta(days=back)
        minute = rng.randint(0, 50)
        done = []
        if day in sit_on:
            contest = sit_on[day]
            s.sit(day, contest, gradable(contest))
            done.append('mock')
        if rng.random() < 0.72 or day in sit_on:
            # Reviews due today, at most eight.
            due = sorted((r for r in s.reviews.values() if r['status'] == 'active' and r['due'] <= day.isoformat()),
                         key=lambda r: r['due'])[:8]
            for r in due:
                s.answer(day, minute, pb.get(r['problem_id']), 'review', boost=0.22)
                minute += 4
            if due:
                done.append('review')
            # New practice, easiest-unsolved-first with some wandering.
            for _ in range(rng.randint(3, 8) if day not in sit_on else rng.randint(0, 2)):
                open_ = [i for i, q in enumerate(queue[:40])
                         if q['id'] not in s.solved and q['id'] not in s.reviews
                         and sat_after.get(q['id'], day) <= day]
                if not open_:
                    break
                p = queue.pop(open_[min(len(open_) - 1, rng.randint(0, 3))])
                if rng.random() < 0.03:
                    s.reveal(day, minute, p)
                else:
                    s.answer(day, minute, p, 'practice')
                minute += 5
            done.append('practice')
        if back <= 14 and done:
            checks[day.isoformat()] = sorted(set(done) & {'review', 'practice'})
    for row in s.reviews.values():
        sql = store.review_upsert(user, row)
        # Keep the day the miss happened as both added_at and updated_at.
        delete, insert = sql
        params = list(insert[1])
        params[-1] = row['added_at']
        s.rows += [delete, (insert[0], tuple(params))]
    store.write(s.rows)
    exam = date(2027, 11, 4)
    store.save_plan(user, 'AMC 10', exam.isoformat(), 120, 7, checks)
    attempts = sum(1 for sql, _ in s.rows if sql.startswith('INSERT INTO amc_attempts'))
    mocks = sum(1 for sql, _ in s.rows if sql.startswith('INSERT INTO amc_mocks'))
    print('Seeded {}: {} answers, {} sittings, {} problems in the error log ({} mastered).'.format(
        user, attempts, mocks, len(s.reviews), sum(1 for r in s.reviews.values() if r['status'] == 'mastered')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--user', required=True)
    parser.add_argument('--replace', action='store_true', help='clear the account\'s AMC rows first')
    parser.add_argument('--clear', action='store_true', help='only clear the account\'s AMC rows')
    args = parser.parse_args()
    if not account_exists(args.user):
        raise SystemExit('No account named {!r}.'.format(args.user))
    if args.clear:
        clear(args.user)
        print('Cleared AMC rows for {}.'.format(args.user))
        sys.exit(0)
    if row_count(args.user) and not args.replace:
        raise SystemExit('{} already has AMC rows; pass --replace to start over.'.format(args.user))
    if args.replace:
        clear(args.user)
    seed(args.user)
