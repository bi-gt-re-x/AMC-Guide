/**
 * The placement check (components/Amc/Placement.tsx): offered in one line,
 * then a problem at a time with "Not sure" and "Stop here", then where they are.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Placement } from './Placement';
import { amc } from '@/services/amc';

/* eslint-disable @typescript-eslint/no-explicit-any */
const problem = (n: number) => ({
  id: `p${n}`, statement: `Problem number ${n}?`, choices: ['$1$', '$2$', '$3$', '$4$', '$5$'], format: 'choice',
  topic_name: 'Linear Equations', category: 'algebra', category_name: 'Algebra',
});
const at = (n: number) => ({ level: 'AMC 10', answered: n, total: 12, problem: problem(n + 1), done: false, result: null });
const RESULT = {
  theta: 5.2, se: 0.7, level: 5, right: 8, answered: 12, blank: 2, reach: 16, contest: 'AMC 10',
  subjects: [{ id: 'algebra', name: 'Algebra', right: 3, total: 3 }, { id: 'geometry', name: 'Geometry', right: 1, total: 3 }],
  summary: 'You’re at about 5 on the 1–12 scale: you’d get most problems up to about #16 of an AMC 10.',
  strongest: 'Algebra', weakest: 'Geometry',
};

beforeEach(() => {
  vi.spyOn(amc, 'placement').mockResolvedValue({ success: true, placement: null, offer: true, size: 12 } as any);
});
afterEach(() => vi.restoreAllMocks());

describe('the placement check', () => {
  it('is offered in a line, then deals a problem at a time, and says where they are', async () => {
    vi.spyOn(amc, 'startPlacement').mockResolvedValue({ success: true, placement: at(0) } as any);
    const answer = vi.spyOn(amc, 'answerPlacement').mockImplementation((id: string) =>
      Promise.resolve({ success: true, placement: id === 'p2'
        ? { ...at(12), problem: null, done: true, result: RESULT } : at(Number(id.slice(1))) } as any));
    const done = vi.fn();
    render(<Placement level="AMC 10" onDone={done} />);
    expect(screen.getByText('Find your level')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Start' }));
    expect(await screen.findByText('Problem number 1?')).toBeInTheDocument();
    expect(screen.getByText('1 of 12')).toBeInTheDocument();
    // Next waits for an answer; "Not sure" sends a blank.
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
    fireEvent.click(document.querySelectorAll('.am-choice')[2]!);
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    await waitFor(() => expect(answer).toHaveBeenCalledWith('p1', 'C', expect.any(Number)));
    expect(await screen.findByText('Problem number 2?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Not sure' }));
    await waitFor(() => expect(answer).toHaveBeenLastCalledWith('p2', '', expect.any(Number)));
    expect(await screen.findByText(/You’re at about 5 on the 1–12 scale/)).toBeInTheDocument();
    expect(screen.getByLabelText('3 of 3 right')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Go to my dashboard' }));
    expect(done).toHaveBeenCalledWith(RESULT);
  });

  it('picks up a check begun before, and can be stopped with what was answered', async () => {
    vi.spyOn(amc, 'placement').mockResolvedValue({ success: true, placement: at(5), offer: true, size: 12 } as any);
    const stop = vi.spyOn(amc, 'stopPlacement').mockResolvedValue({
      success: true, placement: { ...at(5), problem: null, done: true, result: { ...RESULT, answered: 5 } } } as any);
    render(<Placement level="AMC 10" onDone={() => undefined} />);
    expect(await screen.findByText('6 of 12')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Stop here and use these answers' }));
    await waitFor(() => expect(stop).toHaveBeenCalled());
    expect(await screen.findByText('Your starting level')).toBeInTheDocument();
  });

  it('skipping it goes straight on', async () => {
    vi.spyOn(amc, 'stopPlacement').mockResolvedValue({
      success: true, placement: { level: 'AMC 10', answered: 0, total: 12, problem: null, done: true, result: null } } as any);
    const done = vi.fn();
    render(<Placement level="AMC 10" onDone={done} />);
    fireEvent.click(screen.getByRole('button', { name: 'Skip for now' }));
    await waitFor(() => expect(done).toHaveBeenCalledWith(null));
  });
});
