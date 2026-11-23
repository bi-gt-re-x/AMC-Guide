"""Import the official AMC 10 papers not yet in the database (2000-2012A in a
fresh one) from Hugging Face datasets, as far as they reach.

    .venv-fastapi/bin/python scripts/import_amc10_hf.py --user temu --dry-run   # report only
    .venv-fastapi/bin/python scripts/import_amc10_hf.py --user temu             # import
    .venv-fastapi/bin/python scripts/import_amc10_hf.py --user temu --only 2010-amc-10b

## Where the problems come from

No one dataset has the AMC 10 whole, so each problem is taken from the first
source that has it with its five choices and a letter answer:

1. `pkuAI4M/AOPS` - AoPS wiki problems with their choices, linked to the page
   (so to the paper and number), with a letter answer, or a value that picks
   the letter out of the choices.
2. `furonghuang-lab/Easy2Hard-Bench`, config `E2H-AMC` - every AMC 10 from
   2003 to 2021 by paper and number (`tag` AMC10, `subtest` 10A/10B, `index`),
   mixed in with AMC 8/12, AIME and HMMT, but with the choices cut off and the
   answer given as a value (`24`, `\\frac{15}{32}\\sqrt{3}`). Its text is used to
   find the same problem with choices, and its value to pick the letter:
   a. on the same year's AMC 12 paper, already in the database (the two papers
      share about half their problems), whose letter it must agree with;
   b. in the NuminaMath AMC/AIME problems (`felixZzz/numina_162k_amc_aime_problems`,
      `Blancy/amc_aime_math_220k_subset`), which keep the choices but not where
      a problem came from.

Matches are by normalised text, at least 90% alike (80% when the value also
picks the AMC 12 twin's letter). Where two sources both have a problem, their
answers must agree or the run says so.

## What is left out

A problem none of them has with choices is not invented: the paper is saved
with the problems found, and the app treats it as it treats any part-imported
paper (the problems can be read and practised; a timed sitting needs all 25,
and "Import many papers" still lists the paper, so pasting the AoPS page fills
the rest). A paper already complete in the database is never touched, and a
partial one is replaced only by a run that finds more of it.

Development tool. Writes to whatever database the app is configured for.
"""
import argparse
import collections
import difflib
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

E2H = ('furonghuang-lab/Easy2Hard-Bench', 'E2H-AMC', ('train', 'eval'))
AOPS = 'pkuAI4M/AOPS'
NUMINA = ('felixZzz/numina_162k_amc_aime_problems', 'Blancy/amc_aime_math_220k_subset')
LETTERS = 'ABCDE'


# ---------------------------------------------------------------------------
# Reading the sources
# ---------------------------------------------------------------------------
def contest_id(year, paper):
    """(2005, 'A') -> '2005-amc-10a'; 2000 and 2001 had one AMC 10."""
    return '{}-amc-10'.format(year) if year < 2002 else '{}-amc-10{}'.format(year, paper.lower())


