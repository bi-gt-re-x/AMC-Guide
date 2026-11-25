/**
 * The study plan: which contest, when, what score, how many hours a week. The
 * weeks are rebuilt from those four answers and your results every time the
 * page opens (backend/amc/engine.py plan_weeks), so the focus topics follow
 * your weak spots as they move: Foundations, Core, Contest mode, then a taper
 * in the exam's own week. Topics are scheduled by the points studying them
 * would add, each trained the way its kind of weakness wants
 * (backend/amc/planning.py).
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useNotice, ErrorState, Loading } from '@/components';
import { CategoryDot, Meter, PageHeader } from '@/components/Amc/bits';
import { useApi, useDocumentTitle } from '@/hooks';
import {
  amc,
  announceAmcChanged,
  shortDate,
  type CategoryId,
  type Level,
  type PlanDetails,
  type PlanPayload,
  type PlanSettings,
  type PlanLevel,
  type PlanDay,
  type PlanWeek,
  type SubjectStrength,
  type TodayItem,
} from '@/services/amc';
import { MixBar, ModeTag, PrioritiesCard, WeaknessKinds } from '@/components/Amc/Study';
import { isRestDay, TodayList } from './Dashboard';
import '@/styles/amc.css';

const LEVELS: Level[] = ['AMC 10', 'AMC 12', 'AIME'];
const MAX: Record<Level, number> = { 'AMC 10': 150, 'AMC 12': 150, AIME: 15 };

const EXPERIENCE: { key: NonNullable<PlanDetails['experience']>; label: string }[] = [
  { key: 'first', label: 'First time' },
  { key: 'taken', label: 'Taken it before' },
  { key: 'qualified', label: 'Made the AIME before' },
];

/** Topic chips that toggle membership of a list. */
function TopicPicker({
  topics,
  value,
  onChange,
  exclude,
}: {
  topics: { id: string; name: string; category: CategoryId }[];
  value: string[];
  onChange: (next: string[]) => void;
  exclude: string[];
}) {
  return (
    <div className="am-chips">
      {topics.filter((t) => !exclude.includes(t.id)).map((t) => {
        const on = value.includes(t.id);
        return (
          <button key={t.id} type="button" className={`am-chip${on ? ' is-on' : ''}`} aria-pressed={on}
                  onClick={() => onChange(on ? value.filter((x) => x !== t.id) : [...value, t.id])}>
            {t.name}
          </button>
        );
      })}
    </div>
  );
}

const STRENGTHS: { key: SubjectStrength; label: string }[] = [
  { key: 'weak', label: 'Weak' }, { key: 'ok', label: 'Okay' }, { key: 'strong', label: 'Strong' },
];

/**
 * How strong the student feels in each subject — a tap each — with an
 * optional box per subject for anything more ("fine until circles", "slow at
 * casework"). The plan leans on these while there are few answers, and the
 * answers take over as they come (backend/amc/planning.py `subject_lean`).
 */
export function SubjectStrengths({ categories, details, onChange }: {
  categories: { id: CategoryId; name: string }[];
  details: PlanDetails;
  onChange: (next: PlanDetails) => void;
}) {
  if (!categories.length) return null;
  const subjects = details.subjects ?? {};
  const notes = details.subject_notes ?? {};
  return (
    <div className="am-field am-field-wide">
      <span>How strong are you in each subject?</span>
      <div className="am-subjects">
        {categories.map((c) => (
          <div key={c.id} className="am-subject">
            <span className="am-subject-name"><CategoryDot category={c.id} /> {c.name}</span>
            <div className="am-seg" role="radiogroup" aria-label={`${c.name}: how strong`}>
              {STRENGTHS.map((s) => (
                <button key={s.key} type="button" role="radio" aria-checked={subjects[c.id] === s.key}
                        className={subjects[c.id] === s.key ? 'is-on' : ''}
                        onClick={() => onChange({ ...details, subjects: { ...subjects, [c.id]: subjects[c.id] === s.key ? undefined : s.key } })}>
                  {s.label}
                </button>
              ))}
            </div>
            <input className="am-input am-subject-note" maxLength={200} aria-label={`More on ${c.name} (optional)`}
                   placeholder="More on this (optional)" value={notes[c.id] ?? ''}
                   onChange={(e) => onChange({ ...details, subject_notes: { ...notes, [c.id]: e.target.value } })} />
          </div>
        ))}
      </div>
    </div>
  );
}

