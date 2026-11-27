/**
 * The phone's navigation (components/PhoneMenu.tsx): below 640px the top bar
 * carries the mark and a menu with every destination, and there is no rail.
 */
import { fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Topbar } from './Topbar';
import { TABS } from './Rail';
import { forgetAmcSummary } from '@/hooks/useAmcSummary';
import { amc } from '@/services/amc';
import { renderWithProviders } from '@/test/render';
import { setMatchMedia } from '@/test/media';

beforeEach(() => {
  forgetAmcSummary();
  vi.spyOn(amc, 'dashboard').mockResolvedValue({
    success: true, stats: { solved: 12, total: 60, attempted: 15, accuracy: 0.8, streak: 3, due: 4, in_review: 5,
                            mastered: 1, minutes: 30, mocks: 1 },
    target: 'AMC 10', projected: { 'AMC 10': 96, 'AMC 12': null, AIME: null },
  } as never);
});
afterEach(() => {
  vi.restoreAllMocks();
  forgetAmcSummary();
  document.body.style.overflow = '';
});

describe('the top bar on a phone', () => {
  it('carries the mark and a menu with every destination, Settings and Sign out', async () => {
    setMatchMedia({ '(max-width: 640px)': true });
    const signOut = vi.fn(async () => {});
    renderWithProviders(<Topbar />, { route: '/topics', auth: { signOut } });
    expect(screen.getByRole('link', { name: /AMC Guide: dashboard/ })).toHaveAttribute('href', '/dashboard');
    const button = screen.getByRole('button', { name: 'Menu: Topics' });
    fireEvent.click(button);
    const menu = within(screen.getByRole('menu', { name: 'Pages' }));
    for (const tab of TABS) expect(menu.getByRole('menuitem', { name: tab.label })).toHaveAttribute('href', tab.to);
    expect(menu.getByRole('menuitem', { name: 'Topics' })).toHaveAttribute('aria-current', 'page');
    expect(menu.getByRole('menuitem', { name: 'Settings' })).toHaveAttribute('href', '/settings');
    expect(await menu.findByText('12 of 60 solved')).toBeInTheDocument();
    // The page under it holds still while it is open.
    expect(document.body.style.overflow).toBe('hidden');
    fireEvent.click(menu.getByRole('menuitem', { name: 'Sign out' }));
    expect(signOut).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('menu', { name: 'Pages' })).not.toBeInTheDocument();
    expect(document.body.style.overflow).toBe('');
  });

  it('closes on Escape and on a tap outside', () => {
    setMatchMedia({ '(max-width: 640px)': true });
    renderWithProviders(<Topbar />);
    fireEvent.click(screen.getByRole('button', { name: /^Menu/ }));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('menu', { name: 'Pages' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^Menu/ }));
    fireEvent.click(screen.getAllByRole('button', { name: 'Close menu' }).find((b) => b.classList.contains('phone-menu-scrim'))!);
    expect(screen.queryByRole('menu', { name: 'Pages' })).not.toBeInTheDocument();
  });

  it('is not there on a wider screen, where the rail is', () => {
    setMatchMedia({ '(max-width: 640px)': false });
    renderWithProviders(<Topbar />);
    expect(screen.queryByRole('button', { name: /^Menu/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /AMC Guide: dashboard/ })).not.toBeInTheDocument();
  });
});
