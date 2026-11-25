/**
 * Analytics, under Prep: one page, read top to bottom.
 *
 *   Mock contest scores  every timed mock and logged score over time, against
 *                        the goal and the AIME cutoff.
 *   Performance          week by week: how often you solve, in which
 *                        categories, how accurately, how hard the problems
 *                        were, and your best test score that week.
 *   By difficulty        first-try accuracy at each point of the 1-12 rating,
 *                        beside the list of topics costing you the most.
 *   Where the points are topics by the points studying them would add, and the
 *                        five kinds of weakness with the training each wants
 *                        (backend/amc/planning.py).
 *   AI coach             the model (Grok when XAI_API_KEY is set) reads all of
 *                        it and says what to do this week.
 *
 * The numbers come from backend/amc/insights.py on each visit; the coach from
 * /api/amc/insights (backend/api/amc_ai.py), loaded on its own so a slow model
 * status never holds up the charts.
 */
import { Link } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { DifficultyChart, PerformanceChart, ScoreChart } from '@/components/Amc/AnalyticsCharts';
import { Coach } from '@/components/Amc/Insights';
import { PrioritiesCard, Takeaways, WeaknessLines } from '@/components/Amc/Study';
import { CategoryDot, Empty, Meter, PageHeader, ratingText } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, pct, type Analytics as AnalyticsData, type CategoryId } from '@/services/amc';
import '@/styles/amc.css';

function tone(accuracy: number | null): 'good' | 'warn' | 'bad' {
  if (accuracy == null || accuracy < 0.5) return 'bad';
  return accuracy >= 0.75 ? 'good' : 'warn';
}

function Weaknesses({ data }: { data: AnalyticsData }) {
  const p = data.performance;
  // The API sends tried topics weakest first; a topic with no misses is not a weakness.
  const weak = p.topics.filter((t) => t.accuracy != null && t.accuracy < 1).slice(0, 8);
  const r = p.recovery;
  const lost = data.mock_mistakes;
  return (
    <section className="am-card am-an-weak">
      <div className="am-card-head"><h2>Weaknesses</h2><Link to="/review">Review</Link></div>
      <MockLosses lost={lost} />
      <h3 className="am-an-weak-sub">In practice</h3>
      {weak.length ? (
        <ol className="am-an-weak-list">
          {weak.map((t, i) => {
            const right = Math.round((t.accuracy ?? 0) * t.attempted);
            return (
              <li key={t.id}>
                <span className="am-an-weak-rank">{i + 1}</span>
                <div className="am-an-weak-main">
                  <div className="am-an-weak-head">
                    <Link className="am-link am-an-weak-name" to={`/topics/${t.id}`}>
                      <CategoryDot category={t.category as CategoryId} /> {t.name}
                    </Link>
                    <span className="am-muted">{right}/{t.attempted} · {pct(t.accuracy)}</span>
                  </div>
                  <Meter value={t.accuracy ?? 0} tone={tone(t.accuracy)} />
                </div>
                <Link className="am-link am-an-weak-go" to={`/problems?topic=${t.id}`}>Practice</Link>
              </li>
            );
          })}
        </ol>
      ) : (
        <Empty title="No weak spots yet">Every topic you have tried, you got right first time.</Empty>
      )}
      <dl className="am-mini-stats am-an-weak-misses">
        <div><dt>Missed</dt><dd>{r.missed_first}</dd></div>
        <div><dt>Fixed since</dt><dd>{r.recovered}</dd></div>
        <div><dt>Still open</dt><dd>{r.open}</dd></div>
      </dl>
    </section>
  );
}

/**
 * Points lost in recent timed sittings, by topic: a wrong answer costs 6 on
 * the AMC and a blank 4.5, against a right one. These come first, and the
 * study plan targets them first (backend/amc/planning.py MOCK_RECOVERY).
 */
