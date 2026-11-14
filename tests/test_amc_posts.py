"""Posting problems, and whole tests with answer keys, by hand (backend/amc/posts.py, backend/api/amc_posts.py)."""
import pytest

from backend.amc import posts

AMC = {'level': 'AMC 10', 'title': 'Test 1', 'statement': r'What is $\frac12+\frac13$?',
       'choices': [r'$\frac16$', r'\frac25', r'$\frac56$', '$1$', r'$\frac76$'], 'answer': 'c',
       'solution': 'Common denominator:\n\n$\\frac36+\\frac26=\\frac56$.'}


def test_an_amc_post_is_saved_and_listed(client):
    made = client.post('/api/amc/posts', json=AMC).json()
    assert made['success']
    post = made['post']
    assert post['id'].startswith('post-') and post['author'] == 'tester' and post['can_edit']
    assert post['answer'] == 'C'
    assert post['choices'][1] == r'$\frac25$'          # TeX typed without $ is wrapped
    listed = client.get('/api/amc/posts').json()['posts']
    assert [p['id'] for p in listed] == [post['id']]
    assert client.get('/api/amc/posts', params={'level': 'AIME'}).json()['posts'] == []


def test_an_aime_post_needs_an_integer_answer(client):
    body = {'level': 'AIME', 'statement': 'Find $2^{10} \\bmod 1000$.', 'answer': '1024', 'solution': ''}
    assert 'whole number' in client.post('/api/amc/posts', json=body).json()['message']
    made = client.post('/api/amc/posts', json={**body, 'answer': '024'}).json()
    assert made['success'] and made['post']['answer'] == '24' and made['post']['choices'] is None


@pytest.mark.parametrize('change, message', [
    ({'statement': ''}, 'has no text'),
    ({'choices': ['$1$', '$2$', '$3$', '$4$']}, 'five answer choices'),
    ({'choices': ['$1$', '$1$', '$3$', '$4$', '$5$']}, 'the same'),
    ({'answer': 'F'}, 'A to E'),
    ({'answer': ''}, 'A to E'),
    ({'statement': 'What is $1+1?'}, 'unmatched $'),
    ({'level': 'AMC 8'}, 'AMC 10, AMC 12 or AIME'),
])
def test_bad_posts_are_refused_with_a_reason(client, change, message):
    reply = client.post('/api/amc/posts', json={**AMC, **change}).json()
    assert not reply['success'] and message in reply['message']


def test_aops_markup_and_a_pasted_choices_line_are_understood():
    pasted = (r'What is <math>2+3</math>?' '\n\n'
              r'<math>\textbf{(A)}\ 4 \qquad \textbf{(B)}\ 5 \qquad \textbf{(C)}\ 6 \qquad '
              r'\textbf{(D)}\ 7 \qquad \textbf{(E)}\ 8</math>')
    post = posts.clean('AMC 12', '', pasted, None, 'B', r'\[2+3=5\]')
    assert post['statement'] == 'What is $2+3$?'
    assert post['choices'] == ['$4$', '$5$', '$6$', '$7$', '$8$']
    assert post['solution'] == '$$2+3=5$$'


def test_split_pulls_the_choices_out(client):
    reply = client.post('/api/amc/posts/split', json={
        'statement': r'Pick one. $\textbf{(A) } 1 \qquad \textbf{(B) } 2 \qquad \textbf{(C) } 3 \qquad '
                     r'\textbf{(D) } 4 \qquad \textbf{(E) } 5$'}).json()
    assert reply['success'] and reply['statement'] == 'Pick one.' and reply['choices'][4] == '$5$'
    assert not client.post('/api/amc/posts/split', json={'statement': 'No choices here.'}).json()['success']


def test_only_the_author_can_edit_or_delete(client, stranger):
    pid = client.post('/api/amc/posts', json=AMC).json()['post']['id']
    theirs = stranger.get('/api/amc/posts').json()['posts'][0]
    assert theirs['id'] == pid and not theirs['can_edit']
    assert not stranger.put('/api/amc/posts/' + pid, json={**AMC, 'title': 'Mine now'}).json()['success']
    assert not stranger.delete('/api/amc/posts/' + pid).json()['success']
    edited = client.put('/api/amc/posts/' + pid, json={**AMC, 'title': 'Renamed'}).json()
    assert edited['success'] and edited['post']['title'] == 'Renamed'
    assert client.delete('/api/amc/posts/' + pid).json()['success']
    assert client.get('/api/amc/posts').json()['posts'] == []


