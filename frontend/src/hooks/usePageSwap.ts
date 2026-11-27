import { useEffect, useLayoutEffect, useRef, useState } from 'react';

/** How long to wait for the next subject's read to start before giving up on dimming. */
const NO_READ_MS = 250;

/**
 * The way from one subject to the next on a page that stays mounted while it
 * changes: one problem to the next, one topic, contest, set or mock to another.
 *
 * Such a page keeps showing what it had until the new read lands (useApi keeps
 * the last answer), so without this the old problem sat there as if it were
 * the new one and the new one then appeared in a single frame. Returns the
 * class for the page's `.amc-page` (styles/page-enter.css):
 *
 * * `pg-leave` from the moment `key` changes until its read is back: dimmed.
 * * `pg-swap` once it is: the arrival cascade, played again.
 * * '' before the first change: the page's first arrival is the plain mount
 *   animation every AMC page has.
 *
 * `loading` is whether the page's read is in flight: useApi's `loading ||
 * refreshing` (a read over data already shown is `refreshing`, and that is
 * exactly the case here). The read for a new key starts a
 * render after the key changes, so the page counts as back only once a read
 * has been seen to start and then finish; if none starts (nothing to fetch),
 * it is back at once.
 */
export function usePageSwap(key: string, loading: boolean): string {
  const [phase, setPhase] = useState<'' | 'pg-leave' | 'pg-swap'>('');
  // The subject shown last. Compared rather than a "first run" flag, because
  // StrictMode runs a mount's effects twice and a flag would call the second
  // run a change, dimming and replaying a page that had only just arrived.
  const shown = useRef(key);
  const sawRead = useRef(false);

  // Before paint, so the old subject is never shown undimmed under the new address.
  useLayoutEffect(() => {
    if (shown.current === key) return;
    shown.current = key;
    sawRead.current = false;
    setPhase('pg-leave');
  }, [key]);

  useEffect(() => {
    if (phase !== 'pg-leave') return undefined;
    if (loading) {
      sawRead.current = true;
      return undefined;
    }
    if (sawRead.current) {
      setPhase('pg-swap');
      return undefined;
    }
    const id = window.setTimeout(() => {
      if (!sawRead.current) setPhase('pg-swap');
    }, NO_READ_MS);
    return () => window.clearTimeout(id);
  }, [phase, loading]);

  return phase;
}
