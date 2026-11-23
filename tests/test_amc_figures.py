"""Official problems' figures (backend/amc/official.py, scripts/figures.py): a
drawing survives re-importing its paper, unsafe SVG is refused, and the list
of figures not drawn yet sees Asymptote, missing pictures and figures the text
mentions."""
from backend.amc import official

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>'


def _paper(diagram_3=''):
    problems = [{'number': n, 'statement': 'Problem {} asks for something.'.format(n),
                 'choices': ['$1$', '$2$', '$3$', '$4$', '$5$'], 'diagram': ''} for n in range(1, 26)]
    problems[2]['diagram'] = diagram_3
    problems[4]['statement'] = 'In the figure below, find the area.'
    problems[5]['diagram'] = 'image'
    return problems


def test_a_drawing_survives_a_reimport(client):
    official.save_contest('2015-amc-10a', _paper('draw(unitcircle);'), ['A'] * 25, 'temu')
    assert official.set_figure('2015-amc-10a-3', SVG) == ''
    assert official.get('2015-amc-10a-3')['diagram'] == SVG
    # Pasting the paper again brings the Asymptote back; the drawing is kept.
    official.save_contest('2015-amc-10a', _paper('draw(unitcircle);'), ['A'] * 25, 'temu')
    assert official.get('2015-amc-10a-3')['diagram'] == SVG
    # A new drawing in an import wins over the old one.
    newer = SVG.replace('r="4"', 'r="3"')
    official.save_contest('2015-amc-10a', _paper(newer), ['A'] * 25, 'temu')
    assert official.get('2015-amc-10a-3')['diagram'] == newer


def test_unsafe_or_wrong_figures_are_refused(client):
    official.save_contest('2015-amc-10a', _paper(), ['A'] * 25, 'temu')
    assert 'one <svg>' in official.set_figure('2015-amc-10a-3', 'draw(unitcircle);')
    for bad in ('<svg><script>alert(1)</script></svg>', '<svg onload="x()"></svg>',
                '<svg><image href="http://x/y.png"/></svg>', '<svg><a href="javascript:x"></a></svg>'):
        assert official.set_figure('2015-amc-10a-3', bad), bad
    assert 'No such' in official.set_figure('not-a-problem', SVG)
    assert official.get('2015-amc-10a-3')['diagram'] == ''


def test_the_undrawn_list(client):
    official.save_contest('2015-amc-10a', _paper('draw(unitcircle);'), ['A'] * 25, 'temu')
    found = {p['id']: why for p, why in official.undrawn() if p['contest'] == '2015-amc-10a'}
    assert found == {'2015-amc-10a-3': 'asy', '2015-amc-10a-5': 'mentioned', '2015-amc-10a-6': 'image'}
    official.set_figure('2015-amc-10a-3', SVG)
    assert '2015-amc-10a-3' not in {p['id'] for p, _ in official.undrawn()}
