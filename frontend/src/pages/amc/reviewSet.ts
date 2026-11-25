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

export function readReviewSet(): string[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    const ids: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(ids) ? ids.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

export function writeReviewSet(ids: string[]): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    /* storage blocked: the walk falls back to the next due review */
  }
}
