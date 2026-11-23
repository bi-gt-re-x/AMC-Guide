"""scripts/import_aime_hf.py: AIME problems from allenai, gneubig and AoPS rows,
first source first, answers checked against each other, the allenai rows'
escaping damage undone, and a whole paper through the paste importer's check.
No network: the rows are made up here."""
import importlib.util
import os

from backend.amc import official

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    path = os.path.join(ROOT, 'scripts', 'import_aime_hf.py')
    spec = importlib.util.spec_from_file_location('import_aime_hf', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aime = _load()
WIKI = 'https://artofproblemsolving.com/wiki/index.php/{}_AIME_{}_Problems/Problem_{}'


def _allenai(year, part, n, text, answer):
    return {'url': WIKI.format(year, part, n), 'problem': text, 'answer': str(answer), 'year': str(year)}


def _gneubig(year, part, n, text, answer):
    return {'ID': '{}-{}-{}'.format(year, part, n), 'Year': str(year), 'Part': part,
            'Problem Number': str(n), 'Question': text, 'Answer': str(answer)}


def _aops(year, part, n, text, answer):
    return {'link': WIKI.format(year, part, n), 'problem': text, 'answer': '{}.0'.format(answer), 'letter': None}


def test_escaping_damage_is_undone():
    eaten = 'is $\\\x0crac{m}{n}$ where \\\x08egin{align*} a &= 1 \\ &= 2 \\end{align*} in $\triangle ABC$ and $\\left(x\\\right)$.$'
    assert aime.unescape(eaten) == ('is $\\frac{m}{n}$ where \\begin{align*} a &= 1 \\\\ &= 2 \\end{align*} '
                                    'in $\\triangle ABC$ and $\\left(x\\right)$.')
    clean = 'Find $\\frac{m}{n}$ and $x \\\\ y$.'
    assert aime.unescape(clean) == clean


def test_answers_are_whole_numbers():
    assert aime.number('089') == 89 and aime.number('89.0') == 89 and aime.number(7) == 7
    assert aime.number('080 or 081 (both were accepted)') is None
    assert aime.number('1000') is None


def _paper(year, part, skip=()):
    return [_gneubig(year, part, n, 'Problem {} asks for ${}$.'.format(n, n * 7), n * 7)
            for n in range(1, 16) if n not in skip]


def test_each_problem_from_the_first_source_that_has_it():
    sources = {'allenai': [_allenai(2024, 'I', 1, 'The allenai wording of one.', 7)],
               'gneubig': _paper(2024, 'I', skip=(4,)),
               'aops': [_aops(2024, 'I', 4, 'Only AoPS has four, labeled as shown below.', 28),
                        _aops(2024, 'I', 5, 'AoPS also has five.', 35)]}
    built, conflicts = aime.build(sources, ['2024-aime-i'])
    source, key, where = built['2024-aime-i']
    assert conflicts == []
    assert where[1] == 'allenai' and where[4] == 'aops' and where[5] == 'gneubig'
    problems, answers, issues, complete = official.check('2024-aime-i', source, key)
    assert complete and not issues
    assert answers == [n * 7 for n in range(1, 16)]
    assert problems[0]['statement'] == 'The allenai wording of one.'
    flagged = aime.flag_figures(problems)
    assert flagged[3]['diagram'] == 'image' and flagged[4]['diagram'] == ''


def test_disagreeing_answers_hold_the_problem_back():
    sources = {'allenai': [], 'gneubig': _paper(2010, 'II'),
               'aops': [_aops(2010, 'II', 3, 'Problem 3 asks for $21$.', 22)]}
    built, conflicts = aime.build(sources, ['2010-aime-ii'])
    assert conflicts and conflicts[0][:2] == ('2010-aime-ii', 3)
    assert 3 not in built['2010-aime-ii'][2]


def test_two_accepted_answers_settle_to_one():
    rows = _paper(2022, 'II')
    rows[7]['Answer'] = '080 or 081 (both were accepted)'
    built, conflicts = aime.build({'allenai': [], 'gneubig': rows, 'aops': []}, ['2022-aime-ii'])
    assert conflicts == [] and '8. 80' in built['2022-aime-ii'][1].splitlines()


def test_an_imported_aime_is_sat_and_graded(client):
    built, _ = aime.build({'allenai': [], 'gneubig': _paper(2015, 'I'), 'aops': []}, ['2015-aime-i'])
    problems, key, _, complete = official.check('2015-aime-i', *built['2015-aime-i'][:2])
    assert complete
    official.save_contest('2015-aime-i', problems, key, 'temu')
    detail = client.get('/api/amc/contests/2015-aime-i').json()
    assert detail['contest']['imported'] and len(detail['problems']) == 15
    reply = client.post('/api/amc/problems/2015-aime-i-2/attempt', json={'answer': '14'}).json()
    assert reply['success'] and reply['correct']
    answers = {str(n): str(n * 7) for n in range(1, 11)}
    mock = client.post('/api/amc/contests/2015-aime-i/submit', json={'answers': answers}).json()
    assert mock['success']
    result = client.get('/api/amc/mocks/' + mock['id']).json()['result']
    assert result['score'] == 10
