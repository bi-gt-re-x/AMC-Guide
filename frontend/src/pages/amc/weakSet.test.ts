/** The weak-topics walk between the Review page and each problem: per tab. */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { readWeakSet, writeWeakSet } from './weakSet';

afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
});

describe('weakSet', () => {
  it('reads back what was written', () => {
    writeWeakSet(['a', 'b']);
    expect(readWeakSet()).toEqual(['a', 'b']);
  });

  it('is empty when nothing was written', () => {
    expect(readWeakSet()).toEqual([]);
  });

  it('ignores anything that is not a list of ids', () => {
    sessionStorage.setItem('amc-weak-set', JSON.stringify({ not: 'a list' }));
    expect(readWeakSet()).toEqual([]);
    sessionStorage.setItem('amc-weak-set', JSON.stringify(['a', 3, null, 'b']));
    expect(readWeakSet()).toEqual(['a', 'b']);
    sessionStorage.setItem('amc-weak-set', '{broken');
    expect(readWeakSet()).toEqual([]);
  });

  it('keeps working when storage is blocked', () => {
    // On the prototype: jsdom's Storage would store an own `setItem` as an item.
    const proto = Object.getPrototypeOf(sessionStorage) as Storage;
    vi.spyOn(proto, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
    vi.spyOn(proto, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
    expect(() => writeWeakSet(['a'])).not.toThrow();
    expect(readWeakSet()).toEqual([]);
  });
});
