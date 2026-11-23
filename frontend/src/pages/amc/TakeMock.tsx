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
 * Answers, flags and the time used are kept on the account (table
 * `amc_sittings`, PUT /api/amc/contests/:id/sitting), so a reload, an
 * accidental back or another device resumes the same sitting where its clock
 * left off; time with the page closed does not count either. An answer or a
 * flag is saved at once, the clock every few seconds and whenever it pauses.
 *
 * **Leaving asks first.** Mid-sitting, the Leave button, any link elsewhere in
 * the app and the browser's Back all ask before going, and say the sitting is
 * saved and resumes where it left off. Leave keeps the sitting; Discard is the
 * separate way to throw it away. (Closing the tab or reloading can't show a
 * custom question; the sitting is saved by then all the same, give or take
 * the last few seconds of clock.)
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useNotice, ErrorState, Loading } from '@/components';
import { MathText } from '@/components/Amc/MathText';
import { AnswerInput, DiagramNote, clock, useWindowActive, windowActive } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, announceAmcChanged, type SittingState } from '@/services/amc';
import '@/styles/amc.css';

type Sitting = Pick<SittingState, 'used' | 'answers' | 'flags'>;

const LETTERS = ['A', 'B', 'C', 'D', 'E'];
/** How often the clock is saved while it runs. Answers and flags save at once. */
export const SAVE_EVERY_MS = 10_000;

/**
 * A sitting this browser kept before sittings moved to the account. Read once
 * so a contest in progress during the upgrade is not lost, then removed.
 */
const legacyKey = (id: string) => `amc-mock:${id}`;

function takeLegacySitting(id: string): Sitting | null {
  try {
    const raw = localStorage.getItem(legacyKey(id));
    localStorage.removeItem(legacyKey(id));
    if (!raw) return null;
    const stored = JSON.parse(raw) as Partial<Sitting> & { started?: number };
    const used = typeof stored.used === 'number'
      ? stored.used
      : typeof stored.started === 'number' ? Math.max(0, (Date.now() - stored.started) / 1000) : 0;
    return { used, answers: stored.answers ?? {}, flags: stored.flags ?? [] };
  } catch {
    return null;
  }
}

