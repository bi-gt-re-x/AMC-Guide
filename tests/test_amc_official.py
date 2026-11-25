"""Importing an official contest by pasting it.

The fixtures are made-up problems laid out the way the AoPS wiki source and a
PDF's text are laid out — the parsing is what is under test, not the content.
"""
import pytest

from backend.amc import official


@pytest.fixture(autouse=True)
def _tester_imports(monkeypatch):
    """The tests import as `tester`; the real install allows only `temu`."""
    monkeypatch.setenv('AMC_IMPORTERS', 'temu,tester')

WIKI = r"""{{AMC10 Problems|year=2023|ab=A}}
==Problem 1==
What is <math>2+3</math>?

<math>\textbf{(A) } 4 \qquad\textbf{(B) } 5 \qquad\textbf{(C) } 6 \qquad\textbf{(D) } 7 \qquad\textbf{(E) } 8</math>

[[2023 AMC 10A Problems/Problem 1|Solution]]

==Problem 2==
A '''circle''' has radius <math>r</math>. Find <math>\frac{\pi r^2}{r}</math> when <math>r=2</math>.
<asy>
draw(circle((0,0),2));
</asy>

<math>\mathrm{(A)}\ \pi \qquad \mathrm{(B)}\ 2\pi \qquad \mathrm{(C)}\ 3\pi</math>
<math>\mathrm{(D)}\ 4\pi \qquad \mathrm{(E)}\ 5\pi</math>

[[2023 AMC 10A Problems/Problem 2|Solution]]

==Problem 3==
How many ways can 3 friends sit in a row?

<math>\textbf{(A)}~3\qquad\textbf{(B)}~4\qquad\textbf{(C)}~5\qquad\textbf{(D)}~6\qquad\textbf{(E)}~\text{none of these}</math>

==See also==
{{AMC10 box|year=2023|ab=A|before=First|after=[[2023 AMC 10B Problems]]}}
"""

TEXT = """1. What is 2 + 3? (A) 4 (B) 5 (C) 6 (D) 7 (E) 8
2. What is 10 - 4? (A) 4 (B) 5 (C) 6 (D) 7 (E) 8
"""


def test_wiki_source():
    found = official.parse_contest(WIKI, 'AMC 10')
    assert [p['number'] for p in found] == [1, 2, 3]
    one, two, three = found
    assert one['statement'] == 'What is $2+3$?'
    assert one['choices'] == ['$4$', '$5$', '$6$', '$7$', '$8$']
    assert 'Solution' not in one['statement'] and '[[' not in one['statement']
    # Choices split over two math blocks, an Asymptote diagram kept aside,
    # bold markup removed.
    assert two['choices'] == ['$\\pi$', '$2\\pi$', '$3\\pi$', '$4\\pi$', '$5\\pi$']
    assert 'draw(circle' in two['diagram'] and '<asy>' not in two['statement']
    assert "'''" not in two['statement'] and 'circle' in two['statement']
    assert three['choices'][3] == '$6$' and three['choices'][4] == 'none of these'
    assert 'See also' not in three['statement']


def test_plain_text():
    found = official.parse_contest(TEXT, 'AMC 10')
    assert found[0]['statement'] == 'What is 2 + 3?'
    assert found[0]['choices'] == ['4', '5', '6', '7', '8']
    assert found[1]['choices'][2] == '6'


def test_inequalities_in_choices_are_not_html_tags():
    # 2016 AMC 10A #12: `p<\dfrac..` and `..p>` once read as a <p> tag and ate choices C to E.
    src = r"""==Problem 1==
Which is true of $p$?

<math>\textbf{(A)}\ p<\dfrac{1}{8}\qquad\textbf{(B)}\ p=\dfrac{1}{8}\qquad\textbf{(C)}\ \dfrac{1}{8}<p<\dfrac{1}{3}\qquad\textbf{(D)}\ p=\dfrac{1}{3}\qquad\textbf{(E)}\ p>\dfrac{1}{3}</math>
<p align="center">x</p>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['choices'] == ['$p<\\dfrac{1}{8}$', '$p=\\dfrac{1}{8}$', '$\\dfrac{1}{8}<p<\\dfrac{1}{3}$',
                              '$p=\\dfrac{1}{3}$', '$p>\\dfrac{1}{3}$']
    assert '<p' not in one['statement'] and 'align' not in one['statement']


def test_a_full_stop_after_the_solution_link_is_dropped():
    # 2015 AMC 10A #25 ends `[[2015 AMC 10A Problems/Problem 25|Solution]].`
    src = r"""==Problem 1==
