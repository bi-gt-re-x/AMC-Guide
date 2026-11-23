/**
 * The last step of sign-up: a handful of taps about the student's contest,
 * and their study plan is made from the answers. Three short screens with a
 * progress bar — the contest, where they are and what they want, then time and
 * (optionally) how strong they feel in each subject — each moving on as soon
 * as it has what it needs.
 *
 * It replaced two screens — a theme and daily-XP-goal picker, then four long
 * free-text questions — that belonged to the productivity app. Everything here
 * is a tap except one optional number, there is no typing to get through, and
 * "Skip" still lands on the dashboard. Theme and the rest live in Settings;
 * anything longer belongs in the study plan's details, where the AI coach
 * reads it.
 */
import { useEffect, useState } from 'react';
import { amc, type CategoryId, type Level, type PlanDetails, type SubjectStrength } from '@/services/amc';
import { completeProfile } from '@/services/auth';

const CONTESTS: { key: Level | 'unsure'; label: string; hint: string }[] = [
  { key: 'AMC 10', label: 'AMC 10', hint: 'Grade 10 and below' },
  { key: 'AMC 12', label: 'AMC 12', hint: 'Grade 12 and below' },
  { key: 'AIME', label: 'AIME', hint: 'Already qualified' },
  { key: 'unsure', label: 'Not sure yet', hint: "We'll start you on the AMC 10" },
];
const GRADES = ['6', '7', '8', '9', '10', '11', '12', 'Other'];
const EXPERIENCE: { key: NonNullable<PlanDetails['experience']>; label: string }[] = [
  { key: 'first', label: 'First time' },
  { key: 'taken', label: "I've taken it" },
  { key: 'qualified', label: "I've made the AIME" },
];
type Aim = 'qualify' | 'high' | 'beat' | 'better';
const AIMS: { key: Aim; label: (level: Level) => string }[] = [
  { key: 'qualify', label: (l) => (l === 'AIME' ? 'Score high enough for USAJMO/USAMO' : 'Qualify for the AIME') },
  { key: 'high', label: (l) => (l === 'AIME' ? 'Score 12 or more' : 'Score 120+ (Honor Roll and up)') },
  { key: 'beat', label: () => 'Beat my last score' },
  { key: 'better', label: () => 'Just get better' },
];
const HOURS: { value: number; label: string }[] = [
  { value: 2, label: '1–2 h' },
  { value: 4, label: '3–5 h' },
  { value: 8, label: '6–10 h' },
  { value: 12, label: '10+ h' },
];
const MAX: Record<Level, number> = { 'AMC 10': 150, 'AMC 12': 150, AIME: 15 };
const SUBJECTS: { id: CategoryId; name: string }[] = [
  { id: 'algebra', name: 'Algebra' }, { id: 'number-theory', name: 'Number Theory' },
  { id: 'counting', name: 'Counting & Probability' }, { id: 'geometry', name: 'Geometry' },
  { id: 'misc', name: 'Logic & Misc' },
];
const STRENGTH: { key: SubjectStrength; label: string }[] = [
  { key: 'weak', label: 'Weak' }, { key: 'ok', label: 'OK' }, { key: 'strong', label: 'Strong' },
];
const STEPS = ['Your contest', 'Where you are', 'Your time'];

/** The goal score a choice means, given the defaults and the last score. */
export function goalFor(level: Level, aim: Aim, last: number | undefined, defaults: Record<Level, number>): number {
  const base = defaults[level];
  if (aim === 'qualify') return level === 'AIME' ? 10 : base;
  if (aim === 'high') return level === 'AIME' ? 12 : 120;
  if (aim === 'beat' && last != null) {
    const step = level === 'AIME' ? 2 : 12;
    const raised = Math.min(MAX[level], last + step);
    return level === 'AIME' ? Math.round(raised) : Math.round(raised * 2) / 2;
  }
  return level === 'AIME' ? Math.max(3, base - 2) : base - 15;
}