function PlanForm({
  initial,
  defaults,
  onSaved,
  onCancel,
}: {
  initial: (PlanSettings & { details?: PlanDetails }) | null;
  defaults: PlanPayload['defaults'];
  onSaved: (payload: PlanPayload, fresh: boolean) => void;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<PlanSettings>(
    initial
      ? { target: initial.target, exam_date: initial.exam_date, goal_score: initial.goal_score, hours: initial.hours }
      : { target: 'AMC 10', exam_date: defaults.dates['AMC 10'], goal_score: defaults.goals['AMC 10'], hours: 5 },
  );
  const [details, setDetails] = useState<PlanDetails>(initial?.details ?? {});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const { data: topicData } = useApi(() => amc.topics(), []);
  const { notify } = useNotice();
  const topics = (topicData?.categories ?? [])
    .flatMap((c) => c.topics)
    .filter((t) => t.levels.includes(form.target));

  const pick = (target: Level) =>
    setForm((f) => ({
      ...f,
      target,
      exam_date: initial?.target === target ? initial.exam_date : defaults.dates[target],
      goal_score: initial?.target === target ? initial.goal_score : defaults.goals[target],
    }));
  const set = <K extends keyof PlanDetails>(key: K, value: PlanDetails[K]) =>
    setDetails((d) => ({ ...d, [key]: value }));

  async function save() {
    setBusy(true);
    setMessage('');
    try {
      const reply = await amc.savePlan({ ...form, details });
      if (reply.success) {
        announceAmcChanged();
        notify(initial ? 'Plan updated' : 'Plan built', { body: 'Your weeks are laid out below.' });
        onSaved(reply, !initial || initial.target !== form.target);
      } else setMessage(reply.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="am-card">
      <div className="am-card-head"><h2>{initial ? 'Edit your plan' : 'Build your plan'}</h2></div>
      <div className="am-form">
        <div className="am-field am-field-wide">
          <span>Contest</span>
          <div className="am-seg" role="group" aria-label="Contest">
            {LEVELS.map((l) => (
              <button key={l} type="button" className={form.target === l ? 'is-on' : ''} onClick={() => pick(l)}>{l}</button>
            ))}
          </div>
        </div>
        <label className="am-field">
          <span>Exam date</span>
          <input className="am-input" type="date" value={form.exam_date}
                 onChange={(e) => setForm({ ...form, exam_date: e.target.value })} />
        </label>
        <label className="am-field">
          <span>Goal score (of {MAX[form.target]})</span>
          <input className="am-input" type="number" min={1} max={MAX[form.target]} step={form.target === 'AIME' ? 1 : 1.5}
                 value={form.goal_score} onChange={(e) => setForm({ ...form, goal_score: Number(e.target.value) })} />
        </label>
        <label className="am-field">
          <span>Hours per week</span>
          <input className="am-input" type="number" min={1} max={40} value={form.hours}
                 onChange={(e) => setForm({ ...form, hours: Number(e.target.value) })} />
        </label>
        <label className="am-field">
          <span>Days per week</span>
          <input className="am-input" type="number" min={1} max={7} placeholder="e.g. 4"
                 value={details.days_per_week ?? ''}
                 onChange={(e) => set('days_per_week', e.target.value ? Number(e.target.value) : undefined)} />
        </label>
      </div>

      <h3 className="am-form-sub">About you <span className="am-muted">(optional)</span></h3>
      <div className="am-form">
        <div className="am-field am-field-wide">
          <span>Experience</span>
          <div className="am-seg" role="group" aria-label="Experience">
            {EXPERIENCE.map((e) => (
              <button key={e.key} type="button" className={details.experience === e.key ? 'is-on' : ''}
                      onClick={() => set('experience', details.experience === e.key ? undefined : e.key)}>{e.label}</button>
            ))}
          </div>
        </div>
        <label className="am-field">
          <span>Last real score</span>
          <input className="am-input" type="number" min={0} max={MAX[form.target]} step={form.target === 'AIME' ? 1 : 1.5}
                 placeholder="If you have one" value={details.last_score ?? ''}
                 onChange={(e) => set('last_score', e.target.value ? Number(e.target.value) : undefined)} />
        </label>
        <label className="am-field">
          <span>Books, courses, sites</span>
          <input className="am-input" maxLength={300} placeholder="e.g. AoPS Intro to Counting, Alcumus"
                 value={details.resources ?? ''} onChange={(e) => set('resources', e.target.value)} />
        </label>
        <SubjectStrengths categories={topicData?.categories ?? []} details={details} onChange={setDetails} />
        <details className="am-field am-field-wide am-more">
          <summary>Specific topics you're strong or weak at <span className="am-muted">(optional)</span></summary>
          <div className="am-field am-field-wide">
            <span>Strong at</span>
            <TopicPicker topics={topics} value={details.strong ?? []} exclude={details.weak ?? []}
                         onChange={(v) => set('strong', v)} />
          </div>
          <div className="am-field am-field-wide">
            <span>Weak at</span>
            <TopicPicker topics={topics} value={details.weak ?? []} exclude={details.strong ?? []}
                         onChange={(v) => set('weak', v)} />
          </div>
        </details>
        <label className="am-field am-field-wide">
          <span>Anything else</span>
          <textarea className="am-input" maxLength={1000}
                    placeholder="Schedule limits, what usually goes wrong on contest day, other contests you're doing…"
                    value={details.notes ?? ''} onChange={(e) => set('notes', e.target.value)} />
        </label>
      </div>
      <p className="am-muted" style={{ fontSize: 12, lineHeight: 1.5, margin: '12px 0 0' }}>
        You qualify for the AIME with {defaults.goals['AMC 10']} on the AMC 10 or {defaults.goals['AMC 12']} on the AMC 12.
      </p>
      {message && <p className="am-error">{message}</p>}
      <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
        <button type="button" className="am-btn am-btn-primary" disabled={busy} onClick={() => void save()}>
          {initial ? 'Save changes' : 'Make my plan'}
        </button>
        {onCancel && <button type="button" className="am-btn am-btn-ghost" onClick={onCancel}>Cancel</button>}
      </div>
    </section>
  );
}

/**
 * The AI coach's plan, and the way to ask for it, refine it with answers to
 * its follow-up questions, or have it rewritten.
 */
/** Whether week `n` falls in a phase's "1-16" (or "17–34", or "49"). */
function inWeeks(range: string, n: number) {
  const [lo, hi] = range.split(/[-–]/).map((x) => parseInt(x, 10));
  if (lo == null || Number.isNaN(lo)) return false;
  return n >= lo && n <= (hi == null || Number.isNaN(hi) ? lo : hi);
}

function CoachCard({
  payload,
  busy,
  error,
  onRun,
}: {
  payload: PlanPayload;
  busy: boolean;
  error: string;
  onRun: (answers: Record<string, string>) => void;
}) {
  const written = payload.plan?.coach ?? null;
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const names = new Map((payload.coverage ?? []).map((t) => [t.id, t] as const));
  const answered = Object.values(answers).some((a) => a.trim());
  const thisWeek = payload.weeks?.find((w) => w.current)?.number ?? null;

  if (!payload.ai.available && !written) {
    return (
      <section className="am-card am-coach">
        <div className="am-card-head"><h2>Coach</h2></div>
        <p className="am-muted" style={{ margin: 0, fontSize: 13, lineHeight: 1.6 }}>
          To turn this on, add <code>GROQ_API_KEY</code> to <code>.env</code> (or <code>XAI_API_KEY</code> with{' '}
          <code>MILESTONE_PROVIDER=grok</code>) and restart the server.
        </p>
      </section>
    );
  }

  if (!written) {
    return (
      <section className="am-card am-coach">
        <div className="am-card-head"><h2>Coach</h2></div>
        <p style={{ margin: '0 0 12px', lineHeight: 1.6, color: 'var(--am-body)' }}>
          Get a plan written from your details and results: phases, a weekly routine and milestones.
        </p>
        {error && <p className="am-error">{error}</p>}
        <button type="button" className="am-btn am-btn-primary" disabled={busy} onClick={() => onRun({})}>
          {busy ? 'Writing your plan…' : 'Write my plan'}
        </button>
        {busy && <p className="am-muted" style={{ fontSize: 12, margin: '8px 0 0' }}>This can take up to a minute.</p>}
      </section>
    );
  }

  return (
    <section className="am-card am-coach">
      <div className="am-card-head">
        <h2>Coach's plan</h2>
        <span className="am-muted" style={{ fontSize: 12 }}>
          {payload.plan?.coach_at ? `Written ${shortDate(payload.plan.coach_at)}` : ''}
        </span>
      </div>
      <p className="am-coach-summary">{written.summary}</p>

      {(written.this_week?.length ?? 0) > 0 && (
        <>
          <h3 className="am-form-sub">This week</h3>
          <ol className="am-coach-now">{written.this_week!.map((t, i) => <li key={i}>{t}</li>)}</ol>
        </>
      )}

      <h3 className="am-form-sub">Phases</h3>
      <ol className="am-coach-phases">
        {written.phases.map((p, i) => {
          const isNow = thisWeek != null && inWeeks(p.weeks, thisWeek);
          return (
            <li key={i} className={`am-coach-phase${isNow ? ' is-now' : ''}`}>
              <div className="am-coach-phase-head">
                <strong>{p.name}</strong>
                <span className="am-muted">Weeks {p.weeks}{isNow ? ' · now' : ''}</span>
              </div>
              <p>{p.goal}</p>
              {isNow && p.focus_topics.length > 0 && (
                <div className="am-week-focus">
                  {p.focus_topics.map((id) => (
                    <Link key={id} className="am-tag" to={`/topics/${id}`}>
                      {names.get(id) && <CategoryDot category={names.get(id)!.category} />}{names.get(id)?.name ?? id}
                    </Link>
                  ))}
                </div>
              )}
              {isNow && p.routine && <p className="am-muted" style={{ fontSize: 13 }}>{p.routine}</p>}
            </li>
          );
        })}
      </ol>

      {(written.weekly_schedule.length > 0 || written.milestones.length > 0 || written.tips.length > 0) && (
        <details className="am-coach-more">
          <summary>A typical week, milestones and habits</summary>
          {written.weekly_schedule.length > 0 && (
            <ul className="am-coach-week">
              {written.weekly_schedule.map((d, i) => (
                <li key={i}><strong>{d.day}</strong><span>{d.task}</span><em>{d.minutes} min</em></li>
              ))}
            </ul>
          )}
          {written.milestones.length > 0 && (
            <ul className="am-list">
              {written.milestones.map((m, i) => (
                <li key={i}><span>{m.target}</span><span className="am-muted">Week {m.week}</span></li>
              ))}
            </ul>
          )}
          {written.tips.length > 0 && (
            <ul className="am-coach-tips">{written.tips.slice(0, 3).map((t, i) => <li key={i}>{t}</li>)}</ul>
          )}
        </details>
      )}

      {written.questions.length > 0 && (
        <div className="am-coach-questions">
          <h3 className="am-form-sub">The coach would like to know</h3>
          {written.questions.map((q) => (
            <label key={q} className="am-field">
              <span style={{ textTransform: 'none', letterSpacing: 0, fontSize: 13, color: 'var(--am-ink)' }}>{q}</span>
              <input className="am-input" value={answers[q] ?? ''}
                     onChange={(e) => setAnswers((a) => ({ ...a, [q]: e.target.value }))} />
            </label>
          ))}
        </div>
      )}

      {error && <p className="am-error">{error}</p>}
      <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
        {written.questions.length > 0 && (
          <button type="button" className="am-btn am-btn-primary" disabled={busy || !answered} onClick={() => onRun(answers)}>
            {busy ? 'Refining…' : 'Refine with my answers'}
          </button>
        )}
        <button type="button" className="am-btn" disabled={busy || !payload.ai.available} onClick={() => onRun({})}>
          {busy && written.questions.length === 0 ? 'Rewriting…' : 'Rewrite plan'}
        </button>
      </div>
    </section>
  );
}

type Phase = PlanWeek['phase'];
const PHASE_ABOUT: Record<Phase, string> = {
  Foundations: 'Learn each topic and work its easier problems untimed.',
  Core: 'Practise the topics again, faster, with a mock every few weeks.',
  'Contest mode': 'A timed mock each week; topics at contest pace and mixed together.',
  Taper: 'Light review, nothing new, rest.',
};
const phaseClass = (p: Phase) => `am-phase-${p.split(' ')[0]}`;

/** The weeks in runs of one phase each, in order. */
function phaseRuns(weeks: PlanWeek[]) {
  const runs: { phase: Phase; weeks: PlanWeek[] }[] = [];
  for (const w of weeks) {
    const last = runs[runs.length - 1];
    if (last && last.phase === w.phase) last.weeks.push(w);
    else runs.push({ phase: w.phase, weeks: [w] });
  }
  return runs;
}

/**
 * The top of the plan: where you are and what this week is for, in words.
 * Weeks left and the phase, the score now against the goal, each focus topic
 * with how it is trained and why it was picked, and when the next phase starts.
 */
function NowCard({ payload, weeks, practice }: {
  payload: PlanPayload; weeks: PlanWeek[]; practice?: TodayItem;
}) {
  const plan = payload.plan!;
  const current = weeks.find((w) => w.current);
  const next = current ? weeks.find((w) => w.number > current.number && w.phase !== current.phase) : weeks[0];
  const now = payload.start?.current ?? payload.projected ?? null;
  const left = weeks.filter((w) => !w.past).length;
  const gap = now != null ? Math.round((plan.goal_score - now) * 2) / 2 : null;
  return (
    <section className="am-card am-now">
      <dl className="am-now-facts">
        <div>
          <dt>Time left</dt>
          <dd><strong>{left}</strong> week{left === 1 ? '' : 's'}</dd>
          <dd className="am-muted">{plan.days_left} days to the {plan.target}</dd>
        </div>
        <div>
          <dt>Score</dt>
          {now != null ? (
            <>
              <dd><strong>{now}</strong> now, goal {plan.goal_score}</dd>
              <dd className="am-muted">{gap! > 0 ? `${gap} points to go` : 'At your goal. Keep it there.'}</dd>
            </>
          ) : (
            <>
              <dd>Goal {plan.goal_score}</dd>
              <dd className="am-muted"><Link className="am-link" to="/mock-contests">Sit a timed mock</Link> to see where you start.</dd>
            </>
          )}
        </div>
        <div>
          <dt>This week</dt>
          {current ? (
            <>
              <dd><strong>{current.answered ?? 0}</strong> of {current.problems} problems</dd>
              <dd className="am-muted">
                Week {current.number}, {current.phase}{current.mock ? (current.mock_done ? ' · mock done' : ' · plus a timed mock') : ''}
              </dd>
            </>
          ) : <dd className="am-muted">The plan starts {weeks[0] ? shortDate(weeks[0].start) : 'soon'}.</dd>}
        </div>
      </dl>

      {current && (
        <div className="am-now-focus">
          <h3 className="am-form-sub">What this week is for</h3>
          {current.focus.length ? (
            <ul>
              {current.focus.map((f) => (
                <li key={f.id}>
                  <Link className="am-now-topic" to={`/topics/${f.id}`}><CategoryDot category={f.category} />{f.name}</Link>
                  {f.mode_label && <span className="am-now-mode">{f.mode_label}</span>}
                  {f.reason && <span className="am-muted">{f.reason}</span>}
                </li>
              ))}
            </ul>
          ) : <p className="am-muted">{current.note}</p>}
          <p className="am-now-phase">
            <strong>{current.phase}:</strong> {PHASE_ABOUT[current.phase]}
            {next && <span className="am-muted"> {next.phase} starts {shortDate(next.start)}.</span>}
          </p>
        </div>
      )}
      {practice && !practice.done && (
        <Link className="am-btn am-btn-primary am-week-start" to={practice.to}>Start today's set</Link>
      )}
    </section>
  );
}

/** Minutes as "5 h 30 min", "45 min". */
const hours = (m: number) => (m >= 60 ? `${Math.floor(m / 60)} h${m % 60 ? ` ${m % 60} min` : ''}` : `${m} min`);

/** One day of a week: its minutes and what fills them, or a rest day. */
function DayRow({ d }: { d: PlanDay }) {
  return (
    <li className={`am-day${d.today ? ' is-today' : ''}${d.past ? ' is-past' : ''}${d.rest ? ' is-rest' : ''}`}>
      <div className="am-day-when">
        <strong>{d.weekday}</strong>
        <span className="am-muted">{shortDate(d.date)}</span>
        {d.today && <span className="am-day-now">Today</span>}
      </div>
      {d.rest ? (
        <span className="am-muted am-day-rest">Rest</span>
      ) : (
        <ul className="am-day-blocks">
          {d.blocks.map((b, i) => (
            <li key={i} className={b.done ? 'is-done' : ''}>
              <Link className="am-day-label" to={b.to}>{b.label}</Link>
              {b.kind === 'challenge' && <ModeTag mode="challenge" label="challenge" />}
              <span className="am-muted am-day-detail">{b.detail}</span>
              <em>{b.minutes} min</em>
            </li>
          ))}
        </ul>
      )}
      {!d.rest && <span className="am-day-total">{d.minutes} min</span>}
    </li>
  );
}

function WeekRow({ w }: { w: PlanWeek }) {
  const tracked = w.answered !== undefined && w.problems > 0;
  const days = w.past ? [] : w.days ?? [];
  // This week's days show; the weeks ahead open on request.
  const [open, setOpen] = useState(w.current);
  const studyDays = days.filter((d) => !d.rest);
  return (
    <div className={`am-week${w.current ? ' is-current' : ''}${w.past ? ' is-past' : ''}`}>
      <div className="am-week-when">
        <strong>Week {w.number}{w.current ? ' · now' : ''}</strong>
        {shortDate(w.start)} – {shortDate(w.end)}
      </div>
      <div>
        <div className="am-week-focus">
          {w.focus.map((f) => (
            <Link key={f.id} className="am-tag" to={`/topics/${f.id}`}>
              <CategoryDot category={f.category} />{f.name}<ModeTag mode={f.mode} label={f.mode_label} />
            </Link>
          ))}
          {!w.focus.length && <span className="am-muted" style={{ fontSize: 13 }}>{w.note}</span>}
        </div>
      </div>
      <div className="am-week-side">
        {tracked ? (
          <span className="am-week-progress" title={`${w.answered} of ${w.problems} problems answered`}>
            {w.answered}/{w.problems}
            <Meter value={w.answered! / w.problems} tone={w.answered! >= w.problems ? 'good' : 'sage'} />
          </span>
        ) : w.problems > 0 && <span>{w.problems} problems</span>}
        {w.mock && <span className={`am-pill ${w.mock_done ? 'am-pill-solved' : 'am-pill-review'}`}>{w.mock_done ? 'Mock done' : 'Mock'}</span>}
      </div>
      {days.length > 0 && (
        <div className="am-week-days">
          <button type="button" className="am-week-days-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
            {open ? 'Hide days' : `Day by day · ${studyDays.length} study day${studyDays.length === 1 ? '' : 's'}, ${hours(studyDays.reduce((n, d) => n + d.minutes, 0))}`}
          </button>
          {open && <ol className="am-days">{days.map((d) => <DayRow key={d.date} d={d} />)}</ol>}
        </div>
      )}
    </div>
  );
}

/** How many weeks ahead show before "Show all". */
const AHEAD = 4;

/**
 * Week by week, under a heading for each phase. A long plan is fifty rows, so
 * the weeks already done fold into one line and only this week and the next
 * few show until asked for the rest.
 */
function WeekList({ weeks }: { weeks: PlanWeek[] }) {
  const [all, setAll] = useState(false);
  const [showPast, setShowPast] = useState(false);
  const past = weeks.filter((w) => w.past);
  const ahead = weeks.filter((w) => !w.past);
  const shown = [...(showPast ? past : []), ...(all ? ahead : ahead.slice(0, AHEAD))];
  const hidden = ahead.length - Math.min(ahead.length, all ? ahead.length : AHEAD);
  const pastAnswered = past.reduce((n, w) => n + (w.answered ?? 0), 0);
  const pastGoal = past.reduce((n, w) => n + w.problems, 0);
  return (
    <>
      {past.length > 0 && (
        <button type="button" className="am-weeks-fold" onClick={() => setShowPast((v) => !v)} aria-expanded={showPast}>
          {showPast ? 'Hide' : 'Show'} {past.length} week{past.length === 1 ? '' : 's'} done
          <span className="am-muted"> · {pastAnswered} of {pastGoal} problems answered</span>
        </button>
      )}
      <div className="am-weeks">
        {phaseRuns(shown).map((r) => (
          <div key={r.weeks[0]!.number} className="am-weeks-run">
            <div className="am-weeks-head">
              <span className={`am-phase ${phaseClass(r.phase)}`}>{r.phase}</span>
              <span className="am-muted">{PHASE_ABOUT[r.phase]}</span>
            </div>
            {r.weeks.map((w) => <WeekRow key={w.number} w={w} />)}
          </div>
        ))}
      </div>
      {(hidden > 0 || all) && ahead.length > AHEAD && (
        <button type="button" className="am-btn am-btn-ghost am-weeks-more" onClick={() => setAll((v) => !v)}>
          {all ? 'Show fewer weeks' : `Show all ${ahead.length} weeks to the exam`}
        </button>
      )}
    </>
  );
}

/**
 * The level the plan is built from, and how the last two weeks went. Every
 * number here is worked out from the answers each time the page opens, and
 * the plan with it: which topics lead, how each is trained, the difficulty
 * mix and how soon Contest mode starts.
 */
function LevelCard({ level }: { level?: PlanLevel }) {
  if (!level) return null;
  const { recent, before, pace } = level;
  const change = recent.accuracy != null && before.accuracy != null
    ? Math.round((recent.accuracy - before.accuracy) * 100) : null;
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>Your level now</h2></div>
      {level.measured < 5 ? (
        <p className="am-muted am-level-note">
          Answer a few problems and the plan sets itself to your level. Until then it starts a little below the
          goal's.
        </p>
      ) : (
        <>
          <div className="am-level-now">
            <strong>Level {level.level}</strong><span>{level.name}</span>
          </div>
          <p className="am-muted am-level-note">
            {level.means}. Your goal needs level {level.goal_level} ({level.goal_name.toLowerCase()}).
          </p>
        </>
      )}
      <MixBar mix={level.mix} />
      <dl className="am-level-stats">
        <div>
          <dt>Last 14 days</dt>
          <dd>
            {recent.answered ? `${recent.answered} answered · ${Math.round((recent.accuracy ?? 0) * 100)}% right` : 'Nothing answered'}
            {change != null && change !== 0 && (
              <span className={change > 0 ? 'is-up' : 'is-down'}> {change > 0 ? '▲' : '▼'} {Math.abs(change)} pts</span>
            )}
          </dd>
        </div>
        {pace && (
          <div>
            <dt>Pace</dt>
            <dd>{pace.per_week} a week of {pace.planned} planned</dd>
          </div>
        )}
      </dl>
      <p className="am-muted am-card-note">
        The plan re-plans from your answers every time you open it: the focus topics, how each is trained, the
        difficulty mix and when Contest mode starts.
      </p>
    </section>
  );
}

/** Which topics have been touched at all, and the weakest of those that have. */
function CoverageCard({ coverage, target }: { coverage: NonNullable<PlanPayload['coverage']>; target: Level }) {
  const tried = coverage.filter((t) => (t.attempted ?? 0) > 0);
  const untried = coverage.filter((t) => !(t.attempted ?? 0)).sort((a, b) => b.weight - a.weight);
  const weakest = [...tried].sort((a, b) => a.mastery - b.mastery).slice(0, 6);
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>Topic coverage</h2></div>
      <div className="am-coverage-sum">
        <strong>{tried.length}</strong><span className="am-muted"> of {coverage.length} {target} topics practised</span>
      </div>
      <Meter value={coverage.length ? tried.length / coverage.length : 0} />
      {weakest.length > 0 && (
        <>
          <h3 className="am-form-sub">Weakest so far</h3>
          <div className="am-bars">
            {weakest.map((t) => (
              <div key={t.id} className="am-bar-row">
                <Link className="am-bar-label" to={`/topics/${t.id}`}><CategoryDot category={t.category} />{t.name}</Link>
                <span className="am-muted" style={{ fontSize: 12 }}>{Math.round(t.mastery * 100)}%</span>
                <Meter value={t.mastery} />
              </div>
            ))}
          </div>
        </>
      )}
      {untried.length > 0 && (
        <p className="am-muted am-card-note">
          Not started: {untried.slice(0, 4).map((t, i) => (
            <span key={t.id}>{i ? ', ' : ''}<Link className="am-link" to={`/topics/${t.id}`}>{t.name}</Link></span>
          ))}{untried.length > 4 ? ` and ${untried.length - 4} more` : ''}.
        </p>
      )}
    </section>
  );
}

export default function StudyPlan() {
  useDocumentTitle('Study Plan');
  const { data, error, loading, reload } = useApi(() => amc.plan(), []);
  const { notify, confirm } = useNotice();
  const [payload, setPayload] = useState<PlanPayload | null>(null);
  const [editing, setEditing] = useState(false);
  const [coaching, setCoaching] = useState(false);
  const [coachError, setCoachError] = useState('');
  useEffect(() => {
    if (data) setPayload(data);
  }, [data]);

  /** Ask the AI coach to write (or refine) the plan. Up to a minute. */
  async function runCoach(answers: Record<string, string>) {
    setCoaching(true);
    setCoachError('');
    try {
      const reply = await amc.coach(answers);
      if (reply.success) {
        setPayload(reply);
        announceAmcChanged();
      } else {
        setCoachError(reply.message);
      }
    } catch (cause) {
      setCoachError(cause instanceof Error ? cause.message : 'The coach could not be reached.');
    } finally {
      setCoaching(false);
    }
  }

  if (loading && !payload) return <Loading label="Loading your plan" />;
  if (error || !payload) return <ErrorState message={error ?? 'Could not load the plan.'} onRetry={reload} />;

  const { plan } = payload;
  if (!plan || editing) {
    return (
      <div className="amc-page">
        <PageHeader title="Study Plan">
          <p>A week-by-week plan to contest day, weakest topics first.</p>
        </PageHeader>
        <div style={{ maxWidth: 980 }}>
          <PlanForm
            initial={plan}
            defaults={payload.defaults}
            onSaved={(p) => {
              setPayload(p);
              setEditing(false);
              // A new plan, or one without the coach's yet, gets written
              // straight away; an edited one is rewritten on request.
              if (p.ai.available && !p.plan?.coach) void runCoach({});
            }}
            onCancel={plan ? () => setEditing(false) : undefined}
          />
        </div>
      </div>
    );
  }

  const weeks = payload.weeks ?? [];
  const current = weeks.find((w) => w.current);
  // Today's first set, practice or challenge, for the plan's "Start today's set".
  const practice = (payload.today ?? []).find((i) => i.key === 'practice' || i.key === 'challenge');

  async function toggle(key: string, done: boolean) {
    const reply = await amc.check(key, done);
    if (reply.success) {
      setPayload(reply);
      announceAmcChanged();
    }
  }

  async function clear() {
    const yes = await confirm({
      title: 'Delete your study plan?',
      body: 'Your answers and review log are kept.',
      confirmLabel: 'Delete plan',
      danger: true,
    });
    if (!yes) return;
    const reply = await amc.clearPlan();
    if (!reply.success) {
      notify('Could not delete the plan', { body: reply.message, tone: 'bad' });
      return;
    }
    announceAmcChanged();
    notify('Study plan deleted', { tone: 'info' });
    reload();
  }

  return (
    <div className="amc-page">
      <PageHeader
        kicker={`${plan.target} · ${shortDate(plan.exam_date)}`}
        title="Study Plan"
        actions={
          <>
            <button type="button" className="am-btn am-btn-ghost" onClick={() => void clear()}>Delete plan</button>
            <button type="button" className="am-btn" onClick={() => setEditing(true)}>Edit plan</button>
          </>
        }
      >
        <p>
          Goal {plan.goal_score} on the {plan.target}, with {plan.hours} hour{plan.hours === 1 ? '' : 's'} a week.
        </p>
      </PageHeader>

      <div style={{ marginBottom: 16 }}><NowCard payload={payload} weeks={weeks} practice={practice} /></div>

      <div style={{ marginBottom: 16 }}>
        <CoachCard payload={payload} busy={coaching} error={coachError} onRun={(a) => void runCoach(a)} />
      </div>

      <div className="am-grid am-grid-main">
        <section>
          <div style={{ marginBottom: 16 }}><WeaknessKinds kinds={payload.kinds} /></div>
          <h2 className="am-h2" style={{ marginBottom: 12 }}>Week by week</h2>
          <WeekList weeks={weeks} />
        </section>

        <aside className="am-stack">
          <LevelCard level={payload.level} />
          <section className="am-card">
            <div className="am-card-head"><h2>Today</h2></div>
            <TodayList items={payload.today ?? []} onToggle={(item) => void toggle(item.key, !item.done)} rest={isRestDay(current)} />
            {current && <p className="am-muted" style={{ fontSize: 13, lineHeight: 1.5, margin: '12px 0 0' }}>{current.note}</p>}
          </section>
          <PrioritiesCard priorities={payload.priorities} limit={5} title="This plan's priorities" />
          <CoverageCard coverage={payload.coverage ?? []} target={plan.target} />
        </aside>
      </div>
    </div>
  );
}
