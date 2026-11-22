"""Everything an account does on the AMC pages is stored on the server.

A timed sitting in progress (`amc_sittings`) and an official paper unlocked
before a sitting (`amc_unlocks`) used to live in the browser's localStorage,
so they were lost on another device or a cleared browser. These pin that they
are now the account's: written through the API, read back on the contest
page, ended by handing in or leaving, kept apart between accounts, and gone
with the account.
"""
import json

from backend.amc import catalog, store
from backend.amc.bank import BY_ID
from backend.database.connection import connect

MOCK = 'step-mock-10'
PAPER = '2019-amc-10a'


def _rows(table, user):
    con = connect()
    try:
        return [dict(zip(r.keys(), tuple(r)))
                for r in con.execute('SELECT * FROM {} WHERE user_id = ?'.format(table), (user,)).fetchall()]
    finally:
        con.close()


# -- Sittings in progress ---------------------------------------------------
def test_a_new_contest_has_no_sitting(client):
    body = client.get('/api/amc/contests/' + MOCK).json()
    assert body['success'] and body['sitting'] is None and body['unlocked'] is False


def test_a_sitting_is_saved_and_read_back(client):
    reply = client.put('/api/amc/contests/{}/sitting'.format(MOCK),
                       json={'used': 125.5, 'answers': {'1': 'b', '3': 'E', '4': ''}, 'flags': [3, 3, 7]}).json()
    assert reply['success']
    sitting = client.get('/api/amc/contests/' + MOCK).json()['sitting']
    assert sitting['used'] == 125.5
    assert sitting['answers'] == {'1': 'B', '3': 'E'}       # upper-cased, blanks dropped
    assert sitting['flags'] == [3, 7]                         # de-duplicated, sorted
    row, = _rows('amc_sittings', 'tester')
    assert row['contest_id'] == MOCK and json.loads(row['answers']) == {'1': 'B', '3': 'E'}


def test_saving_again_replaces_the_sitting_and_keeps_its_start(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'used': 10, 'answers': {'1': 'A'}})
    first = client.get('/api/amc/contests/' + MOCK).json()['sitting']
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'used': 40, 'answers': {'2': 'C'}})
    second = client.get('/api/amc/contests/' + MOCK).json()['sitting']
    assert second['used'] == 40 and second['answers'] == {'2': 'C'}
    assert second['started_at'] == first['started_at']
    assert len(_rows('amc_sittings', 'tester')) == 1


def test_the_clock_is_capped_at_the_contest_length(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'used': 10 ** 7})
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting']['used'] == 75 * 60
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'used': -5})
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting']['used'] == 0


def test_an_aime_sitting_keeps_integer_answers(client):
    client.put('/api/amc/contests/step-mock-aime/sitting', json={'answers': {'1': 7, '15': '999'}})
    sitting = client.get('/api/amc/contests/step-mock-aime').json()['sitting']
    assert sitting['answers'] == {'1': '7', '15': '999'}
    assert client.get('/api/amc/contests/step-mock-aime').json()['contest']['minutes'] == 180


def test_an_answer_sheet_that_does_not_fit_the_paper_is_refused(client):
    for answers in ({'26': 'A'}, {'0': 'A'}, {'one': 'A'}, {'1': 'ABCD'}):
        reply = client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': answers}).json()
        assert not reply['success'], answers
    assert _rows('amc_sittings', 'tester') == []


def test_flags_outside_the_paper_are_dropped(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'flags': [0, 1, 25, 26]})
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting']['flags'] == [1, 25]


def test_no_sitting_on_a_contest_that_cannot_be_sat(client):
    assert not client.put('/api/amc/contests/no-such-contest/sitting', json={}).json()['success']
    # An official paper that has not been imported cannot be timed yet.
    assert not client.put('/api/amc/contests/{}/sitting'.format(PAPER), json={}).json()['success']


