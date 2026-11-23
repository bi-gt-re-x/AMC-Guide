"""The account's data lives in the database, not in the browser.

Two things used to be kept only in localStorage and so were lost on another
device or a cleared browser: a timed sitting in progress and an official
paper unlocked before sitting it. Both are tables now (`amc_sittings`,
`amc_unlocks`; see tests/test_amc_storage.py). What is still written to
browser storage is listed here with the reason it may stay there: a cache of
something the server holds, a per-tab convenience, or a view setting. A new
file that writes browser storage fails this test until it is either moved to
the server or added here with its reason.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'frontend', 'src')
WRITES = re.compile(r'\b(?:window\.)?(localStorage|sessionStorage)\.setItem\(')

#: file -> why what it writes may stay in the browser.
ALLOWED = {
    'services/auth.ts': 'a cache of the username; the session cookie is the identity',
    'utils/themeLook.ts': 'a cache of the account\'s look, read before the first paint',
    'components/Rail.tsx': 'a cache of the account\'s folded-rail preference, and which rail groups are open',
    'components/VerifyBanner.tsx': 'per-tab: the banner was dismissed for this tab',
    'components/Topbar.tsx': 'per-tab: the easter-egg chain\'s pass for this tab',
    'utils/settingsExit.ts': 'per-tab: the page to go back to when Settings closes',
    'utils/easterEgg.ts': 'the easter-egg chain, which has no server side by design',
    'utils/rankTitle.ts': 'a title from the easter-egg chain, kept where that chain lives',
    'pages/amc/weakSet.ts': 'per-tab: the weak-topics set being walked on the Review page',
    'pages/amc/practiceSetStore.ts': 'per-tab: the topic practice set being walked from its page',
    'pages/amc/Review.tsx': 'a view setting: whether the weak-topics set draws from the mocks',
}


def _writers():
    found = {}
    for folder, _dirs, files in os.walk(SRC):
        if 'test' in os.path.relpath(folder, SRC).split(os.sep):
            continue
        for name in files:
            if not name.endswith(('.ts', '.tsx')) or '.test.' in name:
                continue
            path = os.path.join(folder, name)
            with open(path, encoding='utf-8') as handle:
                if WRITES.search(handle.read()):
                    found[os.path.relpath(path, SRC).replace(os.sep, '/')] = True
    return set(found)


def test_only_listed_files_write_browser_storage():
    unexpected = _writers() - set(ALLOWED)
    assert not unexpected, (
        'These write localStorage/sessionStorage. Account data belongs in the database '
        '(an API endpoint and a table); if this really is a cache or a per-tab convenience, '
        'add it to ALLOWED with the reason:\n' + '\n'.join(sorted(unexpected)))


def test_the_allow_list_has_no_stale_entries():
    assert set(ALLOWED) - _writers() == set(), 'Remove entries for files that no longer write storage.'


def test_sittings_and_unlocks_are_not_written_to_the_browser():
    for page in ('pages/amc/TakeMock.tsx', 'pages/amc/Contest.tsx'):
        with open(os.path.join(SRC, page), encoding='utf-8') as handle:
            assert not WRITES.search(handle.read()), page
