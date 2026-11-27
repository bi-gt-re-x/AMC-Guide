/**
 * One problem: the statement, an answer sheet, a stopwatch, and — once
 * answered or revealed — the solution, the key insight and the trap.
 *
 * `?review=1` is a review session's problem (pages/amc/Review.tsx): the answer
 * is sent as a review, which is what moves it along the 3/10/21-day schedule.
 * `?weak=1` is one of the Review page's twelve weak-topic problems: always a
 * fresh try, with a button on to the next of the twelve. `?set=1` is one of a
 * topic's eight handpicked practice problems (pages/amc/PracticeSet.tsx): a
 * fresh try too, with the set's clock, and the topic hidden on a mixed set.
 *
 * Each of the three is a set stored on the account (POST /api/amc/sets) once
 * it is started: every answer in it carries the set's id, and finishing it
 * (its last problem, or a practice set's clock) closes the set and opens its
 * report, which says what was right and what was missed in that set.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useNotice, ErrorState, Loading } from '@/components';
import { AIHelp } from '@/components/Amc/AIHelp';
import { MathText } from '@/components/Amc/MathText';
import {
  AnswerInput,
  clock,
  DiagramNote,
  Difficulty,
  ProblemRow,
  problemHref,
  ratingText,
  Solution,
  StatusPill,
  useStopwatch,
} from '@/components/Amc/bits';
import { useApi, useDocumentTitle, usePageSwap } from '@/hooks';
import { amc, announceAmcChanged, shortDate, type AttemptReply, type Problem as ProblemData } from '@/services/amc';
import { activePracticeSet, practiceSetHome, readPracticeSet, updatePracticeSet } from './practiceSetStore';
import { readWeakRun, readWeakSet, setWeakRun } from './weakSet';
import { readReviewRun, readReviewSet, setReviewRun } from './reviewSet';
import { clearDrafts, readDraft, setKey, writeDraft } from './setDrafts';
import '@/styles/amc.css';

const STAGES = 3;

export function ReviewStage({ stage }: { stage: number }) {
  return (
    <span className="am-stage" title={`Stage ${Math.min(stage, STAGES)} of ${STAGES}`}>
      {Array.from({ length: STAGES }, (_, i) => <i key={i} className={i < stage ? 'on' : ''} />)}
    </span>
  );
}

/** The query parameters that pick a mode rather than a list to walk. */
const WALK_IGNORES = new Set(['review', 'weak', 'set']);

/** Previous and Next inside a practice set or the weak-topics set, never out of it. */
function SetSteps({ prev, next, flag, onGo }: {
  prev?: string; next?: string; flag: string; onGo: (to: string) => void;
}) {
  if (!prev && !next) return null;
  return (
    <div className="am-nav-row">
      {prev ? (
        <button type="button" className="am-btn" onClick={() => onGo(`/problems/${prev}?${flag}`)}>← Previous</button>
      ) : <span />}
      {next && <button type="button" className="am-btn" onClick={() => onGo(`/problems/${next}?${flag}`)}>Skip →</button>}
    </div>
  );
}

