/**
 * What to study and how (backend/amc/planning.py): topics ranked by the points
 * a few weeks on them would add, and the five kinds of weakness — conceptual,
 * execution, speed, recognition, retention — each with the topics showing it,
 * the evidence, and the training it wants. Shared by Analytics and the study plan.
 */
import { Link } from 'react-router-dom';
import { CategoryDot } from './bits';
import type { StudyMode, StudyPriority, WeaknessKind } from '@/services/amc';

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
          </li>
        ))}
      </ol>
      <p className="am-muted am-card-note">
        Ranked by the points a few weeks on each would add to your contest: how often it appears, how far it is
        below your level, whether its problems are within reach, how long since you practised it, and how many
        topics build on it.
      </p>
    </section>
  );
}

/** The five kinds of weakness, each with its topics, evidence and training. */
export function WeaknessKinds({ kinds }: { kinds?: WeaknessKind[] }) {
  const list = kinds ?? [];
  if (!list.length) return null;
  const any = list.some((k) => k.topics.length);
  return (
    <section className="am-card">
      <div className="am-card-head"><h2>Kinds of weakness</h2></div>
      {!any && (
        <p className="am-muted" style={{ margin: '0 0 12px', fontSize: 13 }}>
          Not enough answers yet to tell what kind of weakness any topic has. Each kind needs a few answers in a
          topic first.
        </p>
      )}
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
