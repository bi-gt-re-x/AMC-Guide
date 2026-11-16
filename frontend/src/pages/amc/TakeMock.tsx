/**
 * A timed contest, mock or official, laid out like the real one: a cover page
 * first (the clock starts only on Begin), then one problem at a time with the
 * bubble answer sheet beside it, a countdown, and Hand in. Time running out
 * hands it in. The answer sheet is the one map of the paper: it shows what is
 * answered and flagged, and a number jumps to that problem.
 *
 * **The clock only runs while you are here.** It counts while this tab is
 * showing and its window has focus, and stops the moment you switch tabs, apps
 * or windows (the clock shows Paused), so time away is never charged.
 *
 * Answers, flags and the time used are kept in this browser's storage, so a
 * reload or an accidental back resumes the same sitting where its clock left
 * off; time with the page closed does not count either.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { MathText } from '@/components/Amc/MathText';
import { AnswerInput, DiagramNote, clock, useWindowActive, windowActive } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, announceAmcChanged } from '@/services/amc';
import '@/styles/amc.css';

interface Sitting {
  /** Seconds of contest time used so far: only time spent on this page. */
  used: number;
  answers: Record<string, string>;
  flags: number[];
}

const LETTERS = ['A', 'B', 'C', 'D', 'E'];
const key = (id: string) => `amc-mock:${id}`;

function readSitting(id: string): Sitting | null {
  try {
    const raw = localStorage.getItem(key(id));
    if (!raw) return null;
    const stored = JSON.parse(raw) as Partial<Sitting> & { started?: number };
    // A sitting saved before the clock paused (a start time, not time used):
    // carry it over with the wall-clock time since it began.
    const used = typeof stored.used === 'number'
      ? stored.used
      : typeof stored.started === 'number' ? Math.max(0, (Date.now() - stored.started) / 1000) : 0;
    return { used, answers: stored.answers ?? {}, flags: stored.flags ?? [] };
  } catch {
    return null;
  }
}

function writeSitting(id: string, sitting: Sitting | null) {
  try {
    if (sitting) localStorage.setItem(key(id), JSON.stringify(sitting));
    else localStorage.removeItem(key(id));
  } catch {
    /* storage blocked: the sitting still works, it just can't resume */
  }
}

