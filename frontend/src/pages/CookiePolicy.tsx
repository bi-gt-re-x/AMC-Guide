/**
 * The cookie policy: every cookie and every browser-storage entry AMC Guide
 * sets, what it is for and how long it lasts.
 *
 * Checkable against the code, like the privacy policy:
 *
 *   session cookie     backend/main.py (SessionMiddleware), SESSION_MAX_AGE in
 *                      backend/config/settings.py (14 days)
 *   theme cookie       backend/routes/theme.py, THEME_COOKIE_MAX_AGE (1 year)
 *   browser storage    ALLOWED in tests/test_browser_storage.py, which fails
 *                      on any new write; add it here when you add it there
 *   fonts              the Google Fonts <link> in frontend/index.html
 *
 * **A careful draft, not legal advice.** The words are data; LegalDocument
 * draws them.
 */
import { Link } from 'react-router-dom';
import { LegalDocument, type LegalSection } from '@/components/LegalDocument';
import { CONTACT_EMAIL } from '@/utils/contact';

const mail = <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>;
const privacy = <Link to="/privacy-policy">Privacy Policy</Link>;

const SECTIONS: LegalSection[] = [
  {
    id: 'what',
    title: 'What cookies are',
    body: [
      'A cookie is a small text file a website asks your browser to keep and send back on later visits. Browsers also offer "local storage" and "session storage", which do a similar job without being sent to the server. This page lists everything AMC Guide keeps in your browser in either way.',
    ],
  },
  {
    id: 'cookies',
    title: 'The cookies we set',
    body: [
      'AMC Guide sets two cookies, both needed for the site to work. Neither tracks you, and neither is shared with anyone.',
      {
        list: [
          <><strong>session</strong>: keeps you signed in. It holds your signed-in account, is signed so it can't be forged, can't be read by the page's scripts, and is sent only over a secure connection on the live site. It lasts 14 days, or until you sign out.</>,
          <><strong>theme</strong>: remembers whether you chose the light or dark look, so the page is drawn in the right colours before it finishes loading. It lasts one year, and is removed when you sign out.</>,
        ],
      },
      'We set no advertising, analytics, social media or other third-party cookies.',
    ],
  },
  {
    id: 'storage',
    title: 'What we keep in your browser\'s storage',
    body: [
      'Everything that matters (your answers, reviews, scores and plan) lives on our servers, with your account. Your browser keeps only small conveniences, so the site opens faster and remembers where you were:',
      {
        list: [
          <><strong>A copy of your username and your look</strong> (theme, colours, whether the side menu is folded and which groups are open), read before the page loads.</>,
          <><strong>The set you're working through</strong>: the topic practice set or weak-topics set you opened, so Next takes you to the right problem. Kept only for that browser tab.</>,
          <><strong>Small view choices</strong>: whether the weak-topics set draws from the mocks, where to go back to when you close Settings, and whether you dismissed the email banner in this tab.</>,
          <><strong>A hidden game</strong> on the site, which keeps its progress only in your browser.</>,
        ],
      },
      'None of it is sent to anyone. Clearing your browser\'s data removes it, and nothing you need is lost.',
    ],
  },
  {
    id: 'third-party',
    title: 'Other services the pages load',
    body: [
      'AMC Guide\'s fonts come from Google Fonts, so your browser asks Google\'s servers for them and Google sees your IP address when it does. Google Fonts doesn\'t set cookies. If you sign in with Google, Google\'s own sign-in page sets its cookies under Google\'s policies.',
    ],
  },
  {
    id: 'choices',
    title: 'Your choices',
    body: [
      'Because the two cookies are strictly necessary, the site doesn\'t ask before setting them. You can still block or delete cookies in your browser\'s settings, but if you block the session cookie you won\'t be able to stay signed in.',
      <>
        If we ever add a cookie that isn't strictly necessary, we will list it here and ask for
        your consent first. Our {privacy} explains the rest of how we handle your information.
        Questions? Email {mail}.
      </>,
    ],
  },
];

export default function CookiePolicy() {
  return (
    <LegalDocument
      title="Cookie Policy"
      effective="November 24, 2026"
      intro={['This page lists every cookie AMC Guide sets and everything it keeps in your browser, and why.']}
      summary={[
        'Two cookies: one keeps you signed in (14 days), one remembers your theme (1 year).',
        'No advertising, analytics or tracking cookies, and nothing from third parties.',
        'Your browser also keeps a few conveniences, like your theme and the set you\'re working through.',
        'Your study record lives on our servers, not in your browser.',
      ]}
      sections={SECTIONS}
    />
  );
}
