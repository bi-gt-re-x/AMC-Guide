/**
 * Mock Contests: every timed paper this site can grade, by contest.
 *
 * Each contest has five AMC Guide Mock sets, written in real problem order at real
 * difficulty (problem n sits where problem n sits on a real paper; the AMC 12
 * sets share eight problems with their AMC 10, as the real A and B papers do),
 * plus the shorter-ramp Step Mock as a warm-up. A card is the set's name, its
 * length, your best score as a bar, and Start; the rest of the card opens it.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { PageHeader } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, shortDate, type Level, type MockContest } from '@/services/amc';
import '@/styles/amc.css';

const LEVELS: Level[] = ['AMC 10', 'AMC 12', 'AIME'];

function MockCard({ m }: { m: MockContest }) {
  const step = m.family === 'step';
  const taken = Boolean(m.attempts);
  const share = taken && m.max ? Math.max(0, Math.min(1, (m.best ?? 0) / m.max)) : 0;
  return (
    <article className={`am-mock${step ? ' is-step' : ''}`}>
      <h3>
        {/* Stretched over the card, so the whole card opens the set. */}
        <Link className="am-mock-link" to={`/contests/${m.id}`}>{step ? 'Step Mock' : `Set ${m.set}`}</Link>
      </h3>
      <p className="am-mock-meta">
        {step && <span className="am-mock-tag">Warm-up · </span>}{m.count} problems · {m.minutes} min
      </p>
      <div className="am-mock-bar" aria-hidden="true"><i style={{ width: `${share * 100}%` }} /></div>
      <div className="am-mock-foot">
        <span className="am-mock-best">
          {taken ? <><b>{m.best}</b> / {m.max}</> : 'Not taken'}
        </span>
        <Link className="am-btn am-btn-primary am-btn-sm am-mock-start" to={`/contests/${m.id}/take`}>Start</Link>
      </div>
    </article>
  );
}

export default function MockContests() {
  useDocumentTitle('Mock Contests');
  const { data, error, loading, reload } = useApi(() => amc.contests(), []);
  const [level, setLevel] = useState<'All' | Level>('All');

  if (loading && !data) return <Loading label="Loading mock contests" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load mock contests.'} onRetry={reload} />;

  const sittings = data.history.filter((h) => data.mocks.some((m) => m.id === h.contest_id));
  const shown = LEVELS.filter((l) => level === 'All' || l === level);

  return (
    <div className="amc-page">
      <PageHeader title="Mock Contests">
        <p>Five timed sets for each contest, scored like the real thing.</p>
      </PageHeader>

      <div className="am-seg" role="group" aria-label="Contest" style={{ marginBottom: 24 }}>
        {(['All', ...LEVELS] as const).map((f) => (
          <button key={f} type="button" className={level === f ? 'is-on' : ''} onClick={() => setLevel(f)}>{f}</button>
        ))}
      </div>

      {shown.map((l) => {
        const mocks = data.mocks.filter((m) => m.level === l);
        const sets = mocks.filter((m) => m.family === 'summit');
        const step = mocks.filter((m) => m.family === 'step');
        return (
          <section key={l} className="am-mock-section" aria-labelledby={`mocks-${l}`}>
            <h2 className="am-h2" id={`mocks-${l}`}>{l}</h2>
            <div className="am-mock-grid">
              {[...sets, ...step].map((m) => <MockCard key={m.id} m={m} />)}
            </div>
          </section>
        );
      })}

      <section className="am-card" style={{ marginTop: 8 }}>
        <div className="am-card-head"><h2>Recent sittings</h2></div>
        {sittings.length ? (
          <table className="am-table">
            <thead><tr><th>Mock</th><th className="num">Score</th><th className="num">Date</th></tr></thead>
            <tbody>
              {sittings.map((h) => (
                <tr key={h.id}>
                  <td><Link to={`/mocks/${h.id}`}>{h.name}</Link></td>
                  <td className="num">{h.score}</td>
                  <td className="num am-muted">{shortDate(h.at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>None yet.</p>
        )}
      </section>
    </div>
  );
}
