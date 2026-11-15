"""Problems and solutions posted by hand, written in LaTeX the way AoPS writes them.

A post is either one AMC 10, AMC 12 or AIME problem with its answer and,
usually, a solution, or a whole test: all 25 problems of an AMC 10 or AMC 12
(15 of an AIME), each with its choices, its answer (together, the answer key)
and an optional solution. A whole test can be pasted the way an imported paper
is, AoPS wiki source or plain text, with its answer key pasted beside it, and
`parse` reads it into problems to check and edit before it is posted. Both
kinds are stored in `amc_posts` (PostgreSQL in production, SQLite in
tests) and shared by every account. Only its author, or an importer account,
may change or delete it.

Text is saved in the site's one math convention, `$...$` inline and `$$...$$`
on its own line, so the same renderer draws it everywhere. What people paste
from AoPS (`<math>`, `<cmath>`, `\\[...\\]`, `\\(...\\)`) is converted on the
way in, and an AMC problem pasted with its choices line still in it has the
five choices pulled out, the same way an imported paper's are.
"""
import json
import re
import uuid
from datetime import datetime

from backend.amc import catalog, official
from backend.database.connection import connect

LEVELS = ('AMC 10', 'AMC 12', 'AIME')
KINDS = ('problem', 'test')
LIMITS = {'title': 120, 'statement': 8000, 'choice': 400, 'solution': 20000}


class Invalid(ValueError):
    """A post that cannot be saved; the message is the sentence the page shows."""


def to_dollars(text):
    """AoPS math markup into `$...$` and `$$...$$`."""
    text = official._math_to_dollars((text or '').replace('\r\n', '\n'))
    text = re.sub(r'\\\((.*?)\\\)', lambda m: '$' + m.group(1).strip() + '$', text, flags=re.S)
    # Display math is put on its own line; three or more newlines are one break.
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _choice(text):
    """One answer choice. TeX typed without `$` signs (`\\frac12`) is wrapped in them."""
    text = to_dollars(text)
    return '$' + text + '$' if '$' not in text and re.search(r'[\\^_{}]', text) else text


def _unbalanced(text):
    """True when the `$` signs (not counting `\\$`) do not pair up."""
    return len(re.findall(r'(?<!\\)\$', text.replace('$$', ''))) % 2 == 1


def split(statement):
    """A pasted statement with an AoPS choices line in it, as (stem, choices)."""
    text = to_dollars(statement)
    choices, stem = official._find_choices(text)
    return (stem, choices) if choices else (text, None)


def _problem(level, statement, choices, answer, solution, where='The problem'):
    """One problem's statement, choices, answer and solution as stored, or Invalid.

    `where` names the problem in a message, so a test can say which of its
    twenty-five is wrong.
    """
    statement = to_dollars(statement)
    solution = to_dollars(solution)
    if not statement:
        raise Invalid('{} has no text yet.'.format(where))
    if len(statement) > LIMITS['statement']:
        raise Invalid('{} is too long (8000 characters at most).'.format(where))
    if len(solution) > LIMITS['solution']:
        raise Invalid('The solution to {} is too long (20000 characters at most).'.format(where.lower()))
    answer = str(answer or '').strip().upper()
    if level == 'AIME':
        choices = None
        if not re.fullmatch(r'\d{1,3}', answer):
            raise Invalid('{} needs an answer: a whole number from 0 to 999.'.format(where))
        answer = str(int(answer))
    else:
        choices = [_choice(c) for c in (choices or [])]
        if not any(choices):
            stem, found = split(statement)
            if found:
                statement, choices = stem, found
        if len(choices) != 5 or not all(choices):
            raise Invalid('{} needs all five answer choices.'.format(where))
        if any(len(c) > LIMITS['choice'] for c in choices):
            raise Invalid('An answer choice in {} is too long.'.format(where.lower()))
        if len(set(choices)) != 5:
            raise Invalid('Two of the answer choices in {} are the same.'.format(where.lower()))
        if answer not in tuple(official.LETTERS):
            raise Invalid('{} needs its right answer picked, A to E.'.format(where))
    for name, text in [('text', statement), ('solution', solution)] + [
            ('choice ' + 'ABCDE'[i], c) for i, c in enumerate(choices or [])]:
        if _unbalanced(text):
            raise Invalid('The {} of {} has an unmatched $ sign.'.format(name, where.lower()))
    return {'statement': statement, 'choices': choices, 'answer': answer, 'solution': solution}


def clean(level, title, statement, choices, answer, solution):
    """One problem as it will be stored, or Invalid with the reason."""
    if level not in LEVELS:
        raise Invalid('Pick AMC 10, AMC 12 or AIME.')
    title = re.sub(r'\s+', ' ', (title or '')).strip()[:LIMITS['title']]
    body = _problem(level, statement, choices, answer, solution)
    return {'kind': 'problem', 'level': level, 'title': title, **body, 'problems': None}


def clean_test(level, title, problems):
    """A whole test as it will be stored, or Invalid with the reason.

    It needs every problem the contest has (25, or 15 for the AIME), each with
    its answer, so the answer key is complete. Solutions are optional.
    """
    if level not in LEVELS:
        raise Invalid('Pick AMC 10, AMC 12 or AIME.')
    title = re.sub(r'\s+', ' ', (title or '')).strip()[:LIMITS['title']]
    if not title:
        raise Invalid('Give the test a name, e.g. 2024 AMC 10A.')
    count = catalog.FORMATS[level]['count']
    problems = list(problems or [])
    if len(problems) != count:
        raise Invalid('An {} test has {} problems; this one has {}.'.format(level, count, len(problems)))
    out = []
    for n, p in enumerate(problems, 1):
        p = p or {}
        out.append(_problem(level, p.get('statement', ''), p.get('choices'), p.get('answer', ''),
                            p.get('solution', ''), where='Problem {}'.format(n)))
    return {'kind': 'test', 'level': level, 'title': title, 'statement': '', 'choices': None,
            'answer': ' '.join(p['answer'] for p in out), 'solution': '', 'problems': out}


