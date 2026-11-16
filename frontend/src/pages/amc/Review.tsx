/**
 * Review, in two parts.
 *
 * **Weak topics**: twelve problems from the topics the account does worst in
 * (backend/amc/weak.py), from the official papers, and from the Summit and Step
 * mocks too when the box is ticked. "Start the 12" walks them on the problem
 * page (`?weak=1`); the set holds still for the day, "New set" draws another.
 *
 * **Wrong problems**: the error log. Every miss — practice, mock, or "show
 * solution" — comes back here after 3 days; a right answer on the day moves it
 * to 10, then 21, then out as mastered, and a wrong one starts it over. "Start
 * review" walks the due ones in order, each opened as a review.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { Empty, PageHeader, ProblemRow } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, shortDate, type ReviewItem, type WeakBank } from '@/services/amc';
import { ReviewStage } from './Problem';
import { writeWeakSet } from './weakSet';
import '@/styles/amc.css';

/** Whether the weak-topics set takes mock problems too: this reader's choice. */
const WEAK_MOCKS_KEY = 'amc-weak-mocks';

function readMocksChoice(): boolean {
  try {
    return localStorage.getItem(WEAK_MOCKS_KEY) === '1';
  } catch {
    return false;
  }
}

function writeMocksChoice(on: boolean) {
  try {
    if (on) localStorage.setItem(WEAK_MOCKS_KEY, '1');
    else localStorage.removeItem(WEAK_MOCKS_KEY);
  } catch {
    /* storage blocked: the choice lasts until the page is left */
  }
}

function accuracyLabel(t: WeakBank['topics'][number]): string {
  return t.attempted ? `${t.first_right}/${t.attempted} first try` : 'not tried yet';
}

function WeakTopics() {
  const navigate = useNavigate();
  const [mocks, setMocks] = useState(readMocksChoice);
  const [draw, setDraw] = useState(0);
  const { data, error, loading, reload } = useApi(() => amc.weakBank(mocks, draw), [mocks, draw]);
  const ids = data?.problems.map((p) => p.id) ?? [];
  useEffect(() => {
    if (ids.length) writeWeakSet(ids);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the list, not its identity
  }, [ids.join(',')]);

  const toggleMocks = (on: boolean) => {
    writeMocksChoice(on);
    setMocks(on);
    setDraw(0);
  };

  return (
    <section className="am-card am-weak" aria-labelledby="weak-head">
      <div className="am-card-head">
        <h2 id="weak-head">Weak topics</h2>
        <div className="am-weak-actions">
          <label className="am-weak-toggle">
            <input type="checkbox" checked={mocks} onChange={(e) => toggleMocks(e.target.checked)} />
            Include Summit &amp; Step mocks
          </label>
          <button type="button" className="am-btn am-btn-sm" disabled={loading} onClick={() => setDraw((d) => d + 1)}>
            New set
          </button>
          <button type="button" className="am-btn am-btn-sm am-btn-primary" disabled={!ids.length}
                  onClick={() => navigate(`/problems/${ids[0]}?weak=1`)}>
            Start the {ids.length || data?.size || 12}
          </button>
        </div>
      </div>
      {loading && !data ? (
        <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>Picking problems…</p>
      ) : error || !data ? (
        <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>
          Could not load the set. <button type="button" className="am-link am-link-btn" onClick={reload}>Try again</button>
        </p>
      ) : !data.problems.length ? (
        <Empty title="Nothing left to pick">
          {mocks
            ? 'Every problem in these topics is solved or already in your review log.'
            : 'No official problems are left in these topics. Tick “Include Summit & Step mocks” for more.'}
        </Empty>
      ) : (
        <>
          <ul className="am-weak-topics" aria-label="Topics in this set">
            {data.topics.map((t) => (
              <li key={t.id}>
                <Link to={`/topics/${t.id}`} className="am-tag">{t.name}</Link>
                <span className="am-muted">{accuracyLabel(t)} · {t.picked} here</span>
              </li>
            ))}
          </ul>
          <div className="am-rows">
            {data.problems.map((p) => (
              <ProblemRow
                key={p.id}
                problem={p}
                to={`/problems/${p.id}?weak=1`}
                extra={
                  <span className="am-muted" style={{ fontSize: 12, textAlign: 'right' }}>
                    {p.weak_topic_name}
                  </span>
                }
              />
            ))}
          </div>
          <p className="am-card-note">
            For the {data.target}, from {data.pool.official} official problem{data.pool.official === 1 ? '' : 's'}
            {data.mocks ? ` and ${data.pool.mock} mock problem${data.pool.mock === 1 ? '' : 's'}` : ''} you haven't
            solved and that aren't in your review log, pitched where you get about two in three right. The set stays
            the same today; “New set” draws another.
          </p>
        </>
      )}
    </section>
  );
}

