/**
 * The topic practice set being walked (pages/amc/PracticeSet.tsx writes it when
 * the set starts; the problem page's `?set=1` reads it for the next problem,
 * the set's clock and whether to hide the topic). Per tab (sessionStorage), and only
 * a convenience: with storage blocked the walk ends back on the set's page.
 *
 * It also remembers where the walk is (`current`, `answered`) and whether it
 * is over (`finished`, or its clock run out), so a set left part way is the
 * set in progress: highlighted on the study plan and Today, and offered to be
 * continued from its own page.
 *
 * `runId` is the set as the account's database holds it (`amc_set_runs`,
 * POST /api/amc/sets): every answer in the walk carries it, and the set's page
 * reads its report from it at the end. The report is the server's, never
 * worked out from what this tab remembers.
 */
export interface PracticeSetState {
  ids: string[];
  topic: string;
  mode: string;
  title: string;
  /** Seconds a problem should take, for a timed set. */
  seconds: number | null;
  /** A mixed set hides the topic's name until a problem is answered. */
  hideTopic: boolean;
  /** How many problems the set was asked for (the study plan sizes a day's set), or null for the usual. */
  size: number | null;
  /** When a timed set's clock runs out (ms since the epoch): set on Start, the whole set's time. */
  deadline: number | null;
  /** The problem the walk is on. */
  current?: string | null;
  /** The problems answered (or revealed) so far. */
  answered?: string[];
  /** Finished from its last problem, or ended by its clock. */
  finished?: boolean;
  /** The stored set (amc_set_runs.id) its answers are counted in. */
  runId?: string | null;
}

const KEY = 'amc-practice-set';

export function readPracticeSet(): PracticeSetState | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    const value: unknown = raw ? JSON.parse(raw) : null;
    if (!value || typeof value !== 'object') return null;
    const s = value as Partial<PracticeSetState>;
    if (!Array.isArray(s.ids) || typeof s.topic !== 'string') return null;
    return {
      ids: s.ids.filter((id): id is string => typeof id === 'string'),
      topic: s.topic,
      mode: typeof s.mode === 'string' ? s.mode : 'practice',
      title: typeof s.title === 'string' ? s.title : 'Practice set',
      seconds: typeof s.seconds === 'number' ? s.seconds : null,
      hideTopic: Boolean(s.hideTopic),
      size: typeof s.size === 'number' ? s.size : null,
      deadline: typeof s.deadline === 'number' ? s.deadline : null,
      current: typeof s.current === 'string' ? s.current : null,
      answered: Array.isArray(s.answered) ? s.answered.filter((id): id is string => typeof id === 'string') : [],
      finished: Boolean(s.finished),
      runId: typeof s.runId === 'string' && s.runId ? s.runId : null,
    };
  } catch {
    return null;
  }
}

/** Where a set's own page is, with the size it was asked for. */
export function practiceSetHome(s: Pick<PracticeSetState, 'topic' | 'mode' | 'size'>): string {
  return `/practice/${s.topic}?mode=${s.mode}${s.size ? `&n=${s.size}` : ''}`;
}

export function writePracticeSet(state: PracticeSetState): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* storage blocked: the walk falls back to the set's page */
  }
}

/** Change the stored set, if there is one. */
export function updatePracticeSet(patch: Partial<PracticeSetState>): void {
  const now = readPracticeSet();
  if (now) writePracticeSet({ ...now, ...patch });
}

/** The set left part way: started, not finished, clock (if any) not run out. */
export function activePracticeSet(now: number = Date.now()): PracticeSetState | null {
  const s = readPracticeSet();
  if (!s || s.finished || !s.ids.length) return null;
  if (s.deadline != null && s.deadline <= now) return null;
  return s;
}

/** Whether a study plan link (`/practice/<topic>?mode=<mode>…`) is the set in progress. */
export function isActiveSetLink(to: string, active: PracticeSetState | null): boolean {
  if (!active) return false;
  const [path, query = ''] = to.split('?');
  if (path !== `/practice/${active.topic}`) return false;
  return (new URLSearchParams(query).get('mode') || 'practice') === active.mode;
}
