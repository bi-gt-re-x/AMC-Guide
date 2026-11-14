/**
 * Past contests: every real AMC 10, AMC 12 and AIME since 2000, linked to the
 * official problems and answer keys on the AoPS wiki, with a place to log the
 * score you got. The timed mocks have their own page (MockContests.tsx).
 *
 * Papers brought into Summit come first, as cards with what they hold (worked
 * solutions) and how you have done on them, and stand out in the year grid.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { PageHeader } from '@/components/Amc/bits';
import { BulkImporter } from '@/components/Amc/BulkImporter';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, shortDate, type Level } from '@/services/amc';
import '@/styles/amc.css';

const FILTERS: ('All' | Level)[] = ['All', 'AMC 10', 'AMC 12', 'AIME'];

export default function Contests() {
  useDocumentTitle('Past Contests');
  const { data, error, loading, reload } = useApi(() => amc.contests(), []);
  const [level, setLevel] = useState<(typeof FILTERS)[number]>('All');

  const years = useMemo(() => {
    if (!data) return [];
    return data.years
      .map((y) => ({ ...y, contests: y.contests.filter((c) => level === 'All' || c.level === level) }))
      .filter((y) => y.contests.length);
  }, [data, level]);

  if (loading && !data) return <Loading label="Loading contests" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load contests.'} onRetry={reload} />;

  const total = data.years.reduce((n, y) => n + y.contests.length, 0);
  const ready = data.years.flatMap((y) => y.contests).filter((c) => c.imported === c.count);

  return (
    <div className="amc-page">
      <PageHeader title="Past Contests">
        <p>
          All {total} official papers since 2000. Papers marked ● are in Summit
          ({data.imported} so far) and can be practiced and timed here.
        </p>
      </PageHeader>

      <Link className="am-card am-mock-banner" to="/mock-contests">
        <span>
          <strong>Mock Contests</strong>
          <span className="am-muted"> · {data.mocks.filter((m) => m.family === 'summit').length} full sets for the AMC 10, AMC 12 and AIME, timed and graded here</span>
        </span>
        <span aria-hidden="true">→</span>
      </Link>

      {ready.length > 0 && (
        <section className="am-ready" aria-label="Ready to practice">
          <h2 className="am-h2">Ready to practice</h2>
          <div className="am-ready-cards">
            {ready.map((c) => (
              <article key={c.id} className="am-card am-ready-card">
                <Link to={`/contests/${c.id}`} className="am-ready-name">{c.name}</Link>
                <p className="am-muted">
                  {c.count} problems · {c.minutes} min{c.written ? (c.written === c.count ? ' · all worked out' : ` · ${c.written} worked out`) : ''}
                </p>
                <p className="am-ready-score">
                  {c.sittings
                    ? <>Best <b>{c.best}</b> of {c.max} · {c.sittings} sitting{c.sittings === 1 ? '' : 's'}</>
                    : <span className="am-muted">Not sat yet</span>}
                </p>
                <div className="am-ready-actions">
                  <Link className="am-btn am-btn-sm" to={`/contests/${c.id}`}>Open</Link>
                  <Link className="am-btn am-btn-primary am-btn-sm" to={`/contests/${c.id}/take`}>{c.sittings ? 'Sit it again' : 'Sit it'}</Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <div className="am-grid am-grid-main">
        <section className="am-card">
          <div className="am-card-head">
            <h2>Official papers</h2>
            <div className="am-seg" role="group" aria-label="Contest">
              {FILTERS.map((f) => (
                <button key={f} type="button" className={level === f ? 'is-on' : ''} onClick={() => setLevel(f)}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div>
            {years.map((y) => (
              <div key={y.year} className="am-year">
                <h3>{y.year}</h3>
                <div className="am-papers">
                  {y.contests.map((c) => (
                    <Link key={c.id} className={`am-paper${c.imported === c.count ? ' is-in' : ''}`} to={`/contests/${c.id}`}
                          title={c.imported === c.count ? `${c.name}: in Summit` : c.name}>
                      {c.season ? `${c.season} ` : ''}{c.level}{c.paper ? (c.level === 'AIME' ? ` ${c.paper}` : c.paper) : ''}
                      {c.imported === c.count && <i className="am-paper-in" title="In Summit">●</i>}
                      {c.logged && <b>{c.logged.score}</b>}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className="am-stack">
          {data.can_import && <BulkImporter onSaved={reload} />}
          <section className="am-card">
            <div className="am-card-head"><h2>Your scores</h2></div>
            {data.history.length ? (
              <table className="am-table">
                <thead><tr><th>Contest</th><th className="num">Score</th><th className="num">Date</th></tr></thead>
                <tbody>
                  {data.history.map((h) => (
                    <tr key={h.id}>
                      <td>
                        <Link to={h.kind === 'mock' ? `/mocks/${h.id}` : `/contests/${h.contest_id}`}>{h.name}</Link>
                      </td>
                      <td className="num">{h.score}</td>
                      <td className="num am-muted">{shortDate(h.at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>No scores yet.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
