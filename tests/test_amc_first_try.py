"""First-try accuracy, as the Topics page colours its cards by it: of the
problems whose first try had an answer in it, the share right first time. A
solution shown before answering is a blank, and does not count either way."""
from backend.amc import catalog, engine
from backend.amc.bank import BY_ID


def _row(pid, correct, source='practice', answer='X', at='2026-11-01T10:00:00'):
    return {'problem_id': pid, 'answer': answer, 'correct': 1 if correct else 0, 'seconds': 60,
            'source': source, 'at': at}


def test_a_revealed_first_try_is_a_blank():
    hist = engine.history([_row('a', False, 'reveal', ''), _row('a', True, at='2026-11-02T10:00:00'),
                           _row('b', True), _row('c', False)])
    assert hist['a']['first_blank'] and not hist['b']['first_blank'] and not hist['c']['first_blank']
    # `a` was shown before it was tried, so it counts neither way.
    assert engine.first_try(['a', 'b', 'c', 'never'], hist) == (2, 1, 0.5)
    assert engine.first_try(['a', 'never'], hist) == (0, 0, None)


def test_topic_stats_carry_first_try_beside_the_older_accuracy():
    topic = BY_ID['step-10-01']['topic']
    ids = [pid for pid, p in BY_ID.items() if p['topic'] == topic][:4]
    hist = engine.history([_row(ids[0], True), _row(ids[1], True), _row(ids[2], False),
                           _row(ids[3], False, 'reveal', '')])
    s = engine.topic_stats(hist, {})[topic]
    assert (s['answered'], s['answered_right'], s['first_try']) == (3, 2, 0.667)
    # The older measure still counts the reveal as a miss.
    assert s['attempted'] == 4 and s['accuracy'] == 0.5
    untouched = next(t['id'] for t in catalog.TOPICS if t['id'] != topic)
    assert engine.topic_stats(hist, {})[untouched]['first_try'] is None


def test_the_topics_and_strategies_pages_send_it(client):
    pid = 'step-10-01'
    client.post('/api/amc/problems/{}/attempt'.format(pid), json={'answer': str(BY_ID[pid]['answer'])})
    topic = BY_ID[pid]['topic']
    cards = [t for c in client.get('/api/amc/topics').json()['categories'] for t in c['topics']]
    mine = next(t for t in cards if t['id'] == topic)
    assert mine['first_try'] == 1.0 and mine['answered'] == 1
    techniques = [t for f in client.get('/api/amc/strategies').json()['families'] for t in f['techniques']]
    tech = next(t for t in techniques if t['id'] == BY_ID[pid]['technique'])
    assert tech['first_try'] == 1.0 and tech['answered'] == 1
    assert all(t['first_try'] is None for t in techniques if t['id'] != tech['id'] and not t['answered'])