export default function Problem() {
  const { problemId = '' } = useParams();
  const [params] = useSearchParams();
  const reviewing = params.get('review') === '1';
  const weak = !reviewing && params.get('weak') === '1';
  const weakSet = weak ? readWeakSet() : [];
  const weakAt = weakSet.indexOf(problemId);
  const weakNext = weakAt >= 0 ? weakSet[weakAt + 1] : undefined;
  const reviewSet = reviewing ? readReviewSet() : [];
  const reviewAt = reviewSet.indexOf(problemId);
  const reviewNext = reviewAt >= 0 ? reviewSet[reviewAt + 1] : undefined;
  const inSet = !reviewing && !weak && params.get('set') === '1';
  const practiceSet = inSet ? readPracticeSet() : null;
  const setIds = practiceSet?.ids ?? [];
  const setAt = setIds.indexOf(problemId);
  const setNext = setAt >= 0 ? setIds[setAt + 1] : undefined;
  const setHome = practiceSet ? practiceSetHome(practiceSet) : '/topics';
  // The set this problem is being walked in, if any: its stored id (what its
  // answers are saved under on the account) and the key its unchecked picks
  // are kept under in this tab (pages/amc/setDrafts.ts). Read on every render,
  // since a set's stored id can arrive with its first answer.
  const walking = inSet && setAt >= 0 ? { kind: 'practice', run: practiceSet?.runId ?? null, ids: setIds }
    : reviewing && reviewAt >= 0 ? { kind: 'review', run: readReviewRun(), ids: reviewSet }
      : weak && weakAt >= 0 ? { kind: 'weak', run: readWeakRun(), ids: weakSet } : null;
  const draftKey = walking ? setKey(walking.kind, walking.run, walking.ids) : null;
  /** The set is over: what was picked in it goes too. */
  const endDrafts = () => {
    if (walking) clearDrafts(setKey(walking.kind, walking.run, walking.ids), setKey(walking.kind, null, walking.ids));
  };
  // Previous and Next walk the list the problem was opened from, and only
  // that list: a topic (`?topic=`), the Problems page's filters (`?list=1&…`),
  // or, opened from neither, the problem's own paper. The walk's parameters
  // ride along on every step so the next problem walks the same list.
  const walk: Record<string, string> = {};
  params.forEach((value, key) => {
    if (!WALK_IGNORES.has(key)) walk[key] = value;
  });
  const walkQuery = new URLSearchParams(walk).toString();
  const walkHref = (id: string) => `/problems/${id}${walkQuery ? `?${walkQuery}` : ''}`;
  // Inside a practice set or the weak-topics set, Previous and Next step
  // through that set's problems instead.
  const setPrev = setAt > 0 ? setIds[setAt - 1] : undefined;
  const weakPrev = weakAt > 0 ? weakSet[weakAt - 1] : undefined;
  const navigate = useNavigate();
  const { data, error, loading, refreshing, reload } = useApi(() => amc.problem(problemId, walk), [problemId, walkQuery]);
  // One problem to the next: the last one dims, then this one arrives (hooks/usePageSwap).
  const swap = usePageSwap(problemId, loading || refreshing);
  const { notify, confirm } = useNotice();
  useDocumentTitle(data ? data.problem.sources[0] ? `${data.problem.sources[0].name} #${data.problem.sources[0].number}` : 'Problem' : 'Problem');

  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<AttemptReply | null>(null);
  const [revealed, setRevealed] = useState<ProblemData | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [retry, setRetry] = useState(false);
  const [note, setNote] = useState('');
  const [noteSaved, setNoteSaved] = useState(false);

  // A fresh slate per problem: blank, or inside a set, the answer picked on
  // it and not yet checked (kept through a refresh).
  useEffect(() => {
    setAnswer(draftKey ? readDraft(draftKey, problemId) : '');
    setResult(null);
    setRevealed(null);
    setMessage('');
    setRetry(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- per problem
  }, [problemId]);
  // Inside a set, a problem already answered in it shows that answer again,
  // as it was when checked: after a refresh, or on going back to it. The
  // answer is the account's own record (the attempt stored with the set's
  // id), not this tab's. A new set, or the problem opened on its own, starts fresh.
  const fresh = data && data.problem.id === problemId ? data : null;
  const inRun = walking?.run && fresh
    ? [...fresh.attempts].reverse().find((a) => a.set_id === walking.run)
    : undefined;
  useEffect(() => {
    if (!fresh || !inRun || result || revealed) return;
    if (inRun.source === 'reveal') {
      setRevealed(fresh.problem);
      return;
    }
    const review = fresh.review
      ? { stage: fresh.review.stage, due: fresh.review.due, status: fresh.review.review_status }
      : null;
    setResult({
      correct: inRun.correct, given: inRun.answer, problem: fresh.problem, review,
      moved: inRun.source === 'review' && review != null, set_id: inRun.set_id, seconds: inRun.seconds,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- when the problem's record arrives
  }, [fresh, inRun?.at]);
  useEffect(() => {
    setNote(data?.review?.note ?? '');
  }, [data?.review?.note]);

  const answered = Boolean(result || revealed);
  // A problem answered before shows its solution, unless the reader asks to
  // try it again (or it is a review, which is always a fresh try).
  const seenBefore = Boolean(data?.attempts.length) && !reviewing && !weak && !inSet && !retry && !answered;
  const locked = answered || seenBefore;
  // A review (or a weak-topic set, or "Try it again") is a fresh try: until it
  // is answered, the attempts list says only whether each try was right, never
  // which answer was given, so neither the old wrong answer nor the key shows.
  const freshTry = !answered && (reviewing || weak || retry || inSet);
  // A mixed set is practice in recognising the topic: its name waits until answered.
  const hideTopic = Boolean(practiceSet?.hideTopic) && !answered;
  const [seconds, setSeconds] = useStopwatch(!locked && !loading);
  useEffect(() => setSeconds(0), [problemId, retry, setSeconds]);
  // A timed or challenge set runs on one clock for the whole set: when it is
  // out, the set is over, answered or not, and its page says so.
  const setLeft = useCountdown(inSet ? practiceSet?.deadline ?? null : null);
  const timeUp = setLeft === 0;
  useEffect(() => {
    if (!timeUp) return;
    void finishPracticeSet(true).then((run) => {
      navigate(`${setHome}&done=1&timeup=1${run ? `&run=${run}` : ''}`, { replace: true });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- once, when the clock runs out
  }, [timeUp]);
  // The set remembers which problem it is on, so it can be picked up again.
  useEffect(() => {
    if (inSet && setAt >= 0) updatePracticeSet({ current: problemId });
  }, [inSet, setAt, problemId]);
  useLeaveSetGuard(inSet && setAt >= 0, confirm, navigate);

  /**
   * The stored set this problem is answered in: the practice set, review set
   * or weak-topics set being walked, recorded on the account the first time
   * it is needed (a set started before sets were stored, or whose start could
   * not be saved). '' outside a set, or when it cannot be recorded: the answer
   * still counts, just not in a set.
   */
  async function setRun(): Promise<string> {
    if (inSet && setAt >= 0 && practiceSet) {
      const known = readPracticeSet()?.runId;
      if (known) return known;
      const id = await amc.recordSet({
        kind: 'practice', topic: practiceSet.topic, mode: practiceSet.mode, title: practiceSet.title,
        problems: setIds,
        seconds: practiceSet.deadline != null && practiceSet.seconds ? practiceSet.seconds * setIds.length : null,
      });
      if (id) updatePracticeSet({ runId: id });
      return id ?? '';
    }
    if (reviewing && reviewAt >= 0) {
      const known = readReviewRun();
      if (known) return known;
      const id = await amc.recordSet({ kind: 'review', problems: reviewSet });
      if (id) setReviewRun(id);
      return id ?? '';
    }
    if (weak && weakAt >= 0) {
      const known = readWeakRun();
      if (known) return known;
      const id = await amc.recordSet({ kind: 'weak', problems: weakSet });
      if (id) setWeakRun(id);
      return id ?? '';
    }
    return '';
  }

  /** Close the practice set on the account (its last problem, or its clock) and say which it was. */
  async function finishPracticeSet(timeIsUp: boolean): Promise<string> {
    const run = await setRun();
    if (run) await amc.closeSet(run, timeIsUp);
    updatePracticeSet({ finished: true });
    endDrafts();
    announceAmcChanged();
    return run;
  }

  if (loading && !data) return <Loading label="Loading problem" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load this problem.'} onRetry={reload} />;

  const p = result?.problem ?? revealed ?? data.problem;
  const source = p.sources[0];

  async function submit() {
    if (!answer || busy) return;
    setBusy(true);
    setMessage('');
    try {
      const run = await setRun();
      const reply = await amc.attempt(problemId, answer, seconds, reviewing ? 'review' : 'practice', run);
      if (reply.success) {
        if (draftKey) writeDraft(draftKey, problemId, '');
        setResult({ ...reply, seconds });
        markAnswered();
        announceAmcChanged();
        reload();
      } else {
        setMessage(reply.message);
      }
    } finally {
      setBusy(false);
    }
  }

  /** This problem, counted as done in the set being walked. */
  function markAnswered() {
    if (!inSet || setAt < 0) return;
    const answeredSoFar = readPracticeSet()?.answered ?? [];
    if (!answeredSoFar.includes(problemId)) updatePracticeSet({ answered: [...answeredSoFar, problemId] });
  }

  async function reveal() {
    setBusy(true);
    try {
      const run = await setRun();
      const reply = await amc.reveal(problemId, run);
      if (reply.success) {
        if (draftKey) writeDraft(draftKey, problemId, '');
        setRevealed(reply.problem);
        markAnswered();
        announceAmcChanged();
        reload();
      }
    } finally {
      setBusy(false);
    }
  }

  /** The next problem in this review set, or the set's report once it is done.
   *  Outside a set (storage blocked, an old link), the next problem due. */
  async function nextDue() {
    if (reviewAt >= 0) {
      if (reviewNext) {
        navigate(`/problems/${reviewNext}?review=1`);
        return;
      }
      const run = readReviewRun();
      if (run) await amc.closeSet(run);
      endDrafts();
      setReviewRun(null);
      announceAmcChanged();
      navigate(`/review?done=1${run ? `&run=${run}` : ''}`);
      return;
    }
    const queue = await amc.review();
    const next = queue.success ? queue.due.find((item) => item.id !== problemId) : undefined;
    navigate(next ? `/problems/${next.id}?review=1` : '/review');
  }

  async function toggleReview() {
    const removing = data?.review?.review_status === 'active';
    const reply = removing ? await amc.removeReview(problemId) : await amc.addReview(problemId);
    if (!reply.success) {
      notify('Could not update Review', { body: reply.message, tone: 'bad' });
      return;
    }
    announceAmcChanged();
    notify(removing ? 'Removed from Review' : 'Added to Review',
           removing ? { tone: 'info' } : { body: 'It comes back on the review schedule.' });
    reload();
  }

  /** "Too challenging?": on hold in the review log until the level nears it
   *  (backend/amc/reach.py). Asked first, since it takes it off the schedule. */
  async function parkReview() {
    const at = data?.reach;
    if (!at || at.returns_at == null) return;
    // Where confirming goes on to (skipAhead): said in the question, so the move is no surprise.
    const onward = (inSet && setAt >= 0 && !setNext) || (weak && weakAt >= 0 && !weakNext)
      ? ' This was the last one, so the set finishes.'
      : (inSet && setAt >= 0) || (weak && weakAt >= 0) || reviewing || data?.next
        ? " You'll go straight on to the next problem."
        : '';
    const yes = await confirm({
      title: 'Put this problem on hold?',
      body: `It's rated ${ratingText(at.rating ?? 0)} and your level here is about ${at.level}. It stays in your `
        + `review log but won't come due until your level reaches about ${at.returns_at}. Then it comes back on its own.`
        + onward,
      confirmLabel: 'Put on hold',
      cancelLabel: 'Keep it',
    });
    if (!yes) return;
    const reply = await amc.parkReview(problemId);
    if (!reply.success) {
      notify('Could not put it on hold', { body: reply.message, tone: 'bad' });
      reload();
      return;
    }
    announceAmcChanged();
    notify('On hold', { body: `It comes back when your level reaches about ${at.returns_at}.`, tone: 'info' });
    await skipAhead();
  }

  /** The practice set's next problem, or, after its last, the set finished and its report. */
  async function nextInPracticeSet() {
    if (setNext) {
      navigate(`/problems/${setNext}?set=1`);
      return;
    }
    setBusy(true);
    const run = await finishPracticeSet(false);
    setBusy(false);
    navigate(`${setHome}&done=1${run ? `&run=${run}` : ''}`);
  }

  /** The weak-topics set's next problem, or, after its last, the set closed and its report. */
  async function nextInWeakSet() {
    if (weakNext) {
      navigate(`/problems/${weakNext}?weak=1`);
      return;
    }
    const run = weakAt >= 0 ? readWeakRun() : null;
    setBusy(true);
    if (run) await amc.closeSet(run);
    endDrafts();
    setWeakRun(null);
    setBusy(false);
    announceAmcChanged();
    navigate(`/review?done=1${run ? `&run=${run}` : ''}`);
  }

  /**
   * On past a problem put on hold: wherever "Next" goes from here. The next in
   * the set being walked (or, after its last, the set's report, as finishing
   * it would), the next due review, or the next problem in the list it was
   * opened from. With nowhere to go (a problem opened on its own), it stays,
   * showing that it is on hold.
   */
  async function skipAhead() {
    if (inSet && setAt >= 0) return nextInPracticeSet();
    if (weak && weakAt >= 0) return nextInWeakSet();
    if (reviewing) return nextDue();
    if (data?.next) {
      navigate(walkHref(data.next));
      return undefined;
    }
    reload();
    return undefined;
  }

  async function saveNote() {
    const reply = await amc.noteReview(problemId, note);
    if (reply.success) {
      setNoteSaved(true);
      window.setTimeout(() => setNoteSaved(false), 1600);
    } else {
      notify('Could not save the note', { body: reply.message, tone: 'bad' });
    }
  }

  const last = data.attempts[data.attempts.length - 1];
  const given = result?.given ?? (seenBefore ? last?.answer : undefined);
  const showKey = result != null || revealed != null || seenBefore;

  return (
    <div className={`amc-page ${swap}`.trim()}>
      <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {inSet ? (
          <Link to={setHome} className="am-link">← {practiceSet?.title ?? 'Practice set'}</Link>
        ) : (
          <Link to={reviewing || weak ? '/review' : '/problems'} className="am-link">
            {reviewing || weak ? '← Review' : '← Problems'}
          </Link>
        )}
        {!hideTopic && (
          <>
            <span>/</span>
            <Link to={`/topics/${p.topic}`} className="am-link">{p.topic_name}</Link>
          </>
        )}
        {inSet && setAt >= 0 && <span>· {setAt + 1} of {setIds.length}</span>}
        {setLeft !== null && (
          <span className={`am-set-clock${setLeft <= 60 ? ' is-low' : ''}`} role="timer" aria-label="Time left for the set">
            {clock(setLeft)} left
          </span>
        )}
        {reviewing && reviewAt >= 0 && <span>· Review set, {reviewAt + 1} of {reviewSet.length}</span>}
      </nav>

      <div className="am-grid am-grid-main pg-stagger">
        <div className="am-stack">
          <article className="am-card" style={{ padding: 28 }}>
            <div className="am-problem-meta">
              <span className="am-tag">{source ? `${source.name} #${source.number}` : p.ai ? p.level : `${p.level} drill`}</span>
              {!hideTopic && <Link className="am-tag" to={`/topics/${p.topic}`}>{p.topic_name}</Link>}
              {!hideTopic && p.also.map((t) => <Link key={t.id} className="am-tag" to={`/topics/${t.id}`}>{t.name}</Link>)}
              <span className="am-tag"><Difficulty value={p.difficulty} rating={p.rating} /></span>
              {p.official && <span className="am-tag">Official</span>}
              {p.ai && <span className="am-tag" title="Written by the AI; kept because an independent second solve agreed">AI practice</span>}
              <StatusPill status={data.status} />
            </div>

            <MathText text={p.statement} as="p" className="am-statement" />
            {p.diagram && <DiagramNote diagram={p.diagram} href={p.aops_url} />}

            <AnswerInput
              choices={p.choices}
              value={showKey && !answer ? given ?? '' : answer}
              onChange={(value) => {
                setAnswer(value);
                if (draftKey && !locked) writeDraft(draftKey, problemId, value);
              }}
              locked={locked}
              correct={showKey ? p.answer : undefined}
              given={showKey ? given : undefined}
              onSubmit={() => void submit()}
              autoFocus
            />

            {!locked && (
              <div className="am-answer-bar">
                {setLeft !== null ? (
                  <span className="am-timer" aria-label="Time left for the set, and time on this problem">
                    <strong className={`am-set-clock${setLeft <= 60 ? ' is-low' : ''}`}>{clock(setLeft)}</strong> left for the set
                    <span className={`am-pace${seconds > (practiceSet?.seconds ?? Infinity) ? ' is-over' : ''}`}> · {clock(seconds)} on this one</span>
                  </span>
                ) : practiceSet?.seconds ? (
                  <span className={`am-timer${seconds > practiceSet.seconds ? ' is-over' : ''}`}
                        aria-label="Time on this problem, against the set's pace">
                    {clock(seconds)} / {clock(practiceSet.seconds)}
                  </span>
                ) : (
                  <span className="am-timer" aria-label="Time on this problem">{clock(seconds)}</span>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="am-btn am-btn-ghost" disabled={busy} onClick={() => void reveal()}>
                    {p.official && !p.has_solution ? 'Show answer' : 'Show solution'}
                  </button>
                  <button type="button" className="am-btn am-btn-primary" disabled={!answer || busy}
                          onClick={() => void submit()}>
                    Check answer
                  </button>
                </div>
              </div>
            )}
            {message && <p className="am-error">{message}</p>}

            {result && (
              <div className={`am-verdict ${result.correct ? 'is-right' : 'is-wrong'}`} role="status">
                {result.correct ? 'Correct.' : 'Not quite.'}
                <span>
                  {result.correct
                    ? result.moved && result.review
                      ? result.review.status === 'mastered'
                        ? 'Mastered. It leaves your review log.'
                        : `Next review ${shortDate(result.review.due)}.`
                      : `Solved in ${clock(result.seconds ?? seconds)}.`
                    : `The answer is ${p.format === 'choice' ? `(${p.answer})` : p.answer}. ${result.review?.status === 'parked'
                      ? "It stays on hold until you're closer to its level."
                      : `You'll see it again ${result.review ? shortDate(result.review.due) : 'later'}.`}`}
                </span>
              </div>
            )}
            {revealed && (
              <div className="am-verdict is-wrong" role="status">
                Revealed. <span>Counts as a miss. Back in 3 days.</span>
              </div>
            )}
            {seenBefore && last && (
              <div className={`am-verdict ${last.correct ? 'is-right' : 'is-wrong'}`}>
                {last.correct ? 'You solved this.' : 'You missed this last time.'}
                <span>
                  <button type="button" className="am-btn am-btn-sm" onClick={() => setRetry(true)}>
                    Try it again
                  </button>
                </span>
              </div>
            )}

            {/* Keyed to the problem: its hints and explanation belong to this one only. */}
            <AIHelp key={problemId} problemId={problemId} answered={Boolean(result || revealed || seenBefore)}
                    wrong={Boolean((result && !result.correct) || (seenBefore && last && !last.correct))} />

            {(result || revealed || seenBefore) && (
              p.official && !p.solution?.length ? (
                <p className="am-muted" style={{ margin: '16px 0 0', fontSize: 13, lineHeight: 1.6 }}>
                  Official problem: no AMC Guide write-up yet.{' '}
                  {p.aops_url && <a className="am-link" href={p.aops_url} target="_blank" rel="noreferrer">Solutions on AoPS ↗</a>}
                </p>
              ) : (
                <Solution solution={p.solution} insight={p.insight} trap={p.trap} />
              )
            )}

            {inSet && answered && (
              <div className="am-nav-row">
                <span className="am-muted" style={{ fontSize: 13 }}>
                  {practiceSet?.title ?? 'Practice set'}{setAt >= 0 ? ` · ${setAt + 1} of ${setIds.length}` : ''}
                </span>
                <button type="button" className="am-btn am-btn-primary" disabled={busy}
                        onClick={() => void nextInPracticeSet()}>
                  {setNext ? 'Next problem →' : 'Finish the set'}
                </button>
              </div>
            )}

            {weak && answered && (
              <div className="am-nav-row">
                <span className="am-muted" style={{ fontSize: 13 }}>
                  {weakAt >= 0 ? `Weak topics · ${weakAt + 1} of ${weakSet.length}` : 'Weak topics'}
                </span>
                <button type="button" className="am-btn am-btn-primary" disabled={busy}
                        onClick={() => void nextInWeakSet()}>
                  {weakNext ? 'Next weak-topic problem →' : 'Finish the set'}
                </button>
              </div>
            )}

            {reviewing && answered && (
              <div className="am-nav-row">
                <span className="am-muted" style={{ fontSize: 13 }}>
                  {reviewAt >= 0 ? `Review set · ${reviewAt + 1} of ${reviewSet.length}` : ''}
                </span>
                <button type="button" className="am-btn am-btn-primary" onClick={() => void nextDue()}>
                  {reviewAt < 0 ? 'Next due review →' : reviewNext ? 'Next in the set →' : 'Finish the set'}
                </button>
              </div>
            )}

            {inSet || weak ? (
              <SetSteps
                prev={inSet ? setPrev : weakPrev}
                next={inSet ? setNext : weakNext}
                flag={inSet ? 'set=1' : 'weak=1'}
                onGo={navigate}
              />
            ) : !reviewing && (
              <div className="am-nav-row">
                {data.prev ? (
                  <button type="button" className="am-btn" onClick={() => navigate(walkHref(data.prev!))}>← Previous</button>
                ) : <span />}
                {data.position && (
                  <span className="am-muted" style={{ fontSize: 13 }}>{data.position.at} of {data.position.of} in this list</span>
                )}
                {data.next && (
                  <button type="button" className="am-btn" onClick={() => navigate(walkHref(data.next!))}>Next →</button>
                )}
              </div>
            )}
          </article>
        </div>

        <aside className="am-stack">
          <section className="am-card">
            <div className="am-card-head">
              <h2>Details</h2>
              {/* Offered on any problem not already on hold or mastered: the student says when it is too hard. */}
              {data.reach && data.review?.review_status !== 'parked' && data.review?.review_status !== 'mastered' && (
                <button type="button" className="am-btn am-btn-alarm am-btn-sm" onClick={() => void parkReview()}
                        title={`Rated ${data.reach.rating} against your level of about ${data.reach.level}`}>
                  Too challenging?
                </button>
              )}
            </div>
            <dl className="am-kv">
              <dt>Contest</dt><dd>{p.level}</dd>
              {/* A mixed set is practice in recognising what a problem needs: its
                  category and technique wait, with its topic, until it is answered. */}
              {hideTopic ? (
                <><dt>Topic</dt><dd className="am-muted">Hidden until you answer</dd></>
              ) : (
                <>
                  <dt>Category</dt><dd>{p.category_name}</dd>
                  <dt>Technique</dt><dd><Link className="am-link" to={`/problems?technique=${p.technique}`}>{p.technique_name}</Link></dd>
                </>
              )}
              <dt>Rating</dt>
              <dd title="The AoPS rating times 2: an AMC 10 #1 is a 2 and the hardest AIME problem a 12">
                {p.rating != null ? ratingText(p.rating) : '—'}
                {p.aops != null && <span className="am-muted"> · AoPS {p.aops}</span>}
              </dd>
              {p.aops_url && (
                <><dt>Solutions</dt><dd><a className="am-link" href={p.aops_url} target="_blank" rel="noreferrer">AoPS wiki ↗</a></dd></>
              )}
              {p.sources.map((s) => (
                <span key={s.contest} style={{ display: 'contents' }}>
                  <dt>Appears in</dt>
                  <dd><Link className="am-link" to={`/contests/${s.contest}`}>{s.name} #{s.number}</Link></dd>
                </span>
              ))}
            </dl>
          </section>

          <section className="am-card">
            <div className="am-card-head">
              <h2>Review log</h2>
              {data.review && <ReviewStage stage={data.review.stage} />}
            </div>
            {data.review ? (
              <>
                <p className="am-muted" style={{ margin: '0 0 12px', fontSize: 13, lineHeight: 1.5 }}>
                  {data.review.review_status === 'mastered'
                    ? 'Mastered.'
                    : data.review.review_status === 'parked'
                      ? `On hold: too challenging for now. It comes back when your level here reaches about ${data.reach.returns_at} (now ${data.reach.level}).`
                      : `Stage ${data.review.stage} of 3 · next ${shortDate(data.review.due)} · missed ${data.review.misses}×`}
                </p>
                <div className="am-note-box">
                  <textarea className="am-input" placeholder="Why did you miss it?"
                            value={note} onChange={(e) => setNote(e.target.value)} aria-label="Review note" />
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={() => void toggleReview()}>
                      {data.review.review_status === 'active' ? 'Remove from log' : data.review.review_status === 'parked' ? 'Bring it back now' : 'Review again'}
                    </button>
                    <button type="button" className="am-btn am-btn-sm" onClick={() => void saveNote()}>
                      {noteSaved ? 'Saved' : 'Save note'}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <p className="am-muted" style={{ margin: '0 0 12px', fontSize: 13, lineHeight: 1.5 }}>
                  Misses are added on their own.
                </p>
                <button type="button" className="am-btn am-btn-sm" onClick={() => void toggleReview()}>
                  Add to review
                </button>
              </>
            )}
          </section>

          {data.attempts.length > 0 && (
            <section className="am-card">
              <div className="am-card-head"><h2>Your attempts</h2></div>
              <ul className="am-list">
                {data.attempts.slice(-6).reverse().map((a, i) => (
                  <li key={i}>
                    <span>{shortDate(a.at)} · {a.source}</span>
                    <span className={a.correct ? '' : 'am-muted'} style={{ color: a.correct ? 'var(--am-good)' : undefined }}>
                      {a.source === 'reveal'
                        ? 'revealed'
                        : freshTry
                          ? (a.correct ? 'right' : 'missed')
                          : `${a.answer || '—'} ${a.correct ? '✓' : '✗'}`}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {data.related.length > 0 && !hideTopic && (
            <section>
              <h2 className="am-h2" style={{ marginBottom: 10 }}>Same topic</h2>
              <div className="am-rows">
                {data.related.map((r) => <ProblemRow key={r.id} problem={r} to={problemHref(r.id, data.problem.topic)} />)}
              </div>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}


/** Whole seconds until `deadline` (ms since the epoch), ticking each second; null without one. */
function useCountdown(deadline: number | null): number | null {
  const left = () => (deadline == null ? null : Math.max(0, Math.ceil((deadline - Date.now()) / 1000)));
  const [value, setValue] = useState(left);
  useEffect(() => {
    setValue(left());
    if (deadline == null) return undefined;
    const id = window.setInterval(() => setValue(left()), 1000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deadline]);
  return value;
}

/**
 * Leaving a set part way asks first. Any link out of it (its own page, the
 * sidebar, search) is caught before it is followed: staying is the default,
 * and leaving keeps the set where it was, to be continued from its page.
 * Moving on to the set's next problem (`?set=1`) is not leaving. Closing the
 * tab on a timed set gets the browser's own warning, since its clock keeps
 * running.
 */
function useLeaveSetGuard(
  on: boolean,
  confirm: (options: { title: string; body?: string; confirmLabel?: string; cancelLabel?: string }) => Promise<boolean>,
  navigate: (to: string) => void,
) {
  useEffect(() => {
    if (!on) return undefined;
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = (event.target as Element | null)?.closest?.('a[href]') as HTMLAnchorElement | null;
      if (!link || link.target === '_blank') return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin) return;
      if (url.pathname.startsWith('/problems/') && url.searchParams.get('set') === '1') return;
      const set = activePracticeSet();
      if (!set) return;
      event.preventDefault();
      event.stopPropagation();
      const done = set.answered?.length ?? 0;
      const left = set.deadline != null ? Math.max(0, Math.ceil((set.deadline - Date.now()) / 1000)) : null;
      void confirm({
        title: 'Leave this set?',
        body: `${done} of ${set.ids.length} answered.${left != null ? ` ${clock(left)} left, and the clock keeps running.` : ''} You can continue it from the set's page.`,
        confirmLabel: 'Leave set',
        cancelLabel: 'Keep going',
      }).then((leave) => {
        if (leave) navigate(url.pathname + url.search + url.hash);
      });
    };
    const onUnload = (event: BeforeUnloadEvent) => {
      if (activePracticeSet()?.deadline != null) event.preventDefault();
    };
    document.addEventListener('click', onClick, true);
    window.addEventListener('beforeunload', onUnload);
    return () => {
      document.removeEventListener('click', onClick, true);
      window.removeEventListener('beforeunload', onUnload);
    };
  }, [on, confirm, navigate]);
}
