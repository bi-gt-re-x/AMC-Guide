/**
 * A timed sitting is kept on the account, not in the browser: it resumes from
 * what the server holds, every answer and flag is saved as it is made, and
 * handing in or discarding ends it on the server too. Leaving (the Leave
 * button or a link elsewhere) asks first, says the sitting is saved, and keeps
 * it. A sitting an older build left in localStorage is carried over once and
 * then removed.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NoticesProvider } from '@/components';
import TakeMock from './TakeMock';
import { amc, type ContestDetail, type SittingState } from '@/services/amc';

const MOCK = {
  id: 'step-mock-10', kind: 'mock', name: 'Step Mock AMC 10', level: 'AMC 10', minutes: 75, count: 2,
  max: 150, scoring: '', family: 'step', set: 0, blurb: '',
};

function problem(number: number, statement: string) {
  return {
    number, id: `step-10-0${number}`, level: 'AMC 10', topic: 'word-problems', topic_name: 'Word problems',
    category: 'algebra', category_name: 'Algebra', also: [], technique: 't', technique_name: 'T',
    difficulty: 1, rating: 2, statement, choices: ['$1$', '$2$', '$3$', '$4$', '$5$'], format: 'choice', sources: [],
    official: false, has_solution: true, diagram: '', aops_url: null, status: 'new', progress: 'new',
  };
}

function detail(sitting: SittingState | null = null): ContestDetail {
  return {
    contest: MOCK, history: [], can_import: false, sitting,
    problems: [problem(1, 'Andy rides north.'), problem(2, 'A box of nuts.')],
  } as unknown as ContestDetail;
}

function show() {
  render(
    <NoticesProvider>
      <MemoryRouter initialEntries={['/mock-contests/step-mock-10/take']}>
        <Link to="/mock-contests">Sidebar link</Link>
        <Routes>
          <Route path="/mock-contests/:contestId/take" element={<TakeMock />} />
          <Route path="/mocks/:id" element={<p>Result page</p>} />
          <Route path="/mock-contests" element={<p>Mock list</p>} />
        </Routes>
      </MemoryRouter>
    </NoticesProvider>,
  );
}

let save: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  save = vi.spyOn(amc, 'saveSitting').mockImplementation(async (_id, body) => ({
    success: true, sitting: { ...body, started_at: '', updated_at: '' },
  }));
});

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe('TakeMock sitting storage', () => {
  it('shows the cover page when the account has no sitting, and saves one on Begin', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail() });
    show();
    fireEvent.click(await screen.findByRole('button', { name: 'Begin' }));
    expect(await screen.findByText('Andy rides north.')).toBeInTheDocument();
    await waitFor(() => expect(save).toHaveBeenCalledWith('step-mock-10', { used: 0, answers: {}, flags: [] }));
  });

  it('resumes the sitting the account holds, answers and flags included', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({
      success: true, ...detail({ used: 600, answers: { 1: 'B' }, flags: [2] }),
    });
    show();
    expect(await screen.findByText('1/2 answered')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Begin' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Problem 1, answer B' })).toHaveAttribute('aria-pressed', 'true');
    // 75 minutes less the 10 already used.
    expect(screen.getByText('1:05:00')).toBeInTheDocument();
  });

  it('saves an answer to the account the moment it is filled in', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: {}, flags: [] }) });
    show();
    fireEvent.click(await screen.findByRole('button', { name: 'Problem 2, answer D' }));
    await waitFor(() => expect(save).toHaveBeenLastCalledWith('step-mock-10',
      expect.objectContaining({ answers: { 2: 'D' }, flags: [] })));
    fireEvent.click(screen.getByRole('button', { name: 'Flag for later' }));
    await waitFor(() => expect(save).toHaveBeenLastCalledWith('step-mock-10',
      expect.objectContaining({ flags: [2] })));
    expect(localStorage.length).toBe(0);
  });

  it('carries a sitting left in localStorage over to the account once', async () => {
    localStorage.setItem('amc-mock:step-mock-10', JSON.stringify({ used: 30, answers: { 2: 'E' }, flags: [] }));
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail() });
    show();
    expect(await screen.findByText('1/2 answered')).toBeInTheDocument();
    await waitFor(() => expect(save).toHaveBeenCalledWith('step-mock-10',
      expect.objectContaining({ used: 30, answers: { 2: 'E' } })));
    expect(localStorage.getItem('amc-mock:step-mock-10')).toBeNull();
  });

  it('prefers the account’s sitting over a stale one in this browser', async () => {
    localStorage.setItem('amc-mock:step-mock-10', JSON.stringify({ used: 5, answers: { 1: 'A' }, flags: [] }));
    vi.spyOn(amc, 'contest').mockResolvedValue({
      success: true, ...detail({ used: 60, answers: { 1: 'C' }, flags: [] }),
    });
    show();
    expect(await screen.findByRole('button', { name: 'Problem 1, answer C' })).toHaveAttribute('aria-pressed', 'true');
    expect(localStorage.getItem('amc-mock:step-mock-10')).toBeNull();
  });

  it('hands the paper in and goes to the result', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: { 1: 'A' }, flags: [] }) });
    const submit = vi.spyOn(amc, 'submit').mockResolvedValue({ success: true, id: 'm1' });
    show();
    fireEvent.click((await screen.findAllByRole('button', { name: 'Hand in' }))[0]!);
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Hand in' }));
    expect(await screen.findByText('Result page')).toBeInTheDocument();
    expect(submit).toHaveBeenCalledWith('step-mock-10', { 1: 'A' }, 0);
  });

  it('discards the sitting on the server only through Discard', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: {}, flags: [] }) });
    const discard = vi.spyOn(amc, 'discardSitting').mockResolvedValue({ success: true });
    show();
    fireEvent.click(await screen.findByRole('button', { name: 'Discard' }));
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Discard' }));
    expect(await screen.findByText('Mock list')).toBeInTheDocument();
    expect(discard).toHaveBeenCalledWith('step-mock-10');
  });

  it('asks before Leave, says the sitting is saved, and keeps it', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: { 1: 'A' }, flags: [] }) });
    const discard = vi.spyOn(amc, 'discardSitting');
    show();
    fireEvent.click(await screen.findByRole('button', { name: 'Leave' }));
    const dialog = await screen.findByRole('alertdialog');
    expect(dialog).toHaveTextContent(/saved to your account/);
    save.mockClear();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save and leave' }));
    expect(await screen.findByText('Mock list')).toBeInTheDocument();
    expect(save).toHaveBeenCalledWith('step-mock-10', expect.objectContaining({ answers: { 1: 'A' } }));
    expect(discard).not.toHaveBeenCalled();
  });

  it('asks before following a link elsewhere, and staying keeps the paper open', async () => {
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: {}, flags: [] }) });
    show();
    expect(await screen.findByText('Andy rides north.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: 'Sidebar link' }));
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Keep working' }));
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument());
    expect(screen.getByText('Andy rides north.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: 'Sidebar link' }));
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Save and leave' }));
    expect(await screen.findByText('Mock list')).toBeInTheDocument();
  });

  it('says so when a save does not reach the account', async () => {
    save.mockResolvedValue({ success: false, message: 'Signed out.' });
    vi.spyOn(amc, 'contest').mockResolvedValue({ success: true, ...detail({ used: 0, answers: {}, flags: [] }) });
    show();
    fireEvent.click(await screen.findByRole('button', { name: 'Problem 1, answer A' }));
    expect(await screen.findByText(/Not saved to your account yet/)).toBeInTheDocument();
  });
});