def _problems_are(ns, plural, singular):
    """'Problems 3, 9 have ...' or 'Problem 9 has ...'."""
    if len(ns) == 1:
        return 'Problem {} {}'.format(ns[0], singular)
    return 'Problems {} {}'.format(', '.join(map(str, ns)), plural)


def parse(level, source, key_source):
    """A pasted test and answer key, read into the problems a test post is made of.

    Returns (problems, issues): always one entry per problem the contest has,
    in order, with whatever could be read filled in (a problem that was not
    found is left blank to type in), and the issues as sentences to show.
    """
    if level not in LEVELS:
        raise Invalid('Pick AMC 10, AMC 12 or AIME.')
    count = catalog.FORMATS[level]['count']
    found = {p['number']: p for p in official.parse_contest(source or '', level)}
    key = official.parse_key(key_source or '', level) if (key_source or '').strip() else []
    problems, missing, no_choices, diagrams = [], [], [], []
    for n in range(1, count + 1):
        p = found.get(n)
        if not p or not p['statement']:
            missing.append(n)
        elif level != 'AIME' and not p['choices']:
            no_choices.append(n)
        if p and p['diagram']:
            diagrams.append(n)
        choices = None if level == 'AIME' else ((p and p['choices']) or ['', '', '', '', ''])
        answer = str(key[n - 1]) if n <= len(key) else ''
        problems.append({'statement': p['statement'] if p else '', 'choices': choices,
                         'answer': answer, 'solution': ''})
    issues = []
    if len(missing) == count:
        issues.append('No problems were found. Paste the test with each problem numbered '
                      '("1.", "Problem 1" or ==Problem 1==).')
    elif missing:
        issues.append(_problems_are(missing, 'were not found; type them in below.',
                                    'was not found; type it in below.'))
    if no_choices:
        issues.append(_problems_are(no_choices, 'have no answer choices yet.', 'has no answer choices yet.'))
    if diagrams:
        issues.append(_problems_are(diagrams, 'have a diagram', 'has a diagram') +
                      ', which cannot be drawn here; describe it in the text or leave it out.')
    if not key:
        issues.append('No answer key was pasted; pick each answer below.')
    elif len(key) != count:
        issues.append('The answer key has {} of {} answers.'.format(len(key), count))
    return problems, issues


def _row(row):
    (pid, author, level, title, statement, choices, answer, solution, created, updated,
     kind, problems) = tuple(row)
    post = {'id': pid, 'kind': kind or 'problem', 'author': author, 'level': level, 'title': title or '',
            'statement': statement, 'choices': json.loads(choices) if choices else None, 'answer': answer,
            'solution': solution or '', 'problems': None, 'key': None,
            'created_at': created, 'updated_at': updated}
    if post['kind'] == 'test':
        post['problems'] = json.loads(problems) if problems else []
        post['key'] = [p['answer'] for p in post['problems']]
    return post


_COLUMNS = 'id, author, level, title, statement, choices, answer, solution, created_at, updated_at, kind, problems'


def all_posts(level='', kind=''):
    """Every post, newest first, narrowed to one contest and/or one kind when given."""
    where, args = [], []
    if level:
        where.append('level = ?')
        args.append(level)
    if kind == 'test':
        where.append("kind = 'test'")
    elif kind == 'problem':
        where.append("(kind IS NULL OR kind = 'problem')")
    sql = 'SELECT {} FROM amc_posts{} ORDER BY created_at DESC'.format(
        _COLUMNS, ' WHERE ' + ' AND '.join(where) if where else '')
    con = connect()
    try:
        rows = con.execute(sql, tuple(args)).fetchall()
    finally:
        con.close()
    return [_row(r) for r in rows]


def get(post_id):
    con = connect()
    try:
        row = con.execute('SELECT {} FROM amc_posts WHERE id = ?'.format(_COLUMNS), (post_id,)).fetchone()
    finally:
        con.close()
    return _row(row) if row else None


def _now():
    return datetime.now().isoformat(timespec='seconds')


def _problems(post):
    return json.dumps(post['problems']) if post.get('problems') else None


def create(author, post):
    pid = 'post-' + uuid.uuid4().hex[:10]
    now = _now()
    con = connect()
    try:
        with con:
            con.execute('INSERT INTO amc_posts ({}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(_COLUMNS),
                        (pid, author, post['level'], post['title'], post['statement'],
                         json.dumps(post['choices']) if post['choices'] else None,
                         post['answer'], post['solution'], now, now, post['kind'], _problems(post)))
    finally:
        con.close()
    return get(pid)


def update(post_id, post):
    con = connect()
    try:
        with con:
            con.execute('UPDATE amc_posts SET level = ?, title = ?, statement = ?, choices = ?, answer = ?, '
                        'solution = ?, updated_at = ?, kind = ?, problems = ? WHERE id = ?',
                        (post['level'], post['title'], post['statement'],
                         json.dumps(post['choices']) if post['choices'] else None,
                         post['answer'], post['solution'], _now(), post['kind'], _problems(post), post_id))
    finally:
        con.close()
    return get(post_id)


def delete(post_id):
    con = connect()
    try:
        with con:
            con.execute('DELETE FROM amc_posts WHERE id = ?', (post_id,))
    finally:
        con.close()
