/**
 * A topic's practice set: eight problems handpicked from that one topic for a
 * way of training it (backend/amc/practice.py) — learn the ideas, an accuracy
 * drill, a timed set, a mixed set with the topic hidden, spaced review, or a
 * plain practice set at the topic's difficulty mix. The mode the student's
 * data suggests is marked. Starting walks the eight on the problem page
 * (`?set=1`); finishing comes back here with how it went.
 */
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { CategoryDot, PageHeader, StatusPill } from '@/components/Amc/bits';
import { MixBar } from '@/components/Amc/Study';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc } from '@/services/amc';
import { writePracticeSet } from './practiceSetStore';
import '@/styles/amc.css';

export default function PracticeSet() {
  const { topicId = '' } = useParams();
  const [params, setParams] = useSearchParams();
  const mode = params.get('mode') || 'practice';
  const done = params.get('done') === '1';
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi(() => amc.topicSet(topicId, mode), [topicId, mode]);
  useDocumentTitle(data ? `${data.topic.name} · ${data.title}` : 'Practice set');

  if (loading && !data) return <Loading label="Picking eight problems" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not pick a set.'} onRetry={reload} />;

  const right = data.problems.filter((p) => p.status === 'solved').length;
  const open = data.problems.filter((p) => p.status === 'new').length;

  function start(from = 0) {
    if (!data) return;
    writePracticeSet({
      ids: data.problems.map((p) => p.id), topic: data.topic.id, mode: data.mode, title: data.title,
      seconds: data.seconds, hideTopic: data.hide_topic,
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
                  actions={<button type="button" className="am-btn am-btn-primary" onClick={() => start(0)}>
                    {done ? 'Go again' : 'Start set'}
                  </button>}>
        <p>{data.instructions}</p>
      </PageHeader>

      <div className="am-seg am-set-modes" role="group" aria-label="Kind of set">
        {data.modes.map((m) => (
          <button key={m.id} type="button" className={m.id === data.mode ? 'is-on' : ''}
                  onClick={() => setParams({ mode: m.id })}>
            {m.title}{m.id === data.suggested ? ' ★' : ''}
          </button>
        ))}
      </div>
      <p className="am-muted" style={{ fontSize: 12, margin: '6px 0 16px' }}>★ what your answers in this topic call for</p>

      {done && (
        <section className="am-card am-set-done" role="status">
          <strong>{right} of {data.problems.length}</strong> solved
          {open ? <span className="am-muted"> · {open} not tried yet</span> : null}
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
              <button type="button" className="am-set-row" onClick={() => start(i)}>
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
