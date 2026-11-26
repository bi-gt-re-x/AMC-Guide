/**
 * The end of a set: what was right, what was missed (with the answer given
 * and the right one), what was left, and what it changes. Read from the set
 * as the account's database holds it (GET /api/amc/sets/:id,
 * backend/amc/setreport.py), never from problems' lifetime status, so a
 * problem solved last month and missed today is a miss here.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { CategoryDot, clock, ratingText } from '@/components/Amc/bits';
import { shortDate, type SetReport as Report, type SetReportRow } from '@/services/amc';

function pct(value: number | null): string {
  return value == null ? '—' : `${Math.round(value * 100)}%`;
}

function signed(value: number): string {
  const r = Math.round(value * 100) / 100;
  return `${r > 0 ? '+' : r < 0 ? '−' : '±'}${Math.abs(r).toFixed(2)}`;
}

function Row({ row, flag }: { row: SetReportRow; flag: string }) {
  return (
    <li className={`am-report-row is-${row.result}`}>
      <span className="am-report-n">{row.n}</span>
      <span className="am-report-main">
        <Link className="am-link" to={`/problems/${row.id}`}>{row.source}</Link>
        <span className="am-muted">
          <CategoryDot category={row.category} /> {row.topic_name} · {row.technique_name} · {ratingText(row.rating)}
        </span>
      </span>
      <span className="am-report-answer">
        {row.result === 'right' && <>You answered <strong>{row.given}</strong> ✓</>}
        {row.result === 'wrong' && (
          <>You answered <s>{row.given}</s> · answer <strong>{row.answer}</strong></>
        )}
        {row.result === 'revealed' && <>Solution shown · answer <strong>{row.answer}</strong></>}
        {row.result === 'skipped' && <span className="am-muted">Not answered · still open</span>}
      </span>
      <span className="am-report-meta">
        {row.result !== 'skipped' && row.result !== 'revealed' && (
          <span className={row.slow || row.over_pace ? 'is-over' : ''} title={`About ${clock(row.par)} at contest pace for its difficulty`}>
            {clock(row.seconds)}
          </span>
        )}
        {row.careless && <span className="am-report-flag is-careless" title={`Your level gave you ${pct(row.chance)} on it`}>slip</span>}
        {row.stretch && <span className="am-report-flag is-stretch" title={`Your level gave you ${pct(row.chance)} on it`}>stretch</span>}
        {row.slow && <span className="am-report-flag is-slow">slow</span>}
        {row.review && row.review.status === 'active' && (
          <span className="am-muted" title="Back in your review log">review {shortDate(row.review.due)}</span>
        )}
        {flag && <span className="am-muted">{flag}</span>}
      </span>
    </li>
  );
}

function Group({ title, rows, tone, empty }: { title: string; rows: SetReportRow[]; tone: string; empty?: string }) {
  if (!rows.length && !empty) return null;
  return (
    <section className={`am-report-group is-${tone}`} aria-label={title}>
      <h3>{title} <small>{rows.length}</small></h3>
      {rows.length ? (
        <ol className="am-report-list">
          {rows.map((r) => (
            <Row key={r.id} row={r} flag={r.seen_before ? (r.before === 'right' ? 'right before' : 'missed before') : ''} />
          ))}
        </ol>
      ) : <p className="am-muted am-report-empty">{empty}</p>}
    </section>
  );
}

export function SetReport({ report, actions }: { report: Report; actions?: ReactNode }) {
  const rows = report.problems;
  const right = rows.filter((r) => r.result === 'right');
  const missed = rows.filter((r) => r.result === 'wrong' || r.result === 'revealed');
  const skipped = rows.filter((r) => r.result === 'skipped');
  const moved = report.level.moved;
  return (
    <section className="am-card am-report" role="region" aria-label="How the set went">
      <header className="am-report-head">
        <div>
          <p className="am-report-kicker">
            {report.time_up ? <span className="am-set-timeup">Time's up · </span> : null}
            {report.title}{report.topic_name ? ` · ${report.topic_name}` : ''}
          </p>
          <p className="am-report-score"><strong>{report.right} of {report.total}</strong> right</p>
          <p className="am-report-verdict">{report.verdict}</p>
        </div>
        {actions && <div className="am-report-actions">{actions}</div>}
      </header>

      <dl className="am-report-stats">
        <div><dt>Right</dt><dd className="is-right">{report.right}</dd></div>
        <div><dt>Missed</dt><dd className="is-wrong">{report.wrong + report.revealed}</dd></div>
        <div><dt>Not answered</dt><dd>{report.skipped}</dd></div>
        <div><dt>Accuracy</dt><dd>{pct(report.accuracy)}</dd></div>
        <div>
          <dt>Time</dt>
          <dd>{clock(report.used)}{report.seconds ? <small> of {clock(report.seconds)}</small> : null}</dd>
        </div>
        <div>
          <dt>Your level</dt>
          <dd title="AMC Guide's 1-12 scale: the rating you solve half the time">
            {report.level.after.toFixed(1)} <small className={moved > 0 ? 'is-up' : moved < 0 ? 'is-down' : ''}>{signed(moved)}</small>
          </dd>
        </div>
      </dl>

      {report.notes.length > 0 && (
        <ul className="am-report-notes">
          {report.notes.map((n) => <li key={n.kind} className={`is-${n.kind}`}>{n.text}</li>)}
        </ul>
      )}

      <Group title="What you missed" rows={missed} tone="wrong" empty="Nothing missed." />
      <Group title="What you got right" rows={right} tone="right" empty="None right this time." />
      <Group title="Not answered" rows={skipped} tone="skipped" />

      {report.topics.length > 0 && (
        <section className="am-report-group" aria-label="By topic">
          <h3>By topic</h3>
          <ul className="am-report-topics">
            {report.topics.map((t) => (
              <li key={t.id}>
                <span><CategoryDot category={t.category} /> {t.name}</span>
                <span>{t.right} of {t.total}</span>
                <span className="am-muted" title="Your level in this topic, before the set and after it">
                  {t.before != null && t.after != null
                    ? <>level {t.before.toFixed(1)} → {t.after.toFixed(1)} <small className={(t.moved ?? 0) > 0 ? 'is-up' : (t.moved ?? 0) < 0 ? 'is-down' : ''}>{signed(t.moved ?? 0)}</small></>
                    : t.after != null ? <>level {t.after.toFixed(1)} (first answers)</> : ''}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {report.next.length > 0 && (
        <section className="am-report-group am-report-next" aria-label="What next">
          <h3>What next</h3>
          <p className="am-muted am-report-empty">
            Your study plan is rebuilt from these answers. Here is what it now asks for.
          </p>
          <ul>
            {report.next.map((n) => (
              <li key={n.topic}>
                <div>
                  <strong>{n.topic_name}: {n.mode_title}</strong>
                  <span className="am-muted"> · #{n.rank} of {n.of} topics by points to gain</span>
                  <p className="am-muted">
                    {n.kind_name ? `${n.kind_name} weakness: ${n.evidence}. ${n.approach}` :
                      n.answered < 3 ? 'Too few answers here to read a weakness yet: learn the ideas first.' :
                        `First-try accuracy ${pct(n.mastery)} over ${n.answered}. No single weakness stands out: keep practising at ${n.mix}.`}
                  </p>
                </div>
                <Link className="am-btn am-btn-sm" to={n.href}>Start</Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}
