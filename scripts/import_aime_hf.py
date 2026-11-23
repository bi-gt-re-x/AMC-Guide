"""Import the official AIME papers not yet in the database (2000 I-2025 II)
from Hugging Face datasets.

    .venv-fastapi/bin/python scripts/import_aime_hf.py --user temu --dry-run   # check only
    .venv-fastapi/bin/python scripts/import_aime_hf.py --user temu             # import
    .venv-fastapi/bin/python scripts/import_aime_hf.py --user temu --only 2012-aime-i

Each problem comes from the first of these that has it:

1. `allenai/aime-2022-2025` - every problem of 2022 I to 2025 II, linked to its
   AoPS page, with its Asymptote figures.
2. `gneubig/aime-1983-2024` - 1983 to 2024 by year, part and number, but with
   a few dozen problems left out (2024 I entirely). The catalogue starts at 2000.
3. `pkuAI4M/AOPS` - AoPS wiki problems by page, which has every one the other
   two leave out.

Where two of them have a problem, their answers must agree or the run says so
and saves nothing for that paper. Each paper then goes through
backend/amc/official.py's `check` and `save_contest` like a pasted one, and is
saved only when all 15 problems and answers are there. A paper already in the
database is left alone unless --replace or --only says otherwise.

The allenai rows lost backslashes to JSON escapes in 2025 (`\\frac` became a
form feed and `rac`); those are put back. A problem that speaks of a figure
("as shown", "the diagram") but arrives without its Asymptote source is
flagged as having a picture, as the paste importer flags one it could not get.

Development tool. Writes to whatever database the app is configured for.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from backend.config import settings  # noqa: E402

settings.load_dotenv()

from backend.amc import catalog, official  # noqa: E402
import import_amc12_hf as hf  # noqa: E402

ALLENAI = 'allenai/aime-2022-2025'
GNEUBIG = 'gneubig/aime-1983-2024'
AOPS = 'pkuAI4M/AOPS'

#: Answers given as more than one number, settled to one. 2022 AIME II #8: the
#: MAA accepted both 080 and 081 (the problem's wording allowed either reading).
ANSWER_OVERRIDES = {'2022-aime-ii-8': 80}

_FIGURE = re.compile(r'\b(?:as shown|shown below|shown above|shown in the|diagram|figure|pictured|'
                     r'labeled as shown)\b', re.I)
#: A JSON escape that ate a LaTeX command's first letter: `\f`rac, `\b`egin, `\t`imes, `\r`ight.
_EATEN = {'\x0c': 'f', '\x08': 'b', '\t': 't', '\r': 'r'}


def contest_id(year, part):
    """(2012, 'I') -> '2012-aime-i'."""
    return '{}-aime-{}'.format(int(year), part.lower())


def unescape(text):
    """Put back what the allenai rows lost to escaping: the LaTeX letters a JSON
    escape turned into control characters, the `\\\\` line break inside an
    `align*` cut to one backslash (2025 I #8), and a stray closing `$` left at
    the end (2025 I #5 and #8)."""
    text = re.sub(r'(\\?)([\x0c\x08\t\r])(?=[A-Za-z])', lambda m: (m.group(1) or '\\') + _EATEN[m.group(2)], text)
    text = re.sub(r'\\begin\{(align\*?|aligned|cases)\}.*?\\end\{\1\}',
                  lambda m: re.sub(r'(?<![\\])\\(?=\s+&)', r'\\\\', m.group(0)), text, flags=re.S)
    if len(re.findall(r'(?<!\\)\$', text)) % 2 and text.rstrip().endswith('$'):
        text = text.rstrip()[:-1]
    return text


def number(answer):
    """'089', '89.0', 89 -> 89; None for anything that is not one whole number."""
    m = re.fullmatch(r'\s*(\d{1,3})(?:\.0+)?\s*', str(answer))
    return int(m.group(1)) if m else None


def load(cache=None):
    """{'allenai': [...], 'gneubig': [...], 'aops': [...]}, fetched or read from `cache`."""
    def get(name, dataset):
        path = os.path.join(cache, name + '.json') if cache else None
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        rows = hf.fetch_rows(dataset)
        if path:
            os.makedirs(cache, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(rows, f)
        return rows
    return {'allenai': get('allenai', ALLENAI), 'gneubig': get('gneubig', GNEUBIG), 'aops': get('aops', AOPS)}


def by_number(sources):
    """{source name: {(contest id, number): (text, answer)}} for papers in the catalogue."""
    out = {'allenai': {}, 'gneubig': {}, 'aops': {}}
    page = re.compile(r'(\d{4})_AIME_(I{1,2})_Problems/Problem_(\d+)$')
    for r in sources['allenai']:
        m = page.search(r.get('url') or '')
        if m:
            out['allenai'][(contest_id(m.group(1), m.group(2)), int(m.group(3)))] = (unescape(r['problem']), r['answer'])
    for r in sources['gneubig']:
        if r.get('Part') in ('I', 'II'):
            out['gneubig'][(contest_id(r['Year'], r['Part']), int(r['Problem Number']))] = (r['Question'], r['Answer'])
    for r in sources['aops']:
        m = page.search(r.get('link') or '')
        if m:
            out['aops'][(contest_id(m.group(1), m.group(2)), int(m.group(3)))] = (r['problem'], r['answer'])
    return {name: {k: v for k, v in rows.items() if k[0] in catalog.PAST_BY_ID} for name, rows in out.items()}


def build(sources, contests):
    """{contest id: (wiki source, key source, {number: source name})}, and the conflicts."""
    rows = by_number(sources)
    out, conflicts = {}, []
    for cid in contests:
        texts, answers, where = {}, {}, {}
        for n in range(1, catalog.PAST_BY_ID[cid]['count'] + 1):
            pid = official.problem_id(cid, n)
            found = [(name, rows[name][(cid, n)]) for name in ('allenai', 'gneubig', 'aops') if (cid, n) in rows[name]]
            if not found:
                continue
            values = {name: number(ANSWER_OVERRIDES.get(pid, a)) for name, (_, a) in found}
            if len(set(v for v in values.values() if v is not None)) > 1:
                conflicts.append((cid, n, values))
                continue
            answer = next((v for v in values.values() if v is not None), None)
            if answer is None:
                conflicts.append((cid, n, {name: a for name, (_, a) in found}))
                continue
            name, (text, _) = found[0]
            texts[n], answers[n], where[n] = hf.repair(pid, text), answer, name
        source = '\n\n'.join('==Problem {}==\n{}'.format(n, texts[n]) for n in sorted(texts))
        key = '\n'.join('{}. {}'.format(n, answers[n]) for n in sorted(answers))
        out[cid] = (source, key, where)
    return out, conflicts


def flag_figures(problems):
    """A problem that speaks of a figure it arrived without is marked as having one."""
    for p in problems:
        if not p['diagram'] and _FIGURE.search(p['statement']):
            p['diagram'] = 'image'
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--user', required=True, help='username recorded as the importer')
    ap.add_argument('--dry-run', action='store_true', help='check every paper, save nothing')
    ap.add_argument('--replace', action='store_true', help='re-import papers already in the database')
    ap.add_argument('--only', help='comma-separated contest ids, e.g. 2012-aime-i,2012-aime-ii')
    ap.add_argument('--cache', help='keep the downloaded rows in this folder and reuse them')
    args = ap.parse_args()

    have = official.imported_contests()
    only = set(filter(None, (args.only or '').split(',')))
    contests = [c['id'] for c in catalog.PAST if c['level'] == 'AIME' and (not only or c['id'] in only)
                and (only or args.replace or have.get(c['id'], 0) < c['count'])]
    sources = load(args.cache)
    print('{} allenai, {} gneubig and {} AoPS rows'.format(*(len(sources[k]) for k in ('allenai', 'gneubig', 'aops'))))
    built, conflicts = build(sources, contests)
    for c in conflicts:
        print('CONFLICT', *c)
    bad = {c[0] for c in conflicts}

    saved, short = [], []
    for cid in contests:
        source, key_source, where = built[cid]
        if not where:
            short.append('{} (in none of them)'.format(cid))
            continue
        problems, key, issues, complete = official.check(cid, source, key_source)
        if not complete or cid in bad:
            short.append('{}: {}'.format(cid, ' '.join(issues) or 'answers disagree'))
            continue
        if not args.dry_run:
            official.save_contest(cid, flag_figures(problems), key, args.user)
        saved.append(cid)
        used = sorted(set(where.values()))
        print('{:<13} 15/15  from {}'.format(cid, ', '.join('{} {}'.format(
            sum(1 for v in where.values() if v == u), u) for u in used)))

    print('{} {} papers.'.format('Would import' if args.dry_run else 'Imported', len(saved)))
    for s in short:
        print('NOT SAVED', s)
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
