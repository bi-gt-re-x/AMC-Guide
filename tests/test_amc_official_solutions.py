"""Summit's own solutions to official papers (backend/amc/official_solutions.py),
and how an imported paper serves them."""
import re

import pytest

from backend.amc import catalog, official, official_solutions
from backend.amc.official_solutions import SOLUTIONS

KEY_2026_10A = 'BADACAACDCDDCBBDCDCCCADDB'


@pytest.fixture(autouse=True)
def _tester_imports(monkeypatch):
    monkeypatch.setenv('AMC_IMPORTERS', 'temu,tester')


def _texts(entry):
    return [entry['insight'], entry['trap']] + entry['steps']


@pytest.mark.parametrize('pid', sorted(SOLUTIONS))
def test_each_solution_ends_on_its_answer_and_is_clean_tex(pid):
    entry = SOLUTIONS[pid]
    assert official.split_id(pid), pid
    assert len(entry['steps']) >= 2 and entry['insight'] and entry['trap']
    assert entry['topics'] and all(t in catalog.TOPIC_BY_ID for t in entry['topics'])
    # As the paper writes it: `\textbf{(B)}` or `\textbf{(B) }`.
    assert re.search(r'\\textbf\{\(' + entry['answer'] + r'\)\s*\}', entry['steps'][-1]), entry['steps'][-1]
    for text in _texts(entry):
        # A '' inside r'...' silently ends the raw string; a \f or \b then
        # turns into a control character instead of \frac or \binom.
        assert not re.search(r'[\x00-\x09\x0b-\x1f]', text), (pid, text)
        assert len(re.findall(r'(?<!\\)\$', text)) % 2 == 0, (pid, text)


