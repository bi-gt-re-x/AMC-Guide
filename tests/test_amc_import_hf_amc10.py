"""scripts/import_amc10_hf.py: an AMC 10 problem is taken from whichever
source has it with choices and a letter (AoPS rows, the same year's AMC 12
twin, NuminaMath), checked against Easy2Hard-Bench's value answer; and a paper
saved part-way serves its problems without passing for a whole contest.
No network: the rows are made up here."""
import importlib.util
import os

from backend.amc import official

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(ROOT, 'scripts', 'import_amc10_hf.py')
    spec = importlib.util.spec_from_file_location('import_amc10_hf', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hf10 = _load()

CHOICES = '\n$\\textbf{(A) } %s\\qquad\\textbf{(B) } %s\\qquad\\textbf{(C) } %s\\qquad\\textbf{(D) } %s\\qquad\\textbf{(E) } %s$'


def _e2h(year, paper, n, text, answer):
    return {'tag': 'AMC10', 'year': year, 'subtest': '10' + paper, 'index': n, 'problem': text, 'answer': answer}


def _aops(year, paper, n, text, letter=None, answer=None):
    return {'link': 'https://artofproblemsolving.com/wiki/index.php/{}_AMC_10{}_Problems/Problem_{}'.format(year, paper, n),
            'problem': text, 'letter': letter, 'answer': answer}


def test_values_pick_the_letter():
    choices = ['$\\dfrac{1}{4}$', '$\\frac12$', '$1{,}000$', '$\\mathdollar 5.84$', 'none of these']
    assert hf10.letter_for(choices, '\\frac{1}{4}') == 'A'
    assert hf10.letter_for(choices, '\\frac{1}{2}') is None      # `\frac12` is not normalised; no guess
    assert hf10.letter_for(choices, '1000') == 'C'
    assert hf10.letter_for(choices, '5.84') == 'D'
    assert hf10.letter_for(choices, '') is None
    assert hf10.letter_for(['$1$', '$1$', '$2$', '$3$', '$4$'], '1') is None   # two hits: not sure which


def test_ids_by_paper_and_number():
    e2h, aops = hf10.by_number({
        'e2h': [_e2h(2005, 'A', 3, 'x', '1'), _e2h(2021, 'A', 3, 'x', '1'),
                {'tag': 'AMC12', 'year': 2005, 'subtest': '12A', 'index': 3, 'problem': 'x', 'answer': '1'}],
        'aops': [_aops(2001, '', 7, 'x'), _aops(2002, 'B', 25, 'x'),
                 {'link': 'https://artofproblemsolving.com/wiki/index.php/2002_AMC_12B_Problems/Problem_1'}]})
    assert set(e2h) == {('2005-amc-10a', 3)}          # 2021's sittings are told apart only by month
    assert set(aops) == {('2001-amc-10', 7), ('2002-amc-10b', 25)}


def test_each_problem_from_the_first_source_that_has_it(client, monkeypatch):
    # The same year's AMC 12 paper is in the database.
    twin = [{'id': '2005-amc-12a-4', 'contest': '2005-amc-12a', 'level': 'AMC 12', 'number': 4,
             'statement': 'A twin problem asked on both papers that year, about seven apples.',
             'choices': ['$5$', '$6$', '$7$', '$8$', '$9$'], 'answer': 'C', 'diagram': ''}]
    monkeypatch.setattr(official, 'all_problems', lambda: twin)
    sources = {
        'e2h': [_e2h(2005, 'A', 1, 'Problem one has its own words here.', '2'),
                _e2h(2005, 'A', 2, 'A twin problem asked on both papers that year, about seven apples.', '7'),
                _e2h(2005, 'A', 3, 'Only NuminaMath keeps the choices of this third problem.', '30'),
                _e2h(2005, 'A', 4, 'Nobody has the choices of this fourth problem at all.', '4')],
        'aops': [_aops(2005, 'A', 1, 'Problem one has its own words here.' + CHOICES % (1, 2, 3, 4, 5), 'B'),
                 _aops(2005, 'A', 5, 'Problem five, no letter given.' + CHOICES % (10, 20, 30, 40, 50), None, '40.0')],
        'numina': [{'problem': 'Only NuminaMath keeps the choices of this third problem.'
                               + CHOICES % (10, 20, 30, 40, 50)}],
    }
    built, conflicts = hf10.build(sources, ['2005-amc-10a'])
    problems, key, source = built['2005-amc-10a']
    assert conflicts == []
    assert sorted(problems) == [1, 2, 3, 5]                        # 4 has no choices anywhere
    assert key == {1: 'B', 2: 'C', 3: 'C', 5: 'D'}
    assert source == {1: 'aops', 2: 'amc12:2005-amc-12a-4', 3: 'numina', 5: 'aops'}
    assert problems[2]['choices'] == ['$5$', '$6$', '$7$', '$8$', '$9$']
    assert problems[3]['statement'] == 'Only NuminaMath keeps the choices of this third problem.'


def test_sources_that_disagree_are_reported():
    sources = {'e2h': [_e2h(2006, 'B', 1, 'Which one is it?', '3')],
               'aops': [_aops(2006, 'B', 1, 'Which one is it?' + CHOICES % (1, 2, 3, 4, 5), 'A')],
               'numina': []}
    built, conflicts = hf10.build(sources, ['2006-amc-10b'])
    assert built['2006-amc-10b'][1] == {1: 'A'}
    assert conflicts and conflicts[0][:2] == ('2006-amc-10b', 1)


def test_a_part_imported_paper_serves_its_problems_but_is_not_a_contest(client):
    problems = [{'number': n, 'statement': 'What is {0}+{0}?'.format(n),
                 'choices': ['$1$', '$2$', '$3$', '$4$', '$5$'], 'diagram': ''} for n in (1, 2, 5)]
    key = ['B', 'C', '', '', 'A'] + [''] * 20
    official.save_contest('2005-amc-10a', problems, key, 'temu')
    assert official.imported_contests()['2005-amc-10a'] == 3

    body = client.get('/api/amc/problems/2005-amc-10a-5').json()
    assert body['success'] and body['problem']['choices'] == ['$1$', '$2$', '$3$', '$4$', '$5$']
    reply = client.post('/api/amc/problems/2005-amc-10a-5/attempt', json={'answer': 'A'}).json()
    assert reply['correct']

    # The paper itself waits for all 25: not shown as imported, not sittable.
    page = client.get('/api/amc/contests/2005-amc-10a').json()
    assert page['contest']['imported'] is False and page['problems'] == []
    assert page['partial'] == [1, 2, 5]           # the page lists what can be practised
    assert not client.post('/api/amc/contests/2005-amc-10a/submit', json={'answers': {}}).json()['success']
    listing = client.get('/api/amc/contests').json()
    row = next(c for y in listing['years'] for c in y['contests'] if c['id'] == '2005-amc-10a')
    assert row['imported'] == 3
