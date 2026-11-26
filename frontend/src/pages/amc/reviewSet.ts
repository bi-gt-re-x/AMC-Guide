/**
 * The review set being walked: up to REVIEW_SET due problems, weakest topics
 * first, so a backlog of hundreds is worked through a set at a time. The
 * Review page writes the ids when a set starts, and the problem page's
 * `?review=1` reads them for "k of N" and the next one. Per tab
 * (sessionStorage); with storage blocked the walk falls back to the next due.
 */
const KEY = 'amc-review-set';

/** Matches backend/amc/engine.py REVIEW_SET. */
export const REVIEW_SET = 12;

/** The walk as stored: its problems, and the stored set (amc_set_runs.id) its answers count in. */
export interface SetWalk {
  ids: string[];
  runId: string | null;
}

function readWalk(): SetWalk {
  try {
    const raw = sessionStorage.getItem(KEY);
    const value: unknown = raw ? JSON.parse(raw) : null;
    // A plain list is what this key held before sets were stored.
    const list: unknown = Array.isArray(value) ? value : (value as { ids?: unknown } | null)?.ids;
    const runId: unknown = Array.isArray(value) ? null : (value as { runId?: unknown } | null)?.runId;
    return {
      ids: Array.isArray(list) ? list.filter((id): id is string => typeof id === 'string') : [],
      runId: typeof runId === 'string' && runId ? runId : null,
    };
  } catch {
    return { ids: [], runId: null };
  }
}

function writeWalk(walk: SetWalk): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(walk));
  } catch {
    /* storage blocked: the walk falls back to the next due review */
  }
}

export function readReviewSet(): string[] {
  return readWalk().ids;
}

/** The stored set this walk's answers count in, if one has been started. */
export function readReviewRun(): string | null {
  return readWalk().runId;
}

/** A new review set: a new walk, with the stored set it was started as (or none yet). */
export function writeReviewSet(ids: string[], runId: string | null = null): void {
  writeWalk({ ids, runId: runId });
}

/** Set (or, with null, end) the stored set this walk's answers count in. */
export function setReviewRun(runId: string | null): void {
  writeWalk({ ...readWalk(), runId });
}
