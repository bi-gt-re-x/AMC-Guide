"""Every problem the site can serve: the original bank plus imported official
problems and the AI-written ones (backend/amc/create.py). Everything that looks
a problem up goes through here, so an official or AI problem can be answered, reviewed, searched and sat in a timed contest exactly
like a bank one.
"""
from backend.amc import bank, create, official


def all_problems():
    return bank.PROBLEMS + official.all_problems() + create.all_problems()


def get(pid):
    return bank.BY_ID.get(pid) or official.get(pid) or create.get(pid)


def by_id():
    return {p['id']: p for p in all_problems()}


def is_official(pid):
    """Whether `pid` is a real contest problem, not a mock, bank or AI one."""
    return bool(official.split_id(pid))


def mix_sources(rows, key=lambda r: 0):
    """`rows` (anything with an 'id') in `key` order, real contest problems and
    mock ones interleaved in proportion within each run of equal `key`, each
    kind keeping the order it came in.

    Every list used to break ties by contest order, which puts the Step Mocks
    before every official paper: a filtered list, a topic's problems at one
    rating, a practice set's easiest level all opened with a run of mock
    problems and only then reached a real one. `rows` must already be in the
    order wanted within each kind."""
    streams = {}
    for r in rows:
        streams.setdefault((key(r), is_official(r['id'])), []).append(r['id'])
    pos = {}
    for ids in streams.values():
        for i, pid in enumerate(ids):
            pos[pid] = (i + 0.5) / len(ids)
    return sorted(rows, key=lambda r: (key(r), pos[r['id']], not is_official(r['id'])))
