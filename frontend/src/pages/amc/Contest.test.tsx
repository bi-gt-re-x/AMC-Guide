/**
 * An official paper's page before its first sitting: the problems are locked,
 * and unlock only after the reader confirms that reading them spoils a fresh
 * sitting. A paper already sat opens straight away.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Contest from './Contest';
import { amc, type ContestDetail } from '@/services/amc';

const PAPER = {
  id: '2025-amc-10a', kind: 'past', imported: true, name: '2025 AMC 10A', year: 2025, level: 'AMC 10', paper: 'A',
  season: '', count: 2, minutes: 75, max: 150, scoring: '', problems_url: '#', answers_url: '#',
};

function problem(number: number, statement: string) {
  return {
    number, id: `2025-amc-10a-${number}`, level: 'AMC 10', topic: 'word-problems', topic_name: 'Word problems',
    category: 'algebra', category_name: 'Algebra', also: [], technique: 'official', technique_name: 'Official',
    difficulty: 1, rating: 1, statement, choices: ['$1$', '$2$', '$3$', '$4$', '$5$'], format: 'choice', sources: [],
    official: true, has_solution: true, diagram: '', aops_url: null, status: 'new', progress: 'new',
  };
}

function detail(history: unknown[]): ContestDetail {
  return {
    contest: PAPER, history, can_import: false,
    problems: [problem(1, 'Andy rides north.'), problem(2, 'A box of nuts.')],
  } as unknown as ContestDetail;
}

function show() {
  render(
    <MemoryRouter initialEntries={['/contests/2025-amc-10a']}>
      <Routes><Route path="/contests/:contestId" element={<Contest />} /></Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe('Contest page lock', () => {
  it('keeps an unsat paper locked until the reader confirms', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail([]) });
    show();
    expect(await screen.findByText('Locked until you sit it')).toBeInTheDocument();
    expect(screen.queryByText('Andy rides north.')).not.toBeInTheDocument();
    expect(screen.queryByText('Practice one by one')).not.toBeInTheDocument();
    expect(screen.queryByText('Answer key')).not.toBeInTheDocument();

    const unlock = screen.getByRole('button', { name: 'Unlock the problems' });
    expect(unlock).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(unlock);

    expect(screen.getByText('Andy rides north.')).toBeInTheDocument();
    expect(localStorage.getItem('amc-unlocked:2025-amc-10a')).toBe('1');
    fireEvent.click(screen.getByRole('button', { name: 'Lock them again' }));
    expect(screen.getByText('Locked until you sit it')).toBeInTheDocument();
  });

  it('opens a paper that has been sat', async () => {
    const sitting = { id: 'm1', contest_id: '2025-amc-10a', name: '2025 AMC 10A', level: 'AMC 10', kind: 'mock',
                      score: 90, correct: 15, wrong: 0, blank: 0, seconds: 4000, at: '2026-11-14T10:00:00', note: '' };
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail([sitting]) });
    show();
    expect(await screen.findByText('Andy rides north.')).toBeInTheDocument();
    expect(screen.queryByText('Locked until you sit it')).not.toBeInTheDocument();
    expect(screen.getByText('Answer key')).toBeInTheDocument();
  });
});
