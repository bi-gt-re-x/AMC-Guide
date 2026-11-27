/**
 * "Why did you miss it?" — asked after a wrong answer, and on a mock report
 * for each wrong answer and blank (backend/amc/misses.py).
 *
 * One tap from five reasons. The reason decides the next step, shown in
 * place of the question: an accuracy drill for a careless slip, the idea and
 * two problems that use it for a method not known yet, wordier problems for a
 * misreading, a timed set for running out of time, a learn set for a guess.
 * The reason can be changed or taken back. Over time the reasons make the
 * profile on Analytics.
 *
 * `compact` is the mock report's form: the same question, and a one-line
 * next step rather than the whole card.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MathText } from '@/components/Amc/MathText';
import { ratingText } from '@/components/Amc/bits';
import type { MissChoice, MissReasonId, MissStep } from '@/services/amc';
import type { ApiResult } from '@/types/api';

type Reply = ApiResult<{ reason: MissReasonId | null; step: MissStep | null }>;

export function MissReason({
  choices, reason, step, save, compact = false,
}: {
  choices: MissChoice[];
  reason: MissReasonId | null;
  step: MissStep | null;
  /** Store the reason ('' takes it back); replies with the next step. */
  save: (reason: MissReasonId | '') => Promise<Reply>;
  compact?: boolean;
}) {
  const [picked, setPicked] = useState<MissReasonId | null>(reason);
  const [next, setNext] = useState<MissStep | null>(step);
  const [asking, setAsking] = useState(reason == null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // A different miss (another problem, or the page's record arriving) starts from what is stored.
  useEffect(() => {
    setPicked(reason);
    setNext(step);
    setAsking(reason == null);
    setError('');
    // eslint-disable-next-line react-hooks/exhaustive-deps -- when the stored reason changes
  }, [reason, step?.reason]);

  async function choose(id: MissReasonId) {
    if (busy) return;
    setBusy(true);
    setError('');
    const before = picked;
    setPicked(id);
    try {
      const reply = await save(id);
      if (reply.success) {
        setNext(reply.step);
        setAsking(false);
      } else {
        setPicked(before);
        setError(reply.message);
      }
    } catch {
      setPicked(before);
      setError('Could not save that. Try again.');
    } finally {
      setBusy(false);
    }
  }

  async function takeBack() {
    setBusy(true);
    try {
      const reply = await save('');
      if (reply.success) {
        setPicked(null);
        setNext(null);
        setAsking(true);
      }
    } finally {
      setBusy(false);
    }
  }

  const label = choices.find((c) => c.id === picked)?.label;

  if (!asking && next) {
    if (compact) {
      return (
        <div className="am-miss is-compact" aria-live="polite">
          <span className="am-miss-said">{label}</span>
          {next.action ? (
            <Link className="am-link" to={next.action.to}>{next.action.label} →</Link>
          ) : next.problems[0] ? (
            <Link className="am-link" to={`/problems/${next.problems[0].id}`}>{next.title}: {next.problems[0].short} →</Link>
          ) : (
            <span className="am-muted">{next.title}</span>
          )}
          <button type="button" className="am-miss-change" onClick={() => setAsking(true)}>Change</button>
        </div>
      );
    }
    return (
      <section className="am-miss" aria-live="polite" aria-label="What to do next">
        <div className="am-miss-head">
          <span className="am-kicker">Next step · {label}</span>
          <button type="button" className="am-miss-change" onClick={() => setAsking(true)}>Change reason</button>
        </div>
        <h3 className="am-miss-title">{next.title}</h3>
        <p className="am-miss-body">{next.body}</p>
        {next.idea && (
          <div className="am-callout am-callout-insight am-miss-idea">
            <span>The idea · {next.idea.name}</span>
            <MathText text={next.idea.text} as="p" />
          </div>
        )}
        {next.problems.length > 0 && (
          <ul className="am-miss-list">
            {next.problems.map((q) => (
              <li key={q.id}>
                <Link className="am-miss-problem" to={`/problems/${q.id}`}>
                  <span className="am-miss-problem-head">
                    <strong>{q.source}</strong>
                    {q.rating != null && <span className="am-muted">{ratingText(q.rating)}</span>}
                  </span>
                  {q.why && <span className="am-miss-why">{q.why}</span>}
                  <span className="am-miss-preview">{q.preview}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
        {(next.action || next.more) && (
          <div className="am-miss-actions">
            {next.action && <Link className="am-btn am-btn-primary am-btn-sm" to={next.action.to}>{next.action.label}</Link>}
            {next.more && <Link className="am-link" to={next.more.to}>{next.more.label}</Link>}
          </div>
        )}
      </section>
    );
  }

  return (
    <section className={`am-miss${compact ? ' is-compact is-asking' : ''}`} aria-label="Why did you miss it?">
      {compact ? (
        <span className="am-miss-ask">Why?</span>
      ) : (
        <div className="am-miss-head">
          <span className="am-kicker">Why did you miss it?</span>
          {picked && <button type="button" className="am-miss-change" disabled={busy} onClick={() => void takeBack()}>Clear</button>}
        </div>
      )}
      {!compact && <p className="am-miss-body">Pick one. It decides what you practice next.</p>}
      <div className="am-chips am-miss-chips" role="group" aria-label="Reasons">
        {choices.map((c) => (
          <button key={c.id} type="button" className={`am-chip${picked === c.id ? ' is-on' : ''}`}
                  aria-pressed={picked === c.id} title={c.means} disabled={busy}
                  onClick={() => void choose(c.id)}>
            {c.label}
          </button>
        ))}
      </div>
      {error && <p className="am-error" role="alert">{error}</p>}
    </section>
  );
}
