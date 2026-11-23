"""Import the official AMC 12 papers not yet in the database from the Hugging
Face dataset `edev2000/amc12-full` (2000-2025: problem text, answer key,
difficulty and problem id for each problem).

    .venv-fastapi/bin/python scripts/import_amc12_hf.py --user temu --dry-run   # check only
    .venv-fastapi/bin/python scripts/import_amc12_hf.py --user temu             # import
    .venv-fastapi/bin/python scripts/import_amc12_hf.py --user temu --replace   # redo all

Papers already imported are left alone unless --replace says otherwise, so the
ones pasted in from the AoPS wiki (better text, worked solutions) keep theirs.

Each row is turned into the AoPS wiki source the paste importer already reads
(`==Problem N==`, `<asy>` for diagrams, `[[Image:...]]` for pictures the
dataset only names) and goes through backend/amc/official.py's `check` and
`save_contest`, exactly as a pasted paper would. A paper is saved only when
`check` finds all 25 problems with text and a full answer key.

The dataset's ids are `2019A-P5` (2000 and 2001 ran one AMC 12, filed as `A`);
AMC Guide's are `2019-amc-12a-5`. Its difficulty is the position band
(problems 1-10 are 2, 11-20 are 3, 21-25 are 4), which AMC Guide already
derives, finer, from the position (backend/amc/scale.py); the script checks
that the two agree in order rather than storing a second, coarser scale.

Development tool. Writes to whatever database the app is configured for.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.config import settings  # noqa: E402

settings.load_dotenv()

from backend.amc import catalog, official  # noqa: E402

DATASET = 'edev2000/amc12-full'
ROWS_URL = 'https://datasets-server.huggingface.co/rows'
PAGE = 100

#: Answers the dataset gives as more than one letter, settled to the one the
#: answer key stores. 2012 AMC 12B #12: the MAA accepted both (D) 380 and
#: (E) 382 (the wording let "all the zeros consecutive" hold with no zeros);
#: AoPS's answer key lists (D).
ANSWER_OVERRIDES = {'2012B-P12': 'D'}


def fetch_rows(dataset=DATASET):
    """Every row of the dataset's train split."""
    rows, offset = [], 0
    while True:
        url = ROWS_URL + '?' + urllib.parse.urlencode(
            dict(dataset=dataset, config='default', split='train', offset=offset, length=PAGE))
        for attempt in range(6):
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    page = json.load(resp)
                break
            except Exception:  # noqa: BLE001 - the server rate-limits; back off and retry
                time.sleep(2 + attempt * 3)
        else:
            raise SystemExit('Could not fetch rows at offset {}.'.format(offset))
        batch = [r['row'] for r in page['rows']]
        rows += batch
        offset += len(batch)
        if not batch or offset >= page['num_rows_total']:
            return rows


def contest_id(dataset_id):
    """'2019A-P5' -> ('2019-amc-12a', 5); 2000 and 2001 had one paper."""
    m = re.fullmatch(r'(\d{4})([AB])-P(\d+)', dataset_id)
    if not m:
        return None, None
    year, paper, number = int(m.group(1)), m.group(2), int(m.group(3))
    cid = '{}-amc-12'.format(year) if year < 2002 else '{}-amc-12{}'.format(year, paper.lower())
    return cid, number


_CHOICE_START = re.compile(r'^\s*(?:\\(?:textbf|mathrm|text|textrm|mathbf)\s*\{\s*\(A\)|\(A\))')
_LAST_MARK = re.compile(r'\\(?:textbf|mathrm|text)\s*\{\s*\(E\)\s*\}\s*$')


def repair(pid, question):
    """Mend the few rows the dataset scraped out of order."""
    text = question.replace('\r\n', '\n')
    # A wiki section heading caught mid-problem (2012 AMC 12B #25) would end the
    # problem there and lose its choices.
    text = re.sub(r'\n\s*==+\s*See also\s*==+\s*\n', '\n\n', text, flags=re.I)
    # Choice (E)'s words scraped to before the choices, which then end on a bare
    # `\textbf{(E)}` (2013 AMC 12B #18, 2017 AMC 12B #7 and #17): move them back.
    paras = re.split(r'\n\s*\n', text.strip())
    if len(paras) >= 3 and _CHOICE_START.match(paras[-1]) and _LAST_MARK.search(paras[-1]):
        stray, choices = paras[-2].strip(), paras[-1].strip()
        if re.match(r'\\(?:textbf|mathrm|text)\s*\{\s*\(A\)\s*\}\s*\$', choices):
            # Choices in words, each letter in math of its own: `\textbf{(A)}$ words  $\textbf{(B)}$ ...`.
            choices = '$' + choices + '$ ' + stray
        else:
            choices = choices + r'\ \text{' + stray.replace('$', '') + '}'
        paras[-2:] = [choices]
        text = '\n\n'.join(paras)
    # 2002 AMC 12A #25: the choices are the five graphs, labelled (A)-(E) in the figure.
    if pid == '2002A-P25':
        text += '\n\n$' + r'\qquad'.join(r'\textbf{(%s)}\ \text{Graph %s}' % (c, c) for c in 'ABCDE') + '$'
    return text


