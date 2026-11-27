/**
 * Answers picked in a set but not yet checked, so a refresh part way does not
 * lose them. What *was* checked needs nothing here: every answer in a set is
 * stored on the account with the set's id (amc_attempts.set_id), and the
 * problem page shows it again from that (pages/amc/Problem.tsx).
 *
 * Per tab (sessionStorage), like the sets themselves, and keyed by the set:
 * its stored id once it has one, else its problems. A set's drafts go when it
 * is finished; a new set has a new key, so it starts blank. Only a
 * convenience: with storage blocked a refresh clears the pick, as before.
 */
const KEY = 'amc-set-drafts';
/** How many sets' drafts are kept: the newest few, so old ones do not pile up. */
const KEEP = 6;

type Drafts = Record<string, Record<string, string>>;

function read(): Drafts {
  try {
    const raw = sessionStorage.getItem(KEY);
    const value: unknown = raw ? JSON.parse(raw) : null;
    return value && typeof value === 'object' && !Array.isArray(value) ? (value as Drafts) : {};
  } catch {
    return {};
  }
}

function write(drafts: Drafts): void {
  try {
    const keys = Object.keys(drafts);
    for (const old of keys.slice(0, Math.max(0, keys.length - KEEP))) delete drafts[old];
    sessionStorage.setItem(KEY, JSON.stringify(drafts));
  } catch {
    /* storage blocked: a refresh clears the pick */
  }
}

/** The key a set's drafts are kept under: its stored id, or (before it has one) its problems. */
export function setKey(kind: string, runId: string | null | undefined, ids: string[]): string {
  return runId ? `run:${runId}` : `${kind}:${ids.join(',')}`;
}

export function readDraft(set: string, problemId: string): string {
  const value = read()[set]?.[problemId];
  return typeof value === 'string' ? value : '';
}

/** Keep (or, with '', drop) the answer picked on one problem of a set. */
export function writeDraft(set: string, problemId: string, answer: string): void {
  const drafts = read();
  const mine = { ...(drafts[set] ?? {}) };
  if (answer) mine[problemId] = answer;
  else delete mine[problemId];
  delete drafts[set];
  if (Object.keys(mine).length) drafts[set] = mine;     // re-added last: the newest
  write(drafts);
}

/** A set is over: its drafts go. */
export function clearDrafts(...sets: string[]): void {
  const drafts = read();
  for (const set of sets) delete drafts[set];
  write(drafts);
}
