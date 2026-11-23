"""Official problems' figures: which are drawn, and storing a drawing.

    .venv-fastapi/bin/python scripts/figures.py status              # what is not drawn yet, paper by paper
    .venv-fastapi/bin/python scripts/figures.py status --level "AMC 12"
    .venv-fastapi/bin/python scripts/figures.py set 2024-amc-10b-19 path/to/figure.svg
    .venv-fastapi/bin/python scripts/figures.py copy 2024-amc-10b-11 2024-amc-12b-7

A figure is drawn when the problem's `diagram` holds an SVG, which the problem
page shows as an image. Until then the page shows "a figure we can't draw yet"
with a link to AoPS: for Asymptote source (kept from the AoPS page, not drawn
here) and for a picture the import could not bring. Like the problem text, the
drawings live in this install's database, not the repository
(backend/amc/official.py); re-importing a paper keeps them.

`copy` is for the problems an AMC 10 and an AMC 12 share: the same figure.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.config import settings  # noqa: E402

settings.load_dotenv()

from backend.amc import catalog, official  # noqa: E402

WHY = {'asy': 'Asymptote', 'image': 'picture missing', 'mentioned': 'no figure came, text mentions one'}


def status(level=''):
    rows = [(p, why) for p, why in official.undrawn() if not level or p['level'] == level]
    order = {c['id']: i for i, c in enumerate(catalog.PAST)}
    by_paper = {}
    for p, why in rows:
        by_paper.setdefault(p['contest'], []).append((p['number'], why))
    drawn = sum(1 for p in official.all_problems() if official.is_drawn(p['diagram'])
                and (not level or p['level'] == level))
    print('{} drawn, {} not drawn yet{}'.format(drawn, len(rows), ' ({})'.format(level) if level else ''))
    for cid in sorted(by_paper, key=lambda c: order.get(c, 10 ** 6)):
        items = sorted(by_paper[cid])
        print('  {:<20} {}'.format(catalog.PAST_BY_ID[cid]['name'], ', '.join(
            '#{}{}'.format(n, '' if why == 'asy' else ' ({})'.format(WHY[why])) for n, why in items)))
    counts = {}
    for _, why in rows:
        counts[why] = counts.get(why, 0) + 1
    print('  by kind: ' + ', '.join('{} {}'.format(n, WHY[k]) for k, n in sorted(counts.items())))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    st = sub.add_parser('status', help='list the figures not drawn yet')
    st.add_argument('--level', default='', choices=['', 'AMC 10', 'AMC 12', 'AIME'])
    put = sub.add_parser('set', help='store an SVG as a problem\'s figure')
    put.add_argument('pid')
    put.add_argument('svg_file')
    cp = sub.add_parser('copy', help='give a problem the figure another one already has')
    cp.add_argument('source')
    cp.add_argument('target')
    args = ap.parse_args()

    if args.cmd == 'status':
        status(args.level)
        return
    if args.cmd == 'set':
        with open(args.svg_file) as f:
            svg = f.read()
        problem = args.pid
    else:
        source = official.get(args.source)
        if not source or not official.is_drawn(source['diagram']):
            raise SystemExit('{} has no drawn figure to copy.'.format(args.source))
        svg, problem = source['diagram'], args.target
    error = official.set_figure(problem, svg)
    if error:
        raise SystemExit(error)
    print('Stored the figure for {}.'.format(problem))


if __name__ == '__main__':
    main()