def load(cache=None):
    """{'e2h': [...], 'aops': [...], 'numina': [...]}, fetched or read from `cache`."""
    def get(name, fetch):
        path = os.path.join(cache, name + '.json') if cache else None
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        rows = fetch()
        if path:
            os.makedirs(cache, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(rows, f)
        return rows

    e2h = get('e2h_amc', lambda: [r for split in E2H[2] for r in hf.fetch_rows(E2H[0], E2H[1], split)])
    aops = get('aops', lambda: hf.fetch_rows(AOPS))
    numina = get('numina', lambda: [{'problem': r['problem']} for ds in NUMINA for r in hf.fetch_rows(ds)
                                    if r.get('source', 'amc_aime') == 'amc_aime'])
    return {'e2h': e2h, 'aops': aops, 'numina': numina}


def by_number(sources):
    """The E2H and AoPS rows keyed by (contest id, problem number)."""
    e2h = {}
    for r in sources['e2h']:
        # 2021 ran twice and E2H tells the sittings apart only by month; those
        # papers came in from AoPS already.
        if r.get('tag') == 'AMC10' and r.get('year') and r['year'] != 2021 and r.get('subtest'):
            e2h[(contest_id(int(r['year']), r['subtest'][-1]), int(r['index']))] = r
    aops = {}
    for r in sources['aops']:
        m = re.search(r'index\.php/(\d{4})_AMC_10([AB]?)_Problems/Problem_(\d+)$', r.get('link') or '')
        if m:
            aops[(contest_id(int(m.group(1)), m.group(2)), int(m.group(3)))] = r
    return e2h, aops


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def norm(text):
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def value(text):
    """An answer or a choice reduced for comparing: `$\\dfrac{1}{2}$` and `\\frac{1}{2}` alike."""
    s = '' if text is None else str(text)
    s = re.sub(r'\\(?:d|t)frac', r'\\frac', s)
    s = re.sub(r'\\text\{\s*([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\(?:left|right|,|;|!|\s)', '', s)
    s = s.replace('$', '').replace('{,}', '').replace('\\%', '%').replace('\\mathdollar', '').replace('\\$', '')
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    s = re.sub(r'\.0+$', '', s.strip())
    return re.sub(r'\s+', '', s).lower()


def letter_for(choices, answer):
    """The one choice whose value is `answer`, as a letter; None if not exactly one."""
    hits = [i for i, c in enumerate(choices or []) if value(c) == value(answer)]
    return LETTERS[hits[0]] if len(hits) == 1 and value(answer) else None


def parse_one(text, pid=''):
    """One problem's text as {'statement', 'choices', 'diagram'}, through the paste parser."""
    found = official.parse_contest('==Problem 1==\n' + hf.to_wiki(text, pid), 'AMC 10')
    return found[0] if found else None


class Pool:
    """Texts to find a problem among, with a cheap shingle filter before difflib."""

    def __init__(self, items, text):
        self.items = [(norm(text(i)), i) for i in items]
        self.shingles = [{k[j:j + 12] for j in range(0, max(1, len(k) - 11), 3)} for k, _ in self.items]

    def best(self, target):
        t = norm(target)
        ts = {t[j:j + 12] for j in range(max(1, len(t) - 11))}
        score, found = 0.0, None
        for (k, item), ks in zip(self.items, self.shingles):
            if len(self.items) > 100 and len(ks & ts) < max(2, len(ks) // 10):
                continue
            sm = difflib.SequenceMatcher(None, k, t, autojunk=False)
            if sm.real_quick_ratio() <= score or sm.quick_ratio() <= score:
                continue
            r = sm.ratio()
            if r > score:
                score, found = r, item
        return score, found


_CHOICES_START = re.compile(r'\$?\s*\\(?:textbf|text|mathrm)\s*\{\s*\(A\)|\(\s*\\mathrm\s*\{?\s*A')


def build(sources, contests):
    """{contest id: ({number: problem}, {number: letter}, {number: source})} and a list of conflicts."""
    e2h, aops = by_number(sources)
    numina = Pool(sources['numina'], lambda r: _CHOICES_START.split(r['problem'])[0])
    twelve = collections.defaultdict(list)
    for p in official.all_problems():
        if p['level'] == 'AMC 12':
            twelve[p['contest']].append(p)
    twins = {}
    out, conflicts = {}, []
    for cid in contests:
        problems, key, source = {}, {}, {}
        for n in range(1, catalog.PAST_BY_ID[cid]['count'] + 1):
            e = e2h.get((cid, n))
            got = _from_aops(aops.get((cid, n)), e, conflicts, cid, n)
            if not got and e:
                if cid not in twins:
                    twins[cid] = Pool(twelve.get(cid.replace('amc-10', 'amc-12'), []), lambda p: p['statement'])
                got = _from_twin(twins[cid], e, conflicts, cid, n) or _from_numina(numina, e)
            if got:
                p, letter, where = got
                problems[n], key[n], source[n] = dict(p, number=n), letter, where
        out[cid] = (problems, key, source)
    return out, conflicts


def _from_aops(row, e, conflicts, cid, n):
    if not row:
        return None
    p = parse_one(row['problem'])
    if not (p and p['choices']):
        return None
    letter = row.get('letter') if row.get('letter') in list(LETTERS) else None
    letter = letter or letter_for(p['choices'], row.get('answer')) or (e and letter_for(p['choices'], e['answer']))
    if not letter:
        return None
    check = e and letter_for(p['choices'], e['answer'])
    if check and check != letter:
        conflicts.append((cid, n, 'AoPS says {}, E2H\'s {} is {}'.format(letter, e['answer'], check)))
    return p, letter, 'aops'


def _from_twin(pool, e, conflicts, cid, n):
    score, twin = pool.best(e['problem'])
    if not twin:
        return None
    check = letter_for(twin['choices'], e['answer'])
    if score > 0.9 or (score > 0.8 and check == twin['answer']):
        if check and check != twin['answer']:
            conflicts.append((cid, n, '{} says {}, E2H\'s {} is {}'.format(twin['id'], twin['answer'], e['answer'], check)))
        p = {'statement': twin['statement'], 'choices': twin['choices'], 'diagram': twin['diagram']}
        return p, twin['answer'], 'amc12:' + twin['id']
    return None


def _from_numina(pool, e):
    score, row = pool.best(e['problem'])
    if score <= 0.9:
        return None
    p = parse_one(row['problem'])
    letter = letter_for(p and p['choices'], e['answer'])
    return (p, letter, 'numina') if letter else None


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--user', required=True, help='username recorded as the importer')
    ap.add_argument('--dry-run', action='store_true', help='report what would be saved, save nothing')
    ap.add_argument('--only', help='comma-separated contest ids, e.g. 2010-amc-10b')
    ap.add_argument('--cache', help='keep the downloaded rows in this folder and reuse them')
    args = ap.parse_args()

    have = official.imported_contests()
    only = set(filter(None, (args.only or '').split(',')))
    contests = [c['id'] for c in catalog.PAST if c['level'] == 'AMC 10'
                and have.get(c['id'], 0) < c['count'] and (not only or c['id'] in only)]
    if not contests:
        print('Every AMC 10 asked for is already complete.')
        return
    sources = load(args.cache)
    print('{} E2H, {} AoPS and {} NuminaMath rows'.format(
        len(sources['e2h']), len(sources['aops']), len(sources['numina'])))
    built, conflicts = build(sources, contests)

    totals, saved = collections.Counter(), []
    for cid in contests:
        problems, key, source = built[cid]
        count = catalog.PAST_BY_ID[cid]['count']
        totals.update(s.split(':')[0] for s in source.values())
        gaps = [n for n in range(1, count + 1) if n not in problems]
        print('{:<15} {:>2}/{}  {}'.format(cid, len(problems), count,
                                           'missing ' + ', '.join(map(str, gaps)) if gaps else 'complete'))
        if not problems or len(problems) <= have.get(cid, 0):
            continue
        if not args.dry_run:
            letters = [key.get(n, '') for n in range(1, count + 1)]
            official.save_contest(cid, [problems[n] for n in sorted(problems)], letters, args.user)
        saved.append(cid)

    found = sum(totals.values())
    print('{} problems: {} from AoPS, {} from the AMC 12 twin, {} from NuminaMath'.format(
        found, totals['aops'], totals['amc12'], totals['numina']))
    print('{} {} papers ({} complete)'.format('Would save' if args.dry_run else 'Saved', len(saved),
                                              sum(1 for c in saved if len(built[c][0]) == 25)))
    for c in conflicts:
        print('CONFLICT', *c)


if __name__ == '__main__':
    main()
