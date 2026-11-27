/**
 * A topic's practice set: eight problems handpicked from that one topic for a
 * way of training it (backend/amc/practice.py) — learn the ideas, an accuracy
 * drill, a timed set, a mixed set with the topic hidden, spaced review, or a
 * plain practice set at the topic's difficulty mix, or a challenge set of
 * harder ones. The mode the student's data suggests is marked. `?n=` is the
 * size the study plan asked for today. Starting walks the set on the problem
 * page (`?set=1`); a timed or challenge set starts its clock then, the whole
 * set's time, and ends when it runs out. Finishing comes back here with how
 * it went (`?done=1&run=<id>`, and `&timeup=1` if the clock ended it).
 *
 * Starting records the set on the account as dealt (POST /api/amc/sets), and
 * how it went is that stored set's report (components/Amc/SetReport.tsx):
 * these problems and the answers given in this set, not the set the picker
 * would deal now (it deals others once these are answered) nor any problem's
 * lifetime status. A set in progress lists the problems it was dealt, too.
 */
import { useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ErrorState, Loading, useNotice } from '@/components';
import { CategoryDot, clock, PageHeader, StatusPill } from '@/components/Amc/bits';
import { SetReport } from '@/components/Amc/SetReport';
import { MixBar } from '@/components/Amc/Study';
import { useApi, useDocumentTitle, usePageSwap } from '@/hooks';
import { amc, type SetResult } from '@/services/amc';
import { activePracticeSet, writePracticeSet } from './practiceSetStore';
import '@/styles/amc.css';