export default function TakeMock() {
  const { contestId = '' } = useParams();
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi(() => amc.contest(contestId), [contestId]);

  const [sitting, setSitting] = useState<Sitting | null>(() => readSitting(contestId));
  useDocumentTitle(data ? `${data.contest.name}${sitting ? ' — in progress' : ''}` : 'Contest');
  const [at, setAt] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const submitted = useRef(false);
  const active = useWindowActive();
  const running = Boolean(sitting) && active;

  useEffect(() => {
    if (sitting) writeSitting(contestId, sitting);
  }, [contestId, sitting]);
  // The clock: add the real time between ticks, but only while the reader is
  // here, and never more than a couple of seconds at once (a laptop waking from
  // sleep should not lose the time it slept).
  useEffect(() => {
    if (!running) return undefined;
    let last = Date.now();
    const id = window.setInterval(() => {
      const now = Date.now();
      const step = Math.min(2, (now - last) / 1000);
      last = now;
      if (!windowActive()) return;
      setSitting((s) => (s ? { ...s, used: s.used + step } : s));
    }, 1000);
    return () => window.clearInterval(id);
  }, [running]);

  const minutes = data?.contest.minutes ?? 75;
  const elapsed = sitting ? Math.floor(sitting.used) : 0;
  const left = minutes * 60 - elapsed;
  const problems = useMemo(() => data?.problems ?? [], [data]);

  const submit = useCallback(async () => {
    if (submitted.current || !sitting) return;
    submitted.current = true;
    setBusy(true);
    setMessage('');
    try {
      const reply = await amc.submit(contestId, sitting.answers, Math.min(elapsed, minutes * 60));
      if (reply.success) {
        writeSitting(contestId, null);
        announceAmcChanged();
        navigate(`/mocks/${reply.id}`, { replace: true });
      } else {
        submitted.current = false;
        setMessage(reply.message);
      }
    } catch (cause) {
      submitted.current = false;
      setMessage(cause instanceof Error ? cause.message : 'Could not hand it in. Try again.');
    } finally {
      setBusy(false);
    }
  }, [contestId, elapsed, minutes, navigate, sitting]);

  // Time is up: hand it in as it stands.
  useEffect(() => {
    if (data && sitting && left <= 0 && !submitted.current) void submit();
  }, [data, sitting, left, submit]);

  const setAnswerFor = useCallback((n: number, value: string) => {
    setSitting((s) => (s ? { ...s, answers: { ...s.answers, [String(n)]: value } } : s));
  }, []);

  // Arrow keys move between problems; A-E mark (or clear) a bubble.
  useEffect(() => {
    if (!sitting) return undefined;
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;
      if (event.key === 'ArrowRight') setAt((n) => Math.min(problems.length, n + 1));
      if (event.key === 'ArrowLeft') setAt((n) => Math.max(1, n - 1));
      const p = problems[at - 1];
      const letter = event.key.toUpperCase();
      if (p?.choices && LETTERS.includes(letter) && !event.metaKey && !event.ctrlKey) {
        setAnswerFor(at, sitting.answers[String(at)] === letter ? '' : letter);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [at, problems, sitting, setAnswerFor]);

  if (loading && !data) return <Loading label="Setting out your paper" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load this contest.'} onRetry={reload} />;
  if (!data.problems.length) {
    return (
      <div className="amc-page">
        <p>This contest is not in Summit yet. <Link className="am-link" to={`/contests/${contestId}`}>Back</Link></p>
      </div>
    );
  }

  const c = data.contest;
  const aime = c.level === 'AIME';
  const back = c.kind === 'mock' ? '/mock-contests' : `/contests/${contestId}`;

  // The cover page: what the paper is, the rules, and one button.
  if (!sitting) {
    const scoring = aime ? '1 point each' : '6 · 1.5 · 0';
    return (
      <div className="amc-page">
        <section className="am-cover" aria-labelledby="cover-title">
          <p className="am-kicker">{c.level}{c.kind === 'past' ? ' · Official paper' : ' · Mock'}</p>
          <h1 id="cover-title">{c.name}</h1>
          <dl className="am-cover-facts">
            <div><dt>Problems</dt><dd>{problems.length}</dd></div>
            <div><dt>Minutes</dt><dd>{c.minutes}</dd></div>
            <div><dt>Scoring</dt><dd>{scoring}</dd></div>
          </dl>
          <ul className="am-cover-rules">
            <li>
              {aime
                ? 'Every answer is an integer from 000 to 999. A wrong answer costs nothing, so answer everything.'
                : '6 points for a right answer, 1.5 for a blank, 0 for a wrong one. A blank beats a guess you can’t narrow down.'}
            </li>
            <li>No calculator. Pencil, scratch paper, ruler and compass are fine.</li>
            <li>The clock pauses whenever you leave this window, and picks up when you come back.</li>
            <li>When time runs out, your sheet is handed in as it stands. Misses and blanks go to Review.</li>
          </ul>
          <div className="am-cover-actions">
            <button type="button" className="am-btn am-btn-primary am-cover-begin"
                    onClick={() => setSitting({ used: 0, answers: {}, flags: [] })}>
              Begin
            </button>
            <Link className="am-link" to={back}>Not now</Link>
          </div>
        </section>
      </div>
    );
  }

  const p = problems[at - 1];
  const answered = Object.values(sitting.answers).filter(Boolean).length;
  const flagged = sitting.flags.includes(at);
  const toggleFlag = () =>
    setSitting((s) => (s ? { ...s, flags: flagged ? s.flags.filter((n) => n !== at) : [...s.flags, at] } : s));

  const handIn = () => {
    const blank = problems.length - answered;
    const ask = blank
      ? `Hand in now? ${blank} problem${blank === 1 ? ' is' : 's are'} blank.`
      : 'Hand in your answers?';
    if (window.confirm(ask)) void submit();
  };
  const abandon = () => {
    if (!window.confirm('Leave this contest? Your answers will be discarded and nothing is graded.')) return;
    writeSitting(contestId, null);
    navigate(back);
  };

  return (
    <div className="amc-page">
      <div className="am-exam-top">
        <strong>{c.name}</strong>
        <span className={`am-exam-clock${left < 300 ? ' is-low' : ''}${active ? '' : ' is-paused'}`}
              aria-live="off" aria-label={active ? 'Time left' : 'Time left, paused'}>
          {clock(Math.max(0, left))}
          {!active && <small>Paused</small>}
        </span>
        <span className="am-muted" style={{ fontSize: 13 }}>{answered}/{problems.length} answered</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={abandon}>Leave</button>
          <button type="button" className="am-btn am-btn-primary am-btn-sm" disabled={busy} onClick={handIn}>
            Hand in
          </button>
        </div>
      </div>
      {message && <p className="am-error">{message}</p>}

      <div className="am-exam">
        <article className="am-card am-exam-paper">
          <p className="am-qnum">Problem {at} of {problems.length}</p>
          {p && (
            <>
              <MathText text={p.statement} as="p" className="am-statement" />
              {p.diagram && <DiagramNote diagram={p.diagram} href={p.aops_url} />}
              <AnswerInput choices={p.choices} value={sitting.answers[String(at)] ?? ''} onChange={(v) => setAnswerFor(at, v)} />
            </>
          )}
          <div className="am-nav-row">
            <button type="button" className="am-btn" disabled={at === 1} onClick={() => setAt(at - 1)}>← Previous</button>
            <span style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
              <button type="button" className={`am-btn${flagged ? ' am-btn-sage' : ''}`} onClick={toggleFlag}>
                {flagged ? 'Flagged' : 'Flag for later'}
              </button>
              {sitting.answers[String(at)] && (
                <button type="button" className="am-btn am-btn-ghost" onClick={() => setAnswerFor(at, '')}>Clear answer</button>
              )}
            </span>
            {at < problems.length ? (
              <button type="button" className="am-btn" onClick={() => setAt(at + 1)}>Next →</button>
            ) : (
              <button type="button" className="am-btn am-btn-primary" onClick={handIn}>Hand in</button>
            )}
          </div>
        </article>

        <aside className="am-card am-exam-side">
          <div className="am-card-head"><h2>Answer sheet</h2></div>
          <ol className="am-bubbles" aria-label="Answer sheet">
            {problems.map((q) => {
              const a = sitting.answers[String(q.number)] ?? '';
              const rowClass = `am-bubble-row${q.number === at ? ' is-current' : ''}${sitting.flags.includes(q.number) ? ' is-flagged' : ''}`;
              return (
                <li key={q.number} className={rowClass}>
                  <button type="button" className="am-bubble-num" onClick={() => setAt(q.number)}
                          aria-label={`Go to problem ${q.number}`}>
                    {q.number}
                  </button>
                  {q.choices ? (
                    LETTERS.map((letter) => (
                      <button key={letter} type="button"
                              className={`am-bubble${a === letter ? ' is-filled' : ''}`}
                              aria-pressed={a === letter}
                              aria-label={`Problem ${q.number}, answer ${letter}`}
                              onClick={() => { setAt(q.number); setAnswerFor(q.number, a === letter ? '' : letter); }}>
                        {letter}
                      </button>
                    ))
                  ) : (
                    <button type="button" className={`am-bubble-int${a ? ' is-filled' : ''}`} onClick={() => setAt(q.number)}
                            aria-label={`Problem ${q.number}${a ? `, answered ${a.padStart(3, '0')}` : ', blank'}`}>
                      {a ? a.padStart(3, '0') : '—'}
                    </button>
                  )}
                </li>
              );
            })}
          </ol>
          <p className="am-muted" style={{ fontSize: 12, lineHeight: 1.5, margin: '12px 0 0' }}>
            Fill a bubble to answer, click it again to erase. ← → move{p?.choices ? ', A–E answer' : ''}. Amber = flagged.
          </p>
        </aside>
      </div>
    </div>
  );
}
