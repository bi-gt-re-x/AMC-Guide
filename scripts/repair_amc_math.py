"""Repair the math in official problems already in the database, so the page
can draw them. Imports now go through these rules (backend/amc/official.py),
but papers imported before them keep what they were saved with.

    .venv-fastapi/bin/python scripts/repair_amc_math.py            # report only
    .venv-fastapi/bin/python scripts/repair_amc_math.py --apply    # save the repairs

What it mends, in each statement and choice:

- LaTeX KaTeX does not have (`\\mathdollar`, `\\mbox`, `\\hdots`, `tabular` and
  `\\multicolumn`, a no-break space after a backslash), through
  `official.katex_compat`.
- Dollar signs that throw the page's `$`-splitting out of step: a price typed
  as `$$3$` or `$$ $1$` (a bare dollar sign before the math), two inline maths
  touching (`$\\triangle$$EBD$`) or running into a display block
  (`$b,$$$f(a+b)...$$`), and a lone `$` left at the end.
- Two problems whose text was cut short on import, restored from the paper
  (2019 AMC 12A #21's `z^{{12}^2}` lost to template stripping, and the `=`
  missing from 2023 AMC 12A #15).

A row is changed only if it is broken now and the repair leaves it whole; the
report lists every change. Development tool. Writes to whatever database the
app is configured for.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.config import settings  # noqa: E402

settings.load_dotenv()

from backend.amc import official  # noqa: E402

#: Text cut short on import, by problem: (as stored, as on the paper).
RESTORE = {
    '2019-amc-12a-21': (
        r'\left(z^{1^2}+z^{2^2}+z^{3^2}+\dots+z^+\frac{1}{z^{2^2}}+\frac{1}{z^{3^2}}+\dots+\frac{1}{z^\right)?',
        r'\left(z^{1^2}+z^{2^2}+z^{3^2}+\dots+z^{{12}^2}\right) \cdot '
        r'\left(\frac{1}{z^{1^2}}+\frac{1}{z^{2^2}}+\frac{1}{z^{3^2}}+\dots+\frac{1}{z^{{12}^2}}\right)?',
    ),
    '2023-amc-12a-15': (
        r'What angle $\theta$$\angle PAB=',
        r'What angle $\theta=\angle PAB=',
    ),
}

_KATEX_GAPS = re.compile(r'\\(?:mathdollar|textdollar|mbox|hdots|overarc)(?![A-Za-z])|\\begin\{tabular\}'
                         r'|\\begin\{array\}\s*\[|\\multicolumn| ')


def steps(text):
    """Where `text` throws the page's splitter out of step (MathText.splitMath):
    a `$$` closing inline math, a `$` closing display math, or math left open."""
    bad, mode, i = [], 'text', 0
    while i < len(text):
        if text.startswith('\\$', i):
            i += 2
            continue
        if text[i] != '$':
            i += 1
            continue
        double = text.startswith('$$', i)
        if mode == 'text':
            mode = 'display' if double else 'inline'
        else:
            if (mode == 'inline') == double:
                bad.append(i)
            mode = 'text'
        i += 2 if double else 1
    if mode != 'text':
        bad.append(len(text))
    return bad


def mend_dollars(text):
    """The dollar-sign repairs, left to right as the splitter reads."""
    # A price: a bare dollar sign straight before inline math (`$$3$`, `$$ $1$`).
    text = re.sub(r'(?<![\\$])\$\$ ?\$(?=[\d.,]+\$(?!\$))', r'\\$$', text)
    text = re.sub(r'(?<![\\$])\$\$(?=[\d.,]+\$(?!\$))', r'\\$$', text)
    out, mode, i = [], 'text', 0
    while i < len(text):
        if text.startswith('\\$', i):
            out.append('\\$')
            i += 2
            continue
        if text[i] != '$':
            out.append(text[i])
            i += 1
            continue
        if mode == 'inline' and text.startswith('$$$', i):
            # Inline math running into a display block: close one, open the other.
            out.append('$ $$')
            mode = 'display'
            i += 3
        elif mode == 'inline' and text.startswith('$$', i):
            # Two inline maths touching.
            out.append('$ $')
            i += 2
        elif text.startswith('$$', i):
            out.append('$$')
            mode = 'display' if mode == 'text' else 'text'
            i += 2
        else:
            out.append('$')
            mode = 'inline' if mode == 'text' else 'text'
            i += 1
    text = ''.join(out)
    # A lone `$` with nothing after it.
    if steps(text) == [len(text)]:
        text = re.sub(r'\s*(?<!\\)\$\s*$', '', text)
    return text


def mend(pid, text):
    if pid in RESTORE and RESTORE[pid][0] in text:
        text = text.replace(*RESTORE[pid])
    return mend_dollars(official.katex_compat(text))


def broken(pid, text):
    return bool(steps(text) or _KATEX_GAPS.search(text) or (pid in RESTORE and RESTORE[pid][0] in text))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--apply', action='store_true', help='save the repairs (default: report only)')
    args = ap.parse_args()

    con = official.connect()
    changes = []
    try:
        rows = con.execute('SELECT contest_id, number, statement, choices FROM amc_official').fetchall()
        for r in rows:
            pid = official.problem_id(r['contest_id'], r['number'])
            statement = r['statement'] or ''
            choices = json.loads(r['choices']) if r['choices'] else None
            texts = [statement] + (choices or [])
            if not any(broken(pid, t) for t in texts):
                continue
            new_statement = mend(pid, statement) if broken(pid, statement) else statement
            new_choices = [mend(pid, c) if broken(pid, c) else c for c in choices] if choices else choices
            after = [new_statement] + (new_choices or [])
            left = [t for t in after if broken(pid, t)]
            if left:
                print('NOT MENDED', pid, '|', left[0][:120].replace('\n', ' '))
                continue
            changes.append(pid)
            print('==', pid)
            for old, new in zip(texts, after):
                if old != new:
                    print('  -', old[:200].replace('\n', ' '))
                    print('  +', new[:200].replace('\n', ' '))
            if args.apply:
                with con:
                    con.execute('UPDATE amc_official SET statement = ?, choices = ? WHERE contest_id = ? AND number = ?',
                                (new_statement, json.dumps(new_choices) if new_choices else None,
                                 r['contest_id'], r['number']))
    finally:
        con.close()
    official.forget()
    print('{} {} problems'.format('Repaired' if args.apply else 'Would repair', len(changes)))


if __name__ == '__main__':
    main()
