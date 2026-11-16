/**
 * The weak-topics set being walked: the Review page writes the twelve ids when
 * it loads them, and the problem page's `?weak=1` reads them to find the next
 * one. Per tab (sessionStorage), and only a convenience: when storage is
 * blocked the walk ends back on the Review page.
 */
const KEY = 'amc-weak-set';

export function readWeakSet(): string[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    const ids: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(ids) ? ids.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

export function writeWeakSet(ids: string[]): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    /* storage blocked: the walk falls back to the review page */
  }
}
