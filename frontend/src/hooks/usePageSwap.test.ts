import { act, renderHook } from '@testing-library/react';
import { StrictMode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { usePageSwap } from './usePageSwap';

afterEach(() => vi.useRealTimers());

describe('usePageSwap', () => {
  it('adds nothing on the first arrival, even with StrictMode running the effects twice', () => {
    const { result } = renderHook(({ id, loading }) => usePageSwap(id, loading), {
      initialProps: { id: 'a', loading: true }, wrapper: StrictMode,
    });
    expect(result.current).toBe('');
  });

  it('dims from the moment the subject changes until its read is back, then arrives again', () => {
    const { result, rerender } = renderHook(({ id, loading }) => usePageSwap(id, loading), {
      initialProps: { id: 'a', loading: false },
    });
    // The new address, the old data still showing: dimmed at once.
    rerender({ id: 'b', loading: false });
    expect(result.current).toBe('pg-leave');
    rerender({ id: 'b', loading: true });
    expect(result.current).toBe('pg-leave');
    rerender({ id: 'b', loading: false });
    expect(result.current).toBe('pg-swap');
    // A reload of the same subject (an answer checked) changes nothing.
    rerender({ id: 'b', loading: true });
    rerender({ id: 'b', loading: false });
    expect(result.current).toBe('pg-swap');
    // And the next one dims again.
    rerender({ id: 'c', loading: false });
    expect(result.current).toBe('pg-leave');
  });

  it('does not stay dim when no read starts', () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ id, loading }) => usePageSwap(id, loading), {
      initialProps: { id: 'a', loading: false },
    });
    rerender({ id: 'b', loading: false });
    expect(result.current).toBe('pg-leave');
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe('pg-swap');
  });
});