def _amc_test(count=25):
    return [{'statement': 'What is ${} + 1$?'.format(n),
             'choices': ['${}$'.format(n + k) for k in range(5)],
             'answer': 'ABCDE'[n % 5], 'solution': 'It is ${}$.'.format(n + 1) if n == 1 else ''}
            for n in range(1, count + 1)]


def test_a_whole_test_is_saved_with_its_answer_key(client):
    made = client.post('/api/amc/posts', json={
        'kind': 'test', 'level': 'AMC 10', 'title': 'Practice 10A', 'problems': _amc_test()}).json()
    assert made['success'], made
    post = made['post']
    assert post['kind'] == 'test' and len(post['problems']) == 25
    assert post['key'] == ['ABCDE'[n % 5] for n in range(1, 26)]
    assert post['problems'][0]['solution'] == 'It is $2$.' and post['problems'][1]['solution'] == ''
    client.post('/api/amc/posts', json=AMC)
    assert [p['kind'] for p in client.get('/api/amc/posts', params={'kind': 'test'}).json()['posts']] == ['test']
    assert [p['kind'] for p in client.get('/api/amc/posts', params={'kind': 'problem'}).json()['posts']] == ['problem']
    assert len(client.get('/api/amc/posts').json()['posts']) == 2
    fixed = _amc_test()
    fixed[24]['answer'] = 'A'
    edited = client.put('/api/amc/posts/' + post['id'], json={
        'kind': 'test', 'level': 'AMC 10', 'title': 'Practice 10A', 'problems': fixed}).json()
    assert edited['success'] and edited['post']['key'][24] == 'A'


def test_an_aime_test_has_fifteen_integer_answers(client):
    problems = [{'statement': 'Find ${}^2$.'.format(n), 'answer': str(n * n)} for n in range(1, 16)]
    made = client.post('/api/amc/posts', json={
        'kind': 'test', 'level': 'AIME', 'title': 'Practice AIME', 'problems': problems}).json()
    assert made['success'] and made['post']['key'][14] == '225'
    assert made['post']['problems'][0]['choices'] is None


@pytest.mark.parametrize('change, message', [
    ({'problems': _amc_test(24)}, 'has 25 problems; this one has 24'),
    ({'title': ''}, 'Give the test a name'),
    ({'problems': _amc_test()[:6] + [{**_amc_test()[6], 'answer': ''}] + _amc_test()[7:]}, 'Problem 7 needs'),
    ({'problems': _amc_test()[:2] + [{**_amc_test()[2], 'statement': ''}] + _amc_test()[3:]}, 'Problem 3 has no text'),
])
def test_bad_tests_are_refused_with_a_reason(client, change, message):
    body = {'kind': 'test', 'level': 'AMC 12', 'title': 'T', 'problems': _amc_test(), **change}
    reply = client.post('/api/amc/posts', json=body).json()
    assert not reply['success'] and message in reply['message'], reply


def test_a_pasted_test_and_key_are_read_into_problems(client):
    lines = []
    for n in range(1, 26):
        if n == 9:
            continue
        lines.append('{}. What is ${} \\times 2$?'.format(n, n))
        lines.append(' '.join('({}) {}'.format(l, 2 * n + k) for k, l in enumerate('ABCDE')))
    key = '\n'.join('{}. A'.format(n) for n in range(1, 26))
    reply = client.post('/api/amc/posts/parse', json={'level': 'AMC 10', 'problems': '\n'.join(lines), 'key': key}).json()
    assert reply['success']
    problems = reply['problems']
    assert len(problems) == 25 and problems[0]['statement'] == 'What is $1 \\times 2$?'
    assert problems[0]['choices'] == ['2', '3', '4', '5', '6'] and problems[0]['answer'] == 'A'
    assert problems[8]['statement'] == '' and any('Problem 9 was not found' in i for i in reply['issues'])


def test_a_pasted_aime_key_fills_the_answers():
    source = '\n'.join('Problem {}. Find the value of ${}$.'.format(n, n) for n in range(1, 16))
    problems, issues = posts.parse('AIME', source, ' '.join(str(n * 7) for n in range(1, 16)))
    assert [p['answer'] for p in problems] == [str(n * 7) for n in range(1, 16)]
    assert issues == []
