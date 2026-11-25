/**
 * The front of the hidden chain, run as the plain scripts they are
 * (frontend/secret/door-egg.js, pentagon-egg.js): the dashboard title's ten
 * clicks write the day's unlock and show the clue, and the landing page's
 * pentagon only wakes once that unlock is there.
 */
import { readFileSync } from 'node:fs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const DAY = '2026-11-25';
const KEY = `easterEgg:myles:${DAY}`;

function run(file: string) {
  new Function(readFileSync(`frontend/secret/${file}`, 'utf8'))();
}

/** The dashboard as React renders it: the page marked as the door, and its title. */
function dashboard() {
  document.body.innerHTML = '<div class="amc-page" data-egg="door"><header><h1 class="am-title">345 days to the AMC 10</h1></header></div>';
  return document.querySelector('.am-title') as HTMLElement;
}

/** Ten clicks, `gap` ms apart. */
function knock(el: HTMLElement, times: number, gap = 200) {
  for (let i = 0; i < times; i++) {
    el.click();
    vi.advanceTimersByTime(gap);
  }
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date(`${DAY}T15:00:00`));
  localStorage.clear();
  localStorage.setItem('currentUser', 'myles');
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  document.body.innerHTML = '';
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('the door on the dashboard', () => {
  it('opens on the tenth click in a row: the day is unlocked and the clue shows', () => {
    const title = dashboard();
    run('door-egg.js');
    knock(title, 9);
    expect(localStorage.getItem(KEY)).toBeNull();
    expect(document.getElementById('doorQuote')).toBeNull();
    knock(title, 1);
    expect(localStorage.getItem(KEY)).toBe('1');
    const quote = document.getElementById('doorQuote');
    expect(quote?.textContent).toBe('“The pentagon is the key. Find it.”');
    expect(quote?.classList.contains('show')).toBe(true);
  });

  it('starts counting again after a pause', () => {
    const title = dashboard();
    run('door-egg.js');
    knock(title, 6);
    vi.advanceTimersByTime(3000);
    knock(title, 6);
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('keeps the clue for the rest of the day, and only for this account', () => {
    localStorage.setItem(KEY, '1');
    dashboard();
    run('door-egg.js');
    expect(document.getElementById('doorQuote')?.classList.contains('show')).toBe(true);

    document.body.innerHTML = '';
    localStorage.setItem('currentUser', 'grace');
    dashboard();
    run('door-egg.js');
    expect(document.getElementById('doorQuote')).toBeNull();
  });
});

describe('the pentagon among the stars', () => {
  const landing = () => {
    document.body.innerHTML = '<div class="lp"><main><section class="lp-final"><svg class="lp-pentagon"></svg></section></main></div>';
    return document.querySelector('.lp-pentagon') as SVGElement;
  };

  it('stays asleep until the door has been opened today', () => {
    const pent = landing();
    run('pentagon-egg.js');
    expect(pent.style.pointerEvents).toBe('');
  });

  it('wakes once it has, and three clicks leave an arrow into the void', () => {
    localStorage.setItem(KEY, '1');
    const pent = landing();
    run('pentagon-egg.js');
    expect(pent.style.pointerEvents).toBe('auto');
    for (let i = 0; i < 3; i++) pent.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    vi.advanceTimersByTime(720 + 820 + 1300 + 50);
    expect(document.getElementById('pentArrow')).not.toBeNull();
    expect(document.body.classList.contains('pent-void')).toBe(true);
  });
});