What is <math>1+1</math>?

<math>\textbf{(A) }1\qquad\textbf{(B) }2\qquad\textbf{(C) }3\qquad\textbf{(D) }4\qquad\textbf{(E) }5</math>

[[2015 AMC 10A Problems/Problem 1|Solution]].
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'What is $1+1$?'
    assert one['choices'][4] == '$5$'


def test_textdollar_becomes_a_dollar_katex_can_draw():
    # 2014 AMC 10A #11 prices its choices as `\textdollar179.95`, which KaTeX does not know.
    src = r"""==Problem 1==
Coupon: <math>\textdollar 20</math> off.

<math>\textbf{(A) }\textdollar179.95\qquad\textbf{(B) }\textdollar199.95\qquad\textbf{(C) }\textdollar219.95\qquad\textbf{(D) }\textdollar239.95\qquad\textbf{(E) }\textdollar259.95</math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == r'Coupon: $\$20$ off.'
    assert one['choices'][0] == r'$\$179.95$'


def test_a_choice_letter_in_doubled_braces_still_marks_a_choice():
    # 2013 AMC 10B #5 writes `\textbf{{(B)}}` for every choice after the first.
    src = r"""==Problem 1==
What is the least value?

<math>\textbf{(A)}\ -20\qquad\textbf{{(B)}}\ -15\qquad\textbf{{(C)}}\ -10\qquad\textbf{{(D)}}\ 0\qquad\textbf{{(E)}}\ 2</math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'What is the least value?'
    assert one['choices'] == ['$-20$', '$-15$', '$-10$', '$0$', '$2$']


def test_choices_split_across_many_math_tags_are_joined():
    # 2011 AMC 10A #9 breaks its one choices line into six <math> tags, mid-choice.
    src = r"""==Problem 1==
Which of the following represents the area of this region?

<math> \textbf{(A)}\ ac+ad+bc+bd\qquad\textbf{(B)}\ ac-ad</math> <math>+bc-bd\qquad\textbf{(C)}\ ac+ad</math> <math>-bc-bd   \quad\quad\qquad\textbf{(D)}\ -ac-ad</math> <math>+bc+bd\qquad\textbf{(E)}\ ac-ad</math> <math> -bc+bd </math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'Which of the following represents the area of this region?'
    assert one['choices'] == ['$ac+ad+bc+bd$', '$ac-ad +bc-bd$', '$ac+ad -bc-bd$', '$-ac-ad +bc+bd$', '$ac-ad -bc+bd$']


def test_a_space_inside_a_choice_is_kept():
    # 2012 AMC 10A #2: `2\ \text{by}\ 4` read as `2 \text{by} 4`, which math draws as "2by4".
    src = r"""==Problem 1==
What are the dimensions?

<math> \textbf{(A)}\ 2\ \text{by}\ 4\qquad\textbf{(B)}\ \ 2\ \text{by}\ 6\qquad\textbf{(C)}\ \ 2\ \text{by}\ 8\qquad\textbf{(D)}\ 4\ \text{by}\ 4\qquad\textbf{(E)}\ 4\ \text{by}\ 8 </math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['choices'] == ['$2\\ \\text{by}\\ 4$', '$2\\ \\text{by}\\ 6$', '$2\\ \\text{by}\\ 8$',
                              '$4\\ \\text{by}\\ 4$', '$4\\ \\text{by}\\ 8$']


