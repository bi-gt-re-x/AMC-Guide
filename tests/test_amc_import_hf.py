"""scripts/import_amc12_hf.py: the Hugging Face AMC 12 rows become AoPS-style
source that backend/amc/official.py's own `check` accepts, with the dataset's
few out-of-order rows mended. No network: the rows are made up here."""
import importlib.util
import os

from backend.amc import official

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(ROOT, 'scripts', 'import_amc12_hf.py')
    spec = importlib.util.spec_from_file_location('import_amc12_hf', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hf = _load()


def test_ids_map_to_catalog_contests():
    assert hf.contest_id('2019A-P5') == ('2019-amc-12a', 5)
    assert hf.contest_id('2012B-P25') == ('2012-amc-12b', 25)
    # 2000 and 2001 ran one AMC 12; the dataset files it as A.
    assert hf.contest_id('2000A-P1') == ('2000-amc-12', 1)
    assert hf.contest_id('nonsense') == (None, None)


def _rows(contest="2010A", overrides=None):
    rows = []
    for n in range(1, 26):
        q = 'What is ${0}+{0}$?\n\n\\textbf{{(A)}}\\ 1\\qquad\\textbf{{(B)}}\\ 2\\qquad' \
            '\\textbf{{(C)}}\\ 3\\qquad\\textbf{{(D)}}\\ 4\\qquad\\textbf{{(E)}}\\ 10\\%'.format(n)
        rows.append({'question': (overrides or {}).get(n, q), 'answer': 'ABCDE'[n % 5],
                     'difficulty': 2 if n <= 10 else 3 if n <= 20 else 4,
                     'problem_id': '{}-P{}'.format(contest, n)})
    return rows


def test_a_whole_paper_passes_the_paste_importers_check():
    source, key, bands = hf.build(_rows())['2010-amc-12a']
    problems, answers, issues, complete = official.check('2010-amc-12a', source, key)
    assert complete and not issues
    assert answers == ['ABCDE'[n % 5] for n in range(1, 26)]
    assert problems[0]['statement'] == 'What is $1+1$?'
    assert problems[0]['choices'] == ['$1$', '$2$', '$3$', '$4$', r'$10\%$']
    assert hf.difficulty_agrees('AMC 12', bands)


def test_a_missing_problem_leaves_the_paper_incomplete():
    rows = [r for r in _rows() if r['problem_id'] != '2010A-P7']
    source, key, _ = hf.build(rows)['2010-amc-12a']
    *_, complete = official.check('2010-amc-12a', source, key)
    assert not complete


def test_diagrams_and_named_pictures():
    asy = 'Find $x$.\n\n```asy\ndraw((0,0)--(1,1));\n```\n\n$\\textbf{(A) } 1 \\qquad \\textbf{(B) } 2 ' \
          '\\qquad \\textbf{(C) } 3 \\qquad \\textbf{(D) } 4 \\qquad \\textbf{(E) } 5$'
    pic = 'Find $y$.\n\n<center>Image:2007_12B_AMC-3.png</center>\n\n$\\mathrm{(A)}\\ 1 \\qquad\\mathrm{(B)}\\ 2' \
          ' \\qquad\\mathrm{(C)}\\ 3 \\qquad\\mathrm{(D)}\\ 4 \\qquad\\mathrm{(E)}\\ 5$'
    source, key, _ = hf.build(_rows(overrides={1: asy, 2: pic}))['2010-amc-12a']
    problems, *_ = official.check('2010-amc-12a', source, key)
    assert problems[0]['diagram'] == 'draw((0,0)--(1,1));'
    assert problems[0]['choices'] == ['$1$', '$2$', '$3$', '$4$', '$5$']
    assert problems[1]['diagram'] == 'image' and problems[1]['statement'] == 'Find $y$.'


def test_choice_e_scraped_above_the_choices_is_moved_back():
    words = ('Who wins?\n\n Whoever goes first.\n\n\\textbf{(A)}$ Barbara.  $\\textbf{(B)}$ Jenna.  '
             '$\\textbf{(C)}$ Nobody.  $\\textbf{(D)}$ Both.  $\\textbf{(E)}')
    math = ("What is the period?\n\n It's not periodic.\n\n\\textbf{(A)}\\ \\pi\\qquad\\textbf{(B)}\\ 2\\pi"
            "\\qquad\\textbf{(C)}\\ 3\\pi\\qquad\\textbf{(D)}\\ 4\\pi\\qquad\\textbf{(E)}")
    seealso = 'What is $1$?\n\n\n==See also==\n\n\\textbf{(A)}\\ 1\\qquad\\textbf{(B)}\\ 2\\qquad' \
              '\\textbf{(C)}\\ 3\\qquad\\textbf{(D)}\\ 4\\qquad\\textbf{(E)}\\ 5'
    source, key, _ = hf.build(_rows(overrides={1: words, 2: math, 3: seealso}))['2010-amc-12a']
    problems, _, issues, complete = official.check('2010-amc-12a', source, key)
    assert complete and not issues
    assert problems[0]['statement'] == 'Who wins?'
    assert problems[0]['choices'] == ['Barbara.', 'Jenna.', 'Nobody.', 'Both.', 'Whoever goes first.']
    assert problems[1]['choices'] == ['$\\pi$', '$2\\pi$', '$3\\pi$', '$4\\pi$', "It's not periodic."]
    assert problems[2]['choices'] == ['$1$', '$2$', '$3$', '$4$', '$5$']


def test_two_accepted_answers_settle_to_the_keys_letter():
    rows = _rows('2012B')
    rows[11]['answer'] = 'D or E (both were accepted)'
    _, key, _ = hf.build(rows)['2012-amc-12b']
    assert '12. D' in key.splitlines()
