"""The two development seeders (scripts/seed_amc_demo.py and
scripts/seed_amc_history.py) write through the app's own connection, so they
fill whichever database the app is on: Postgres when DATABASE_URL is set.
These run them against the test database and check what they leave behind,
and that clearing an account reaches every AMC table the account owns,
including sittings in progress and unlocked papers."""
import importlib.util
import os

import pytest

from backend.amc import store
from backend.database.connection import connect
from tests.conftest import make_account

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT_TABLES = {'amc_attempts', 'amc_reviews', 'amc_mocks', 'amc_plans', 'amc_sittings', 'amc_unlocks',
                  'amc_set_runs', 'amc_plan_days'}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, 'scripts', name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _counts(user):
    con = connect()
    try:
        return {t: con.execute('SELECT COUNT(*) FROM {} WHERE user_id = ?'.format(t), (user,)).fetchall()[0][0]
                for t in sorted(ACCOUNT_TABLES)}
    finally:
        con.close()


def _user_tables():
    """Every amc_* table with a user_id column, read from the live schema."""
    con = connect()
    try:
        found = set()
        for table in ('amc_attempts', 'amc_reviews', 'amc_mocks', 'amc_plans', 'amc_official', 'amc_ai',
                      'amc_generated', 'amc_posts', 'amc_sittings', 'amc_unlocks', 'amc_set_runs', 'amc_plan_days'):
            try:
                con.execute('SELECT user_id FROM {} LIMIT 0'.format(table)).fetchall()
            except Exception:
                continue
            found.add(table)
        return found
    finally:
        con.close()


def test_the_seeders_clear_every_per_account_amc_table(fresh_db):
    # amc_ai keeps a per-account model budget, not study history: left alone.
    assert _user_tables() - {'amc_ai'} == ACCOUNT_TABLES
    assert set(_load('seed_amc_history').TABLES) == ACCOUNT_TABLES
    assert set(_load('seed_amc_demo').TABLES) == ACCOUNT_TABLES


@pytest.fixture
def history(fresh_db, monkeypatch):
    module = _load('seed_amc_history')
    # Only the original mocks: the official papers are pasted in per install,
    # so a test database has none of them.
    monkeypatch.setattr(module, 'SITTINGS', [(40, 'step-mock-10'), (20, 'mock-10-1'), (5, 'mock-10-2')])
    make_account('seeded')
    return module


def test_history_seeds_eight_weeks_of_practice(history, capsys):
    history.seed('seeded')
    counts = _counts('seeded')
    assert counts['amc_mocks'] == 3
    assert counts['amc_attempts'] > 200
    assert counts['amc_reviews'] > 10
    assert counts['amc_plans'] == 1
    assert 'Seeded seeded' in capsys.readouterr().out
    plan = store.plan('seeded')
    assert plan['target'] == 'AMC 10' and plan['checks']


def test_history_is_the_same_every_time(history):
    history.seed('seeded')
    first = sorted((r['problem_id'], r['correct']) for r in store.attempts('seeded'))
    history.clear('seeded')
    assert set(_counts('seeded').values()) == {0}
    history.seed('seeded')
    assert sorted((r['problem_id'], r['correct']) for r in store.attempts('seeded')) == first


def test_history_clear_takes_sittings_and_unlocks_too(history):
    history.seed('seeded')
    store.save_sitting('seeded', 'step-mock-12', 30, {'1': 'A'}, [])
    store.set_unlocked('seeded', '2019-amc-10a', True)
    history.clear('seeded')
    assert set(_counts('seeded').values()) == {0}


def test_history_only_touches_the_named_account(history):
    make_account('bystander')
    store.save_sitting('bystander', 'step-mock-10', 5, {}, [])
    history.seed('seeded')
    history.clear('seeded')
    assert _counts('bystander')['amc_sittings'] == 1


def test_history_reports_an_unimported_paper(history, monkeypatch):
    monkeypatch.setattr(history, 'SITTINGS', [(10, '2019-amc-10a')])
    with pytest.raises(SystemExit, match='not fully imported'):
        history.seed('seeded')


def test_demo_builds_its_own_account_with_history(fresh_db):
    demo = _load('seed_amc_demo')
    demo.ensure_account()
    demo.seed()
    counts = _counts(demo.USERNAME)
    assert counts['amc_attempts'] > 0 and counts['amc_mocks'] >= 1 and counts['amc_plans'] == 1
    demo.clear()
    assert set(_counts(demo.USERNAME).values()) == {0}
