/**
 * Posts: AMC 10, AMC 12 and AIME problems posted by hand, either one problem
 * at a time or a whole test with its answer key (backend/api/amc_posts.py),
 * saved to the database and shared by every account.
 *
 * Write the way AoPS does: math in LaTeX between `$` signs, `$$...$$` or
 * `\[...\]` for a line of its own; `<math>` tags pasted from the wiki work
 * too. The preview beside the form draws it as the list will, in Computer
 * Modern (KaTeX's font, the one AoPS's LaTeX renders in), with the choices
 * laid out in one row like an AoPS problem page. Paste an AMC problem with its
 * choices line still in it and "Pull out the choices" fills the five boxes.
 *
 * A whole test is pasted in one go (AoPS wiki source or plain text, problems
 * numbered) with its answer key beside it; "Read the test" splits it into its
 * 25 problems (15 for the AIME) and fills in the answers, and each problem can
 * then be checked, fixed and given a solution before the test is posted. The
 * answer key grid shows at a glance which problems still need something.
 *
 * Anyone signed in can post. Only the author (or an importer account) sees
 * Edit and Delete.
 */
import { useState, type ReactNode } from 'react';
import { ErrorState, Loading } from '@/components';
import { Empty, PageHeader } from '@/components/Amc/bits';
import { MathText } from '@/components/Amc/MathText';
import { useApi, useDocumentTitle } from '@/hooks';
import { amc, type Level, type Post, type PostDraft, type PostProblem } from '@/services/amc';
import '@/styles/amc.css';

type Kind = 'problem' | 'test';

const LEVELS: Level[] = ['AMC 10', 'AMC 12', 'AIME'];
const LETTERS = ['A', 'B', 'C', 'D', 'E'];
/** How many problems each contest has (backend/amc/catalog.py FORMATS). */
export const TEST_LENGTH: Record<Level, number> = { 'AMC 10': 25, 'AMC 12': 25, AIME: 15 };
const BLANK: PostDraft = { level: 'AMC 10', title: '', statement: '', choices: ['', '', '', '', ''], answer: '', solution: '' };

const blankProblem = (level: Level): PostProblem =>
  ({ statement: '', choices: level === 'AIME' ? null : ['', '', '', '', ''], answer: '', solution: '' });

