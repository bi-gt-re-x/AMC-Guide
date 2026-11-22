/**
 * In-app notices: the short "done" / "that didn't work" line after an action,
 * and the "are you sure?" question before a destructive one.
 *
 * ## Never the browser's own
 *
 * `window.confirm`, `alert` and system notifications are drawn by the browser,
 * in its own style, and block the page (a timed contest's clock included).
 * These are drawn by the app: the question sits over the page in AMC Guide's own
 * look, and a notice slides up, says one thing and leaves.
 *
 * ## Not the bell
 *
 * The bell (components/Notifications) is the record of what the account should
 * know about; its pop-ups come from the server. These are the other kind: the
 * immediate answer to something the reader just did, held only on screen and
 * gone after a few seconds. They sit bottom-centre so they never stack on the
 * bell's pop-ups in the corner.
 *
 *     const { notify, confirm } = useNotice();
 *     if (!(await confirm({ title: 'Delete this score?', danger: true }))) return;
 *     notify('Score deleted');
 *
 * Without the provider (a page rendered alone in a test) `notify` does nothing
 * and `confirm` answers no, which is the safe answer to every question asked.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import '@/styles/notices.css';

export type NoticeTone = 'good' | 'info' | 'warn' | 'bad';

export interface ConfirmOptions {
  title: string;
  body?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Deletes or discards something: the button is red and Cancel has focus. */
  danger?: boolean;
}

export interface NoticeApi {
  notify: (title: string, options?: { body?: string; tone?: NoticeTone }) => void;
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

interface Notice {
  id: number;
  title: string;
  body?: string;
  tone: NoticeTone;
}

interface Asking extends ConfirmOptions {
  resolve: (answer: boolean) => void;
}

const NoticeContext = createContext<NoticeApi>({
  notify: () => {},
  confirm: async () => false,
});

export function useNotice(): NoticeApi {
  return useContext(NoticeContext);
}

/** How long a notice stays up; a failure gets longer, it's the one to read. */
const LIFE_MS: Record<NoticeTone, number> = { good: 3200, info: 4200, warn: 6000, bad: 7000 };
/** The most on screen at once; an older one makes way. */
const AT_ONCE = 3;

function NoticeItem({ notice, onClose }: { notice: Notice; onClose: () => void }) {
  const [held, setHeld] = useState(false);
  useEffect(() => {
    if (held) return undefined;
    const timer = window.setTimeout(onClose, LIFE_MS[notice.tone]);
    return () => window.clearTimeout(timer);
  }, [held, notice.tone, onClose]);
  return (
    <div className={`nt-notice is-${notice.tone}`} role={notice.tone === 'bad' ? 'alert' : 'status'}
         onMouseEnter={() => setHeld(true)} onMouseLeave={() => setHeld(false)}>
      <span className="nt-mark" aria-hidden="true" />
      <div className="nt-text">
        <strong>{notice.title}</strong>
        {notice.body && <p>{notice.body}</p>}
      </div>
      <button type="button" className="nt-close" aria-label="Dismiss" onClick={onClose}>×</button>
    </div>
  );
}

function ConfirmDialog({ asking, onAnswer }: { asking: Asking; onAnswer: (yes: boolean) => void }) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const okRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    (asking.danger ? cancelRef : okRef).current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onAnswer(false);
      } else if (event.key === 'Tab') {
        // Two buttons, so Tab simply moves between them and stays inside.
        event.preventDefault();
        (document.activeElement === okRef.current ? cancelRef : okRef).current?.focus();
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => {
      window.removeEventListener('keydown', onKey, true);
      before?.focus?.();
    };
  }, [asking, onAnswer]);
  return (
    <div className="nt-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onAnswer(false); }}>
      <div className="nt-dialog" role="alertdialog" aria-modal="true" aria-labelledby="nt-dialog-title"
           aria-describedby={asking.body ? 'nt-dialog-body' : undefined}>
        <h2 id="nt-dialog-title">{asking.title}</h2>
        {asking.body && <p id="nt-dialog-body">{asking.body}</p>}
        <div className="nt-dialog-actions">
          <button ref={cancelRef} type="button" className="nt-btn" onClick={() => onAnswer(false)}>
            {asking.cancelLabel ?? 'Cancel'}
          </button>
          <button ref={okRef} type="button" className={`nt-btn ${asking.danger ? 'is-danger' : 'is-primary'}`}
                  onClick={() => onAnswer(true)}>
            {asking.confirmLabel ?? 'OK'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function NoticesProvider({ children }: { children: ReactNode }) {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [asking, setAsking] = useState<Asking | null>(null);
  const next = useRef(1);

  const notify = useCallback<NoticeApi['notify']>((title, options) => {
    const notice = { id: next.current++, title, body: options?.body, tone: options?.tone ?? 'good' };
    setNotices((list) => [...list, notice].slice(-AT_ONCE));
  }, []);

  const confirm = useCallback<NoticeApi['confirm']>((options) => new Promise<boolean>((resolve) => {
    setAsking((current) => {
      current?.resolve(false);
      return { ...options, resolve };
    });
  }), []);

  const answer = useCallback((yes: boolean) => {
    setAsking((current) => {
      current?.resolve(yes);
      return null;
    });
  }, []);

  const close = useCallback((id: number) => setNotices((list) => list.filter((n) => n.id !== id)), []);
  const api = useMemo(() => ({ notify, confirm }), [notify, confirm]);

  return (
    <NoticeContext.Provider value={api}>
      {children}
      <div className="nt-stack" aria-live="polite">
        {notices.map((n) => <NoticeItem key={n.id} notice={n} onClose={() => close(n.id)} />)}
      </div>
      {asking && <ConfirmDialog asking={asking} onAnswer={answer} />}
    </NoticeContext.Provider>
  );
}