def to_wiki(question, pid=''):
    """A dataset question as the AoPS wiki source official.parse_contest reads."""
    text = repair(pid, question)
    # Diagrams arrive as fenced ```asy blocks.
    text = re.sub(r'```\s*asy\s*\n(.*?)```', lambda m: '<asy>' + m.group(1) + '</asy>', text, flags=re.S)
    # Pictures the dataset only names (`Image:2004 AMC 12A Problem 5.png`).
    text = re.sub(r'(?:<center>\s*)?\b(?:Image|File):([^\n<]*?\.(?:png|gif|jpe?g|svg))(?:\s*</center>)?',
                  lambda m: '[[Image:' + m.group(1).strip() + ']]', text, flags=re.I)
    # A choices paragraph written without math delimiters goes in math, as the
    # wiki writes it, so `10\%` and `\frac{1}{2}` come out as math.
    paras = re.split(r'(\n\s*\n)', text)
    for i, para in enumerate(paras):
        if _CHOICE_START.match(para) and not re.search(r'(?<!\\)\$', para):
            paras[i] = '$' + para.strip() + '$'
    return ''.join(paras)


def build(rows):
    """{contest_id: (wiki source, key source, [(number, difficulty)])}."""
    by_contest = {}
    for row in rows:
        cid, number = contest_id(row['problem_id'])
        if cid not in catalog.PAST_BY_ID:
            print('skipped {}: no such AMC 12'.format(row['problem_id']))
            continue
        answer = ANSWER_OVERRIDES.get(row['problem_id'], str(row['answer']).strip())
        by_contest.setdefault(cid, {})[number] = (to_wiki(row['question'], row['problem_id']),
                                                  answer, row.get('difficulty'))
    out = {}
    for cid, problems in by_contest.items():
        numbers = sorted(problems)
        source = '\n\n'.join('==Problem {}==\n{}'.format(n, problems[n][0]) for n in numbers)
        # One `N. X` line each, so a gap in the dataset leaves the key short
        # (and the paper unsaved) rather than shifting every later answer.
        key = '\n'.join('{}. {}'.format(n, problems[n][1]) for n in numbers)
        out[cid] = (source, key, [(n, problems[n][2]) for n in numbers])
    return out


def difficulty_agrees(level, bands):
    """True when the dataset's difficulty never falls as AMC Guide's rises."""
    ours = sorted((official.difficulty_at(level, n), d) for n, d in bands if d is not None)
    theirs = [d for _, d in ours]
    return theirs == sorted(theirs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--user', required=True, help='username recorded as the importer')
    ap.add_argument('--dry-run', action='store_true', help='check every paper, save nothing')
    ap.add_argument('--replace', action='store_true', help='re-import papers already in the database')
    ap.add_argument('--rows', help='read the dataset from this JSON file instead of fetching it')
    args = ap.parse_args()

    if args.rows:
        with open(args.rows) as f:
            rows = json.load(f)
    else:
        rows = fetch_rows()
    print('{} rows from {}'.format(len(rows), DATASET))

    have = official.imported_contests()
    saved, skipped, failed = [], [], []
    for cid, (source, key_source, bands) in sorted(build(rows).items()):
        if cid in have and not args.replace:
            skipped.append(cid)
            continue
        problems, key, issues, complete = official.check(cid, source, key_source)
        if not difficulty_agrees(catalog.PAST_BY_ID[cid]['level'], bands):
            issues.append("The dataset's difficulty runs against the problem order.")
        if not complete:
            failed.append(cid)
            print('NOT SAVED {}: {}'.format(cid, ' '.join(issues)))
            continue
        if issues:
            print('{}: {}'.format(cid, ' '.join(issues)))
        if not args.dry_run:
            official.save_contest(cid, problems, key, args.user)
        saved.append(cid)

    verb = 'Would import' if args.dry_run else 'Imported'
    print('{} {} papers: {}'.format(verb, len(saved), ', '.join(saved) or '-'))
    print('Already in the database, left alone: {}'.format(len(skipped)))
    if failed:
        print('Could not import {}: {}'.format(len(failed), ', '.join(failed)))
        sys.exit(1)


if __name__ == '__main__':
    main()