type Tab = 'due' | 'upcoming' | 'mastered';

function Rows({ items, empty }: { items: ReviewItem[]; empty: { title: string; body: string } }) {
  if (!items.length) return <Empty title={empty.title}>{empty.body}</Empty>;
  return (
    <div className="am-rows">
      {items.map((item) => (
        <div key={item.id}>
          <ProblemRow
            problem={{ ...item }}
            extra={
              <span style={{ display: 'grid', gap: 4, justifyItems: 'end', fontSize: 12 }} className="am-muted">
                <ReviewStage stage={item.stage} />
                {item.review_status === 'mastered' ? 'mastered' : item.overdue ? `overdue · ${shortDate(item.due)}` : `due ${shortDate(item.due)}`}
              </span>
            }
          />
          {item.note && (
            <p className="am-muted" style={{ margin: 0, padding: '0 16px 12px', fontSize: 13, fontStyle: 'italic' }}>
              “{item.note}”
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

export default function Review() {
  useDocumentTitle('Review');
  const navigate = useNavigate();
  const { data, error, loading, reload } = useApi(() => amc.review(), []);
  const [tab, setTab] = useState<Tab>('due');
  if (loading && !data) return <Loading label="Loading your review log" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load the review log.'} onRetry={reload} />;

  const max = Math.max(1, ...data.forecast.map((f) => f.count));
  const lists: Record<Tab, ReviewItem[]> = { due: data.due, upcoming: data.upcoming, mastered: data.mastered };

  return (
    <div className="amc-page">
      <PageHeader
        title="Review"
        actions={data.due.length ? (
          <button type="button" className="am-btn am-btn-primary"
                  onClick={() => navigate(`/problems/${data.due[0]?.id ?? ''}?review=1`)}>
            Start review ({data.due.length})
          </button>
        ) : undefined}
      >
        <p>
          Twelve problems from your weakest topics, then every problem you got wrong, brought back after{' '}
          {data.intervals.join(', ')} days until you get it right three times.
        </p>
      </PageHeader>

      <WeakTopics />

      <h2 className="am-h2 am-section-head" id="wrong-head">Wrong problems</h2>

      <dl className="am-stats" aria-labelledby="wrong-head">
        <div className="am-stat"><dt>Due today</dt><dd className="am-stat-value">{data.due.length}</dd></div>
        <div className="am-stat"><dt>Coming up</dt><dd className="am-stat-value">{data.upcoming.length}</dd></div>
        <div className="am-stat"><dt>Mastered</dt><dd className="am-stat-value">{data.mastered.length}</dd></div>
        <div className="am-stat">
          <dt>Most missed</dt>
          <dd className="am-stat-value" style={{ fontSize: 20, lineHeight: 1.2 }}>{data.by_topic[0]?.name ?? '—'}</dd>
        </div>
      </dl>

      <div className="am-grid am-grid-main">
        <div>
          <div className="am-tabs" role="tablist">
            {(['due', 'upcoming', 'mastered'] as Tab[]).map((t) => (
              <button key={t} type="button" role="tab" aria-selected={tab === t}
                      className={`am-tab${tab === t ? ' is-on' : ''}`} onClick={() => setTab(t)}>
                {t === 'due' ? 'Due now' : t === 'upcoming' ? 'Upcoming' : 'Mastered'}
                <small>{lists[t].length}</small>
              </button>
            ))}
          </div>
          <Rows
            items={lists[tab]}
            empty={
              tab === 'due'
                ? { title: 'All caught up', body: 'Nothing due today.' }
                : tab === 'upcoming'
                  ? { title: 'Nothing scheduled', body: 'Missed problems show up here.' }
                  : { title: 'Nothing mastered yet', body: 'Problems you get right on all three reviews end up here.' }
            }
          />
        </div>
        <aside className="am-stack">
          <section className="am-card">
            <div className="am-card-head"><h2>Next two weeks</h2></div>
            <div className="am-forecast" aria-label="Reviews due per day for the next 14 days">
              {data.forecast.map((f, i) => (
                <div key={f.date} className={`am-forecast-col${i === 0 ? ' is-today' : ''}`} title={`${shortDate(f.date)}: ${f.count}`}>
                  <i className={f.count ? '' : 'is-empty'} style={{ height: `${Math.max(4, (f.count / max) * 70)}px` }} />
                  <span>{new Date(`${f.date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'narrow' })}</span>
                </div>
              ))}
            </div>
          </section>
          <section className="am-card">
            <div className="am-card-head">
              <h2>By topic</h2>
              <Link to="/problems?status=missed">All misses</Link>
            </div>
            {data.by_topic.length ? (
              <ul className="am-list">
                {data.by_topic.map((t) => <li key={t.name}><span>{t.name}</span><span className="am-muted">{t.count}</span></li>)}
              </ul>
            ) : (
              <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>Nothing yet.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
