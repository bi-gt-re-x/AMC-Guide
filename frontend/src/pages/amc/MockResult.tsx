/**
 * A graded mock: the score, where the points went (by topic and by stretch of
 * the paper), and every problem with your answer, the key and the solution.
 */
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { MathText } from '@/components/Amc/MathText';
import { DiagramNote, Difficulty, Meter, PageHeader, Solution, StandingNote } from '@/components/Amc/bits';
import { MissReason } from '@/components/Amc/MissReason';
import { useApi, useDocumentTitle, usePageSwap } from '@/hooks';
import { amc, shortDate, type MissReasonId } from '@/services/amc';
import { clock } from '@/components/Amc/bits';
import '@/styles/amc.css';

export default function MockResult() {
  const { mockId = '' } = useParams();
  const { data, error, loading, refreshing, reload } = useApi(() => amc.mock(mockId), [mockId]);
  const swap = usePageSwap(mockId, loading || refreshing);
  // Reasons given on this visit, by problem number (null: taken back), so the count above the list keeps up.
  const [told, setTold] = useState<Record<number, MissReasonId | null>>({});
  useDocumentTitle(data ? `${data.contest.name} report` : 'Mock report');
  if (loading && !data) return <Loading label="Grading" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load this report.'} onRetry={reload} />;

  const { result, report, rows, contest } = data;
  const aime = contest.level === 'AIME';
  const fmt = (v: string | number) => (aime ? String(v).padStart(3, '0') : String(v));
  const worst = report.topics.filter((t) => t.lost > 0).slice(0, 6);
  const maxLost = Math.max(1, ...report.bands.map((b) => b.lost));
  const missed = rows.filter((r) => r.reasons).length;
  const untold = rows.filter((r) => r.reasons && !(r.number in told ? told[r.number] : r.miss_reason)).length;

  return (
    <div className={`amc-page ${swap}`.trim()}>
      <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12 }}>
        <Link to={`/contests/${contest.id}`} className="am-link">← {contest.name}</Link>
      </nav>
      <PageHeader kicker={`${contest.level} · ${shortDate(result.at)}`} title={contest.name}
                  actions={
                    <>
                      <Link className="am-btn" to="/review">Review misses</Link>
                      <Link className="am-btn am-btn-primary" to={`/contests/${contest.id}/take`}>Sit it again</Link>
                    </>
                  } />

      <div className="am-grid am-grid-3" style={{ marginBottom: 16 }}>
        <section className="am-card">
          <span className="am-kicker">Score</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span className="am-big">{result.score}</span>
            <span className="am-muted">/ {result.max}</span>
          </div>
          <p className="am-muted" style={{ margin: '8px 0 0', fontSize: 13 }}>
            {result.correct} right · {result.wrong} wrong · {result.blank} blank · {clock(result.seconds)} used
          </p>
          <StandingNote standing={result.standing} />
        </section>
        <section className="am-card">
          <span className="am-kicker">Points lost by position</span>
          <div className="am-bars" style={{ marginTop: 8 }}>
            {report.bands.map((b) => (
              <div key={b.label} className="am-bar-row">
                <span>{b.label}</span>
                <span className="am-muted" style={{ fontSize: 12 }}>{b.correct}/{b.total} · −{b.lost}</span>
                <Meter value={b.lost / maxLost} tone="bad" />
              </div>
            ))}
          </div>
        </section>
        <section className="am-card">
          <span className="am-kicker">Costliest topics</span>
          {worst.length ? (
            <ul className="am-list" style={{ marginTop: 8 }}>
              {worst.map((t) => (
                <li key={t.topic}>
                  <Link className="am-link" style={{ color: 'var(--am-ink)', fontWeight: 500 }} to={`/topics/${t.topic}`}>{t.name}</Link>
                  <span className="am-muted">−{t.lost} · {t.correct}/{t.total}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: '8px 0 0' }}>Perfect paper.</p>
          )}
        </section>
      </div>

      <section className="am-card">
        <div className="am-card-head">
          <h2>Problem by problem</h2>
          {missed > 0 && (
            <span className="am-muted" style={{ fontSize: 12 }}>
              {untold ? `Say why for ${untold} of ${missed} misses: it shapes what you practice next` : 'Every miss has a reason'}
            </span>
          )}
        </div>
        {rows.map((r) => (
          <div key={r.number} className="am-result-row">
            <span className="am-result-num">{r.number}</span>
            <div style={{ minWidth: 0 }}>
              <div className="am-row-head" style={{ marginBottom: 6 }}>
                <Link className="am-link" to={`/problems/${r.problem_id}`}>{r.topic_name}</Link>
                <Difficulty value={r.difficulty} rating={r.rating} />
              </div>
              <MathText text={r.statement} as="p" className="am-statement" />
              {r.diagram && <DiagramNote diagram={r.diagram} />}
              {r.reasons && (
                <MissReason compact choices={r.reasons} reason={r.miss_reason ?? null} step={null}
                            save={async (reason) => {
                              const reply = await amc.mockMissReason(mockId, r.number, reason);
                              if (reply.success) setTold((was) => ({ ...was, [r.number]: reply.reason }));
                              return reply;
                            }} />
              )}
              {r.solution && (
                <details>
                  <summary>Solution</summary>
                  <Solution solution={r.solution} insight={r.insight} trap={r.trap} />
                </details>
              )}
            </div>
            <div style={{ textAlign: 'right', display: 'grid', gap: 4, justifyItems: 'end' }}>
              <span className={`am-pill ${r.result === 'correct' ? 'am-pill-solved' : r.result === 'wrong' ? 'am-pill-missed' : ''}`}>
                {r.result === 'correct' ? 'Right' : r.result === 'wrong' ? 'Wrong' : 'Blank'}
              </span>
              <span className="am-muted" style={{ fontSize: 12 }}>
                You: {r.given ? fmt(r.given) : '—'} · Key: {fmt(r.answer)}
              </span>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
