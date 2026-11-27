/**
 * The placement check (backend/amc/placement.py): twelve short problems, so
 * the level and the study plan start out personal instead of empty.
 *
 * Kept light on purpose. One line says what it is, then the problems, one at
 * a time: no clock, nothing marked right or wrong as it goes, "Not sure" as a
 * first-class answer, and "Stop here" always there. The end is one sentence
 * about where they are, a line per subject, and the way into the site. No
 * tour: the site is there to be found.
 *
 * Used as the last step of sign-up (components/Auth/AmcProfile.tsx) and on its
 * own page, /placement, which the dashboard offers to an account that skipped
 * it.
 */
import { useEffect, useState } from 'react';
import { MathText } from '@/components/Amc/MathText';
import { AnswerInput, useStopwatch } from '@/components/Amc/bits';
import { amc, announceAmcChanged, type Level, type PlacementResult, type PlacementState } from '@/services/amc';
import '@/styles/amc.css';

export function Placement({
  level, onDone, intro = true, doneLabel = 'Go to my dashboard',
}: {
  level: Level;
  /** Called once it is finished, stopped or skipped. */
  onDone: (result: PlacementResult | null) => void;
  /** Show the one-screen offer before the first problem. */
  intro?: boolean;
  doneLabel?: string;
}) {
  const [state, setState] = useState<PlacementState | null>(null);
  const [offered, setOffered] = useState(intro);
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const asking = Boolean(state && !state.done && state.problem);
  const [seconds, setSeconds] = useStopwatch(asking && !busy);

  // A check begun before (a refresh, or back from elsewhere) carries on where it was.
  useEffect(() => {
    let live = true;
    void amc.placement().then((reply) => {
      if (!live || !reply.success || !reply.placement) return;
      setState(reply.placement);
      setOffered(false);
    }).catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    setAnswer('');
    setSeconds(0);
  }, [state?.problem?.id, setSeconds]);

  async function call(work: () => Promise<{ success: boolean; message?: string; placement?: PlacementState }>) {
    setBusy(true);
    setError('');
    try {
      const reply = await work();
      if (reply.success && reply.placement) {
        setState(reply.placement);
        if (reply.placement.done) announceAmcChanged();
      } else if (!reply.success) {
        setError(reply.message || 'That did not save. Try again.');
      }
    } catch {
      setError('Couldn’t reach the server. Try again.');
    } finally {
      setBusy(false);
    }
  }

  const start = () => {
    setOffered(false);
    void call(() => amc.startPlacement(level));
  };
  const send = (given: string) => {
    if (!state?.problem) return;
    const id = state.problem.id;
    void call(() => amc.answerPlacement(id, given, seconds));
  };

  async function skipAll() {
    setBusy(true);
    try {
      const reply = await amc.stopPlacement();
      if (reply.success && reply.placement.result) {
        setState(reply.placement);
        announceAmcChanged();
        return;
      }
    } catch {
      /* nothing to keep: on to the site */
    } finally {
      setBusy(false);
    }
    onDone(null);
  }

  if (offered) {
    return (
      <div className="am-place">
        <h2 className="am-place-title">Find your level</h2>
        <p className="am-place-lede">
          Twelve short problems, so your level and your plan start from you rather than from a guess. No timer,
          nothing marked as you go, and “Not sure” is a fine answer. About ten minutes.
        </p>
        <div className="am-place-actions">
          <button type="button" className="am-btn am-btn-primary am-place-go" disabled={busy} onClick={start}>Start</button>
          <button type="button" className="am-btn am-btn-ghost" disabled={busy} onClick={() => void skipAll()}>Skip for now</button>
        </div>
        {error && <p className="am-error" role="alert">{error}</p>}
      </div>
    );
  }

  if (!state) {
    return <div className="am-place"><p className="am-place-lede">{error || 'Getting your first problem…'}</p></div>;
  }

  if (state.done) {
    return <PlacementDone result={state.result} onDone={() => onDone(state.result)} label={doneLabel} />;
  }

  const p = state.problem!;
  return (
    <div className="am-place">
      <div className="am-place-head">
        <span className="am-place-count">{state.answered + 1} of {state.total}</span>
        <span className="am-place-subject">{p.category_name}</span>
      </div>
      <div className="am-place-bar" role="progressbar" aria-label="Placement check" aria-valuemin={0}
           aria-valuemax={state.total} aria-valuenow={state.answered}>
        <i style={{ width: `${(state.answered / state.total) * 100}%` }} />
      </div>
      {/* Keyed to the problem, so it eases in rather than swapping in place. */}
      <div key={p.id} className="am-place-problem">
        <MathText text={p.statement} as="p" className="am-statement" />
        <AnswerInput choices={p.choices} value={answer} onChange={setAnswer} onSubmit={() => answer && send(answer)} />
      </div>
      <div className="am-place-actions">
        <button type="button" className="am-btn am-btn-ghost" disabled={busy} onClick={() => send('')}>Not sure</button>
        <button type="button" className="am-btn am-btn-primary am-place-go" disabled={busy || !answer} onClick={() => send(answer)}>
          {state.answered + 1 === state.total ? 'Finish' : 'Next'}
        </button>
      </div>
      {error && <p className="am-error" role="alert">{error}</p>}
      <button type="button" className="am-place-stop" disabled={busy} onClick={() => void skipAll()}>
        Stop here{state.answered >= 4 ? ' and use these answers' : ''}
      </button>
    </div>
  );
}

function PlacementDone({ result, onDone, label }: { result: PlacementResult | null; onDone: () => void; label: string }) {
  if (!result) {
    return (
      <div className="am-place">
        <h2 className="am-place-title">That’s fine</h2>
        <p className="am-place-lede">
          A few more answers are needed to place you. Your level will settle as you practice, and the dashboard
          can start the check again any time.
        </p>
        <div className="am-place-actions">
          <button type="button" className="am-btn am-btn-primary am-place-go" onClick={onDone}>{label}</button>
        </div>
      </div>
    );
  }
  return (
    <div className="am-place" aria-live="polite">
      <span className="am-kicker">Your starting level</span>
      <p className="am-place-level"><strong>{result.level}</strong><span>/ 12</span></p>
      <p className="am-place-lede">{result.summary}</p>
      <ul className="am-place-subjects">
        {result.subjects.map((s) => (
          <li key={s.id}>
            <span>{s.name}</span>
            <span className="am-place-dots" aria-label={`${s.right} of ${s.total} right`}>
              {Array.from({ length: s.total }, (_, i) => <i key={i} className={i < s.right ? 'is-right' : ''} />)}
            </span>
          </li>
        ))}
      </ul>
      <p className="am-place-note">
        {result.right} of {result.answered} right. Your study plan and practice sets now start here, and they move
        as you do. A timed mock gives you a projected score.
      </p>
      <div className="am-place-actions">
        <button type="button" className="am-btn am-btn-primary am-place-go" onClick={onDone}>{label}</button>
      </div>
    </div>
  );
}
