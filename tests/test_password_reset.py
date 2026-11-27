"""Forgot your password: a link by email, good once for an hour, that sets a
new password, signs in, and ends every other session of the account."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.database import connection as db
from backend.tracking import auth
from tests.conftest import PASSWORD, make_account, sign_in

NEW = 'Brand-new-pass-42!'


@pytest.fixture
def mail(monkeypatch):
    """Every email the app sends, instead of sending it."""
    sent = []
    monkeypatch.setattr(auth, '_send_mail', lambda to, subject, body, html=None: sent.append(
        {'to': to, 'subject': subject, 'body': body, 'html': html}) or True)
    return sent


def _link(mail):
    body = mail[-1]['body']
    return body[body.index('/reset/'):].split()[0]


def _rows(user):
    con = db.connect()
    try:
        return [dict(zip(r.keys(), tuple(r))) for r in
                con.execute('SELECT * FROM password_resets WHERE user_id = ?', (user,)).fetchall()]
    finally:
        con.close()


def _ask(client, email='tester@example.test'):
    return client.post('/api/auth/forgot', json={'email': email}).json()


def test_asking_says_the_same_with_or_without_an_account(app, mail):
    make_account('tester')
    known, unknown = _ask(TestClient(app)), _ask(TestClient(app), 'nobody@example.test')
    assert known['success'] and unknown['success']
    assert known['message'].replace('tester@', 'X@') == unknown['message'].replace('nobody@', 'X@')
    assert known['dev_link'] is None and unknown['dev_link'] is None
    assert len(mail) == 1 and mail[0]['to'] == 'tester@example.test'
    assert 'Reset your AMC Guide password' == mail[0]['subject'] and '/reset/' in mail[0]['body']


def test_only_a_hash_of_the_token_is_stored(app, mail):
    make_account('tester')
    _ask(TestClient(app))
    token = _link(mail).rsplit('/', 1)[1]
    [row] = _rows('tester')
    assert token not in row.values() and row['token_hash'] == auth._token_hash(token)
    assert row['used_at'] is None and row['expires_at'] > row['created_at']


def test_the_link_sets_a_new_password_and_signs_in(app, mail):
    make_account('tester')
    browser = TestClient(app)
    _ask(browser)
    opened = browser.get(_link(mail), follow_redirects=False)
    assert opened.status_code == 303 and opened.headers['location'] == '/login?auth=reset'
    status = browser.get('/api/auth/reset').json()
    assert status == {'success': True, 'valid': True, 'email': 'tester@example.test'}
    weak = browser.post('/api/auth/reset', json={'password': 'short'}).json()
    assert not weak['success'] and weak['field'] == 'password'
    done = browser.post('/api/auth/reset', json={'password': NEW}).json()
    assert done['success'] and done['user']['username'] == 'tester'
    # Signed in, with the new password; the old one opens nothing.
    assert browser.get('/api/amc/dashboard').status_code == 200
    assert TestClient(app).post('/api/login', json={'username': 'tester', 'password': NEW}).json()['success']
    assert not TestClient(app).post('/api/login', json={'username': 'tester', 'password': PASSWORD}).json()['success']


def test_a_link_works_once(app, mail):
    make_account('tester')
    browser = TestClient(app)
    _ask(browser)
    link = _link(mail)
    browser.get(link, follow_redirects=False)
    assert browser.post('/api/auth/reset', json={'password': NEW}).json()['success']
    again = TestClient(app)
    assert again.get(link, follow_redirects=False).headers['location'] == '/login?auth=forgot&reset=invalid'
    reply = again.post('/api/auth/reset', json={'password': 'Another-pass-77!'}).json()
    assert not reply['success'] and reply['expired']


def test_a_newer_link_spends_the_older_one(app, mail):
    make_account('tester')
    _ask(TestClient(app))
    first = _link(mail)
    _ask(TestClient(app))
    assert TestClient(app).get(first, follow_redirects=False).headers['location'].endswith('reset=invalid')
    assert TestClient(app).get(_link(mail), follow_redirects=False).headers['location'] == '/login?auth=reset'


def test_a_link_runs_out_after_an_hour(app, mail):
    make_account('tester')
    user = auth.find_user(db.users(), username='tester')
    token = auth.new_reset_token(user, now=datetime.now() - auth.RESET_TTL - timedelta(minutes=1))
    assert auth.reset_user(token) is None
    assert auth.reset_user(auth.new_reset_token(user)) is not None


def test_resetting_ends_every_other_session(app, mail):
    make_account('tester')
    elsewhere = sign_in(app, 'tester')
    assert elsewhere.get('/api/amc/dashboard').status_code == 200
    browser = TestClient(app)
    _ask(browser)
    browser.get(_link(mail), follow_redirects=False)
    assert browser.post('/api/auth/reset', json={'password': NEW}).json()['success']
    # The device that was signed in with the old password is signed out.
    assert elsewhere.get('/api/amc/dashboard').status_code == 401
    assert not elsewhere.post('/api/auth/complete_profile', json={'username': 'taken-over'}).json()['success']
    # Signing in again with the new one works as ever.
    assert elsewhere.post('/api/login', json={'username': 'tester', 'password': NEW}).json()['success']
    assert elsewhere.get('/api/amc/dashboard').status_code == 200


def test_without_mail_a_dev_server_hands_the_link_back(app, monkeypatch):
    make_account('tester')
    monkeypatch.setattr(auth, '_send_mail', lambda *a, **k: False)
    monkeypatch.setattr('backend.config.settings.dev_mode', lambda: True)
    reply = _ask(TestClient(app))
    assert reply['dev_link'] and '/reset/' in reply['dev_link']
    assert _ask(TestClient(app), 'nobody@example.test')['dev_link'] is None
    monkeypatch.setattr('backend.config.settings.dev_mode', lambda: False)
    assert _ask(TestClient(app))['dev_link'] is None


def test_asking_is_rate_limited(app, mail):
    make_account('tester')
    client = TestClient(app)
    replies = [client.post('/api/auth/forgot', json={'email': 'tester@example.test'}) for _ in range(7)]
    assert replies[-1].status_code == 429
    assert len(mail) == 5
