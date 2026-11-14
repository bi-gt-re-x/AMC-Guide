/**
 * One contest. A Step Mock shows its format, your past sittings, and the
 * button that starts the clock. An imported official paper is shown whole, in
 * problem order like its AoPS wiki page, each problem with its choices, topic,
 * 1-10 rating and links to answer it here.
 *
 * An official paper also shows where you stand on it (a tile per problem:
 * right first time, put right later, still open, untouched) and, closed until
 * asked for, its answer key and Summit's own solutions. Those come from a
 * separate call (`amc.contestKey`) so the timed sitting, which loads this
 * page's data, never carries the answers.
 */
import { useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ErrorState, Loading } from '@/components';
import { CategoryDot, DiagramNote, Difficulty, PageHeader, Solution, StatusPill } from '@/components/Amc/bits';
import { MathText } from '@/components/Amc/MathText';
import { Importer } from '@/components/Amc/Importer';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, announceAmcChanged, shortDate, type ContestProgress, type KeyRow, type MockBrief } from '@/services/amc';
import '@/styles/amc.css';

function History({ rows, onDelete }: { rows: MockBrief[]; onDelete: (id: string) => void }) {
  if (!rows.length) return <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>No sittings yet.</p>;
  return (
    <table className="am-table">
      <thead><tr><th>Date</th><th className="num">Score</th><th /></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <td>{r.kind === 'mock' ? <Link to={`/mocks/${r.id}`}>{shortDate(r.at)}</Link> : shortDate(r.at)}
              {r.note && <div className="am-muted" style={{ fontSize: 12 }}>{r.note}</div>}</td>
            <td className="num">{r.score}{r.kind === 'mock' ? ` (${r.correct}✓ ${r.wrong}✗ ${r.blank}–)` : ''}</td>
            <td className="num">
              <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={() => onDelete(r.id)}
                      aria-label="Delete this score">✕</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const PROGRESS: Record<ContestProgress, { mark: string; label: string }> = {
  first: { mark: '✓', label: 'right first time' },
  fixed: { mark: '✓', label: 'put right later' },
  open: { mark: '✕', label: 'still to put right' },
  new: { mark: '', label: 'not tried yet' },
};

/** A tile per problem showing how it stands, each a link down to the problem. */
function Standing({ problems }: { problems: { number: number; progress: ContestProgress }[] }) {
  const count = (k: ContestProgress) => problems.filter((p) => p.progress === k).length;
  const solved = count('first') + count('fixed');
  const open = count('open');
  const fresh = count('new');
  return (
    <section className="am-card am-standing">
      <div className="am-card-head">
        <h2>Where you stand</h2>
        <span className="am-muted" style={{ fontSize: 13 }}>
          {solved} solved{open ? ` · ${open} to put right` : ''}{fresh ? ` · ${fresh} untouched` : ''}
        </span>
      </div>
      <ol className="am-standing-tiles">
        {problems.map((p) => (
          <li key={p.number}>
            <a href={`#problem-${p.number}`} className={`am-standing-tile is-${p.progress}`}
               aria-label={`Problem ${p.number}: ${PROGRESS[p.progress].label}`}>
              <b>{p.number}</b><i aria-hidden="true">{PROGRESS[p.progress].mark}</i>
            </a>
          </li>
        ))}
      </ol>
      <p className="am-standing-legend">
        {(['first', 'fixed', 'open', 'new'] as ContestProgress[]).map((k) => (
          <span key={k}><i className={`am-standing-swatch is-${k}`} aria-hidden="true">{PROGRESS[k].mark}</i>{PROGRESS[k].label}</span>
        ))}
      </p>
    </section>
  );
}

/** The answer key as a compact table, ten to a row. */
function KeyTable({ rows }: { rows: KeyRow[] }) {
  return (
    <ol className="am-keytable" aria-label="Answer key">
      {rows.map((r) => <li key={r.number}><small>{r.number}</small><b>{r.answer}</b></li>)}
    </ol>
  );
}

export default function Contest() {
  const { contestId = '' } = useParams();
  const { data, error, loading, reload } = useApi(() => amc.contest(contestId), [contestId]);
  useDocumentTitle(data?.contest.name ?? 'Contest');
  const [score, setScore] = useState('');
  const [note, setNote] = useState('');
  const [message, setMessage] = useState('');
  // The answer key and write-ups: fetched the first time anything asks for them.
  const [key, setKey] = useState<KeyRow[] | null>(null);
  const [keyError, setKeyError] = useState('');
  const [keyOpen, setKeyOpen] = useState(false);
  const [shown, setShown] = useState<number[]>([]);

  async function loadKey(): Promise<boolean> {
    if (key) return true;
    setKeyError('');
    try {
      const reply = await amc.contestKey(contestId);
      if (reply.success) { setKey(reply.key); return true; }
      setKeyError(reply.message);
    } catch (cause) {
      setKeyError(cause instanceof Error ? cause.message : 'Could not load the answer key.');
    }
    return false;
  }
  async function toggleKey() {
    if (keyOpen) { setKeyOpen(false); return; }
    if (await loadKey()) setKeyOpen(true);
  }
  async function toggleSolution(n: number) {
    if (shown.includes(n)) { setShown(shown.filter((x) => x !== n)); return; }
    if (await loadKey()) setShown([...shown, n]);
  }

  if (loading && !data) return <Loading label="Loading contest" />;
  if (error || !data) return <ErrorState message={error ?? 'Could not load this contest.'} onRetry={reload} />;
  const c = data.contest;

  async function remove(id: string) {
    if (!window.confirm('Delete this score? This cannot be undone.')) return;
    await amc.deleteMock(id);
    announceAmcChanged();
    reload();
  }

  async function log() {
    setMessage('');
    const value = Number(score);
    if (!score || Number.isNaN(value)) {
      setMessage('Enter your score.');
      return;
    }
    const reply = await amc.logScore(contestId, value, note);
    if (!reply.success) {
      setMessage(reply.message);
      return;
    }
    setScore('');
    setNote('');
    announceAmcChanged();
    reload();
  }

  const logCard = c.kind === 'past' && (
    <section className="am-card">
      <div className="am-card-head"><h2>Took it on paper?</h2></div>
      <div className="am-form">
        <label className="am-field">
          <span>Score (out of {c.max})</span>
          <input className="am-input" inputMode="decimal" value={score} onChange={(e) => setScore(e.target.value)}
                 placeholder={c.level === 'AIME' ? 'e.g. 7' : 'e.g. 103.5'} />
        </label>
        <label className="am-field">
          <span>Note</span>
          <input className="am-input" value={note} onChange={(e) => setNote(e.target.value)}
                 placeholder="Timed? Which ones cost you?" maxLength={300} />
        </label>
        <button type="button" className="am-btn" onClick={() => void log()}>Log score</button>
      </div>
      {message && <p className="am-error">{message}</p>}
    </section>
  );

  async function unimport() {
    if (!window.confirm('Remove this contest from Summit for every account? Answers already given are kept.')) return;
    await amc.removeImport(contestId);
    announceAmcChanged();
    reload();
  }

  const back = (
    <nav className="am-muted" style={{ fontSize: 13, marginBottom: 12 }}>
      {c.kind === 'mock'
        ? <Link to="/mock-contests" className="am-link">← Mock Contests</Link>
        : <Link to="/contests" className="am-link">← Past Contests</Link>}
    </nav>
  );

  // An official paper nobody has brought in yet: the importer, and a place to
  // log a score taken elsewhere.
  if (c.kind === 'past' && !c.imported) {
    return (
      <div className="amc-page">
        {back}
        <PageHeader kicker={`${c.year} · ${c.level}`} title={c.name}>
          <p>
            {c.count} problems in {c.minutes} minutes.{data.can_import ? ' Import it once to practice it here.' : ''}
          </p>
        </PageHeader>
        <div className="am-grid am-grid-main">
          {data.can_import ? (
            <Importer contest={{ ...c, imported: 0 }} onSaved={reload} />
          ) : (
            <section className="am-card">
              <div className="am-card-head"><h2>Not in Summit yet</h2></div>
              <p className="am-muted" style={{ margin: 0 }}>
                This paper hasn't been brought in yet. Read it on the{' '}
                <a className="am-link" href={c.problems_url} target="_blank" rel="noreferrer">AoPS wiki ↗</a>
                {' '}and log your score here.
              </p>
            </section>
          )}
          <aside className="am-stack">
            {logCard}
            <section className="am-card">
              <div className="am-card-head"><h2>Your scores</h2></div>
              <History rows={data.history} onDelete={(id) => void remove(id)} />
            </section>
          </aside>
        </div>
      </div>
    );
  }

  const problems = data.problems;
  const official = c.kind === 'past';
  const firstOpen = problems.find((p) => p.status === 'new') ?? problems[0];
  const sat = data.history.some((h) => h.kind === 'mock');
  const written = problems.filter((p) => p.has_solution).length;
  const keyCard: ReactNode = official && (
    <section className="am-card">
      <div className="am-card-head">
        <h2>Answer key</h2>
        <button type="button" className="am-btn am-btn-sm" aria-expanded={keyOpen} onClick={() => void toggleKey()}>
          {keyOpen ? 'Fold it away' : 'Unfold'}
        </button>
      </div>
      {keyOpen && key
        ? <KeyTable rows={key} />
        : <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>Closed so it can't catch your eye. Opening it doesn't count against you.</p>}
      {keyError && <p className="am-error" style={{ fontSize: 13 }}>{keyError}</p>}
    </section>
  );
  return (
    <div className="amc-page">
      {back}
      <PageHeader
        kicker={official ? `${c.year} · ${c.level} · Official` : `${c.level} · ${c.family === 'summit' ? 'Summit Mock' : 'Step Mock'}`}
        title={c.name}
        actions={
          <>
            {firstOpen && (
              <Link className="am-btn" to={`/problems/${firstOpen.id}`}>Practice one by one</Link>
            )}
            <Link className="am-btn am-btn-primary" to={`/contests/${c.id}/take`}>
              {official ? (sat ? `Sit it again (${c.minutes} min)` : 'Start timed contest') : 'Start timed mock'}
            </Link>
          </>
        }
      >
        <p>
          {official
            ? `${c.count} problems in ${c.minutes} minutes${c.level === 'AIME' ? ', one point each' : ', 6 for a right answer, 1.5 for a blank, 0 for a wrong one'}.${written ? ` Summit's own worked solution${written === 1 ? ' is' : 's are'} folded under ${written === c.count ? 'every problem' : `${written} of the problems`}, and the answer key has a card of its own. Both stay closed until you open them.` : ''}`
            : c.blurb}
        </p>
      </PageHeader>
      {official && <Standing problems={problems} />}
      <div className="am-grid am-grid-main">
        <section className="am-card">
          <div className="am-card-head">
            <h2>{official ? 'Problems' : "What's on it"}</h2>
            <span className="am-muted" style={{ fontSize: 13 }}>
              {official ? (
                <>
                  <a className="am-link" href={c.problems_url} target="_blank" rel="noreferrer">AoPS page ↗</a>
                  {' · '}
                  <a className="am-link" href={c.answers_url} target="_blank" rel="noreferrer">Answer key ↗</a>
                </>
              ) : 'Hidden until you start'}
            </span>
          </div>
          {official ? (
            <ol className="am-booklet">
              {problems.map((p) => (
                <li key={p.number} id={`problem-${p.number}`} className="am-booklet-item">
                  <div className="am-booklet-head">
                    <h3><Link to={`/problems/${p.id}`}>Problem {p.number}</Link></h3>
                    <span className="am-booklet-tags">
                      <CategoryDot category={p.category} />
                      <Link className="am-muted" to={`/topics/${p.topic}`}>{p.topic_name}</Link>
                      <Difficulty value={p.difficulty} rating={p.rating} />
                      <StatusPill status={p.status} />
                    </span>
                  </div>
                  <MathText text={p.statement} as="p" className="am-statement" />
                  {p.diagram && <DiagramNote diagram={p.diagram} href={p.aops_url} />}
                  {p.choices && (
                    <p className="am-booklet-choices">
                      {p.choices.map((choice, i) => (
                        <span key={i}><strong>({'ABCDE'.charAt(i)})</strong> <MathText text={choice} /></span>
                      ))}
                    </p>
                  )}
                  <p className="am-booklet-links">
                    <Link className="am-link" to={`/problems/${p.id}`}>Answer it here</Link>
                    {p.has_solution && (
                      <button type="button" className="am-link am-link-button" aria-expanded={shown.includes(p.number)}
                              onClick={() => void toggleSolution(p.number)}>
                        {shown.includes(p.number) ? 'Hide the solution' : 'Our solution'}
                      </button>
                    )}
                    {p.aops_url && (
                      <a className="am-link" href={p.aops_url} target="_blank" rel="noreferrer">AoPS discussion ↗</a>
                    )}
                  </p>
                  {shown.includes(p.number) && (() => {
                    const row = key?.[p.number - 1];
                    if (!row) return null;
                    return (
                      <div className="am-booklet-solution">
                        <p className="am-booklet-answer">Answer: <b>{c.level === 'AIME' ? row.answer.padStart(3, '0') : `(${row.answer})`}</b></p>
                        <Solution solution={row.solution} insight={row.insight} trap={row.trap} />
                      </div>
                    );
                  })()}
                </li>
              ))}
            </ol>
          ) : (
            <div className="am-table-wrap">
              <table className="am-table">
                <thead><tr><th>#</th><th>Topic</th><th>Technique</th><th className="num">Rating</th></tr></thead>
                <tbody>
                  {problems.map((p) => (
                    <tr key={p.number}>
                      <td>{p.number}</td>
                      <td><span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}><CategoryDot category={p.category} />{p.topic_name}</span></td>
                      <td className="am-muted">{p.technique_name}</td>
                      <td className="num"><Difficulty value={p.difficulty} rating={p.rating} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {official && (
            <p className="am-muted" style={{ fontSize: 12, margin: '12px 0 0' }}>
              {written === c.count
                ? "Problems © MAA, figures redrawn. The topics and solutions are Summit's own."
                : `Topics are guessed from the wording${written ? ' where Summit has no write-up' : ''}. Problems © MAA${written ? "; the solutions are Summit's own" : ''}.`}{' '}
              {data.can_import && (
                <button type="button" className="am-link am-link-button" onClick={() => void unimport()}>Remove import</button>
              )}
            </p>
          )}
        </section>
        <aside className="am-stack">
          {keyCard}
          <section className="am-card">
            <div className="am-card-head"><h2>Before you start</h2></div>
            <ul className="am-list" style={{ display: 'grid', gap: 8 }}>
              <li>You need {c.minutes} minutes. The clock keeps running if you leave.</li>
              <li>Pencil and paper. No calculator.</li>
              {c.level !== 'AIME' && <li>A blank is worth 1.5, so skip what you can't narrow down.</li>}
              <li>Wrong and blank answers go to Review.</li>
            </ul>
          </section>
          {logCard}
          <section className="am-card">
            <div className="am-card-head"><h2>Your sittings</h2></div>
            <History rows={data.history} onDelete={(id) => void remove(id)} />
          </section>
        </aside>
      </div>
    </div>
  );
}
