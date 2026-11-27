/**
 * Onboarding in three short steps: each moves on once it has what it needs,
 * the subject ratings are optional, and the plan is saved with them.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AmcProfile } from './AmcProfile';
import { amc } from '@/services/amc';
import * as authService from '@/services/auth';

beforeEach(() => {
  // No check begun yet; declining one is accepted.
  vi.spyOn(amc, 'placement').mockResolvedValue({ success: true, placement: null, offer: true, size: 12 } as any);
  vi.spyOn(amc, 'stopPlacement').mockResolvedValue({ success: true, placement: {
    level: 'AMC 10', answered: 0, total: 12, problem: null, done: true, result: null } } as any);
});
afterEach(() => vi.restoreAllMocks());

describe('AmcProfile', () => {
  it('walks three steps and saves the plan with the subject ratings', async () => {
    /* eslint-disable @typescript-eslint/no-explicit-any */
    vi.spyOn(amc, 'plan').mockResolvedValue({
      success: true, plan: null, ai: { available: false, label: '' },
      defaults: { dates: { 'AMC 10': '2027-11-05', 'AMC 12': '2027-11-05', AIME: '2027-02-05' },
                  goals: { 'AMC 10': 100, 'AMC 12': 85, AIME: 7 } },
    } as any);
    const saved = vi.spyOn(amc, 'savePlan').mockResolvedValue({ success: true, ai: { available: false } } as any);
    vi.spyOn(authService, 'completeProfile').mockResolvedValue({ success: true } as any);
    const done = vi.fn();
    render(<AmcProfile onDone={done} say={() => undefined} />);

    const next = screen.getByRole('button', { name: 'Next' });
    expect(next).toBeDisabled();
    expect(screen.getByText('1 of 3 · Your contest')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('radio', { name: /^AMC 10/ }));
    fireEvent.click(next);

    expect(screen.getByText('2 of 3 · Where you are')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('radio', { name: /Score 120\+/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('3 of 3 · Your time')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('radio', { name: '3–5 h' }));
    const geometry = screen.getByRole('radiogroup', { name: 'Geometry' });
    fireEvent.click(geometry.querySelector('button')!);              // Weak
    await waitFor(() => expect(screen.getByRole('button', { name: 'Make my plan' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Make my plan' }));

    // The plan is saved, and the placement check is offered as the last, optional step.
    expect(await screen.findByText('Find your level')).toBeInTheDocument();
    const body = saved.mock.calls[0]![0] as any;
    expect(body.goal_score).toBe(120);
    expect(body.details.subjects).toEqual({ geometry: 'weak' });
    expect(done).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Skip for now' }));
    await waitFor(() => expect(done).toHaveBeenCalled());
  });

  it('skipping the questions skips the check too', async () => {
    vi.spyOn(amc, 'plan').mockResolvedValue({ success: true, plan: null, ai: { available: false, label: '' },
      defaults: { dates: {}, goals: {} } } as any);
    vi.spyOn(authService, 'completeProfile').mockResolvedValue({ success: true } as any);
    const done = vi.fn();
    render(<AmcProfile onDone={done} say={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: 'Skip for now' }));
    await waitFor(() => expect(done).toHaveBeenCalled());
    expect(screen.queryByText('Find your level')).not.toBeInTheDocument();
  });
});
