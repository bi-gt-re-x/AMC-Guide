/**
 * The weak-topics set being walked: the Review page writes the twelve ids when
 * it loads them, and the problem page's `?weak=1` reads them to find the next
 * one. Per tab (sessionStorage), and only a convenience: when storage is
 * blocked the walk ends back on the Review page.
 */
const KEY = 'amc-weak-set';

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
    /* storage blocked: the walk falls back to the review page */
  }
}

export function readWeakSet(): string[] {
  return readWalk().ids;
}

/** The stored set this walk's answers count in, if one has been started. */
export function readWeakRun(): string | null {
  return readWalk().runId;
}

/** The twelve, as the Review page shows them. The same twelve keep the stored set
 *  already started on them; another twelve start without one. */
export function writeWeakSet(ids: string[], runId: string | null = null): void {
  const now = readWalk();
  const same = now.ids.length === ids.length && now.ids.every((id, i) => id === ids[i]);
  writeWalk({ ids, runId: runId ?? (same ? now.runId : null) });
}

/** Set (or, with null, end) the stored set this walk's answers count in. */
export function setWeakRun(runId: string | null): void {
  writeWalk({ ...readWalk(), runId });
}
