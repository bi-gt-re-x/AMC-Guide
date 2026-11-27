/**
 * The phone's navigation: the rail, folded into the top bar.
 *
 * On a phone a side rail costs a quarter of the screen, and the bottom tab bar
 * that replaced it held four of the eight destinations, put the rest behind
 * "More", and took another 62px off the bottom of every page. So below 640px
 * there is no rail (components/Rail.tsx returns nothing): the top bar carries
 * the mark on the left, and this button on the right opens a sheet that drops
 * down from under the bar with every destination, in the rail's two groups,
 * the problems solved, Settings and Sign out. The page itself gets the whole
 * width and height.
 *
 * The sheet closes on a choice, on a tap outside it, on Escape, and whenever
 * the page changes, and the page under it does not scroll while it is open.
 */
import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks';
import { useAmcSummary } from '@/hooks/useAmcSummary';
import { onPage, SETTINGS_TAB, SIGNOUT_ICON, TABS, type Tab } from './Rail';

const GROUPS: { id: Tab['section']; label: string }[] = [
  { id: 'prep', label: 'Prep' },
  { id: 'practice', label: 'Practice' },
];

export function PhoneMenu() {
  const { pathname } = useLocation();
  const { signOut } = useAuth();
  const summary = useAmcSummary();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    // The page under the sheet stays put while it is open.
    const was = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = was;
    };
  }, [open]);

  const here = TABS.find((tab) => onPage(tab, pathname)) ?? (pathname.startsWith('/settings') ? SETTINGS_TAB : null);
  const solved = summary?.stats.solved ?? 0;
  const total = summary?.stats.total ?? 0;
  const target = summary?.target ?? 'AMC 10';
  const projected = summary ? summary.projected[target] : null;

  const link = (tab: Tab) => (
    <NavLink key={tab.to} to={tab.to} role="menuitem"
             className={() => `phone-menu-link${onPage(tab, pathname) ? ' active' : ''}`}
             aria-current={onPage(tab, pathname) ? 'page' : undefined}
             onClick={() => setOpen(false)}>
      {tab.icon}
      <span>{tab.label}</span>
    </NavLink>
  );

  return (
    <>
      <button type="button" className={`topbar-btn phone-menu-button${open ? ' is-on' : ''}`}
              aria-label={open ? 'Close menu' : `Menu${here ? `: ${here.label}` : ''}`}
              aria-haspopup="menu" aria-expanded={open} aria-controls="phone-menu"
              onClick={() => setOpen((was) => !was)}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
          {open ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
        </svg>
      </button>
      {open && (
        <>
          <button type="button" className="phone-menu-scrim" aria-label="Close menu" tabIndex={-1}
                  onClick={() => setOpen(false)} />
          <div className="phone-menu" id="phone-menu" role="menu" aria-label="Pages">
            {GROUPS.map((group) => (
              <section key={group.id} className="phone-menu-group" aria-label={group.label}>
                <h2>{group.label}</h2>
                <div className="phone-menu-grid">{TABS.filter((tab) => tab.section === group.id).map(link)}</div>
              </section>
            ))}
            <div className="phone-menu-foot">
              <div className="phone-menu-progress">
                <span>{solved} of {total || '—'} solved</span>
                <span>{projected != null ? `${target} ≈ ${projected}` : target}</span>
                <div className="phone-menu-bar" role="progressbar" aria-label="Problems solved"
                     aria-valuenow={total ? Math.round((solved / total) * 100) : 0} aria-valuemin={0} aria-valuemax={100}>
                  <i style={{ width: `${total ? (solved / total) * 100 : 0}%` }} />
                </div>
              </div>
              <div className="phone-menu-actions">
                {link(SETTINGS_TAB)}
                <button type="button" role="menuitem" className="phone-menu-link"
                        onClick={() => { setOpen(false); void signOut(); }}>
                  {SIGNOUT_ICON}
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
