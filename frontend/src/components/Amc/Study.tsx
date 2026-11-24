/**
 * What to study and how (backend/amc/planning.py): topics ranked by the points
 * a few weeks on them would add, and the five kinds of weakness — conceptual,
 * execution, speed, recognition, retention — each with the topics showing it,
 * the evidence, and the training it wants. Shared by Analytics and the study plan.
 */
import { Link } from 'react-router-dom';
import { CategoryDot } from './bits';
import type { DifficultyMix, StudyMode, StudyPriority, Takeaway, WeaknessKind } from '@/services/amc';

const MODE_TONE: Record<StudyMode, string> = {
  learn: 'is-learn', accuracy: 'is-accuracy', timed: 'is-timed', mixed: 'is-mixed', spaced: 'is-spaced', practice: '',
};

export function ModeTag({ mode, label }: { mode?: StudyMode; label?: string }) {
  if (!mode || mode === 'practice') return null;
  return <span className={`am-mode ${MODE_TONE[mode]}`}>{label ?? mode}</span>;
}

const pts = (v: number) => (v >= 0.995 ? v.toFixed(1) : v.toFixed(2));

/** Topics by expected score gain, with what puts each where it is. */
export function PrioritiesCard({ priorities, limit = 6, title = 'Where the points are' }: {
  priorities?: StudyPriority[]; limit?: number; title?: string;
}) {
  const rows = (priorities ?? []).slice(0, limit);
  if (!rows.length) return null;
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>{title}</h2></div>
      <ol className="am-priorities">
        {rows.map((r) => (
          <li key={r.id}>
            <div className="am-priority-head">
              <Link className="am-link" to={`/topics/${r.id}`}><CategoryDot category={r.category} /> {r.name}</Link>
              <strong className="am-points">+{pts(r.gain)} pts</strong>
            </div>
            <div className="am-priority-why">
              <ModeTag mode={r.mode} label={r.mode_label} />
              <span className="am-muted">{r.why}</span>
            </div>
            <MixBar mix={r.mix} labels={false} />
          </li>
        ))}
      </ol>
      <p className="am-muted am-card-note">Ranked by the points a few weeks on each would add. Bars: the difficulty mix to practise it at.</p>
    </section>
  );
}

/** The five kinds of weakness, each with its topics, evidence and training. */
export function WeaknessKinds({ kinds }: { kinds?: WeaknessKind[] }) {
  const list = kinds ?? [];
  if (!list.length) return null;
  const any = list.some((k) => k.topics.length);
  // Five empty boxes saying "None found" say one thing five times: say it once,
  // with the kinds the plan will be looking for.
  if (!any) {
    return (
      <section className="am-card">
        <div className="am-card-head"><h2>Kinds of weakness</h2></div>
        <p className="am-muted" style={{ margin: '0 0 10px', fontSize: 13, lineHeight: 1.55 }}>
          Not enough answers yet to tell what kind of weakness any topic has. After a few answers in a topic, the
          plan looks for these and changes how it trains that topic:
        </p>
        <div className="am-kind-tags">
          {list.map((k) => (
            <span key={k.id} title={`${k.means} ${k.approach}`}><ModeTag mode={k.mode} label={k.name} /></span>
          ))}
        </div>
      </section>
    );
  }
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>Kinds of weakness</h2></div>
      <div className="am-kinds">
        {list.map((k) => (
          <div key={k.id} className={`am-kind${k.topics.length ? '' : ' is-clear'}`}>
            <div className="am-kind-head">
              <ModeTag mode={k.mode} label={k.name} />
              <span className="am-muted">{k.means}</span>
            </div>
            <p className="am-kind-approach"><b>Train it:</b> {k.approach}</p>
            {k.topics.length ? (
              <ul className="am-kind-topics">
                {k.topics.slice(0, 4).map((t) => (
                  <li key={t.id}>
                    <Link className="am-link" to={`/topics/${t.id}`}><CategoryDot category={t.category} /> {t.name}</Link>
                    <span className="am-muted"> · {t.evidence}</span>
                  </li>
                ))}
                {k.topics.length > 4 && <li className="am-muted">and {k.topics.length - 4} more</li>}
              </ul>
            ) : (
              <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>None found.</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

/** A practice mix across the five difficulty levels, as one thin stacked bar. */
export function MixBar({ mix, labels = true }: { mix?: DifficultyMix; labels?: boolean }) {
  if (!mix?.length) return null;
  const text = mix.map((m) => `${Math.round(m.share * 100)}% level ${m.level}`).join(', ');
  return (
    <div className="am-mix" title={text} aria-label={`Practice mix: ${text}`} role="img">
      <div className="am-mix-bar">
        {mix.map((m) => (
          <span key={m.level} className={`am-mix-seg is-l${m.level}`} style={{ flexGrow: m.share }} />
        ))}
      </div>
      {labels && (
        <div className="am-mix-labels">
          {mix.map((m) => (
            <span key={m.level} style={{ flexGrow: m.share }}>{m.share >= 0.15 ? `L${m.level} ${Math.round(m.share * 100)}%` : ''}</span>
          ))}
        </div>
      )}
    </div>
  );
}

/** The Analytics page in four tiles: projected vs goal, level, next topic, main weakness. */
export function Takeaways({ items }: { items?: Takeaway[] }) {
  if (!items?.length) return null;
  return (
    <div className="am-takeaways">
      {items.map((t) => {
        const body = (
          <>
            <span className="am-kicker">{t.label}</span>
            <strong className={`am-take-value${t.tone ? ` is-${t.tone}` : ''}${t.value.length > 16 ? ' is-long' : ''}`}>{t.value}</strong>
            {t.mix ? <MixBar mix={t.mix} labels={false} /> : null}
            <span className="am-muted am-take-note">{t.note}</span>
          </>
        );
        return t.to
          ? <Link key={t.id} className="am-card am-take" to={t.to}>{body}</Link>
          : <div key={t.id} className="am-card am-take">{body}</div>;
      })}
    </div>
  );
}

/** Only the kinds of weakness found, one line each: for Analytics, where the
 *  study plan has the full card. */
export function WeaknessLines({ kinds }: { kinds?: WeaknessKind[] }) {
  const found = (kinds ?? []).filter((k) => k.topics.length);
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>Kinds of weakness</h2><Link to="/study-plan">Plan</Link></div>
      {found.length ? (
        <ul className="am-kind-lines">
          {found.map((k) => (
            <li key={k.id} title={k.means}>
              <ModeTag mode={k.mode} label={k.name} />
              <span>{k.topics.slice(0, 2).map((t) => t.name).join(', ')}{k.topics.length > 2 ? ` +${k.topics.length - 2}` : ''}</span>
              <span className="am-muted">{k.approach.split(/[:.]/)[0] ?? k.approach}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="am-muted" style={{ margin: 0, fontSize: 13 }}>Too early to tell: a few answers per topic first.</p>
      )}
    </section>
  );
}