/** AoPS math markup into `$...$` / `$$...$$`, the same conversion the server makes on save. */
export function toDollars(text: string): string {
  return text
    .replace(/<cmath>([\s\S]*?)<\/cmath>/g, (_, m: string) => `$$${m.trim()}$$`)
    .replace(/<math>([\s\S]*?)<\/math>/g, (_, m: string) => `$${m.trim()}$`)
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, m: string) => `$$${m.trim()}$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, m: string) => `$${m.trim()}$`);
}

/** A choice written without `$` but full of TeX (`\frac12`) is math. */
export function choiceTex(text: string): string {
  const t = toDollars(text.trim());
  return !t.includes('$') && /[\\^_{}]/.test(t) ? `$${t}$` : t;
}

/** What a test problem still needs before the test can be posted, or '' when it has everything. */
export function problemGap(level: Level, p: PostProblem): string {
  if (!p.statement.trim()) return 'needs its text';
  if (level !== 'AIME' && (!p.choices || p.choices.some((c) => !c.trim()))) return 'needs its five choices';
  if (!p.answer) return 'needs its answer';
  return '';
}

/** Text in paragraphs: a blank line starts a new one. */
function Paragraphs({ text }: { text: string }) {
  const parts = toDollars(text).split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return <>{parts.map((p, i) => <MathText key={i} text={p} as="div" className="am-tex-p" />)}</>;
}

/** A problem as AoPS lays it out: the statement, then the choices in one row, then (revealed) the answer and solution. */
function PostBody({ level, problem, reveal, heading = 'Problem' }: {
  level: Level; problem: PostProblem; reveal: boolean; heading?: string;
}) {
  return (
    <div className="am-tex">
      <h3 className="am-tex-h">{heading}</h3>
      {problem.statement.trim() ? <Paragraphs text={problem.statement} /> : <p className="am-muted">The problem will appear here.</p>}
      {level !== 'AIME' && problem.choices && problem.choices.some((c) => c.trim()) && (
        <div className="am-tex-choices">
          {problem.choices.map((c, i) => (
            <span key={i} className={reveal && problem.answer === LETTERS[i] ? 'is-right' : ''}>
              <b>({LETTERS[i]})</b>&nbsp;<MathText text={choiceTex(c) || '…'} />
            </span>
          ))}
        </div>
      )}
      {reveal && (
        <>
          <h3 className="am-tex-h">Answer</h3>
          <p className="am-tex-answer">
            {problem.answer
              ? level === 'AIME' ? <MathText text={`$\\boxed{${problem.answer.padStart(3, '0')}}$`} /> : `(${problem.answer})`
              : <span className="am-muted">Not set yet.</span>}
          </p>
          <h3 className="am-tex-h">Solution</h3>
          {problem.solution.trim() ? <Paragraphs text={problem.solution} /> : <p className="am-muted">No solution posted.</p>}
        </>
      )}
    </div>
  );
}

/** The answer key as a grid of numbered cells. Clicking one opens that problem when `onPick` is given. */
function AnswerKey({ level, answers, current, gaps, onPick }: {
  level: Level; answers: string[]; current?: number; gaps?: string[]; onPick?: (i: number) => void;
}) {
  return (
    <ol className="am-post-key" aria-label="Answer key">
      {answers.map((a, i) => {
        const shown = a ? (level === 'AIME' ? a.padStart(3, '0') : a) : '–';
        const cls = [gaps?.[i] ? 'is-gap' : '', current === i ? 'is-on' : ''].filter(Boolean).join(' ');
        const label = `Problem ${i + 1}: ${a || 'no answer'}${gaps?.[i] ? `, ${gaps[i]}` : ''}`;
        return (
          <li key={i} className={cls}>
            {onPick
              ? <button type="button" aria-label={label} aria-current={current === i} onClick={() => onPick(i)}><small>{i + 1}</small>{shown}</button>
              : <span aria-label={label}><small>{i + 1}</small>{shown}</span>}
          </li>
        );
      })}
    </ol>
  );
}

/** One problem's form fields: text, choices with the right one picked (or the AIME answer), and solution. */
function ProblemFields({ level, value, onChange, rows = 7 }: {
  level: Level; value: PostProblem; onChange: (patch: Partial<PostProblem>) => void; rows?: number;
}) {
  const [message, setMessage] = useState('');
  const aime = level === 'AIME';
  const choices = value.choices ?? ['', '', '', '', ''];
  const canSplit = !aime && !choices.some((c) => c.trim()) && /\(\s*A\s*\)|\{\s*\(A\)/.test(value.statement);

  async function split() {
    setMessage('');
    const reply = await amc.splitChoices(value.statement);
    if (reply.success) onChange({ statement: reply.statement, choices: reply.choices });
    else setMessage(reply.message);
  }

  return (
    <>
      <label className="am-field">
        <span>Problem <small className="am-muted">LaTeX between $ signs; a blank line starts a paragraph</small></span>
        <textarea className="am-input am-code" rows={rows} value={value.statement}
                  placeholder={'What is the value of $\\frac{1}{2} + \\frac{1}{3}$?'}
                  onChange={(e) => onChange({ statement: e.target.value })} />
      </label>
      {!aime && (
        <div className="am-field">
          <span className="am-post-label">
            Answer choices <small className="am-muted">pick the right one</small>
            {canSplit && <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={() => void split()}>Pull out the choices</button>}
          </span>
          <div className="am-post-choices">
            {LETTERS.map((l, i) => (
              <div key={l} className={`am-post-choice${value.answer === l ? ' is-right' : ''}`}>
                <button type="button" aria-pressed={value.answer === l} aria-label={`${l} is the answer`}
                        onClick={() => onChange({ answer: l })}>{l}</button>
                <input className="am-input am-code" value={choices[i]} placeholder={'$5$'} aria-label={`Choice ${l}`}
                       onChange={(e) => onChange({ choices: choices.map((c, j) => (j === i ? e.target.value : c)) })} />
              </div>
            ))}
          </div>
          {message && <p className="am-error" style={{ margin: 0, fontSize: 13 }}>{message}</p>}
        </div>
      )}
      {aime && (
        <label className="am-field">
          <span>Answer <small className="am-muted">a whole number from 0 to 999</small></span>
          <input className="am-input" inputMode="numeric" value={value.answer} style={{ maxWidth: 140 }}
                 onChange={(e) => onChange({ answer: e.target.value.replace(/\D/g, '').slice(0, 3) })} />
        </label>
      )}
      <label className="am-field">
        <span>Solution <small className="am-muted">optional</small></span>
        <textarea className="am-input am-code" rows={rows + 1} value={value.solution}
                  placeholder={'Use a common denominator: $\\frac{3}{6} + \\frac{2}{6} = \\frac{5}{6}$.'}
                  onChange={(e) => onChange({ solution: e.target.value })} />
      </label>
    </>
  );
}

function LevelPicker({ level, onPick }: { level: Level; onPick: (l: Level) => void }) {
  return (
    <div className="am-seg" role="group" aria-label="Contest">
      {LEVELS.map((l) => (
        <button key={l} type="button" className={level === l ? 'is-on' : ''} onClick={() => onPick(l)}>{l}</button>
      ))}
    </div>
  );
}

/** One problem: the form beside its preview. */
function ProblemComposer({ editing, kindSwitch, onSaved, onCancel }: {
  editing: Post | null; kindSwitch: ReactNode; onSaved: () => void; onCancel: () => void;
}) {
  const [draft, setDraft] = useState<PostDraft>(() => editing
    ? { level: editing.level, title: editing.title, statement: editing.statement,
        choices: editing.choices ?? ['', '', '', '', ''], answer: editing.answer, solution: editing.solution }
    : BLANK);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const set = (patch: Partial<PostDraft>) => setDraft((d) => ({ ...d, ...patch }));
  const aime = draft.level === 'AIME';
  const choices = draft.choices ?? ['', '', '', '', ''];

  async function save() {
    setBusy(true);
    setMessage('');
    const body: PostDraft = { ...draft, kind: 'problem', choices: aime ? null : choices };
    try {
      const reply = editing ? await amc.editPost(editing.id, body) : await amc.createPost(body);
      if (reply.success) {
        setDraft(BLANK);
        onSaved();
      } else {
        setMessage(reply.message);
      }
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not save. Try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="am-post-compose">
      <section className="am-card">
        <div className="am-card-head"><h2>{editing ? 'Edit the problem' : 'Post a problem'}</h2></div>
        <div className="am-post-form">
          {kindSwitch}
          <LevelPicker level={draft.level}
                       onPick={(l) => set({ level: l, answer: l === 'AIME' || draft.level === 'AIME' ? '' : draft.answer })} />
          <label className="am-field">
            <span>Title <small className="am-muted">optional, e.g. 2024 AMC 10A Problem 12</small></span>
            <input className="am-input" value={draft.title} maxLength={120} onChange={(e) => set({ title: e.target.value })} />
          </label>
          <ProblemFields level={draft.level} value={{ ...draft, choices }} onChange={set} />
          {message && <p className="am-error" style={{ margin: 0, fontSize: 13 }}>{message}</p>}
          <div className="am-post-actions">
            <button type="button" className="am-btn am-btn-primary" disabled={busy} onClick={() => void save()}>
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Post it'}
            </button>
            {editing && <button type="button" className="am-btn" onClick={onCancel}>Cancel</button>}
          </div>
        </div>
      </section>
      <section className="am-card am-post-preview" aria-label="Preview">
        <div className="am-card-head"><h2>Preview</h2><span className="am-muted" style={{ fontSize: 12 }}>as it will be posted</span></div>
        {draft.title && <p className="am-post-title">{draft.title}</p>}
        <PostBody level={draft.level} problem={{ ...draft, choices }} reveal />
      </section>
    </div>
  );
}

/** A whole test: paste it and its key, read it into problems, check each one, post it. */
function TestComposer({ editing, kindSwitch, onSaved, onCancel }: {
  editing: Post | null; kindSwitch: ReactNode; onSaved: () => void; onCancel: () => void;
}) {
  const [level, setLevel] = useState<Level>(editing?.level ?? 'AMC 10');
  const [title, setTitle] = useState(editing?.title ?? '');
  const [problems, setProblems] = useState<PostProblem[]>(editing?.problems ?? []);
  const [source, setSource] = useState('');
  const [key, setKey] = useState('');
  const [issues, setIssues] = useState<string[]>([]);
  const [open, setOpen] = useState(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const count = TEST_LENGTH[level];
  const gaps = problems.map((p) => problemGap(level, p));
  const ready = gaps.filter((g) => !g).length;
  const started = problems.some((p) => p.statement.trim() || p.answer || p.solution.trim());

  function pickLevel(l: Level) {
    if (l === level) return;
    // AMC 10 and AMC 12 papers have the same shape; the AIME's is different, so its problems start over.
    const reshape = (l === 'AIME') !== (level === 'AIME');
    if (reshape && started && !window.confirm(`Switching to ${l} clears the problems below. Go ahead?`)) return;
    setLevel(l);
    if (reshape) { setProblems([]); setIssues([]); setOpen(0); }
  }

  async function read() {
    setMessage('');
    if (started && !window.confirm(`Replace the ${count} problems below with what you pasted?`)) return;
    setBusy(true);
    try {
      const reply = await amc.parseTest(level, source, key);
      if (reply.success) { setProblems(reply.problems); setIssues(reply.issues); setOpen(0); }
      else setMessage(reply.message);
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not read the test. Try again.');
    } finally {
      setBusy(false);
    }
  }

  function byHand() {
    setProblems(Array.from({ length: count }, () => blankProblem(level)));
    setIssues([]);
    setOpen(0);
  }

  const change = (patch: Partial<PostProblem>) =>
    setProblems((ps) => ps.map((p, i) => (i === open ? { ...p, ...patch } : p)));

  async function save() {
    setBusy(true);
    setMessage('');
    const body: PostDraft = { kind: 'test', level, title, statement: '', choices: null, answer: '', solution: '', problems };
    try {
      const reply = editing ? await amc.editPost(editing.id, body) : await amc.createPost(body);
      if (reply.success) {
        setTitle(''); setProblems([]); setSource(''); setKey(''); setIssues([]); setOpen(0);
        onSaved();
      } else {
        setMessage(reply.message);
        // "Problem 7 needs …": open the problem the server is talking about.
        const n = /problem (\d+)/i.exec(reply.message);
        if (n && Number(n[1]) <= problems.length) setOpen(Number(n[1]) - 1);
      }
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not save. Try again.');
    } finally {
      setBusy(false);
    }
  }

  const pasteFields = (
    <>
      <label className="am-field">
        <span>The test <small className="am-muted">AoPS wiki source or plain text, with each problem numbered</small></span>
        <textarea className="am-input am-code" rows={problems.length ? 5 : 9} value={source}
                  placeholder={'1. What is $1 + 1$?\n(A) 1 (B) 2 (C) 3 (D) 4 (E) 5\n\n2. ...'}
                  onChange={(e) => setSource(e.target.value)} />
      </label>
      <label className="am-field">
        <span>Answer key <small className="am-muted">{level === 'AIME' ? 'e.g. 1. 204  2. 33 …' : 'e.g. BCDAE… or 1. B  2. C …'}</small></span>
        <textarea className="am-input am-code" rows={3} value={key} onChange={(e) => setKey(e.target.value)} />
      </label>
      <div className="am-post-actions">
        <button type="button" className="am-btn am-btn-primary" disabled={busy || !source.trim()} onClick={() => void read()}>
          {busy ? 'Reading…' : 'Read the test'}
        </button>
        {!problems.length && <button type="button" className="am-btn" onClick={byHand}>Type it in by hand</button>}
      </div>
    </>
  );

  const current = problems[open];
  return (
    <div className="am-post-compose">
      <section className="am-card">
        <div className="am-card-head"><h2>{editing ? 'Edit the test' : 'Post a whole test'}</h2></div>
        <div className="am-post-form">
          {kindSwitch}
          <LevelPicker level={level} onPick={pickLevel} />
          <label className="am-field">
            <span>Name <small className="am-muted">e.g. 2024 AMC 10A</small></span>
            <input className="am-input" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} />
          </label>
          {problems.length
            ? <details className="am-post-paste"><summary>Paste the test again</summary><div className="am-post-form">{pasteFields}</div></details>
            : pasteFields}
          {issues.length > 0 && (
            <div className="am-callout am-callout-trap" role="status">
              <span>Check these</span>
              {issues.map((i) => <p key={i}>{i}</p>)}
            </div>
          )}
          {current && (
            <>
              <div className="am-field">
                <span className="am-post-label">
                  Answer key <small className="am-muted">{ready} of {count} problems ready; pick one to edit it</small>
                </span>
                <AnswerKey level={level} answers={problems.map((p) => p.answer)} current={open} gaps={gaps} onPick={setOpen} />
              </div>
              <div className="am-post-problemhead">
                <h3>Problem {open + 1} <small className="am-muted">of {count}</small></h3>
                {gaps[open] && <span className="am-post-gap">{gaps[open]}</span>}
                <span className="am-post-tools">
                  <button type="button" className="am-btn am-btn-ghost am-btn-sm" disabled={open === 0} onClick={() => setOpen(open - 1)}>Previous</button>
                  <button type="button" className="am-btn am-btn-ghost am-btn-sm" disabled={open === count - 1} onClick={() => setOpen(open + 1)}>Next</button>
                </span>
              </div>
              <ProblemFields key={open} level={level} value={current} onChange={change} rows={5} />
            </>
          )}
          {message && <p className="am-error" style={{ margin: 0, fontSize: 13 }}>{message}</p>}
          {(problems.length > 0 || editing) && (
            <div className="am-post-actions">
              <button type="button" className="am-btn am-btn-primary" disabled={busy || !problems.length} onClick={() => void save()}>
                {busy ? 'Saving…' : editing ? 'Save changes' : 'Post the test'}
              </button>
              {editing && <button type="button" className="am-btn" onClick={onCancel}>Cancel</button>}
            </div>
          )}
        </div>
      </section>
      <section className="am-card am-post-preview" aria-label="Preview">
        <div className="am-card-head"><h2>Preview</h2><span className="am-muted" style={{ fontSize: 12 }}>as it will be posted</span></div>
        {title && <p className="am-post-title">{title}</p>}
        {current
          ? <PostBody level={level} problem={current} reveal heading={`Problem ${open + 1}`} />
          : <p className="am-muted">Paste the test and its answer key, then press Read the test. Each problem shows here as you check it.</p>}
      </section>
    </div>
  );
}

function Composer({ editing, onSaved, onCancel }: {
  editing: Post | null; onSaved: () => void; onCancel: () => void;
}) {
  const [kind, setKind] = useState<Kind>(editing?.kind ?? 'problem');
  // An existing post keeps its kind; only a new one can be either.
  const kindSwitch = editing ? null : (
    <div className="am-seg" role="group" aria-label="What to post">
      {([['problem', 'One problem'], ['test', 'A whole test']] as [Kind, string][]).map(([k, label]) => (
        <button key={k} type="button" className={kind === k ? 'is-on' : ''} onClick={() => setKind(k)}>{label}</button>
      ))}
    </div>
  );
  const props = { editing, kindSwitch, onSaved, onCancel };
  return kind === 'test' ? <TestComposer {...props} /> : <ProblemComposer {...props} />;
}

function PostHead({ post, meta, onEdit, onDeleted, onError }: {
  post: Post; meta: string; onEdit: () => void; onDeleted: () => void; onError: (m: string) => void;
}) {
  async function remove() {
    const what = post.kind === 'test' ? 'this test' : 'this problem';
    if (!window.confirm(`Delete ${what} for everyone? This cannot be undone.`)) return;
    const reply = await amc.deletePost(post.id);
    if (reply.success) onDeleted(); else onError(reply.message);
  }
  return (
    <header className="am-post-head">
      <div>
        <p className="am-post-title">{post.title || `${post.level} problem`}</p>
        <span className="am-muted" style={{ fontSize: 12 }}>
          {meta} · posted by {post.author} · {post.created_at.slice(0, 10)}
          {post.updated_at !== post.created_at ? ' · edited' : ''}
        </span>
      </div>
      {post.can_edit && (
        <span className="am-post-tools">
          <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={onEdit}>Edit</button>
          <button type="button" className="am-btn am-btn-ghost am-btn-sm" onClick={() => void remove()}>Delete</button>
        </span>
      )}
    </header>
  );
}

function PostCard({ post, onEdit, onDeleted }: { post: Post; onEdit: () => void; onDeleted: () => void }) {
  const [reveal, setReveal] = useState(false);
  const [message, setMessage] = useState('');
  return (
    <article className="am-card am-post">
      <PostHead post={post} meta={post.level} onEdit={onEdit} onDeleted={onDeleted} onError={setMessage} />
      <PostBody level={post.level} problem={post} reveal={reveal} />
      <button type="button" className="am-btn am-btn-sm" style={{ marginTop: 14 }} onClick={() => setReveal((r) => !r)}>
        {reveal ? 'Hide the answer and solution' : 'Show the answer and solution'}
      </button>
      {message && <p className="am-error" style={{ fontSize: 13 }}>{message}</p>}
    </article>
  );
}

/** A posted test: its problems and its answer key, each behind a button. */
function TestCard({ post, onEdit, onDeleted }: { post: Post; onEdit: () => void; onDeleted: () => void }) {
  const [show, setShow] = useState(false);
  const [reveal, setReveal] = useState(false);
  const [message, setMessage] = useState('');
  const problems = post.problems ?? [];
  const solved = problems.filter((p) => p.solution.trim()).length;
  const meta = `${post.level} · whole test · ${problems.length} problems${solved ? ` · ${solved} with solutions` : ''}`;
  return (
    <article className="am-card am-post">
      <PostHead post={post} meta={meta} onEdit={onEdit} onDeleted={onDeleted} onError={setMessage} />
      <div className="am-post-actions">
        <button type="button" className="am-btn am-btn-sm" aria-expanded={show} onClick={() => setShow((s) => !s)}>
          {show ? 'Hide the problems' : `Show the ${problems.length} problems`}
        </button>
        <button type="button" className="am-btn am-btn-sm" aria-expanded={reveal} onClick={() => setReveal((r) => !r)}>
          {reveal ? 'Hide the answer key' : show ? 'Show the answer key and solutions' : 'Show the answer key'}
        </button>
      </div>
      {reveal && <AnswerKey level={post.level} answers={post.key ?? problems.map((p) => p.answer)} />}
      {show && (
        <div className="am-post-test">
          {problems.map((p, i) => (
            <PostBody key={i} level={post.level} problem={p} reveal={reveal} heading={`Problem ${i + 1}`} />
          ))}
        </div>
      )}
      {message && <p className="am-error" style={{ fontSize: 13 }}>{message}</p>}
    </article>
  );
}

export default function Posts() {
  useDocumentTitle('Posted problems');
  const [level, setLevel] = useState<Level | ''>('');
  const [kind, setKind] = useState<Kind | ''>('');
  const [editing, setEditing] = useState<Post | null>(null);
  const [round, setRound] = useState(0);
  const { data, error, loading, reload } = useApi(() => amc.posts(level, kind), [level, kind, round]);
  const refresh = () => { setEditing(null); setRound((n) => n + 1); };
  const edit = (p: Post) => { setEditing(p); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  return (
    <div className="amc-page">
      <PageHeader kicker="Temporary" title="Posted problems">
        <p>Post AMC 10, AMC 12 and AIME problems one at a time, or a whole test with its answer key. Write math in LaTeX between $ signs, as on AoPS; the preview shows exactly how it will look.</p>
      </PageHeader>

      <Composer key={editing?.id ?? 'new'} editing={editing} onSaved={refresh} onCancel={() => setEditing(null)} />

      <div className="am-post-listhead">
        <h2 className="am-h2">All posts{data ? ` (${data.posts.length})` : ''}</h2>
        <div className="am-post-filters">
          <div className="am-seg" role="group" aria-label="Kind">
            {([['', 'All'], ['problem', 'Problems'], ['test', 'Tests']] as [Kind | '', string][]).map(([k, label]) => (
              <button key={k || 'all'} type="button" className={kind === k ? 'is-on' : ''} onClick={() => setKind(k)}>{label}</button>
            ))}
          </div>
          <div className="am-seg" role="group" aria-label="Contest">
            {(['', ...LEVELS] as (Level | '')[]).map((l) => (
              <button key={l || 'all'} type="button" className={level === l ? 'is-on' : ''} onClick={() => setLevel(l)}>{l || 'All'}</button>
            ))}
          </div>
        </div>
      </div>
      {loading && !data ? <Loading label="Loading posts" />
        : error || !data ? <ErrorState message={error ?? 'Could not load the posts.'} onRetry={reload} />
          : data.posts.length ? (
            <div className="am-stack">
              {data.posts.map((p) => p.kind === 'test'
                ? <TestCard key={p.id} post={p} onDeleted={refresh} onEdit={() => edit(p)} />
                : <PostCard key={p.id} post={p} onDeleted={refresh} onEdit={() => edit(p)} />)}
            </div>
          ) : <Empty title="Nothing posted yet">Post the first problem or test above.</Empty>}
    </div>
  );
}
