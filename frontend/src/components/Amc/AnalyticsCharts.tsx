/**
 * The analytics page's three charts, drawn as SVG sized to their card so text
 * stays crisp at any width, and coloured only with the AMC pages' tokens so
 * they follow light and dark.
 *
 *   ScoreChart        every mock and logged contest score over time, against
 *                     the goal and the AIME qualifying line.
 *   PerformanceChart  week by week: how much was answered (stacked by
 *                     category), first-try accuracy, the average difficulty of
 *                     what was answered, and the week's best test score.
 *   DifficultyChart   first-try accuracy at each point of the 1-12 rating.
 *
 * Each one has a readout under it that names what the pointer (or keyboard
 * focus) is on, which doubles as the chart's text for screen readers.
 */
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import {
  CATEGORY_TONE,
  pct,
  RATING_TOP,
  shortDate,
  type Category,
  type CategoryId,
  type Level,
  type PerformanceWeek,
  type RatingRow,
  type ScorePoint,
} from '@/services/amc';
import { clock } from './bits';

const MAX: Record<Level, number> = { 'AMC 10': 150, 'AMC 12': 150, AIME: 15 };
/** The AIME qualifying score, fixed from the 2026-27 contests. */
const QUALIFY: Partial<Record<Level, number>> = { 'AMC 10': 100, 'AMC 12': 85 };
const CATEGORY_ORDER: CategoryId[] = ['algebra', 'number-theory', 'counting', 'geometry', 'misc'];

const tone = (name: string) => `var(--am-${name})`;

/** The element's content width, kept current as the layout changes. */
function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    setWidth(el.clientWidth);
    if (typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w) setWidth(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width || 640] as const;
}

/** A smooth path through points (monotone in x), so lines read as trends. */
function smooth(points: [number, number][]): string {
  return points.reduce((d, [x1, y1], i) => {
    if (i === 0) return `M${x1},${y1}`;
    const [x0, y0] = points[i - 1] ?? [x1, y1];
    const mx = (x0 + x1) / 2;
    return `${d} C${mx},${y0} ${mx},${y1} ${x1},${y1}`;
  }, '');
}

function Readout({ children }: { children: ReactNode }) {
  return <figcaption className="am-an-readout" aria-live="polite">{children}</figcaption>;
}

function SummaryStat({ label, value, hint, trend }: {
  label: string; value: string; hint?: string; trend?: 'up' | 'down' | null;
}) {
  return (
    <div className="am-an-sum">
      <dt>{label}</dt>
      <dd>
        <strong>{value}</strong>
        {hint && <span className={trend ? `am-an-trend is-${trend}` : 'am-muted'}>{hint}</span>}
      </dd>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mock contest scores
// ---------------------------------------------------------------------------
const fmtScore = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));