def test_leaving_discards_the_sitting(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': {'1': 'A'}})
    assert client.delete('/api/amc/contests/{}/sitting'.format(MOCK)).json()['success']
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting'] is None
    # Nothing was graded.
    assert client.get('/api/amc/contests/' + MOCK).json()['history'] == []


def test_handing_in_ends_the_sitting(client):
    first = catalog.MOCK_BY_ID[MOCK]['problems'][0]
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': {'1': BY_ID[first]['answer']}})
    reply = client.post('/api/amc/contests/{}/submit'.format(MOCK),
                        json={'answers': {'1': BY_ID[first]['answer']}, 'seconds': 60}).json()
    assert reply['success']
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting'] is None
    assert _rows('amc_sittings', 'tester') == []


def test_handing_in_one_contest_leaves_another_in_progress(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': {'1': 'A'}})
    client.put('/api/amc/contests/step-mock-12/sitting', json={'answers': {'2': 'B'}})
    client.post('/api/amc/contests/{}/submit'.format(MOCK), json={'answers': {'1': 'A'}})
    assert client.get('/api/amc/contests/step-mock-12').json()['sitting']['answers'] == {'2': 'B'}


def test_sittings_are_per_account(client, stranger):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': {'1': 'A'}})
    assert stranger.get('/api/amc/contests/' + MOCK).json()['sitting'] is None
    stranger.delete('/api/amc/contests/{}/sitting'.format(MOCK))
    assert client.get('/api/amc/contests/' + MOCK).json()['sitting']['answers'] == {'1': 'A'}


def test_signed_out_cannot_touch_a_sitting(anon):
    assert anon.put('/api/amc/contests/{}/sitting'.format(MOCK), json={}).status_code == 401
    assert anon.delete('/api/amc/contests/{}/sitting'.format(MOCK)).status_code == 401
    assert anon.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': True}).status_code == 401


def test_a_sitting_with_unreadable_json_reads_as_empty(client):
    store.write([('INSERT INTO amc_sittings (user_id, contest_id, used, answers, flags, started_at, updated_at) '
                  'VALUES (?, ?, ?, ?, ?, ?, ?)', ('tester', MOCK, 3, 'not json', '{"also": "bad"}', 'x', 'x'))])
    sitting = store.sitting('tester', MOCK)
    assert sitting['answers'] == {} and sitting['flags'] == [] and sitting['used'] == 3


# -- Papers unlocked before a sitting ----------------------------------------
def test_unlocking_a_paper_is_kept_on_the_account(client):
    assert client.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': True}).json()['unlocked'] is True
    assert store.unlocked('tester', PAPER)
    assert len(_rows('amc_unlocks', 'tester')) == 1
    # Unlocking twice is still one row.
    client.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': True})
    assert len(_rows('amc_unlocks', 'tester')) == 1
    client.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': False})
    assert not store.unlocked('tester', PAPER) and _rows('amc_unlocks', 'tester') == []


def test_only_an_official_paper_can_be_unlocked(client):
    assert not client.put('/api/amc/contests/{}/unlock'.format(MOCK), json={'on': True}).json()['success']
    assert not client.put('/api/amc/contests/nope/unlock', json={'on': True}).json()['success']
    # A mock never reads as unlocked: it is never locked.
    assert client.get('/api/amc/contests/' + MOCK).json()['unlocked'] is False


def test_unlocks_are_per_account(client, stranger):
    client.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': True})
    assert not store.unlocked('stranger', PAPER)


# -- The account owns its rows -----------------------------------------------
def test_deleting_the_account_takes_its_sittings_and_unlocks(client):
    client.put('/api/amc/contests/{}/sitting'.format(MOCK), json={'answers': {'1': 'A'}})
    client.put('/api/amc/contests/{}/unlock'.format(PAPER), json={'on': True})
    con = connect()
    try:
        with con:
            con.execute('DELETE FROM users WHERE username = ?', ('tester',))
    finally:
        con.close()
    assert _rows('amc_sittings', 'tester') == [] and _rows('amc_unlocks', 'tester') == []
