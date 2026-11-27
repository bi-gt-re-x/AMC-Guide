/**
 * One topic: what it covers, the ideas that unlock it, which techniques its
 * problems lean on, how you're doing, and every problem filed under it.
 */
import { Link, useParams } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { MathText } from '@/components/Amc/MathText';
import { Difficulty, Empty, Meter, PageHeader, problemHref } from '@/components/Amc/bits';
import { StrategyList } from '@/components/Amc/StrategyList';
import { useApi, useDocumentTitle, usePageSwap } from '@/hooks';
import { amc, pct, type NextPick } from '@/services/amc';
import '@/styles/amc.css';

const PICK_LABEL: Record<NextPick['kind'], string> = { retry: 'Retry', next: 'Next step', stretch: 'Stretch' };

function Pick({ pick, topic }: { pick: NextPick; topic: string }) {
  return (
    <li>
      <Link to={problemHref(pick.id, topic)} className={`am-pick is-${pick.kind}`}>
        <span className="am-pick-kind">{PICK_LABEL[pick.kind]}</span>
        <span className="am-pick-body">
          <strong>{pick.short ?? pick.id}</strong> <span className="am-muted">{pick.source}</span>
          <span className="am-pick-why">{pick.reason}</span>
        </span>
        <Difficulty value={pick.difficulty} rating={pick.rating} />
      </Link>
    </li>
  );
}

const SETS = [
  { mode: 'learn', label: 'Learn the ideas' }, { mode: 'accuracy', label: 'Accuracy drill' },
  { mode: 'timed', label: 'Timed set' }, { mode: 'mixed', label: 'Mixed set' }, { mode: 'spaced', label: 'Spaced review' },
];

export default function Topic() {
  const { topicId = '' } = useParams();
  const { data, error, loading, refreshing, reload } = useApi(() => amc.topic(topicId), [topicId]);
  const swap = usePageSwap(topicId, loading || refreshing);
  useDocumentTitle(data?.topic.name ?? 'Topic');
  if (loading && !data) return <Loading label="Loading topic" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load this topic.'} onRetry={reload} />;

  const { topic, problems } = data;
  const missed = problems.filter((p) => p.status === 'missed' || p.status === 'review').length;

  return (
    <div className={`amc-page ${swap}`.trim()}>
      <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12 }}>
        <Link to="/topics" className="am-link">← Topics</Link>
      </nav>
      <PageHeader
        kicker={topic.category_name}
        title={topic.name}
        actions={<Link className="am-btn am-btn-primary" to={`/practice/${topic.id}`}>Practice 8 problems</Link>}
      >
        <p>{topic.summary} On the {topic.levels.join(', ')}.</p>
      </PageHeader>

      {/* Eight problems from this topic only, picked for one way of training it. */}
      <div className="am-set-starts" aria-label="Practice sets">
        {SETS.map((s) => (
          <Link key={s.mode} className="am-chip" to={`/practice/${topic.id}?mode=${s.mode}`}>{s.label}</Link>
        ))}
      </div>

      <div className="am-grid am-grid-main">
        <div className="am-stack">
          {data.next.length > 0 && (
            <section className="am-card">
              <div className="am-card-head"><h2>Do these next</h2></div>
              <ol className="am-picks">
                {data.next.map((p) => <Pick key={p.kind} pick={p} topic={topic.id} />)}
              </ol>
            </section>
          )}
          <section className="am-card">
            <div className="am-card-head"><h2>Ideas</h2></div>
            {topic.playbook?.length ? (
              <ol className="am-play">
                {topic.playbook.map((m) => (
                  <li key={m.move}>
                    <h3><MathText text={m.move} /></h3>
                    <p className="am-play-when"><span>When</span><MathText text={m.when} /></p>
                    <p className="am-play-example"><span>Example</span><MathText text={m.example} /></p>
                  </li>
                ))}
              </ol>
            ) : (
              <ol className="am-ideas">
                {topic.ideas.map((idea) => <li key={idea}><MathText text={idea} /></li>)}
              </ol>
            )}
            {topic.trap && (
              <div className="am-callout am-play-trap">
                <span>Watch out</span>
                <MathText text={topic.trap} as="p" />
              </div>
            )}
          </section>
          <section className="am-card">
            <div className="am-card-head">
              <h2>Problems by strategy</h2>
              <Link to={`/problems?topic=${topic.id}`}>Open in Problems</Link>
            </div>
            {data.by_strategy.length ? <StrategyList groups={data.by_strategy} topic={topic.id} /> : <Empty title="No problems yet" />}
          </section>
        </div>
        <aside className="am-stack">
          <section className="am-card">
            <div className="am-card-head"><h2>Your progress</h2></div>
            <dl className="am-kv">
              <dt>Solved</dt><dd>{topic.solved} of {topic.problems}</dd>
              <dt>First-try accuracy</dt><dd>{pct(topic.accuracy)}</dd>
              <dt>Missed or in review</dt><dd>{missed}</dd>
              <dt>Weight on the contest</dt><dd>{['', 'Occasional', 'Regular', 'Every paper'][topic.weight]}</dd>
            </dl>
            <div style={{ marginTop: 14 }}><Meter value={topic.mastery} /></div>
          </section>
          {data.techniques.length > 0 && (
            <section className="am-card">
              <div className="am-card-head"><h2>Techniques</h2></div>
              <div className="am-chips">
                {data.techniques.map((t) => (
                  <Link key={t.id} className="am-chip" to={`/problems?topic=${topic.id}&technique=${t.id}`}>
                    {t.name} <small>{t.count}</small>
                  </Link>
                ))}
              </div>
            </section>
          )}
          <section className="am-card">
            <div className="am-card-head"><h2>Related topics</h2></div>
            <ul className="am-list">
              {data.siblings.map((s) => (
                <li key={s.id}><Link className="am-link" style={{ color: 'var(--am-ink)', fontWeight: 500 }} to={`/topics/${s.id}`}>{s.name}</Link></li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
