/**
 * The AMC service: the small formatting helpers every AMC page leans on, and
 * that the calls which keep a sitting or an unlock on the account go to the
 * endpoints the backend serves (backend/api/amc.py).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as api from './api';
import { AMC_CHANGED, amc, announceAmcChanged, pct, shortDate, versusReal } from './amc';

afterEach(() => vi.restoreAllMocks());

describe('versusReal', () => {
  it('says nothing without a difficulty', () => {
    expect(versusReal(null, 'AMC 10')).toBe('');
    expect(versusReal(undefined, 'AIME')).toBe('');
  });

  it('calls a small gap "about as hard"', () => {
    expect(versusReal({ average: 4, real: 4.2, vs_real: -0.2 }, 'AMC 10')).toBe('About as hard as a real AMC 10');
  });

  it('says easier or harder, by how much, with the right plural', () => {
    expect(versusReal({ average: 3, real: 4.4, vs_real: -1.4 }, 'AMC 12')).toBe('Plays about 1.4 points easier than a real AMC 12');
    expect(versusReal({ average: 5, real: 4, vs_real: 1 }, 'AIME')).toBe('Plays about 1.0 point harder than a real AIME');
  });
});

describe('pct', () => {
  it('rounds a share to a whole percent', () => {
    expect(pct(0.593)).toBe('59%');
    expect(pct(1)).toBe('100%');
    expect(pct(0)).toBe('0%');
  });

  it('shows a dash for no value', () => {
    expect(pct(null)).toBe('—');
    expect(pct(undefined)).toBe('—');
  });
});

describe('shortDate', () => {
  it('reads the date part only, at midday so no time zone moves it', () => {
    const expected = new Date('2026-11-04T12:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    expect(shortDate('2026-11-04')).toBe(expected);
    expect(shortDate('2026-11-04T23:59:59')).toBe(expected);
  });
});

describe('announceAmcChanged', () => {
  it('fires the event the dashboard listens for', () => {
    const heard = vi.fn();
    window.addEventListener(AMC_CHANGED, heard);
    announceAmcChanged();
    window.removeEventListener(AMC_CHANGED, heard);
    expect(heard).toHaveBeenCalledTimes(1);
  });
});

describe('account-kept contest state', () => {
  it('saves a sitting with PUT to the contest', async () => {
    const put = vi.spyOn(api, 'put').mockResolvedValue({ success: true } as never);
    await amc.saveSitting('2019-amc-10a', { used: 12, answers: { 1: 'A' }, flags: [3] });
    expect(put).toHaveBeenCalledWith('/api/amc/contests/2019-amc-10a/sitting', { used: 12, answers: { 1: 'A' }, flags: [3] });
  });

  it('discards a sitting with DELETE', async () => {
    const del = vi.spyOn(api, 'del').mockResolvedValue({ success: true } as never);
    await amc.discardSitting('step-mock-10');
    expect(del).toHaveBeenCalledWith('/api/amc/contests/step-mock-10/sitting');
  });

  it('unlocks or relocks a paper with PUT', async () => {
    const put = vi.spyOn(api, 'put').mockResolvedValue({ success: true } as never);
    await amc.unlock('2019-amc-10a', false);
    expect(put).toHaveBeenCalledWith('/api/amc/contests/2019-amc-10a/unlock', { on: false });
  });

  it('escapes the contest id in the path', async () => {
    const put = vi.spyOn(api, 'put').mockResolvedValue({ success: true } as never);
    await amc.unlock('a/b', true);
    expect(put).toHaveBeenCalledWith('/api/amc/contests/a%2Fb/unlock', { on: true });
  });
});