export function ScoreChart({ points, target, goal }: { points: ScorePoint[]; target: Level; goal: number }) {
  const levels = (['AMC 10', 'AMC 12', 'AIME'] as Level[]).filter((l) => points.some((p) => p.level === l));
  const [picked, setPicked] = useState<Level | null>(null);
  const level: Level = picked ?? (levels.includes(target) ? target : levels[0] ?? target);
  const rows = points.filter((p) => p.level === level).sort((a, b) => a.at.localeCompare(b.at));
  const [ref, width] = useWidth<HTMLDivElement>();
  const [on, setOn] = useState<number | null>(null);

  const max = MAX[level];
  const goalLine = level === target ? goal : null;
  const qualify = QUALIFY[level] ?? null;
  const H = 280;
  const pad = { l: 44, r: 104, t: 22, b: 34 };
  const iw = Math.max(10, width - pad.l - pad.r);
  const ih = H - pad.t - pad.b;
  // Points sit in from the edges so the first and last dots and their labels are never clipped.
  const inset = Math.min(28, iw / 8);
  const x = (i: number) => pad.l + inset + (rows.length === 1 ? (iw - 2 * inset) / 2 : (i / (rows.length - 1)) * (iw - 2 * inset));
  const y = (v: number) => pad.t + ih - (v / max) * ih;
  // Every paper on one footing: the adjusted score is the result on a typical
  // recent paper (backend/amc/results.py), so a hard year is not a slump.
  const val = (r: ScorePoint) => r.adjusted ?? r.score;
  const xy = rows.map((r, i) => [x(i), y(val(r))] as [number, number]);
  const line = smooth(xy);
  const firstXY = xy[0];
  const lastXY = xy[xy.length - 1];
  const area = xy.length > 1 && firstXY && lastXY ? `${line} L${lastXY[0]},${pad.t + ih} L${firstXY[0]},${pad.t + ih} Z` : '';
  const at = (i: number): [number, number] => xy[i] ?? [0, 0];
  const ticks = [0, 0.2, 0.4, 0.6, 0.8, 1].map((f) => Math.round(max * f));
  const every = Math.max(1, Math.ceil(rows.length / Math.max(2, Math.floor(iw / 90))));

  const latest = rows[rows.length - 1];
  const first = rows[0];
  const best = rows.reduce<ScorePoint | null>((b, r) => (!b || val(r) > val(b) ? r : b), null);
  const avg = rows.length ? rows.reduce((s, r) => s + val(r), 0) / rows.length : null;
  const change = rows.length > 1 && latest && first ? val(latest) - val(first) : null;
  const adjustedAny = rows.some((r) => r.adjusted != null && r.adjusted !== r.score);
  const active = on == null ? null : rows[on];

  function nearest(clientX: number, el: SVGSVGElement) {
    const box = el.getBoundingClientRect();
    const px = ((clientX - box.left) / box.width) * width;
    let closest = 0;
    xy.forEach(([cx], i) => { if (Math.abs(cx - px) < Math.abs(at(closest)[0] - px)) closest = i; });
    setOn(closest);
  }

  return (
    <div className="am-an-score">
      <div className="am-an-score-top">
        <dl className="am-an-sums">
          <SummaryStat label="Latest" value={latest ? fmtScore(val(latest)) : '—'}
                       hint={latest ? (latest.top != null ? `top ~${latest.top}% · ${shortDate(latest.at)}` : shortDate(latest.at)) : `out of ${max}`} />
          <SummaryStat label="Best" value={best ? fmtScore(val(best)) : '—'}
                       hint={best ? (best.top != null ? `${best.name} · top ~${best.top}%` : best.name) : undefined} />
          <SummaryStat label="Average" value={avg == null ? '—' : fmtScore(Math.round(avg * 10) / 10)}
                       hint={`${rows.length} contest${rows.length === 1 ? '' : 's'}`} />
          <SummaryStat label="Since first" value={change == null ? '—' : `${change > 0 ? '+' : ''}${fmtScore(change)}`}
                       hint={change == null ? 'take another' : change > 0 ? 'points up' : change < 0 ? 'points down' : 'no change'}
                       trend={change == null || change === 0 ? null : change > 0 ? 'up' : 'down'} />
        </dl>
        {levels.length > 1 && (
          <div className="am-seg" role="group" aria-label="Contest">
            {levels.map((l) => (
              <button key={l} type="button" className={l === level ? 'is-on' : ''} onClick={() => { setPicked(l); setOn(null); }}>
                {l}
              </button>
            ))}
          </div>
        )}
      </div>

      <figure className="am-an-chart" ref={ref} onMouseLeave={() => setOn(null)}>
        <svg width={width} height={H} role="img"
             aria-label={`${level} contest scores adjusted for each paper's difficulty, oldest first: ${rows.map((r) => fmtScore(val(r))).join(', ')}`}
             onMouseMove={(e) => rows.length && nearest(e.clientX, e.currentTarget)}>
          <defs>
            <linearGradient id="am-an-score-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--am-sage)" stopOpacity="0.32" />
              <stop offset="100%" stopColor="var(--am-sage)" stopOpacity="0" />
            </linearGradient>
          </defs>
          {ticks.map((t) => (
            <g key={t}>
              <line className="am-an-grid" x1={pad.l} x2={pad.l + iw} y1={y(t)} y2={y(t)} />
              <text className="am-an-axis" x={pad.l - 10} y={y(t)} textAnchor="end" dominantBaseline="middle">{t}</text>
            </g>
          ))}
          {qualify != null && qualify !== goalLine && (
            <g>
              <line className="am-an-ref is-qualify" x1={pad.l} x2={pad.l + iw} y1={y(qualify)} y2={y(qualify)} />
              <text className="am-an-ref-label is-qualify" x={pad.l + iw + 10} y={y(qualify)} dominantBaseline="middle">
                AIME cutoff {qualify}
              </text>
            </g>
          )}
          {goalLine != null && (
            <g>
              <line className="am-an-ref is-goal" x1={pad.l} x2={pad.l + iw} y1={y(goalLine)} y2={y(goalLine)} />
              <text className="am-an-ref-label is-goal" x={pad.l + iw + 10} y={y(goalLine)} dominantBaseline="middle">
                {qualify === goalLine ? `Goal · AIME ${goalLine}` : `Goal ${goalLine}`}
              </text>
            </g>
          )}
          {area && <path d={area} fill="url(#am-an-score-fill)" />}
          {xy.length > 1 && <path className="am-an-line" d={line} />}
          {active && on != null && (
            <line className="am-an-guide" x1={at(on)[0]} x2={at(on)[0]} y1={pad.t} y2={pad.t + ih} />
          )}
          {rows.map((r, i) => (
            <g key={r.id}>
              <circle className={`am-an-dot${r.kind === 'logged' ? ' is-logged' : ''}${on === i ? ' is-on' : ''}`}
                      cx={at(i)[0]} cy={at(i)[1]} r={on === i ? 7 : 5} />
              {(i === rows.length - 1 || on === i) && (
                <text className="am-an-dot-label" x={at(i)[0]} y={at(i)[1] - 14} textAnchor="middle">{fmtScore(val(r))}</text>
              )}
              {(i % every === 0 || i === rows.length - 1) && (
                <text className="am-an-axis" x={at(i)[0]} y={H - 10} textAnchor="middle">{shortDate(r.at)}</text>
              )}
            </g>
          ))}
        </svg>
        <Readout>
          {active
            ? [
                `${active.name} · ${fmtScore(active.score)} / ${active.max ?? max}`,
                active.adjusted !== active.score ? `${fmtScore(active.adjusted)} on a typical paper` : '',
                active.top != null ? `top ~${active.top}%` : '',
                active.vs_floor != null ? `${active.vs_floor >= 0 ? '+' : ''}${fmtScore(active.vs_floor)} vs that year's AIME floor ${fmtScore(active.floor ?? 0)}` : '',
                active.award,
                shortDate(active.at),
                active.kind === 'mock' ? 'timed mock' : 'logged score',
              ].filter(Boolean).join(' · ')
            : adjustedAny
              ? `${level} scores out of ${max}, adjusted for each paper's difficulty (the same result on a typical recent paper). Point at a dot for the real score.`
              : `${level} scores out of ${max}. Point at a dot for the contest.`}
        </Readout>
      </figure>
      <ul className="am-an-legend">
        <li><i className="am-an-key is-dot" />Timed mock</li>
        <li><i className="am-an-key is-hollow" />Logged score</li>
        {goalLine != null && <li><i className="am-an-key is-goal" />Your goal</li>}
        {qualify != null && qualify !== goalLine && <li><i className="am-an-key is-qualify" />AIME cutoff</li>}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Performance, week by week
// ---------------------------------------------------------------------------
type Series = 'accuracy' | 'difficulty' | 'tests';
const SERIES: { id: Series; label: string }[] = [
  { id: 'accuracy', label: 'First-try accuracy' },
  { id: 'difficulty', label: `Avg difficulty (of ${RATING_TOP})` },
  { id: 'tests', label: 'Best test score (adjusted)' },
];

export function PerformanceChart({ weeks, categories }: { weeks: PerformanceWeek[]; categories: Category[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [on, setOn] = useState<number | null>(null);
  const [shown, setShown] = useState<Record<Series, boolean>>({ accuracy: true, difficulty: true, tests: true });
  const names = Object.fromEntries(categories.map((c) => [c.id, c.name])) as Record<string, string>;

  const H = 300;
  const pad = { l: 40, r: 48, t: 18, b: 34 };
  const iw = Math.max(10, width - pad.l - pad.r);
  const ih = H - pad.t - pad.b;
  const slot = iw / Math.max(1, weeks.length);
  const barW = Math.min(44, slot * 0.58);
  const cx = (i: number) => pad.l + slot * i + slot / 2;
  const top = Math.max(4, ...weeks.map((w) => w.answered));
  const step = top <= 8 ? 2 : top <= 20 ? 5 : top <= 50 ? 10 : 25;
  const countMax = Math.ceil(top / step) * step;
  const yCount = (v: number) => pad.t + ih - (v / countMax) * ih;
  const yShare = (v: number) => pad.t + ih - v * ih;
  const countTicks = Array.from({ length: countMax / step + 1 }, (_, i) => i * step);

  const accPts = weeks.flatMap((w, i) => (w.accuracy == null ? [] : [[cx(i), yShare(w.accuracy)] as [number, number]]));
  const difPts = weeks.flatMap((w, i) => (w.avg_rating == null ? [] : [[cx(i), yShare(w.avg_rating / RATING_TOP)] as [number, number]]));

  const totals = weeks.reduce((t, w) => ({
    answered: t.answered + w.answered, correct: t.correct + w.correct, days: t.days + w.days, minutes: t.minutes + w.minutes,
  }), { answered: 0, correct: 0, days: 0, minutes: 0 });
  const rated = weeks.filter((w) => w.avg_rating != null);
  const avgRating = rated.length
    ? rated.reduce((s, w) => s + (w.avg_rating ?? 0) * w.answered, 0) / rated.reduce((s, w) => s + w.answered, 0)
    : null;
  const half = Math.floor(weeks.length / 2);
  const early = weeks.slice(0, half).reduce((s, w) => s + w.answered, 0);
  const late = weeks.slice(half).reduce((s, w) => s + w.answered, 0);

  const active = on == null ? null : weeks[on];
  const every = Math.max(1, Math.ceil(weeks.length / Math.max(2, Math.floor(iw / 70))));

  return (
    <div className="am-an-perf">
      <dl className="am-an-sums">
        <SummaryStat label="Answered" value={String(totals.answered)} hint={`last ${weeks.length} weeks`} />
        <SummaryStat label="Accuracy" value={pct(totals.answered ? totals.correct / totals.answered : null)}
                     hint={`${totals.correct} right first time`} />
        <SummaryStat label="Days active" value={String(totals.days)}
                     hint={`${(totals.days / Math.max(1, weeks.length)).toFixed(1)} a week`} />
        <SummaryStat label="Avg difficulty" value={avgRating == null ? '—' : avgRating.toFixed(1)} hint={`of ${RATING_TOP}`} />
        <SummaryStat label="Pace" value={late === early ? 'Steady' : late > early ? 'Rising' : 'Slowing'}
                     hint={`${late} vs ${early} earlier`} trend={late === early ? null : late > early ? 'up' : 'down'} />
      </dl>

      <figure className="am-an-chart" ref={ref} onMouseLeave={() => setOn(null)}>
        <svg width={width} height={H} role="img"
             aria-label={`Problems answered each week for the last ${weeks.length} weeks, by category, with accuracy and difficulty`}>
          {countTicks.map((t) => (
            <g key={t}>
              <line className="am-an-grid" x1={pad.l} x2={pad.l + iw} y1={yCount(t)} y2={yCount(t)} />
              <text className="am-an-axis" x={pad.l - 10} y={yCount(t)} textAnchor="end" dominantBaseline="middle">{t}</text>
            </g>
          ))}
          {(shown.accuracy || shown.difficulty || shown.tests) && [0, 0.5, 1].map((f) => (
            <text key={f} className="am-an-axis" x={pad.l + iw + 10} y={yShare(f)} dominantBaseline="middle">
              {`${Math.round(f * 100)}%`}
            </text>
          ))}
          {weeks.map((w, i) => {
            let base = 0;
            return (
              <g key={w.start} className={`am-an-week${on === i ? ' is-on' : ''}`}>
                <rect className="am-an-hit" x={pad.l + slot * i} y={pad.t} width={slot} height={ih}
                      tabIndex={0} aria-label={`Week of ${shortDate(w.start)}: ${w.answered} answered`}
                      onMouseEnter={() => setOn(i)} onFocus={() => setOn(i)} onClick={() => setOn(i)} />
                {CATEGORY_ORDER.map((c) => {
                  const n = w.by_category[c] ?? 0;
                  if (!n) return null;
                  const y0 = yCount(base);
                  base += n;
                  const y1 = yCount(base);
                  return (
                    <rect key={c} className="am-an-stack" x={cx(i) - barW / 2} y={y1} width={barW}
                          height={Math.max(1, y0 - y1 - 1)} rx={3} fill={tone(CATEGORY_TONE[c])} />
                  );
                })}
                {(i % every === 0 || i === weeks.length - 1) && (
                  <text className="am-an-axis" x={cx(i)} y={H - 10} textAnchor="middle">{shortDate(w.start)}</text>
                )}
              </g>
            );
          })}
          {shown.difficulty && difPts.length > 0 && (
            <>
              {difPts.length > 1 && <path className="am-an-line is-difficulty" d={smooth(difPts)} />}
              {difPts.map(([px, py]) => <circle key={`d${px}`} className="am-an-pt is-difficulty" cx={px} cy={py} r={3.5} />)}
            </>
          )}
          {shown.accuracy && accPts.length > 0 && (
            <>
              {accPts.length > 1 && <path className="am-an-line is-accuracy" d={smooth(accPts)} />}
              {accPts.map(([px, py]) => <circle key={`a${px}`} className="am-an-pt is-accuracy" cx={px} cy={py} r={4} />)}
            </>
          )}
          {shown.tests && weeks.map((w, i) => (w.score_share == null ? null : (
            <rect key={`t${w.start}`} className="am-an-test" x={cx(i) - 6} y={yShare(w.score_share) - 6} width={12} height={12}
                  transform={`rotate(45 ${cx(i)} ${yShare(w.score_share)})`} />
          )))}
        </svg>
        <Readout>
          {active ? (
            <>
              <strong>Week of {shortDate(active.start)}</strong>
              {' · '}{active.answered} answered{active.answered ? `, ${active.correct} right (${pct(active.accuracy)})` : ''}
              {active.days ? ` · ${active.days} day${active.days === 1 ? '' : 's'}` : ''}
              {active.minutes ? ` · ${active.minutes} min` : ''}
              {active.avg_rating != null && ` · avg difficulty ${active.avg_rating}/${RATING_TOP}`}
              {active.score_share != null && ` · best test ${pct(active.score_share)}`}
              {Object.keys(active.by_category).length > 0 && (
                <span className="am-an-readout-cats">
                  {CATEGORY_ORDER.filter((c) => active.by_category[c]).map((c) => (
                    <span key={c}><i className={`am-dot am-tone-${CATEGORY_TONE[c]}`} aria-hidden="true" />{names[c] ?? c} {active.by_category[c]}</span>
                  ))}
                </span>
              )}
            </>
          ) : (
            <>Columns are problems answered each week, split by category. Point at a week for its numbers.</>
          )}
        </Readout>
      </figure>

      <div className="am-an-legend-row">
        <ul className="am-an-legend">
          {CATEGORY_ORDER.map((c) => (
            <li key={c}><i className="am-an-key is-block" style={{ background: tone(CATEGORY_TONE[c]) }} />{names[c] ?? c}</li>
          ))}
        </ul>
        <div className="am-an-toggles" role="group" aria-label="Lines on the chart">
          {SERIES.map((s) => (
            <button key={s.id} type="button" aria-pressed={shown[s.id]}
                    className={`am-an-toggle is-${s.id}${shown[s.id] ? ' is-on' : ''}`}
                    onClick={() => setShown((v) => ({ ...v, [s.id]: !v[s.id] }))}>
              <i aria-hidden="true" />{s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// By difficulty
// ---------------------------------------------------------------------------
function accTone(a: number | null): string {
  if (a == null) return 'line';
  if (a >= 0.75) return 'good';
  if (a >= 0.5) return 'warn';
  return 'bad';
}

export function DifficultyChart({ rows, ceiling }: { rows: RatingRow[]; ceiling: number | null }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [on, setOn] = useState<number | null>(null);
  const H = 260;
  const pad = { l: 40, r: 12, t: 26, b: 46 };
  const iw = Math.max(10, width - pad.l - pad.r);
  const ih = H - pad.t - pad.b;
  const slot = iw / Math.max(1, rows.length);
  const barW = Math.min(38, slot * 0.62);
  const cx = (i: number) => pad.l + slot * i + slot / 2;
  const y = (v: number) => pad.t + ih - v * ih;
  const active = on == null ? null : rows[on];

  return (
    <figure className="am-an-chart" ref={ref} onMouseLeave={() => setOn(null)}>
      <svg width={width} height={H} role="img" aria-label="First-try accuracy at each difficulty rating">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line className="am-an-grid" x1={pad.l} x2={pad.l + iw} y1={y(f)} y2={y(f)} />
            <text className="am-an-axis" x={pad.l - 10} y={y(f)} textAnchor="end" dominantBaseline="middle">{`${f * 100}%`}</text>
          </g>
        ))}
        <line className="am-an-ref is-reliable" x1={pad.l} x2={pad.l + iw} y1={y(0.7)} y2={y(0.7)} />
        <text className="am-an-ref-label is-reliable" x={pad.l + iw} y={y(0.7) - 6} textAnchor="end">70% reliable</text>
        {rows.map((r, i) => {
          const tried = r.attempted > 0;
          const h = tried ? Math.max(3, (r.accuracy ?? 0) * ih) : 0;
          return (
            <g key={r.rating} className={`am-an-diff${on === i ? ' is-on' : ''}`}>
              <rect className="am-an-hit" x={pad.l + slot * i} y={pad.t} width={slot} height={ih + 30}
                    tabIndex={0} aria-label={`Rated ${r.rating}: ${tried ? `${r.first_right} of ${r.attempted} right` : 'not tried'}`}
                    onMouseEnter={() => setOn(i)} onFocus={() => setOn(i)} onClick={() => setOn(i)} />
              {tried ? (
                <>
                  <rect className="am-an-diff-bar" x={cx(i) - barW / 2} y={pad.t + ih - h} width={barW} height={h} rx={4}
                        fill={tone(accTone(r.accuracy))} />
                  <text className="am-an-dot-label" x={cx(i)} y={pad.t + ih - h - 7} textAnchor="middle">{pct(r.accuracy)}</text>
                </>
              ) : (
                <rect className="am-an-diff-empty" x={cx(i) - barW / 2} y={pad.t + ih - 4} width={barW} height={4} rx={2} />
              )}
              <text className={`am-an-axis${ceiling === r.rating ? ' is-strong' : ''}`} x={cx(i)} y={pad.t + ih + 18} textAnchor="middle">
                {r.rating}
              </text>
              <text className="am-an-axis is-faint" x={cx(i)} y={pad.t + ih + 34} textAnchor="middle">
                {tried ? `${r.attempted}` : ''}
              </text>
            </g>
          );
        })}
      </svg>
      <Readout>
        {active
          ? active.attempted
            ? `Rated ${active.rating}/${RATING_TOP} · ${active.first_right} of ${active.attempted} right first time (${pct(active.accuracy)})${active.avg_seconds ? ` · ${clock(active.avg_seconds)} each` : ''}`
            : `Rated ${active.rating}/${RATING_TOP} · not tried yet`
          : `Rating 1 to ${RATING_TOP} along the bottom, problems tried under each.${ceiling != null ? ` Reliable up to ${ceiling}.` : ''}`}
      </Readout>
    </figure>
  );
}
