/**
 * The topic practice set being walked (pages/amc/PracticeSet.tsx writes it when
 * the set starts; the problem page's `?set=1` reads it for the next problem,
 * the set's clock and whether to hide the topic). Per tab (sessionStorage), and only
 * a convenience: with storage blocked the walk ends back on the set's page.
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
