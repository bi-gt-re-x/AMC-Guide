/**
 * The dashboard's Recent performance card says a little, plainly: two numbers
 * for the last 7 days, one sentence against the 7 before, the chart with its
 * parts named for what they are (right, missed), and only the latest score.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import type { RecentPerformance } from '@/services/amc';
import { RecentPerformanceCard } from './Performance';

const week = (answered: number, correct: number) => ({
  answered, correct, accuracy: answered ? correct / answered : null, revealed: 0, minutes: 30,
  avg_seconds: 120, days: 5, hardest: null,
});
const mock = (id: string, name: string, score: number) => ({
  id, contest_id: id, name, level: 'AMC 10' as const, kind: 'mock' as const, score, max: 150,
  at: '2026-11-19T19:15:00', adjusted: score, top: null, floor: 100, vs_floor: score - 100, award: '',
});

const data: RecentPerformance = {
  this_week: week(91, 75),
  last_week: week(41, 23),
  days: Array.from({ length: 14 }, (_, i) => ({ date: `2026-11-${String(13 + i).padStart(2, '0')}`, answered: i, correct: Math.floor(i / 2) })),
  mocks: [mock('2026-amc-10b', '2026 AMC 10B', 88.5), mock('2025-amc-10a', '2025 AMC 10A', 99)],
  notes: [{ tone: 'up', text: 'Accuracy up 26 points from last week.' }],
  summary: { tone: 'up', text: 'More problems than the 7 days before, and a higher share right (41 answered, 56% right then).' },
  latest: { ...mock('2026-amc-10b', '2026 AMC 10B', 88.5), change: -6.5,
            change_text: '6.5 below your 2025 AMC 10A before it, allowing for how hard each paper was.' },
};

describe('Recent performance', () => {
  it('shows two numbers, one sentence, the chart and the latest score', () => {
    render(<MemoryRouter><RecentPerformanceCard data={data} /></MemoryRouter>);
    expect(screen.getByText('Last 7 days')).toBeInTheDocument();
    expect(screen.getByText('91')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText(/More problems than the 7 days before/)).toBeInTheDocument();
    // The light part of a bar is the misses, and says so.
    expect(screen.getByText('Missed')).toBeInTheDocument();
    expect(screen.getByRole('listitem', { name: 'Nov 26 · 6 right, 7 missed' })).toBeInTheDocument();
    expect(screen.getByText('Today')).toBeInTheDocument();
    // Only the latest score, with its change allowing for the paper.
    expect(screen.getByText('2026 AMC 10B')).toBeInTheDocument();
    expect(screen.queryByText('2025 AMC 10A')).not.toBeInTheDocument();
    expect(screen.getByText(/6\.5 below your 2025 AMC 10A/)).toHaveClass('is-down');
    // No table of weekly figures, and no list of notes repeating it.
    expect(screen.queryByText('Time per problem')).not.toBeInTheDocument();
    expect(screen.queryByText('Days active')).not.toBeInTheDocument();
    expect(screen.queryByText(/Accuracy up 26 points/)).not.toBeInTheDocument();
  });
});