def test_a_dollar_entity_is_a_dollar_sign():
    # 2010 AMC 10A #8 types its prices as `&#36;<math>0.50</math>`.
    src = r"""==Problem 1==
Tony is paid &#36;<math>0.50</math> per hour and earned &#36;<math>630</math>. How old was he?

<math>\mathrm{(A)}\ 9 \qquad \mathrm{(B)}\ 11 \qquad \mathrm{(C)}\ 12 \qquad \mathrm{(D)}\ 13 \qquad \mathrm{(E)}\ 14</math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'Tony is paid \\$$0.50$ per hour and earned \\$$630$. How old was he?'
    assert one['choices'] == ['$9$', '$11$', '$12$', '$13$', '$14$']


def test_letters_and_signs_are_math_but_words_are_words():
    # 2011 AMC 10B #4 (`B - A`) and #15 (`I only`).
    src = r"""==Problem 1==
How many dollars?

<math> \textbf{(A)}\ \frac{A + B}{2} \qquad\textbf{(B)}\ \dfrac{A - B}{2}\qquad\textbf{(C)}\ \text{I only}\qquad\textbf{(D)}\ B - A \qquad\textbf{(E)}\ A + B </math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['choices'] == ['$\\frac{A + B}{2}$', '$\\dfrac{A - B}{2}$', 'I only', '$B - A$', '$A + B$']


def test_triple_braces_in_math_are_not_a_template():
    # 2008 AMC 10B #13 writes each choice as `{{{2008}}}`; the template strip left `}`.
    src = r"""{{AMC10 Problems|year=2008|ab=B}}
==Problem 1==
What is the 2008th term of the sequence?

<math>\mathrm{(A)}\ {{{2008}}} \qquad \mathrm{(B)}\ {{{4015}}} \qquad \mathrm{(C)}\ {{{4016}}} \qquad \mathrm{(D)}\ {{{4,030,056}}} \qquad \mathrm{(E)}\ {{{4,032,064}}}</math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'What is the 2008th term of the sequence?'
    assert one['choices'] == ['${2008}$', '${4015}$', '${4016}$', '${4,030,056}$', '${4,032,064}$']


def test_a_table_is_one_katex_can_draw():
    # 2008 AMC 10B #2: `\begin{tabular}[t]` and an empty `\multicolumn` row, neither of which KaTeX has.
    src = r"""==Problem 1==
A block of dates is shown.

<math>\begin{tabular}[t]{|c|c|}
\multicolumn{2}{c}{}\\\hline
1&2\\\hline
\end{tabular}</math>

