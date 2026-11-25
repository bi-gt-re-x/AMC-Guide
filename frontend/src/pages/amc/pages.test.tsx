/**
 * Every AMC page renders from what the API really sends.
 *
 * The fixtures in src/test/fixtures/amc are responses captured from the
 * backend for an account seeded with scripts/seed_amc_history.py (trimmed to
 * keep them small), so a page that reads a field the server no longer sends,
 * or crashes on a shape it really gets, fails here rather than in the browser.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NoticesProvider } from '@/components';
import { AuthContext, type AuthValue } from '@/context/contexts';
import { amc } from '@/services/amc';
import analytics from '@/test/fixtures/amc/analytics.json';
import contest from '@/test/fixtures/amc/contest.json';
import contests from '@/test/fixtures/amc/contests.json';
import dashboard from '@/test/fixtures/amc/dashboard.json';
import insights from '@/test/fixtures/amc/insights.json';
import mock from '@/test/fixtures/amc/mock.json';
import plan from '@/test/fixtures/amc/plan.json';
import problem from '@/test/fixtures/amc/problem.json';
import problems from '@/test/fixtures/amc/problems.json';
import review from '@/test/fixtures/amc/review.json';
import search from '@/test/fixtures/amc/search.json';
import strategies from '@/test/fixtures/amc/strategies.json';
import topic from '@/test/fixtures/amc/topic.json';
import topics from '@/test/fixtures/amc/topics.json';
import weak from '@/test/fixtures/amc/weak.json';
import Analytics from './Analytics';
import Contests from './Contests';
import Dashboard from './Dashboard';
import MockContests from './MockContests';
import MockResult from './MockResult';
import Problem from './Problem';
import PracticeSet from './PracticeSet';
import Problems from './Problems';
import { writePracticeSet } from './practiceSetStore';
import Review from './Review';
import Search from './Search';
import StudyPlan from './StudyPlan';
import Topic from './Topic';
import Topics from './Topics';

// The dashboard's greeting reads the nametag, which needs the settings and
// stats providers; the page's own data is what is under test here.
vi.mock('@/hooks/useNametag', () => ({
  useNametag: () => ({ name: 'student', avatar: '', title: null, rank: null, automatic: null, titles: [] }),
}));

/* eslint-disable @typescript-eslint/no-explicit-any */
const reply = (body: unknown) => vi.fn().mockResolvedValue(body as any);

beforeEach(() => {
  const stubs: Partial<Record<keyof typeof amc, unknown>> = {
    dashboard: reply(dashboard),
    analytics: reply(analytics),
    insights: reply(insights),
    review: reply(review),
    weakBank: reply(weak),
    plan: reply(plan),
    problems: reply(problems),
    problem: reply(problem),
    topics: reply(topics),
    topic: reply(topic),
    strategies: reply(strategies),
    contests: reply(contests),
    contest: reply(contest),
    mock: reply(mock),
    search: reply(search),
    aiStatus: reply({ success: true, available: false, provider: '', model: '', used: 0, limit: 0 }),
  };
  const target = amc as unknown as Record<string, (...args: unknown[]) => unknown>;
  for (const [name, fn] of Object.entries(stubs)) vi.spyOn(target, name).mockImplementation(fn as any);
});

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

const SIGNED_IN = {
  status: 'authenticated', username: 'student', profileComplete: true, emailVerified: true, avatar: '',
} as unknown as AuthValue;

/** The route a test ended up on. */
function WhereAmI() {
  const at = useLocation();
  return <p data-testid="where">{at.pathname + at.search}</p>;
}

function show(path: string, route: string, element: React.ReactElement) {
  render(
    <AuthContext.Provider value={SIGNED_IN}>
      <NoticesProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes><Route path={route} element={element} /></Routes>
        </MemoryRouter>
      </NoticesProvider>
    </AuthContext.Provider>,
  );
}

/** The page settled: something from the fixture is on screen and no error is. */
async function settled(text: string | RegExp) {
  expect((await screen.findAllByText(text, undefined, { timeout: 3000 })).length).toBeGreaterThan(0);
  expect(screen.queryByText(/Could not load/i)).not.toBeInTheDocument();
}