export default function PracticeSet() {
  const { topicId = '' } = useParams();
  const [params, setParams] = useSearchParams();
  const mode = params.get('mode') || 'practice';
  const done = params.get('done') === '1';
  const timeUp = done && params.get('timeup') === '1';
  const size = Number(params.get('n')) || null;
  const navigate = useNavigate();
  const { confirm } = useNotice();
  const { data, error, loading, refreshing, reload } = useApi(() => amc.topicSet(topicId, mode, size), [topicId, mode, size]);
  const swap = usePageSwap(`${topicId}|${mode}|${size}`, loading || refreshing);
  // This set, left part way (and not just finished): offered to be continued.
  const open = done ? null : activePracticeSet();
  const going = open && open.topic === topicId && open.mode === mode ? open : null;
  // The stored set: the one just finished, or the one in progress.
  const runId = done ? params.get('run') : going?.runId ?? null;
  const stored = useApi(() => amc.setReport(runId ?? ''), [runId], { enabled: Boolean(runId) });
  const report = runId && stored.data?.report.id === runId ? stored.data.report : null;
  const [starting, setStarting] = useState(false);
  // A mixed set keeps its topic out of sight, the tab's title included.
  useDocumentTitle(data ? (data.hide_topic ? data.title : `${data.topic.name} · ${data.title}`) : 'Practice set');

  if (loading && !data) return <Loading label="Picking eight problems" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not pick a set.'} onRetry={reload} />;

  const answeredIds = new Set(going?.answered ?? []);
  // How each dealt problem went in this set, once there is a stored set to say.
  const results = new Map<string, SetResult>((report?.problems ?? []).map((r) => [r.id, r.result]));
  const left = going?.deadline != null ? Math.max(0, Math.ceil((going.deadline - Date.now()) / 1000)) : null;

  /** Back to the problem the set was left on (or the first not yet answered). */
  function resume() {
    if (!going) return;
    const at = going.current && going.ids.includes(going.current) && !answeredIds.has(going.current)
      ? going.current : going.ids.find((id) => !answeredIds.has(id)) ?? going.current ?? going.ids[0];
    if (at) navigate(`/problems/${at}?set=1`);
  }

  async function startOver() {
    const yes = await confirm({
      title: 'Start this set again?',
      body: `You have answered ${answeredIds.size} of ${going?.ids.length ?? 0}.${left != null ? ' The clock starts again from full.' : ''}`,
      confirmLabel: 'Start over',
      cancelLabel: 'Keep my place',
    });
    if (yes) start(0);
  }

  async function start(from = 0) {
    if (!data || starting) return;
    const ids = data.problems.map((p) => p.id);
    setStarting(true);
    // Recorded as dealt, so its report is about these problems. If it cannot be
    // saved now, the problem page records it at the first answer.
    const run = await amc.recordSet({
      kind: 'practice', topic: data.topic.id, mode: data.mode, title: data.title, problems: ids,
      seconds: data.total_seconds,
    });
    setStarting(false);
    writePracticeSet({
      ids, topic: data.topic.id, mode: data.mode, title: data.title,
      seconds: data.seconds, hideTopic: data.hide_topic, size,
      // The clock is the whole set's, from now: it does not wait between problems.
      deadline: data.total_seconds ? Date.now() + data.total_seconds * 1000 : null,
      runId: run,
    });
    const first = data.problems[from];
    if (first) navigate(`/problems/${first.id}?set=1`);
  }

  /** Back to a problem of the stored set (finished: its solution; in progress: the walk). */
  function openRow(id: string) {
    navigate(going ? `/problems/${id}?set=1` : `/problems/${id}`);
  }

  return (
    <div className={`amc-page ${swap}`.trim()}>
      <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12 }}>
        <Link to={`/topics/${data.topic.id}`} className="am-link">← {data.hide_topic ? 'Back to the topic' : data.topic.name}</Link>
      </nav>
      <PageHeader kicker={data.hide_topic ? data.level : `${data.level} · ${data.topic.name}`} title={data.title}
                  actions={going ? (
                    <>
                      <button type="button" className="am-btn am-btn-ghost" onClick={() => void startOver()}>Start over</button>
                      <button type="button" className="am-btn am-btn-primary" onClick={resume}>Continue set</button>
                    </>
                  ) : (
                    <button type="button" className="am-btn am-btn-primary" disabled={starting} onClick={() => void start(0)}>
                      {done ? 'New set' : 'Start set'}
                    </button>
                  )}>
        <p>{data.instructions}</p>
        {data.total_seconds ? (
          <p className="am-set-clock-note">
            {clock(data.total_seconds)} for the {data.problems.length} problems. The clock starts when you press Start and stops for nothing.
          </p>
        ) : null}
      </PageHeader>

      <div className="am-seg am-set-modes" role="group" aria-label="Kind of set">
        {data.modes.map((m) => (
          <button key={m.id} type="button" className={m.id === data.mode ? 'is-on' : ''}
                  onClick={() => setParams(size ? { mode: m.id, n: String(size) } : { mode: m.id })}>
            {m.title}{m.id === data.suggested ? ' ★' : ''}
          </button>
        ))}
      </div>
      <p className="am-muted" style={{ fontSize: 12, margin: '6px 0 16px' }}>★ what your answers in this topic call for</p>

      {going && (
        <section className="am-card am-set-going" role="status">
          <span className="am-set-going-dot" aria-hidden="true" />
          <span><strong>In progress:</strong> {answeredIds.size} of {going.ids.length} answered{left != null ? `, ${clock(left)} left` : ''}.</span>
          <button type="button" className="am-btn am-btn-primary am-btn-sm" onClick={resume}>Continue</button>
        </section>
      )}

      {done && (
        report ? (
          <SetReport report={report} />
        ) : stored.loading || (runId && !stored.error) ? (
          <Loading label="Marking the set" />
        ) : (
          <section className="am-card am-set-done" role="status">
            {timeUp && <span className="am-set-timeup">Time's up. </span>}
            {stored.error
              ? <span>Could not load how the set went. <button type="button" className="am-btn am-btn-sm" onClick={stored.reload}>Try again</button></span>
              : <span>This set was not recorded, so there is no report for it. Its answers still count in your history.</span>}
          </section>
        )
      )}

      {report && going ? (
        <section className="am-card">
          <div className="am-card-head"><h2>The {report.total} problems in this set</h2></div>
          <ol className="am-set-list">
            {report.problems.map((r) => (
              <li key={r.id}>
                <button type="button" onClick={() => openRow(r.id)}
                        className={`am-set-row${going.current === r.id ? ' is-current' : ''}${r.result !== 'skipped' ? ' is-answered' : ''}`}>
                  <span className="am-set-num">{r.n}</span>
                  <span className="am-set-main">
                    <span className="am-set-source">{r.source}</span>
                    {!data.hide_topic && <span className="am-muted"><CategoryDot category={r.category} /> {r.topic_name}</span>}
                  </span>
                  <span className={`am-mode is-l${r.level_of}`}>Level {r.level_of}</span>
                  <SetResultPill result={results.get(r.id) ?? 'skipped'} going />
                </button>
              </li>
            ))}
          </ol>
        </section>
      ) : !done && (
        <section className="am-card">
          <div className="am-card-head">
            <h2>{data.problems.length} problems, all {data.hide_topic ? 'from this topic (names hidden)' : data.topic.name}</h2>
            <MixBar mix={data.mix} labels={false} />
          </div>
          <ol className="am-set-list">
            {data.problems.map((p, i) => (
              <li key={p.id}>
                <button type="button"
                        className={`am-set-row${going && going.current === p.id ? ' is-current' : ''}${answeredIds.has(p.id) ? ' is-answered' : ''}`}
                        onClick={() => (going ? navigate(`/problems/${p.id}?set=1`) : void start(i))}>
                  <span className="am-set-num">{i + 1}</span>
                  <span className="am-set-main">
                    <span className="am-set-source">{p.source}</span>
                    {!data.hide_topic && (
                      <span className="am-muted"><CategoryDot category={p.category} /> {p.topic_name}</span>
                    )}
                  </span>
                  <span className={`am-mode is-l${p.level_of}`}>Level {p.level_of}</span>
                  <StatusPill status={p.status} />
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

/** How a problem went in this set (not its lifetime status). */
function SetResultPill({ result, going = false }: { result: SetResult; going?: boolean }) {
  const label = { right: 'Right', wrong: 'Missed', revealed: 'Revealed', skipped: going ? 'To do' : 'Not answered' }[result];
  const tone = result === 'right' ? 'solved' : result === 'skipped' ? 'new' : 'missed';
  return <span className={`am-pill am-pill-${tone}`}>{label}</span>;
}
