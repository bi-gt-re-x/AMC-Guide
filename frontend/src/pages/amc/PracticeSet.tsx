/**
 * A topic's practice set: eight problems handpicked from that one topic for a
 * way of training it (backend/amc/practice.py) — learn the ideas, an accuracy
 * drill, a timed set, a mixed set with the topic hidden, spaced review, or a
 * plain practice set at the topic's difficulty mix, or a challenge set of
 * harder ones. The mode the student's data suggests is marked. `?n=` is the
 * size the study plan asked for today. Starting walks the set on the problem
 * page (`?set=1`); a timed or challenge set starts its clock then, the whole
 * set's time, and ends when it runs out. Finishing comes back here with how
 * it went (`?done=1`, and `&timeup=1` if the clock ended it).
 */
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ErrorState, Loading, useNotice } from '@/components';
import { CategoryDot, clock, PageHeader, StatusPill } from '@/components/Amc/bits';
import { MixBar } from '@/components/Amc/Study';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc } from '@/services/amc';
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
  const { data, error, loading, reload } = useApi(() => amc.topicSet(topicId, mode, size), [topicId, mode, size]);
  // This set, left part way (and not just finished): offered to be continued.
  const open = done ? null : activePracticeSet();
  const going = open && open.topic === topicId && open.mode === mode ? open : null;
  useDocumentTitle(data ? `${data.topic.name} · ${data.title}` : 'Practice set');

  if (loading && !data) return <Loading label="Picking eight problems" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not pick a set.'} onRetry={reload} />;

  const right = data.problems.filter((p) => p.status === 'solved').length;
  const untried = data.problems.filter((p) => p.status === 'new').length;
  const answeredIds = new Set(going?.answered ?? []);
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

  function start(from = 0) {
    if (!data) return;
    writePracticeSet({
      ids: data.problems.map((p) => p.id), topic: data.topic.id, mode: data.mode, title: data.title,
      seconds: data.seconds, hideTopic: data.hide_topic, size,
      // The clock is the whole set's, from now: it does not wait between problems.
      deadline: data.total_seconds ? Date.now() + data.total_seconds * 1000 : null,
    });
    const first = data.problems[from];
    if (first) navigate(`/problems/${first.id}?set=1`);
  }

  return (
    <div className="amc-page">
      <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12 }}>
        <Link to={`/topics/${data.topic.id}`} className="am-link">← {data.topic.name}</Link>
      </nav>
      <PageHeader kicker={`${data.level} · ${data.topic.name}`} title={data.title}
                  actions={going ? (
                    <>
                      <button type="button" className="am-btn am-btn-ghost" onClick={() => void startOver()}>Start over</button>
                      <button type="button" className="am-btn am-btn-primary" onClick={resume}>Continue set</button>
                    </>
                  ) : (
                    <button type="button" className="am-btn am-btn-primary" onClick={() => start(0)}>
                      {done ? 'Go again' : 'Start set'}
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
        <section className="am-card am-set-done" role="status">
          {timeUp && <span className="am-set-timeup">Time's up. </span>}
          <strong>{right} of {data.problems.length}</strong> solved
          {untried ? <span className="am-muted"> · {untried} not tried yet</span> : null}
        </section>
      )}

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
                      onClick={() => (going ? navigate(`/problems/${p.id}?set=1`) : start(i))}>
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
    </div>
  );
}
