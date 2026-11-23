"""backend/amc/results.py: every official paper's real results, and a score read
against them, so standings, best scores and improvement follow how hard each
paper was rather than the raw number."""
from backend.amc import catalog, insights, results


def test_the_figures_cover_the_catalogue_and_hang_together():
    assert set(results.RESULTS) <= set(catalog.PAST_BY_ID)
    known = [c['id'] for c in catalog.PAST if c['id'] in results.RESULTS]
    assert len(known) >= len(catalog.PAST) - 8            # a few old AIMEs the page gives nothing for
    for cid, r in results.RESULTS.items():
        level = catalog.PAST_BY_ID[cid]['level']
        top = 15 if level == 'AIME' else 150
        for key in ('mean', 'median', 'floor', 'top25', 'top10', 'hr', 'top2_5', 'dhr', 'top5', 'top1'):
            if r.get(key) is not None:
                assert 0 < r[key] <= top, (cid, key)
        if r.get('mean') is not None and r.get('floor') is not None:
            assert r['floor'] > r['mean'], cid
        if r.get('hr') is not None and r.get('dhr') is not None:
            assert r['dhr'] >= r['hr'], cid
    # Since 2026 the floor is fixed, whatever the paper.
    assert results.floor('2026-amc-10a') == 100 and results.floor('2026-amc-12b') == 85


def test_the_same_result_reads_the_same_on_papers_of_different_difficulty():
    # Both are exactly that year's AIME floor: an easier paper's 105, a harder one's 99.
    assert results.adjusted('2025-amc-10a', 105) == results.adjusted('2025-amc-10b', 99) == 100
    # The 2024 AMC 12A was hard (floor 76.5): its floor is today's 85.
    assert results.adjusted('2024-amc-12a', 76.5) == 85
    # Higher scores stay higher, and the scale stays in bounds.
    assert results.adjusted('2025-amc-10a', 120) > results.adjusted('2025-amc-10a', 105)
    assert 0 <= results.adjusted('2024-amc-12a', 150) <= 150
    # A paper with no figures (a mock set, or an unknown id) keeps its score.
    assert results.adjusted('mock-10-1', 90) == 90


def test_a_standing_places_the_score_among_the_real_field():
    st = results.standing('2025-amc-10b', 103.5)
    assert st['floor'] == 99 and st['vs_floor'] == 4.5 and st['award'] == 'AIME qualifier'
    assert 94 <= st['percentile'] <= 96 and st['top'] in (5, 6)
    dhr = results.standing('2025-amc-10a', 136.5)
    assert dhr['award'] == 'Distinguished Honor Roll' and dhr['top'] == 1
    low = results.standing('2025-amc-10a', 57.13)
    assert low['award'] == '' and low['vs_floor'] < 0 and 48 <= low['percentile'] <= 52
    # Percentiles rise with the score.
    pcts = [results.percentile('2023-amc-12b', s) for s in (30, 60, 90, 120, 145)]
    assert pcts == sorted(pcts)
    aime = results.standing('2025-aime-i', 12)
    assert aime['top'] in (2, 3) and aime['floor'] is None


def test_old_papers_are_read_under_their_own_scoring():
    # Until 2006 a blank was 2.5: 16 right and 8 blank was 116 then (108 here).
    st = results.standing('2005-amc-10a', 108, correct=16, blank=8)
    assert st['scored_as'] == 116 and st['vs_floor'] == -4
    assert results.blank_points('2005-amc-10a') == 2.5 and results.blank_points('2007-amc-10a') == 1.5
    # A logged score has no counts, so it is read as given.
    assert results.of_row({'contest_id': '2005-amc-10a', 'kind': 'logged', 'score': 120,
                           'correct': 0, 'blank': 0})['vs_floor'] == 0


def test_the_score_chart_and_weekly_best_use_the_adjusted_score():
    row = {'id': 'x', 'contest_id': '2025-amc-10a', 'kind': 'mock', 'score': 105, 'correct': 17, 'blank': 2,
           'at': '2026-11-10T18:00:00'}
    point = insights._mock_point(row)
    assert point['score'] == 105 and point['adjusted'] == 100 and point['vs_floor'] == 0
    mock_set = insights._mock_point({**row, 'contest_id': 'mock-10-1'})
    assert mock_set['adjusted'] == 105 and mock_set['top'] is None


def test_the_api_carries_the_readings(client):
    log = client.post('/api/amc/contests/2025-amc-10b/log', json={'score': 103.5}).json()
    assert log['success']
    listing = client.get('/api/amc/contests').json()
    row = next(h for h in listing['history'] if h['contest_id'] == '2025-amc-10b')
    assert row['standing']['vs_floor'] == 4.5 and row['standing']['award'] == 'AIME qualifier'
    page = client.get('/api/amc/contests/2025-amc-10b').json()
    assert page['results']['floor'] == 99 and page['results']['students'] == 25195
    assert page['history'][0]['standing']['top'] in (5, 6)
    analytics = client.get('/api/amc/analytics').json()
    point = analytics['performance']['mocks'][0]
    assert point['adjusted'] == results.adjusted('2025-amc-10b', 103.5)
