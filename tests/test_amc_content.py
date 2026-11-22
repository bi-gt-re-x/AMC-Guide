"""The content every AMC page is built from: each topic's playbook
(backend/amc/ideas.py) and the one lookup every problem goes through
(backend/amc/problems.py)."""
import re

import pytest

from backend.amc import bank, catalog, ideas
from backend.amc import problems as pb


# -- Playbooks -----------------------------------------------------------------
def test_every_topic_has_a_playbook_and_every_playbook_a_topic():
    assert set(ideas.PLAYBOOK) == set(catalog.TOPIC_BY_ID)


@pytest.mark.parametrize('topic_id', sorted(ideas.PLAYBOOK))
def test_a_playbook_is_three_or_four_whole_moves_and_a_trap(topic_id):
    moves, trap = ideas.PLAYBOOK[topic_id]
    assert 3 <= len(moves) <= 4
    for move in moves:
        assert set(move) == {'move', 'when', 'example'}
        assert all(isinstance(v, str) and v.strip() for v in move.values()), move
    assert isinstance(trap, str) and trap.strip()
    # Moves are distinct: a playbook that repeats itself is a copy-paste slip.
    assert len({m['move'] for m in moves}) == len(moves)


@pytest.mark.parametrize('topic_id', sorted(ideas.PLAYBOOK))
def test_playbook_maths_is_balanced(topic_id):
    """Every $...$ closes, so MathText never renders half a sentence as maths."""
    moves, trap = ideas.PLAYBOOK[topic_id]
    for text in [trap] + [v for m in moves for v in m.values()]:
        assert len(re.findall(r'(?<!\\)\$', text)) % 2 == 0, text


def test_the_catalog_carries_the_playbook_onto_each_topic():
    for t in catalog.TOPICS:
        moves, trap = ideas.PLAYBOOK[t['id']]
        assert t['playbook'] == moves and t['trap'] == trap
        assert t['ideas'] == [m['move'] for m in moves]


# -- Problem lookup --------------------------------------------------------------
def test_every_bank_problem_is_found_by_id():
    for p in bank.PROBLEMS:
        assert pb.get(p['id']) is p


def test_problem_ids_are_unique_across_every_source():
    ids = [p['id'] for p in pb.all_problems()]
    assert len(ids) == len(set(ids))
    assert set(pb.by_id()) == set(ids)


def test_an_unknown_id_is_none():
    assert pb.get('no-such-problem') is None
    assert pb.get('') is None


def test_every_problem_points_at_a_real_topic():
    for p in pb.all_problems():
        assert p['topic'] in catalog.TOPIC_BY_ID, p['id']
        assert all(t in catalog.TOPIC_BY_ID for t in p.get('also') or []), p['id']
