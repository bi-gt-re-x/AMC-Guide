/**
 * The dashboard's "Recent performance" card, kept to what can be taken in at
 * a glance: two numbers for the last 7 days (answered, and the share right),
 * one sentence against the 7 days before, the fortnight day by day, and the
 * latest contest score with its change from the one before.
 *
 * It used to be a table of four numbers a week with arrows, a list of notes
 * saying the same things again, and three scores, one of them compared raw
 * against a paper of another year. Everything here is from
 * backend/amc/insights.py `recent_performance`; the score change is by the
 * difficulty-adjusted score (backend/amc/results.py), so a harder paper is not
 * read as a slump. The full picture is on Analytics.
 */
import { Link } from 'react-router-dom';
import { pct, shortDate, type RecentPerformance } from '@/services/amc';
import { Columns, Legend } from './Charts';

export function RecentPerformanceCard({ data }: { data: RecentPerformance }) {
  const { this_week: now, summary, latest } = data;
  const any = data.days.some((d) => d.answered) || data.mocks.length > 0;
  const last = data.days.length - 1;
  return (
    <section className="am-card">
      <div className="am-card-head">
        <h2>Recent performance</h2>
        <Link to="/analytics">Analytics</Link>
      </div>
      {!any ? (
        <p className="am-muted" style={{ margin: 0 }}>Nothing in the last two weeks.</p>
      ) : (
        <div className="am-perf">
          <div>
            <p className="am-perf-kicker">Last 7 days</p>
            <dl className="am-perf-figures">
              <div><dt>answered</dt><dd>{now.answered}</dd></div>
              <div><dt>right</dt><dd>{pct(now.accuracy)}</dd></div>
            </dl>
            <p className={`am-perf-summary is-${summary.tone}`}>{summary.text}</p>
          </div>

          <div>
            <Columns
              caption="Problems answered each day for the last 14 days, and how many were right"
              idle={<>Point at a day to see it</>}
              labelEvery={7}
              points={data.days.map((d, i) => ({
                key: d.date,
                label: i === last ? 'Today' : shortDate(d.date),
                value: d.answered,
                part: d.correct,
                tip: d.answered
                  ? `${shortDate(d.date)} · ${d.correct} right, ${d.answered - d.correct} missed`
                  : `${shortDate(d.date)} · nothing answered`,
              }))}
            />
            <Legend items={[{ label: 'Right', tone: 'strong' }, { label: 'Missed', tone: 'soft' }]} />
          </div>

          {latest && (
            <Link className="am-row am-perf-latest"
                  to={latest.kind === 'mock' ? `/mocks/${latest.id}` : `/contests/${latest.contest_id}`}>
              <div className="am-row-main">
                <div className="am-row-head">
                  <span className="am-muted">Latest {latest.kind === 'mock' ? 'mock' : 'score'}</span>
                  <strong>{latest.name}</strong>
                  <span className="am-muted">{shortDate(latest.at)}</span>
                </div>
                {latest.change_text && (
                  <p className={`am-perf-change${latest.change ? latest.change > 0 ? ' is-up' : ' is-down' : ''}`}>
                    {latest.change_text}
                  </p>
                )}
              </div>
              <div className="am-row-side">
                <strong>{latest.score}{latest.max ? ` / ${latest.max}` : ''}</strong>
              </div>
            </Link>
          )}
        </div>
      )}
    </section>
  );
}