export default function TakeMock() {
  const { contestId = '' } = useParams();
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi(() => amc.contest(contestId), [contestId]);

  const [sitting, setSitting] = useState<Sitting | null>(null);
  // Which contest's saved sitting has been read into `sitting`. Until then the
  // page waits, so a sitting in progress never flashes its cover page.
  const [hydratedFor, setHydratedFor] = useState('');
  useDocumentTitle(data ? `${data.contest.name}${sitting ? ' — in progress' : ''}` : 'Contest');
  const [at, setAt] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [saveError, setSaveError] = useState(false);
  const submitted = useRef(false);
  const { notify, confirm } = useNotice();
  const active = useWindowActive();
  const running = Boolean(sitting) && active;

  // Saving: the latest sitting, and the save in flight, so handing in or
  // leaving waits for it and a late save can't bring a finished sitting back.
  const latest = useRef<Sitting | null>(null);
  latest.current = sitting;
  const inFlight = useRef<Promise<unknown>>(Promise.resolve());
  const persist = useCallback(() => {
    const s = latest.current;
    if (!s || submitted.current) return inFlight.current;
    const body = { used: s.used, answers: s.answers, flags: s.flags };
    inFlight.current = inFlight.current
      .then(() => (submitted.current ? null : amc.saveSitting(contestId, body)))
      .then((reply) => { if (reply) setSaveError(!reply.success); }, () => setSaveError(true));
    return inFlight.current;
  }, [contestId]);

  useEffect(() => {
    if (!data || hydratedFor === contestId) return;
    const saved = data.sitting ?? null;
    const legacy = takeLegacySitting(contestId);
    const start = saved ?? legacy;
    setSitting(start ? { used: start.used, answers: start.answers, flags: start.flags } : null);
    setHydratedFor(contestId);
    if (!saved && legacy) void amc.saveSitting(contestId, legacy).catch(() => setSaveError(true));
  }, [contestId, data, hydratedFor]);

  // An answer or a flag is saved the moment it changes.
  const answersKey = sitting ? JSON.stringify([sitting.answers, sitting.flags]) : '';
  useEffect(() => {
    if (answersKey && hydratedFor === contestId) void persist();
  }, [answersKey, contestId, hydratedFor, persist]);
  // The clock: every few seconds while it runs, and as soon as it pauses.
  useEffect(() => {
    if (!running) return undefined;
    const id = window.setInterval(() => void persist(), SAVE_EVERY_MS);
    return () => {
      window.clearInterval(id);
      void persist();
    };
  }, [running, persist]);
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

  // The copy of this page that guards Back (see below). Handing in or
  // discarding takes it off first, so Back from the result skips the paper.
  const guarded = useRef(false);
  const dropGuard = useCallback(() => new Promise<void>((resolve) => {
    if (!guarded.current) { resolve(); return; }
    guarded.current = false;
    const done = () => { window.clearTimeout(timer); resolve(); };
    const timer = window.setTimeout(() => { window.removeEventListener('popstate', done); resolve(); }, 400);
    window.addEventListener('popstate', done, { once: true });
    window.history.back();
  }), []);

  const submit = useCallback(async () => {
    if (submitted.current || !sitting) return;
    submitted.current = true;
    setBusy(true);
    setMessage('');
    try {
      await inFlight.current;
      const reply = await amc.submit(contestId, sitting.answers, Math.min(elapsed, minutes * 60));
      if (reply.success) {
        await dropGuard();
        announceAmcChanged();
        notify('Handed in', { body: 'Your paper is graded. Misses and blanks are in Review.' });
        navigate(`/mocks/${reply.id}`, { replace: true });
      } else {
        submitted.current = false;
        setMessage(reply.message);
        notify('Could not hand it in', { body: reply.message, tone: 'bad' });
      }
    } catch (cause) {
      submitted.current = false;
      const why = cause instanceof Error ? cause.message : 'Could not hand it in. Try again.';
      setMessage(why);
      notify('Could not hand it in', { body: why, tone: 'bad' });
    } finally {
      setBusy(false);
    }
  }, [contestId, dropGuard, elapsed, minutes, navigate, notify, sitting]);

  // Time is up: hand it in as it stands.
  useEffect(() => {
    if (data && sitting && left <= 0 && !submitted.current) void submit();
  }, [data, sitting, left, submit]);

  const setAnswerFor = useCallback((n: number, value: string) => {
    setSitting((s) => (s ? { ...s, answers: { ...s.answers, [String(n)]: value } } : s));
  }, []);

  // Leaving mid-sitting asks first and says the sitting is kept. Going on
  // saves once more and replaces this page in history, so Back from wherever
  // the reader went returns to the paper rather than to the guard entry below.
  const askToLeave = useCallback(() => confirm({
    title: 'Leave this contest?',
    body: 'Your answers, flags and time so far are saved to your account. The clock stops while you’re away, '
      + 'and the paper picks up where you left off when you come back.',
    confirmLabel: 'Save and leave',
    cancelLabel: 'Keep working',
  }), [confirm]);
  const leaving = useRef(false);
  const leaveTo = useCallback(async (to: string) => {
    leaving.current = true;
    await persist();
    navigate(to, { replace: true });
  }, [navigate, persist]);

  const inSitting = Boolean(sitting);
  // A link anywhere else in the app (the sidebar, a header link) asks first.
  useEffect(() => {
    if (!inSitting) return undefined;
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || submitted.current || leaving.current) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = (event.target as Element | null)?.closest?.('a[href]');
      if (!(link instanceof HTMLAnchorElement) || link.hasAttribute('download')) return;
      if (link.target && link.target !== '_self') return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin || url.pathname === window.location.pathname) return;
      event.preventDefault();
      event.stopPropagation();
      void (async () => {
        if (await askToLeave()) await leaveTo(url.pathname + url.search + url.hash);
      })();
    };
    document.addEventListener('click', onClick, true);
    return () => document.removeEventListener('click', onClick, true);
  }, [inSitting, askToLeave, leaveTo]);

  // The browser's Back: a copy of this entry sits on top of the history, so
  // Back lands on the same page and can ask; staying puts the copy back.
  useEffect(() => {
    if (!inSitting) return undefined;
    if (!guarded.current) {
      window.history.pushState(window.history.state, '', window.location.href);
      guarded.current = true;
    }
    let asking = false;
    const onPop = () => {
      if (submitted.current || leaving.current || asking) return;
      asking = true;
      void (async () => {
        const yes = await askToLeave();
        asking = false;
        if (yes) {
          leaving.current = true;
          guarded.current = false;
          await persist();
          window.history.back();
        } else {
          window.history.pushState(window.history.state, '', window.location.href);
        }
      })();
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [inSitting, askToLeave, persist]);

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
  if (hydratedFor !== contestId) return <Loading label="Setting out your paper" />;
  if (!data.problems.length) {
    return (
      <div className="amc-page">
        <p>This contest is not in AMC Guide yet. <Link className="am-link" to={`/contests/${contestId}`}>Back</Link></p>
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

  const handIn = async () => {
    const blank = problems.length - answered;
    const yes = await confirm({
      title: 'Hand in your paper?',
      body: blank
        ? `${blank} problem${blank === 1 ? ' is' : 's are'} still blank. You can't change answers after this.`
        : "Every problem is answered. You can't change answers after this.",
      confirmLabel: 'Hand in',
      cancelLabel: 'Keep working',
    });
    if (yes) void submit();
  };
  const leave = async () => {
    if (await askToLeave()) await leaveTo(back);
  };
  const abandon = async () => {
    const yes = await confirm({
      title: 'Discard this sitting?',
      body: 'Your answers and time so far are thrown away and nothing is graded. This can’t be undone.',
      confirmLabel: 'Discard',
      cancelLabel: 'Keep working',
      danger: true,
    });
    if (!yes) return;
    submitted.current = true;
    try {
      await inFlight.current;
      const reply = await amc.discardSitting(contestId);
      if (!reply.success) throw new Error(reply.message);
    } catch (cause) {
      submitted.current = false;
      notify('Could not discard the contest', {
        body: cause instanceof Error ? cause.message : 'Try again.', tone: 'bad',
      });
      return;
    }
    leaving.current = true;
    await dropGuard();
    notify('Contest discarded', { tone: 'info' });
    navigate(back, { replace: true });
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
          <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={() => void abandon()}>Discard</button>
          <button type="button" className="am-btn am-btn-sm" onClick={() => void leave()}>Leave</button>
          <button type="button" className="am-btn am-btn-primary am-btn-sm" disabled={busy} onClick={() => void handIn()}>
            Hand in
          </button>
        </div>
      </div>
      {message && <p className="am-error">{message}</p>}
      {saveError && !message && (
        <p className="am-error" role="status">Not saved to your account yet. Your answers are kept on this page; check your connection.</p>
      )}

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
              <button type="button" className="am-btn am-btn-primary" onClick={() => void handIn()}>Hand in</button>
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