def test_the_2026_amc_10a_is_written_up_against_its_key():
    assert [SOLUTIONS['2026-amc-10a-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2026_10A)


def test_a_solution_is_withheld_when_the_key_disagrees():
    assert official_solutions.for_problem('2026-amc-10a-1', 'B')['answer'] == 'B'
    assert official_solutions.for_problem('2026-amc-10a-1', 'C') is None
    assert official_solutions.for_problem('2023-amc-10a-1', 'A') is None


def _paper(key):
    body = '\n'.join(
        'Problem %d\nWhat is $%d+0$?\n\n$\\textbf{(A) }%d\\qquad\\textbf{(B) }%d\\qquad'
        '\\textbf{(C) }%d\\qquad\\textbf{(D) }%d\\qquad\\textbf{(E) }%d$\n\nSolution\n'
        % (n, n, n, n + 1, n + 2, n + 3, n + 4) for n in range(1, 26))
    return body, key


def test_an_imported_paper_serves_the_write_ups_only_on_request(client):
    body, key = _paper(KEY_2026_10A)
    assert client.post('/api/amc/contests/2026-amc-10a/import',
                       json={'problems': body, 'key': key, 'save': True}).json()['saved']

    # The contest page (which the timed sitting also loads) says a write-up
    # exists but carries no answers.
    detail = client.get('/api/amc/contests/2026-amc-10a').json()
    first = detail['problems'][0]
    assert first['has_solution'] and 'answer' not in first and 'solution' not in first
    assert first['topic'] == 'word-problems'          # the write-up's topic, not the keyword guess
    assert first['progress'] == 'new'

    key_rows = client.get('/api/amc/contests/2026-amc-10a/key').json()
    assert key_rows['written'] == 25 and key_rows['key'][0]['answer'] == 'B'
    assert key_rows['key'][0]['solution'][-1].endswith(r'$\textbf{(B)}\ 54$.')
    assert not client.get('/api/amc/contests/2023-amc-10a/key').json()['success']

    # Answering reveals it on the problem page, as for any problem with a write-up.
    reply = client.post('/api/amc/problems/2026-amc-10a-1/attempt', json={'answer': 'A'}).json()
    assert reply['problem']['solution'] and reply['problem']['insight']
    client.post('/api/amc/problems/2026-amc-10a-1/attempt', json={'answer': 'B'})
    client.post('/api/amc/problems/2026-amc-10a-2/attempt', json={'answer': 'A'})
    client.post('/api/amc/problems/2026-amc-10a-3/attempt', json={'answer': 'A'})
    progress = [p['progress'] for p in client.get('/api/amc/contests/2026-amc-10a').json()['problems'][:4]]
    assert progress == ['fixed', 'first', 'open', 'new']


def test_text_copied_from_the_rendered_page_is_read():
    source = (
        'Problem 1\nA square is shown.\n\n[asy] draw(unitsquare); [/asy]\n\nWhat is its area?\n\n'
        r'$\textbf{(A)}~1\qquad\textbf{(B)}~2\qquad\textbf{(C)}~3\qquad\textbf{(D)}~4\qquad'
        r'\textbf{(E)}~\text{The node } \dfrac{1}{2} \text{ is not shown.}$' '\n\nSolution\n\n'
        'Problem 2\nSolve\n\n\\[x=1\\]\\[y=2\\]$\\textbf{(A) } 1 \\qquad\\textbf{(B) } 2 \\qquad\\textbf{(C) } 3 '
        '\\qquad\\textbf{(D) } 4 \\qquad\\textbf{(E) } ~\\text{ none}$\n\nSolution\n')
    one, two = official.parse_contest(source, 'AMC 10')
    assert 'draw(unitsquare)' in one['diagram'] and '[asy]' not in one['statement']
    assert 'Solution' not in one['statement'] and 'Solution' not in two['statement']
    assert one['choices'][4] == r'$\text{The node } \dfrac{1}{2} \text{ is not shown.}$'
    assert two['choices'][4] == 'none'
    assert '$$x=1$$\n\n$$y=2$$' in two['statement']


def test_latex_that_katex_cannot_draw_is_converted():
    source = (
        'Problem 1\nThe rows:\n\n$\\begin{tabular}{cc} 1&2\\\\ 3&4 \\end{tabular}$\n\nThe sum is?\n\n'
        '$\\textbf{(A) } 1 \\qquad\\textbf{(B) } 2 \\qquad\\textbf{(C) } 3 \\qquad\\textbf{(D) } 4 \\qquad\\textbf{(E) } 5$\n\n'
        'Problem 2\nSolve\n\n\\begin{align*} x+y&\\le 2\\\\ x-y&\\le 0 \\end{align*}\n\n'
        '$\\textbf{(A) } 1 \\qquad\\textbf{(B) } 2 \\qquad\\textbf{(C) } 3 \\qquad\\textbf{(D) } 4 \\qquad\\textbf{(E) } 5$\n\n'
        'Problem 3\nThe cost was $\\$ \\underline A.\\underline B$ in all.\n\n'
        '$\\textbf{(A)}~7 \\qquad \\textbf{(B)}~8 \\qquad \\textbf{(C)}~11 \\qquad \\textbf{(D)}~14 \\qquad \\textbf{(E)}~15$\n\n'
        'Problem 4\nA product\n\n\\[\\prod_{k=1}^{3} k ?\\]$\\textbf{(A) } 1 \\qquad\\textbf{(B) } 2 \\qquad'
        '\\textbf{(C) } 3 \\qquad\\textbf{(D) } 6 \\qquad\\textbf{(E) } 9$\n')
    one, two, three, four = official.parse_contest(source, 'AMC 10')
    assert '\\begin{array}{cc}' in one['statement'] and 'tabular' not in one['statement']
    assert '$$\\begin{aligned}x+y&\\le 2' in two['statement'] and 'align*' not in two['statement']
    assert three['choices'] == ['$7$', '$8$', '$11$', '$14$', '$15$']
    assert three['statement'].startswith('The cost was $\\$')
    assert four['statement'].endswith('$$\\prod_{k=1}^{3} k ?$$') and four['choices'][3] == '$6$'
    for p in (one, two, three, four):
        assert len(re.findall(r'(?<!\\)\$', p['statement'])) % 2 == 0, p['statement']


@pytest.mark.parametrize('contest, key', [
    ('2025-amc-10a', 'EBDAECEBCCEDDBADEBAACBDCA'),
    ('2025-amc-10b', 'BDDACCCCCABCACDDBDDACACEB'),
])
def test_the_2025_papers_are_written_up_against_their_keys(contest, key):
    assert [SOLUTIONS['%s-%d' % (contest, n)]['answer'] for n in range(1, 26)] == list(key)
