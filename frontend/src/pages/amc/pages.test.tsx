/**
 * Every AMC page renders from what the API really sends.
 *
 * The fixtures in src/test/fixtures/amc are responses captured from the
 * backend for an account seeded with scripts/seed_amc_history.py (trimmed to
 * keep them small), so a page that reads a field the server no longer sends,
 * or crashes on a shape it really gets, fails here rather than in the browser.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
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
import Problems from './Problems';
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

  it('Analytics', async () => {
    show('/analytics', '/analytics', <Analytics />);
    await waitFor(() => expect(amc.analytics).toHaveBeenCalled());
    await settled(/AMC 10/);
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
    expect(amc.problem).toHaveBeenCalledWith('step-10-01');
  });

  it('Topics', async () => {
    show('/topics', '/topics', <Topics />);
    await settled(topics.categories[0]!.topics[0]!.name);
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