function Chips<T extends string | number>({
  label,
  options,
  value,
  onPick,
}: {
  label: string;
  options: { key: T; label: string; hint?: string }[];
  value: T | null;
  onPick: (key: T) => void;
}) {
  return (
    <fieldset className="auth-fieldset">
      <legend className="auth-label">{label}</legend>
      <div className="auth-choices auth-choices-wrap" role="radiogroup" aria-label={label}>
        {options.map((o) => (
          <button key={String(o.key)} type="button" role="radio" aria-checked={value === o.key}
                  className={`auth-choice${value === o.key ? ' is-on' : ''}`} onClick={() => onPick(o.key)}>
            {o.label}
            {o.hint && <span>{o.hint}</span>}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function AmcProfile({ onDone, say }: { onDone: () => void; say: (text: string, kind?: 'info' | 'error') => void }) {
  const [contest, setContest] = useState<Level | 'unsure' | null>(null);
  const [grade, setGrade] = useState<string | null>(null);
  const [experience, setExperience] = useState<PlanDetails['experience'] | null>(null);
  const [aim, setAim] = useState<Aim | null>(null);
  const [hours, setHours] = useState<number | null>(null);
  const [subjects, setSubjects] = useState<Partial<Record<CategoryId, SubjectStrength>>>({});
  const [step, setStep] = useState(0);
  const [last, setLast] = useState('');
  const [busy, setBusy] = useState(false);
  const [defaults, setDefaults] = useState<{ dates: Record<Level, string>; goals: Record<Level, number> } | null>(null);

  useEffect(() => {
    void amc.plan().then((reply) => {
      if (reply.success) setDefaults(reply.defaults);
    }).catch(() => undefined);
  }, []);

  const level: Level = contest && contest !== 'unsure' ? contest : 'AMC 10';
  const lastScore = last.trim() === '' ? undefined : Number(last);
  const ready = contest && aim && hours;

  async function finish(skip: boolean) {
    setBusy(true);
    say(skip ? '' : 'Setting up your plan…', 'info');
    try {
      const profile = await completeProfile({});
      if (!profile.success) {
        say(profile.message || "That didn't work.");
        return;
      }
      if (!skip && ready && defaults) {
        const details: PlanDetails = {};
        if (experience) details.experience = experience;
        if (lastScore != null && !Number.isNaN(lastScore)) details.last_score = lastScore;
        if (grade) details.grade = grade;
        if (Object.keys(subjects).length) details.subjects = subjects;
        const reply = await amc.savePlan({
          target: level,
          exam_date: defaults.dates[level],
          goal_score: goalFor(level, aim!, lastScore, defaults.goals),
          hours: hours!,
          details,
        });
        if (!reply.success) {
          // The account is set up either way; the plan can be made later.
          say(reply.message || 'Your plan was not saved. Make it from Study Plan.');
        } else if (reply.ai.available) {
          // The AI coach writes the personal plan in the background; nobody
          // waits for it, and it is on the Study Plan page when they look.
          void amc.coach().catch(() => undefined);
        }
      }
      onDone();
    } catch {
      say("Couldn't reach the server.");
    } finally {
      setBusy(false);
    }
  }

  const canNext = [Boolean(contest), Boolean(aim), Boolean(hours)][step];

  return (
    <form className="auth-amc" noValidate
          onSubmit={(e) => { e.preventDefault(); if (step < 2) setStep(step + 1); else void finish(false); }}>
      <div className="auth-progress" aria-label={`Step ${step + 1} of 3: ${STEPS[step]}`}>
        {STEPS.map((label, i) => <span key={label} className={i <= step ? 'is-on' : ''} />)}
      </div>
      <p className="auth-step-name">{step + 1} of 3 · {STEPS[step]}</p>

      {step === 0 && (
        <>
          <Chips label="Which contest are you preparing for?" options={CONTESTS} value={contest} onPick={setContest} />
          <Chips label="Your grade (optional)" options={GRADES.map((g) => ({ key: g, label: g }))} value={grade} onPick={setGrade} />
        </>
      )}
      {step === 1 && (
        <>
          <Chips label="Have you taken it before?" options={EXPERIENCE} value={experience ?? null}
                 onPick={(k) => setExperience(k)} />
          {(experience === 'taken' || experience === 'qualified') && (
            <label className="auth-label" htmlFor="amcLast">
              Your last score <span className="auth-optional">(optional, out of {MAX[level]})</span>
              <input id="amcLast" className="auth-input" inputMode="decimal" value={last}
                     placeholder={level === 'AIME' ? 'e.g. 6' : 'e.g. 93'}
                     onChange={(e) => setLast(e.target.value.replace(/[^0-9.]/g, ''))} />
            </label>
          )}
          <Chips label="What's your goal?" options={AIMS.map((a) => ({ key: a.key, label: a.label(level) }))}
                 value={aim} onPick={setAim} />
        </>
      )}
      {step === 2 && (
        <>
          <Chips label="Time each week" options={HOURS.map((h) => ({ key: h.value, label: h.label }))}
                 value={hours} onPick={setHours} />
          <fieldset className="auth-fieldset">
            <legend className="auth-label">How strong are you in each subject? <span className="auth-optional">(optional)</span></legend>
            <div className="auth-subjects">
              {SUBJECTS.map((sub) => (
                <div key={sub.id} className="auth-subject">
                  <span>{sub.name}</span>
                  <div className="auth-choices" role="radiogroup" aria-label={sub.name}>
                    {STRENGTH.map((o) => (
                      <button key={o.key} type="button" role="radio" aria-checked={subjects[sub.id] === o.key}
                              className={`auth-choice auth-choice-sm${subjects[sub.id] === o.key ? ' is-on' : ''}`}
                              onClick={() => setSubjects((m) => ({ ...m, [sub.id]: m[sub.id] === o.key ? undefined : o.key }))}>
                        {o.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </fieldset>
        </>
      )}

      <div className="auth-step-actions">
        {step > 0 && (
          <button type="button" className="auth-link" disabled={busy} onClick={() => setStep(step - 1)}>Back</button>
        )}
        <button type="submit" className="auth-primary" disabled={busy || !canNext || (step === 2 && !ready)}>
          {step < 2 ? 'Next' : busy ? 'Setting up…' : 'Make my plan'}
        </button>
      </div>
      <button type="button" className="auth-link auth-skip" disabled={busy} onClick={() => void finish(true)}>
        Skip for now
      </button>
    </form>
  );
}
