"""Summit's own solutions to official papers (backend/amc/official_solutions.py),
and how an imported paper serves them."""
import re

import pytest

from backend.amc import catalog, official, official_solutions
from backend.amc.official_solutions import SOLUTIONS

KEY_2026_10A = 'BADACAACDCDDCBBDCDCCCADDB'
KEY_2026_10B = 'DDCDBCADDEBDEEDEBCDECCDCA'
KEY_2018_10B = 'ADBBDDDCDECCCDAEBDEBCCBCC'
KEY_2017_10A = 'CDBBCBABCBDEDDCBDDCDDEBCA'
KEY_2017_10B = 'BCEDDBCCDEDACDEABDEBDDCCE'
KEY_2026_12A = 'ADACACACEBDECCACADDDDCDDB'


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


def test_the_2026_amc_10b_is_written_up_against_its_key():
    assert [SOLUTIONS['2026-amc-10b-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2026_10B)


def test_the_2018_amc_10b_is_written_up_against_its_key():
    assert [SOLUTIONS['2018-amc-10b-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2018_10B)


def test_the_2017_amc_10a_is_written_up_against_its_key():
    assert [SOLUTIONS['2017-amc-10a-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2017_10A)


def test_the_2017_amc_10b_is_written_up_against_its_key():
    assert [SOLUTIONS['2017-amc-10b-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2017_10B)


def test_the_2026_amc_12a_is_written_up_against_its_key():
    assert [SOLUTIONS['2026-amc-12a-%d' % n]['answer'] for n in range(1, 26)] == list(KEY_2026_12A)


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


def test_the_2024_amc_10b_is_written_up_except_the_missing_table():
    key = 'BBEDBBADAACABBCADBCACABEE'
    assert '2024-amc-10b-19' not in SOLUTIONS
    assert [SOLUTIONS['2024-amc-10b-%d' % n]['answer'] for n in range(1, 26) if n != 19] \
        == [k for n, k in enumerate(key, 1) if n != 19]


def test_a_picture_the_wiki_failed_to_render_is_a_missing_figure():
    source = (
        'Problem 1\nHow many entries are possible?\n\n'
        'Error creating thumbnail: Unable to save thumbnail to destination $\\textbf{(A) } 4 \\qquad '
        '\\textbf{(B) } 5 \\qquad \\textbf{(C) } 6 \\qquad \\textbf{(D) } 7 \\qquad \\textbf{(E) } 9$\n\n'
        '[Solution](https://example.org/Problem_1)\n'
        'Problem 2\nWhat is length $x$? [Error creating thumbnail: Unable to save thumbnail to destination]'
        '(https://example.org/File:shot.png)\n\n'
        '$\\textbf{(A) } 1 \\qquad\\textbf{(B) } 2 \\qquad\\textbf{(C) } 3 \\qquad\\textbf{(D) } 4 \\qquad\\textbf{(E) } 5$\n')
    one, two = official.parse_contest(source, 'AMC 10')
    assert one['diagram'] == 'image' and two['diagram'] == 'image'
    assert one['statement'] == 'How many entries are possible?' and one['choices'][2] == '$6$'
    assert two['statement'] == 'What is length $x$?'
    assert 'Solution' not in one['statement'] and 'thumbnail' not in two['statement']


def test_wiki_source_with_imath_bullets_and_wrapped_lines():
    source = (
        '==Problem 1==\nConsider these\nfour moves of the plane:\n\n* a translation <imath>2</imath> units,\n\n'
        '*a rotation by <imath>90^{\\circ}</imath>.\n\nHow many commute? <imath>\\newline</imath>\n'
        '<imath>\\textbf{(A)}~1\\qquad\\textbf{(B)}~2\\qquad\\textbf{(C)}~3\\qquad\\textbf{(D)}~4\\qquad\\textbf{(E)}~5</imath>\n\n'
        '[[2024 AMC 10A Problems/Problem 1|Solution]]\n'
        '==Problem 2==\nWhat is\n<cmath>1+1</cmath>\nin all?\n\n'
        '<imath>\\textbf{(A) }1\\qquad\\textbf{(B) }2\\qquad\\textbf{(C) }3\\qquad\\textbf{(D) }4\\qquad\\textbf{(E) }5</imath>\n')
    one, two = official.parse_contest(source, 'AMC 10')
    assert one['statement'].startswith('Consider these four moves of the plane:\n')
    assert '\n• a translation $2$ units,\n• a rotation by $90^{\\circ}$.' in one['statement']
    assert 'newline' not in one['statement'] and one['choices'] == ['$1$', '$2$', '$3$', '$4$', '$5$']
    assert two['statement'] == 'What is\n$$1+1$$\nin all?'


@pytest.mark.parametrize('contest, key, unwritten', [
    ('2024-amc-10a', 'ABBBDDBABCDECDEDEDECCBDBC', {12, 16, 22}),
    ('2023-amc-10a', 'EAADEDBDEDCBCBEBADEDDDCCA', set()),
    ('2023-amc-10b', 'CBDCAEBABCBCBCCEDEBAEBBEB', set()),
    ('2022-amc-10b', 'ADDABABBDDBCEBDDCBCDEECBA', set()),
    ('2022-amc-10a', 'DBEECABDDECACEDDDACEBDBEB', set()),
    ('2021-amc-10a', 'DCDDBADEDCEECACCDEEDCBDDE', set()),
    ('2021-amc-10b', 'DDCBBCDADADCBBBCCCDDADCBE', set()),
    ('2021-fall-amc-10b', 'EBECEBCCCABDBCDDDEACEBDAE', set()),
    ('2021-fall-amc-10a', 'CEDBEBDBEBADDDCDDCABEBDEA', set()),
    ('2020-amc-10a', 'ECAECBCBBBCCBDEBECEDCAACA', set()),
    ('2020-amc-10b', 'DEEDBBADDCDDBDDACBABBDCCA', set()),
    ('2019-amc-10b', 'DEBAECBBAAACACAACCCEBBCCC', set()),
    ('2019-amc-10a', 'CADBDCCCBCCEDDEADDBBDBCBD', set()),
    ('2018-amc-10a', 'BAEEDBECEAECDADDCDEBEDDDD', set()),
])
def test_the_2024_and_2023_10a_are_written_up_against_their_keys(contest, key, unwritten):
    for n in range(1, 26):
        pid = '%s-%d' % (contest, n)
        if n in unwritten:
            assert pid not in SOLUTIONS
        else:
            assert SOLUTIONS[pid]['answer'] == key[n - 1], pid


def test_dollar_sign_choices_and_parenthesis_math():
    # 2023 AMC 10B #2 prices its choices `\$46`; #18 writes its choices in `\( \)`.
    source = (
        '==Problem 1==\nHow much?\n\n<math>\\textbf{(A) }\\$46\\qquad\\textbf{(B) }\\$50\\qquad\\textbf{(C) }\\$48'
        '\\qquad\\textbf{(D) }\\$47\\qquad\\textbf{(E) }\\$49 </math>\n\n'
        '==Problem 2==\nWhich are true?\n\n\\(\\textbf{(A)}~\\text{I only}\\qquad\\textbf{(B)}~\\text{II only}\\qquad'
        '\\textbf{(C)}~\\text{III only}\\qquad\\textbf{(D)}~\\text{I and II}\\qquad\\textbf{(E)}~\\text{II and III only}\\)\n')
    one, two = official.parse_contest(source, 'AMC 10')
    assert one['choices'] == ['$\\$46$', '$\\$50$', '$\\$48$', '$\\$47$', '$\\$49$']
    assert two['statement'] == 'Which are true?'
    assert two['choices'] == ['I only', 'II only', 'III only', 'I and II', 'II and III only']


def test_choices_one_to_a_line_and_align_inside_cmath():
    # 2022 AMC 10B #4 and #11 put each choice on its own line (#11 with only the
    # letter in math); #8 and #18 write `align*` inside a `<cmath>` block.
    source = (
        '==Problem 1==\nWhen?\n\n' + ''.join(
            '<math>\\textbf{(%s) }%d \\text{ seconds}</math>\n\n' % (c, 5 * i) for i, c in enumerate('ABCDE')) +
        '==Problem 2==\nWhich?\n\n' + ''.join(
            '<math>\\textbf{(%s) }</math> Choice %s.\n\n' % (c, c) for c in 'ABCDE') +
        '==Problem 3==\nThe sets\n<cmath>\\begin{align*}\n&\\{1\\},\\\\\n&\\{2\\}\n\\end{align*}</cmath>\nHow many?\n\n'
        '<math>\\textbf{(A) }1\\qquad\\textbf{(B) }2\\qquad\\textbf{(C) }3\\qquad\\textbf{(D) }4\\qquad\\textbf{(E) }5</math>\n')
    one, two, three = official.parse_contest(source, 'AMC 10')
    assert one['statement'] == 'When?' and one['choices'][4] == '$20 \\text{ seconds}$'
    assert two['statement'] == 'Which?' and two['choices'] == ['Choice %s.' % c for c in 'ABCDE']
    assert three['statement'] == 'The sets\n$$\\begin{aligned}&\\{1\\},\\\\ &\\{2\\}\\end{aligned}$$\nHow many?'


def test_double_prime_in_math_and_choices_mixing_math_and_words():
    # 2021 Fall AMC 10B #17 writes P'' in math, which the wiki's ''italic''
    # stripping must leave alone; #12 puts each choice on a line of its own,
    # with math and words mixed (`<math>\textbf{(A)} \: x>y</math> and <math>y=z</math>`).
    source = (
        "==Problem 1==\nA ''special'' point <math>P'</math> goes to <math>P''</math>.\n\n"
        '<math>\\textbf{(A) }1\\qquad\\textbf{(B) }2\\qquad\\textbf{(C) }3\\qquad\\textbf{(D) }4\\qquad\\textbf{(E) }5</math>\n\n'
        '==Problem 2==\nWhich?\n\n' + ''.join(
            '<math>\\textbf{(%s)} \\: x>%d</math> and <math>y=z</math>\n\n' % (c, i) for i, c in enumerate('ABCDE')))
    one, two = official.parse_contest(source, 'AMC 10')
    assert one['statement'] == "A special point $P'$ goes to $P''$."
    assert two['statement'] == 'Which?'
    assert two['choices'] == ['$x>%d$ and $y=z$' % i for i in range(5)]


def test_emphasis_tags_become_math_and_overarc_becomes_overgroup():
    # 2019 AMC 10B #5: "Which ... is <i><u>not</u></i> always true?" The page
    # escapes plain text, so the tags would show; they become KaTeX instead.
    # #20 writes arcs as \overarc, which KaTeX lacks; \overgroup draws the same.
    source = ('==Problem 1==\nWhich is <i><u>not</u></i> true, and <b>which</b> is?\n\n'
              '<math>\\textbf{(A) }1\\qquad\\textbf{(B) }2\\qquad\\textbf{(C) }3\\qquad\\textbf{(D) }4\\qquad\\textbf{(E) }5</math>\n'
              '==Problem 2==\nArc <math>\\overarc{AEB}</math>?\n\n'
              '<math>\\textbf{(A) }1\\qquad\\textbf{(B) }2\\qquad\\textbf{(C) }3\\qquad\\textbf{(D) }4\\qquad\\textbf{(E) }5</math>\n')
    one, two = official.parse_contest(source, 'AMC 10')
    assert one['statement'] == ('Which is $\\textit{\\underline{\\text{not}}}$ true, '
                                'and $\\textbf{\\text{which}}$ is?')
    assert two['statement'] == 'Arc $\\overgroup{AEB}$?'