function MockLosses({ lost }: { lost?: AnalyticsData['mock_mistakes'] }) {
  if (!lost?.sittings) {
    return (
      <p className="am-muted am-an-weak-note">
        Sit a <Link className="am-link" to="/mock-contests">timed mock</Link> to see which topics cost you points under
        exam conditions. Your study plan targets them first.
      </p>
    );
  }
  const top = lost.topics.slice(0, 6);
  const most = top[0]?.lost ?? 1;
  return (
    <>
      <h3 className="am-an-weak-sub">
        Lost in mocks <span className="am-muted">−{lost.lost} pts over your last {lost.sittings} sitting{lost.sittings === 1 ? '' : 's'}</span>
      </h3>
      {top.length ? (
        <ol className="am-an-weak-list am-an-mock-list">
          {top.map((t, i) => (
            <li key={t.id}>
              <span className="am-an-weak-rank">{i + 1}</span>
              <div className="am-an-weak-main">
                <div className="am-an-weak-head">
                  <Link className="am-link am-an-weak-name" to={`/topics/${t.id}`}>
                    <CategoryDot category={t.category} /> {t.name}
                  </Link>
                  <span className="am-an-lost">−{t.lost} pts</span>
                </div>
                <Meter value={t.lost / most} tone="bad" />
                <span className="am-muted am-an-lost-detail">
                  {t.wrong} wrong{t.blank ? `, ${t.blank} blank` : ''} of {t.asked} asked
                </span>
              </div>
              <Link className="am-link am-an-weak-go" to={`/practice/${t.id}?mode=timed`}>Timed set</Link>
            </li>
          ))}
        </ol>
      ) : (
        <p className="am-muted am-an-weak-note">No points lost in your recent sittings.</p>
      )}
    </>
  );
}

function CoachSection() {
  const { data, error, loading, reload } = useApi(() => amc.insights(), []);
  if (loading && !data) return <section className="am-card"><Loading label="Waking the coach" /></section>;
  if (error || !data) return <ErrorState message={error ?? 'Could not load the coach.'} onRetry={reload} />;
  return (
    <Coach initial={data.diagnosis} available={data.ai.available} setup={data.ai.setup} label={data.ai.label} />
  );
}

export default function Analytics() {
  useDocumentTitle('Analytics');
  const { data, error, loading, reload } = useApi(() => amc.analytics(), []);

  return (
    <div className="amc-page">
      <PageHeader title="Analytics">
        <p>Your test scores, how you practice, where it goes wrong, and what to do next.</p>
      </PageHeader>
      {loading && !data ? (
        <Loading label="Reading your answers" />
      ) : error || !data ? (
        <ErrorState message={error ?? 'Could not load analytics.'} onRetry={reload} />
      ) : (
        <div className="am-stack">
          <Takeaways items={data.takeaways} />
          <section className="am-card">
            <div className="am-card-head">
              <h2>Mock contest scores</h2>
              <Link to="/mock-contests">Take a mock</Link>
            </div>
            {data.performance.mocks.length ? (
              <ScoreChart points={data.performance.mocks} target={data.target} goal={data.goal} />
            ) : (
              <Empty title="No scores yet">
                Take a <Link className="am-link" to="/mock-contests">timed mock</Link> or log a past contest score to start the chart.
              </Empty>
            )}
          </section>

          <section className="am-card">
            <div className="am-card-head">
              <h2>Performance</h2>
              <span className="am-muted" style={{ fontSize: 12 }}>last {data.performance.weeks.length} weeks</span>
            </div>
            {data.performance.attempted ? (
              <PerformanceChart weeks={data.performance.weeks} categories={data.performance.categories} />
            ) : (
              <Empty title="No answers yet">
                Solve a few <Link className="am-link" to="/problems">problems</Link> to see how you practice.
              </Empty>
            )}
          </section>

          <div className="am-grid am-an-split">
            <section className="am-card">
              <div className="am-card-head">
                <h2>By difficulty</h2>
                <span className="am-muted" style={{ fontSize: 12 }}>
                  {data.performance.ceiling != null ? `reliable up to ${ratingText(data.performance.ceiling)}` : 'first-try accuracy'}
                </span>
              </div>
              {data.performance.attempted ? (
                <DifficultyChart rows={data.performance.ratings} ceiling={data.performance.ceiling} />
              ) : (
                <p className="am-muted" style={{ margin: 0 }}>No rated problems answered yet.</p>
              )}
            </section>
            <Weaknesses data={data} />
          </div>

          <div className="am-grid am-an-split">
            <PrioritiesCard priorities={data.priorities} />
            <WeaknessLines kinds={data.kinds} />
          </div>

          <CoachSection />
        </div>
      )}
    </div>
  );
}