describe('AMC pages render the API as it is', () => {
  it('Dashboard', async () => {
    show('/dashboard', '/dashboard', <Dashboard />);
    await settled(new RegExp(dashboard.weakest[0]!.name));
    expect(amc.dashboard).toHaveBeenCalled();
  });

  it('Review: the error log and the weak-topics set', async () => {
    show('/review', '/review', <Review />);
    await settled(new RegExp(weak.topics[0]!.name));
    expect(amc.review).toHaveBeenCalled();
    expect(amc.weakBank).toHaveBeenCalledWith(false, 0);
  });

  it('Review: a long backlog is started ten at a time', async () => {
    const due = Array.from({ length: 25 }, (_, i) => ({ ...review.due[0]!, id: `p-${i}` }));
    vi.spyOn(amc, 'review').mockResolvedValue({ ...review, due, success: true } as any);
    render(
      <AuthContext.Provider value={SIGNED_IN}>
        <NoticesProvider>
          <MemoryRouter initialEntries={['/review']}>
            <Routes>
              <Route path="/review" element={<Review />} />
              <Route path="/problems/:problemId" element={<p>opened problem</p>} />
            </Routes>
          </MemoryRouter>
        </NoticesProvider>
      </AuthContext.Provider>,
    );
    fireEvent.click(await screen.findByRole('button', { name: 'Start a review set (10)' }));
    expect(await screen.findByText('opened problem')).toBeInTheDocument();
    expect(JSON.parse(sessionStorage.getItem('amc-review-set') ?? '[]')).toEqual(due.slice(0, 10).map((d) => d.id));
  });

  it('Analytics', async () => {
    show('/analytics', '/analytics', <Analytics />);
    await waitFor(() => expect(amc.analytics).toHaveBeenCalled());
    await settled(/AMC 10/);
  });

  it('Analytics: points lost in mocks lead the Weaknesses card', async () => {
    vi.spyOn(amc, 'analytics').mockResolvedValue({
      ...analytics,
      mock_mistakes: { sittings: 2, lost: 30, topics: [
        { id: 'circles', name: 'Circles', category: 'geometry', wrong: 3, blank: 2, missed: 5, asked: 6, lost: 27,
          per_sitting: 13.5, problems: [] }] },
    } as any);
    show('/analytics', '/analytics', <Analytics />);
    expect(await screen.findByText(/Lost in mocks/)).toBeInTheDocument();
    expect(screen.getByText('−27 pts')).toBeInTheDocument();
    expect(screen.getByText('3 wrong, 2 blank of 6 asked')).toBeInTheDocument();
    expect(document.querySelector('a[href="/practice/circles?mode=timed"]')).not.toBeNull();
  });

  it('Study plan', async () => {
    show('/study-plan', '/study-plan', <StudyPlan />);
    await settled(/AMC 10/);
    expect(amc.plan).toHaveBeenCalled();
  });

  it('Problems list', async () => {
    show('/problems', '/problems', <Problems />);
    await waitFor(() => expect(amc.problems).toHaveBeenCalled());
    await settled(new RegExp(problems.problems[0]!.topic_name));
  });

  it('One problem', async () => {
    show('/problems/step-10-01', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(amc.problem).toHaveBeenCalledWith('step-10-01', {});
  });

  it('One problem, opened from a topic, asks for that topic\'s Previous and Next', async () => {
    show('/problems/step-10-01?topic=circles', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(amc.problem).toHaveBeenCalledWith('step-10-01', { topic: 'circles' });
  });

  it('One problem, opened from a filtered list, asks for that list\'s Previous and Next', async () => {
    show('/problems/step-10-01?list=1&level=AMC+10&topic=circles&rating=3', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(amc.problem).toHaveBeenCalledWith('step-10-01', { list: '1', level: 'AMC 10', topic: 'circles', rating: '3' });
  });

  it('The problems list links each problem with its filters', async () => {
    show('/problems?topic=circles&level=AMC+10', '/problems', <Problems />);
    await settled(new RegExp(problems.problems[0]!.topic_name));
    const link = document.querySelector(`a[href^="/problems/${problems.problems[0]!.id}?"]`);
    expect(link?.getAttribute('href')).toContain('list=1');
    expect(link?.getAttribute('href')).toContain('topic=circles');
    expect(link?.getAttribute('href')).toContain('level=AMC+10');
  });

  it('Topics: a card per topic, no problem pills, and a dropdown to jump', async () => {
    show('/topics', '/topics', <Topics />);
    const first = topics.categories[0]!.topics[0]!;
    await settled(first.name);
    expect(document.querySelector('.am-pills')).toBeNull();
    const card = document.querySelector(`a.am-topic-card[href="/topics/${first.id}"]`);
    expect(card).not.toBeNull();
    expect(card).toHaveTextContent(String(first.problems));
    const menu = document.querySelector('details.am-jump-menu') as HTMLDetailsElement;
    expect(menu.open).toBe(false);
    fireEvent.click(screen.getByText('Jump to a topic'));
    expect(menu.open).toBe(true);
  });

  it('One topic, with its playbook', async () => {
    show('/topics/linear-equations', '/topics/:topicId', <Topic />);
    await settled(topic.topic.playbook[0]!.move);
    expect(amc.topic).toHaveBeenCalledWith('linear-equations');
  });

  it('Mock contests', async () => {
    show('/mock-contests', '/mock-contests', <MockContests />);
    await settled(contests.mocks[0]!.name);
  });

  it('Past contests', async () => {
    show('/contests', '/contests', <Contests />);
    await settled(String(contests.years[0]!.year));
    const first = contests.years[0]!.contests[0]!;
    expect(document.querySelector(`a[href="/contests/${first.id}"]`)).not.toBeNull();
  });

  it('A mock result', async () => {
    show(`/mocks/${mock.result.id}`, '/mocks/:mockId', <MockResult />);
    await settled(new RegExp(mock.contest.name));
    expect(screen.getAllByText(new RegExp(String(mock.result.score))).length).toBeGreaterThan(0);
  });

  it('Search', async () => {
    show('/search?q=triangle', '/search', <Search />);
    await waitFor(() => expect(document.querySelector(`a[href="/topics/${search.topics[0]!.id}"]`)).not.toBeNull());
    expect(amc.search).toHaveBeenCalledWith('triangle', 40);
    expect(screen.queryByText(/Could not load/i)).not.toBeInTheDocument();
  });
});

describe('Reviewing a miss', () => {
  const missed = {
    ...problem,
    attempts: [{ answer: 'B', at: '2026-11-01T17:00:00', correct: false, seconds: 60, source: 'practice' },
               { answer: 'D', at: '2026-11-04T17:00:00', correct: true, seconds: 40, source: 'review' }],
  };

  it("shows neither the old wrong answer nor the key before it is answered", async () => {
    vi.spyOn(amc, 'problem').mockResolvedValue({ ...missed, success: true } as any);
    show('/problems/step-10-01?review=1', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(await screen.findByText('missed')).toBeInTheDocument();
    expect(screen.getByText('right')).toBeInTheDocument();
    expect(screen.queryByText(/B ✗/)).not.toBeInTheDocument();
    expect(screen.queryByText(/D ✓/)).not.toBeInTheDocument();
  });

  it('says where it is in the review set', async () => {
    sessionStorage.setItem('amc-review-set', JSON.stringify(['step-10-00', 'step-10-01', 'step-10-02']));
    vi.spyOn(amc, 'problem').mockResolvedValue({ ...missed, success: true } as any);
    show('/problems/step-10-01?review=1', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(screen.getByText(/Review set, 2 of 3/)).toBeInTheDocument();
    sessionStorage.removeItem('amc-review-set');
  });

  it('keeps the full history when browsing a problem already answered', async () => {
    vi.spyOn(amc, 'problem').mockResolvedValue({ ...missed, success: true } as any);
    show('/problems/step-10-01', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(await screen.findByText(/B ✗/)).toBeInTheDocument();
  });
});


describe('A topic practice set', () => {
  const summary = (n: number) => ({
    ...problems.problems[0]!, id: `step-10-0${n}`, source: `Step drill #${n}`, topic: 'circles', topic_name: 'Circles',
    rating: 4, status: 'new', level_of: 2,
  });
  const payload = (mode: string) => ({
    success: true, topic: { id: 'circles', name: 'Circles', category: 'geometry' }, mode,
    title: mode === 'mixed' ? 'Mixed set' : 'Timed set', instructions: 'Eight problems.',
    seconds: mode === 'timed' ? 180 : null, hide_topic: mode === 'mixed', level: 'AMC 10',
    mix: [{ level: 2, share: 1 }], suggested: 'timed',
    modes: [{ id: 'timed', title: 'Timed set' }, { id: 'mixed', title: 'Mixed set' }],
    problems: Array.from({ length: 8 }, (_, i) => summary(i + 1)),
  });

  it('lists eight, hides the topic on a mixed set, and starts the walk', async () => {
    vi.spyOn(amc, 'topicSet').mockResolvedValue(payload('mixed') as any);
    show('/practice/circles?mode=mixed', '/practice/:topicId', <PracticeSet />);
    await settled('Mixed set');
    expect(screen.getAllByText(/Step drill #/)).toHaveLength(8);
    expect(screen.queryByText('Circles', { selector: '.am-set-main span' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Start set' }));
    expect(JSON.parse(sessionStorage.getItem('amc-practice-set')!).ids).toHaveLength(8);
  });

  it('walks a timed set on the problem page with its clock and position', async () => {
    writePracticeSet({ ids: ['step-10-01', 'step-10-02'], topic: 'circles', mode: 'timed', title: 'Timed set',
                       seconds: 180, hideTopic: false, size: null, deadline: null });
    show('/problems/step-10-01?set=1', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(screen.getByText('← Timed set')).toBeInTheDocument();
    expect(screen.getByText(/1 of 2/)).toBeInTheDocument();
    expect(screen.getByLabelText(/against the set's pace/)).toHaveTextContent('/ 3:00');
    // Stepping on stays inside the set, never on to the rest of the paper.
    expect(screen.getByRole('button', { name: 'Skip →' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Next →' })).not.toBeInTheDocument();
  });

  it('starts a timed set on one clock for the whole set', async () => {
    vi.spyOn(amc, 'topicSet').mockResolvedValue({ ...payload('timed'), total_seconds: 1440, size: 8 } as any);
    show('/practice/circles?mode=timed', '/practice/:topicId', <PracticeSet />);
    await settled('Timed set');
    expect(screen.getByText(/24:00 for the 8 problems/)).toBeInTheDocument();
    const before = Date.now();
    fireEvent.click(screen.getByRole('button', { name: 'Start set' }));
    const { deadline } = JSON.parse(sessionStorage.getItem('amc-practice-set')!);
    expect(deadline).toBeGreaterThanOrEqual(before + 1440 * 1000);
    expect(deadline).toBeLessThan(before + 1440 * 1000 + 5000);
  });

  it('counts the set down on the problem page', async () => {
    writePracticeSet({ ids: ['step-10-01', 'step-10-02'], topic: 'circles', mode: 'timed', title: 'Timed set',
                       seconds: 180, hideTopic: false, size: null, deadline: Date.now() + 10 * 60 * 1000 });
    show('/problems/step-10-01?set=1', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(screen.getAllByRole('timer')[0]).toHaveTextContent(/^(10:00|9:59) left$/);
    expect(screen.getByLabelText(/Time left for the set, and time on this problem/)).toHaveTextContent('left for the set');
  });

  it('ends the set when its clock runs out', async () => {
    writePracticeSet({ ids: ['step-10-01'], topic: 'circles', mode: 'timed', title: 'Timed set',
                       seconds: 180, hideTopic: false, size: 5, deadline: Date.now() - 1000 });
    render(
      <AuthContext.Provider value={SIGNED_IN}>
        <NoticesProvider>
          <MemoryRouter initialEntries={['/problems/step-10-01?set=1']}>
            <Routes>
              <Route path="/problems/:problemId" element={<Problem />} />
              <Route path="/practice/:topicId" element={<WhereAmI />} />
            </Routes>
          </MemoryRouter>
        </NoticesProvider>
      </AuthContext.Provider>,
    );
    expect(await screen.findByTestId('where')).toHaveTextContent('/practice/circles?mode=timed&n=5&done=1&timeup=1');
  });

  it('hides the topic on a mixed set until it is answered', async () => {
    writePracticeSet({ ids: ['step-10-01'], topic: 'circles', mode: 'mixed', title: 'Mixed set',
                       seconds: null, hideTopic: true, size: null, deadline: null });
    show('/problems/step-10-01?set=1', '/problems/:problemId', <Problem />);
    await settled(/What is the value of/);
    expect(screen.queryByRole('link', { name: problem.problem.topic_name })).not.toBeInTheDocument();
  });
});