<math>\textbf{(A)}\ 2 \qquad \textbf{(B)}\ 4 \qquad \textbf{(C)}\ 6 \qquad \textbf{(D)}\ 8 \qquad \textbf{(E)}\ 10</math>
"""
    (one,) = official.parse_contest(src, 'AMC 10')
    assert '\\begin{array}{|c|c|}' in one['statement']
    assert '[t]' not in one['statement'] and 'multicolumn' not in one['statement'] and 'tabular' not in one['statement']
    assert one['choices'] == ['$2$', '$4$', '$6$', '$8$', '$10$']


CHOICES_LINE = r'<math>\textbf{(A)}\ 1 \qquad \textbf{(B)}\ 2 \qquad \textbf{(C)}\ 3 \qquad \textbf{(D)}\ 4 \qquad \textbf{(E)}\ 5</math>'


def test_math_tags_back_to_back_stay_two_inline_maths():
    # 2011 AMC 10B #9: `<math>\triangle</math><math>EBD</math>` met as `$$`, which opens display math.
    src = '==Problem 1==\nThe area of <math>\\triangle</math><math>EBD</math> is a third.\n\n' + CHOICES_LINE
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'The area of $\\triangle$ $EBD$ is a third.'


def test_a_bare_dollar_before_math_is_a_dollar_sign():
    # 2006 AMC 10A #1: `cost $<math>3</math> each` read as `$$3$`. A `$` that closes math stays.
    src = '==Problem 1==\nSandwiches cost $<math>3</math> each and $x$<math>y</math> is fine.\n\n' + CHOICES_LINE
    (one,) = official.parse_contest(src, 'AMC 10')
    assert one['statement'] == 'Sandwiches cost \\$$3$ each and $x$ $y$ is fine.'


@pytest.mark.parametrize('wiki, drawn', [
    (r'\mathdollar 4.15', r'\$4.15'),                      # 2007 AMC 10A #5
    (r'1 &\mbox{if }x = 1', r'1 &\text{if }x = 1'),         # 2004 AIME I #15
    (r'3! \cdot \hdots \cdot 9!', r'3! \cdot \cdots \cdot 9!'),  # 2003 AMC 12A #23
    ('2^{200}\\ ?', '2^{200}\\ ?'),                    # 2005 AMC 10A #13
])
def test_latex_katex_lacks_is_rewritten(wiki, drawn):
    assert official.katex_compat(wiki) == drawn
    assert official.katex_compat(drawn) == drawn


def test_aime_has_no_choices():
    found = official.parse_contest('==Problem 1==\nFind <math>x</math>.\n==Problem 2==\nFind y.', 'AIME')
    assert found[0]['choices'] is None and found[0]['statement'] == 'Find $x$.'


def test_answer_keys():
    letters = 'BCDAEBCDAEBCDAEBCDAEBCDAE'
    assert official.parse_key('\n'.join('# ' + x for x in letters), 'AMC 10') == list(letters)
    assert official.parse_key('\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(letters)), 'AMC 10') == list(letters)
    assert official.parse_key(letters, 'AMC 10') == list(letters)
    assert official.parse_key(' '.join(letters), 'AMC 10') == list(letters)
    aime = [204, 33, 5, 80, 6, 7, 999, 0, 12, 45, 100, 250, 3, 18, 77]
    assert official.parse_key('\n'.join('# %03d' % n for n in aime), 'AIME') == aime
    assert official.parse_key(' '.join('%d. %d' % (i + 1, n) for i, n in enumerate(aime)), 'AIME') == aime


def test_topic_and_difficulty_guesses():
    assert official.guess_topic('A circle has radius 3.') == 'circles'
    assert official.guess_topic('What is the remainder when 7^5 is divided by 4?') == 'modular-arithmetic'
    assert official.difficulty_at('AMC 10', 1) == 1 and official.difficulty_at('AMC 10', 25) == 5
    assert official.difficulty_at('AIME', 15) == 5
    assert official.guess_topics('How many ordered pairs of positive integers $(x, y)$ satisfy $xy = 12$?')[0] \
        == 'diophantine'
    assert official.guess_topics('In triangle $ABC$, the angle bisector from $A$ meets $BC$ at $D$.')[:2] \
        == ['triangle-centers', 'angle-chasing']
    assert official.guess_topics('A clock shows 3 p.m.')[0] == 'clocks-calendars'


def _full_contest():
    body = '\n'.join(
        '==Problem %d==\nWhat is %d+0?\n\n<math>\\textbf{(A) }%d\\qquad\\textbf{(B) }%d\\qquad'
        '\\textbf{(C) }%d\\qquad\\textbf{(D) }%d\\qquad\\textbf{(E) }%d</math>\n'
        % (n, n, n, n + 1, n + 2, n + 3, n + 4) for n in range(1, 26))
    return body, 'A' * 25


def test_import_then_practice_and_time_it(client):
    body, key = _full_contest()
    preview = client.post('/api/amc/contests/2023-amc-10a/import', json={'problems': body, 'key': key}).json()
    assert preview['success'] and preview['issues'] == [] and not preview['saved']
    assert client.get('/api/amc/contests/2023-amc-10a').json()['contest']['imported'] is False

    saved = client.post('/api/amc/contests/2023-amc-10a/import',
                        json={'problems': body, 'key': key, 'save': True}).json()
    assert saved['saved']

    detail = client.get('/api/amc/contests/2023-amc-10a').json()
    assert detail['contest']['imported'] and len(detail['problems']) == 25
    assert 'answer' not in detail['problems'][0]

    # Practiced one at a time, in-site.
    reply = client.post('/api/amc/problems/2023-amc-10a-3/attempt', json={'answer': 'B'}).json()
    assert reply['success'] and not reply['correct'] and reply['problem']['answer'] == 'A'
    assert client.get('/api/amc/problems/2023-amc-10a-3').json()['next'] == '2023-amc-10a-4'
    assert client.get('/api/amc/problems', params={'source': 'official'}).json()['problems'][0]['source'] \
        == '2023 AMC 10A #1'

    # And timed as a whole contest, scored 6 / 1.5 / 0.
    answers = {str(n): 'A' for n in range(1, 21)}
    mock = client.post('/api/amc/contests/2023-amc-10a/submit', json={'answers': answers}).json()
    result = client.get('/api/amc/mocks/' + mock['id']).json()
    assert result['result']['score'] == 20 * 6 + 5 * 1.5
    assert result['contest']['official']

    # Search finds it.
    assert any(p['id'].startswith('2023-amc-10a') for p in
               client.get('/api/amc/search', params={'q': '2023 AMC 10A'}).json()['problems'])


def test_an_incomplete_import_is_refused(client):
    body, _ = _full_contest()
    reply = client.post('/api/amc/contests/2023-amc-10a/import',
                        json={'problems': body, 'key': 'ABC', 'save': True}).json()
    assert not reply['success'] and '3 of 25' in reply['message']
    assert client.get('/api/amc/contests/2023-amc-10a').json()['contest']['imported'] is False


def _api_page(pages, redirects=()):
    """An AoPS API reply (formatversion 2) holding these {title: source} pages."""
    import json
    return json.dumps({'batchcomplete': True, 'query': {
        'redirects': [{'from': a, 'to': b} for a, b in redirects],
        'pages': [{'ns': 0, 'title': t, 'revisions': [{'slots': {'main': {'contentmodel': 'wikitext', 'content': c}}}]}
                  for t, c in pages.items()]}})


def test_batch_links_cover_problems_and_keys():
    batches = official.batch_urls(['2023-amc-10a', '2024-aime-i'])
    assert len(batches) == 1
    url = batches[0]['url']
    assert url.startswith(official.API) and '2023_AMC_10A_Problems' in url and '2024_AIME_I_Answer_Key' in url
    many = official.batch_urls([c['id'] for c in official.catalog.PAST][:20])
    assert [len(b['contests']) for b in many] == [8, 8, 4]


def test_bundle_imports_every_complete_paper(client):
    body, key = _full_contest()
    first = _api_page({'2023 AMC 10A Problems': body, '2023 AMC 10A Answer Key': '\n'.join('# A' for _ in range(25)),
                       '2023 AMC 10B Problems': body})
    # A second batch pasted after the first, with the browser's chrome around it,
    # and a key that reached the page through a redirect.
    second = 'Pretty-print ' + _api_page({'2023 AMC 12A Answer Key (new)': key, '2023 AMC 12A Problems': body},
                                         redirects=[('2023 AMC 12A Answer Key', '2023 AMC 12A Answer Key (new)')])
    reply = client.post('/api/amc/official/import', json={'text': first + '\n' + second}).json()
    assert reply['success'] and reply['saved'] == 0
    rows = {r['id']: r for r in reply['contests']}
    assert rows['2023-amc-10a']['complete'] and rows['2023-amc-12a']['complete']
    assert not rows['2023-amc-10b']['complete'] and 'answer key was not' in rows['2023-amc-10b']['issues'][0]

    saved = client.post('/api/amc/official/import', json={'text': first + second, 'save': True}).json()
    assert saved['saved'] == 2
    assert client.get('/api/amc/contests/2023-amc-12a').json()['contest']['imported']
    left = client.get('/api/amc/official/batches').json()
    assert left['missing'] == left['total'] - 2
    assert not client.post('/api/amc/official/import', json={'text': 'nothing here'}).json()['success']


def test_official_problems_are_shown_whole_in_order(client):
    body, key = _full_contest()
    client.post('/api/amc/contests/2023-amc-10a/import', json={'problems': body, 'key': key, 'save': True})
    detail = client.get('/api/amc/contests/2023-amc-10a').json()
    assert [p['number'] for p in detail['problems']] == list(range(1, 26))
    first = detail['problems'][0]
    assert first['statement'] == 'What is 1+0?' and first['choices'][0] == '$1$'
    assert first['aops_url'].endswith('2023_AMC_10A_Problems/Problem_1')
    assert [p['rating'] for p in detail['problems']] == sorted(p['rating'] for p in detail['problems'])


def test_problem_list_runs_in_contest_order(client):
    rows = client.get('/api/amc/problems', params={'source': 'step'}).json()['problems']
    order = [(r['source'].rsplit(' #', 1)[0], int(r['source'].rsplit('#', 1)[1])) for r in rows]
    mocks = [m['name'] for m in official.catalog.MOCKS]
    assert order == sorted(order, key=lambda o: (mocks.index(o[0]), o[1]))
    hard = client.get('/api/amc/problems', params={'rating': '4'}).json()
    assert hard['problems'] and all(4 <= r['rating'] < 5 for r in hard['problems'])
    assert sum(hard['rating_counts'].values()) == hard['total']


def test_only_temu_can_import(app, client, monkeypatch):
    """Imports are shared by every account, so only the importer account
    (temu, or AMC_IMPORTERS) may add or remove them."""
    from tests.conftest import make_account, sign_in
    body, key = _full_contest()
    monkeypatch.delenv('AMC_IMPORTERS', raising=False)
    refused = client.post('/api/amc/contests/2023-amc-10a/import', json={'problems': body, 'key': key, 'save': True})
    assert refused.status_code == 403 and 'temu' in refused.json()['message']
    assert client.post('/api/amc/official/import', json={'text': 'x', 'save': True}).status_code == 403
    assert client.get('/api/amc/official/batches').status_code == 403
    assert client.delete('/api/amc/contests/2023-amc-10a/import').status_code == 403
    assert client.get('/api/amc/contests').json()['can_import'] is False
    assert client.get('/api/amc/contests/2023-amc-10a').json()['contest']['imported'] is False

    make_account('Temu')
    temu = sign_in(app, 'Temu')
    assert temu.get('/api/amc/contests').json()['can_import'] is True
    saved = temu.post('/api/amc/contests/2023-amc-10a/import', json={'problems': body, 'key': key, 'save': True}).json()
    assert saved['success'] and saved['saved'] and saved['complete']
    # Everyone can then practice it, but still not remove it.
    assert client.get('/api/amc/contests/2023-amc-10a').json()['contest']['imported'] is True
    assert client.delete('/api/amc/contests/2023-amc-10a/import').status_code == 403


def test_missing_choices_do_not_block_saving(app, monkeypatch):
    from tests.conftest import make_account, sign_in
    monkeypatch.setenv('AMC_IMPORTERS', 'boss')
    make_account('boss')
    boss = sign_in(app, 'boss')
    body, key = _full_contest()
    body = body.replace('==Problem 7==\nWhat is 7+0?\n\n<math>', '==Problem 7==\nWhat is 7+0?\n\n<math>\\text{no choices here}')
    body = body.replace('\\textbf{(A) }7\\qquad', 'seven ', 1)
    reply = boss.post('/api/amc/contests/2023-amc-10a/import', json={'problems': body, 'key': key}).json()
    assert reply['complete'] and any('no answer choices' in i for i in reply['issues'])
    assert boss.post('/api/amc/contests/2023-amc-10a/import',
                     json={'problems': body, 'key': key, 'save': True}).json()['saved']
