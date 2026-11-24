/**
 * Your data: what AMC Guide keeps about an account, and how to see, download,
 * correct, reset or delete it. The privacy policy says what we do with data;
 * this page says what the reader can do with theirs.
 *
 * Checkable against the code:
 *
 *   the export         /api/settings/export, ACCOUNT_TABLES in
 *                      backend/api/settings.py (answers, reviews, mocks, plan)
 *   reset and delete   RESETS in backend/api/settings.py, the Danger zone in
 *                      pages/Settings.tsx (both ask for the username)
 *   shared content     amc_posts and amc_generated in data/sql/amc.sql
 *
 * **A careful draft, not legal advice.** The words are data; LegalDocument
 * draws them.
 */
import { Link } from 'react-router-dom';
import { LegalDocument, type LegalSection } from '@/components/LegalDocument';
import { CONTACT_EMAIL } from '@/utils/contact';

const mail = <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>;
const privacy = <Link to="/privacy-policy">Privacy Policy</Link>;
const dataSettings = <Link to="/settings/data">Settings → Data &amp; export</Link>;
const danger = <Link to="/settings/danger">Settings → Reset and delete</Link>;

const SECTIONS: LegalSection[] = [
  {
    id: 'what',
    title: 'What we keep',
    body: [
      {
        list: [
          <><strong>Your account:</strong> name, email address, username, a hashed password and when you joined.</>,
          <><strong>Your study record:</strong> every answer you give (right or wrong, and how long it took), your review log, your timed sittings and their scores, scores you log, papers you've unlocked, and your study plan.</>,
          <><strong>Your settings:</strong> theme, display preferences and profile picture.</>,
          <><strong>What you share:</strong> your posts on the Posts page, and problems you asked the AI to write.</>,
        ],
      },
      <>All of it is stored on AMC Guide's server, in its database. Our {privacy} explains who else sees any of it (in short: only the AI provider for a feature you use, and other users for what you post).</>,
    ],
  },
  {
    id: 'see',
    title: 'See it',
    body: [
      'Most of it is on screen already: your answers and status on every problem, your review log on Review, your sittings on Mock Contests and Past Contests, your plan on Study Plan, and your level, predictions and trends on Analytics. Your account details are in Settings → Profile.',
    ],
  },
  {
    id: 'download',
    title: 'Download it',
    body: [
      <>
        {dataSettings} has an "Export everything" button. It downloads one JSON file with your
        answers, review log, mock scores, study plan and settings, in a form other software can
        read. You can do this as often as you like.
      </>,
    ],
  },
  {
    id: 'correct',
    title: 'Correct it',
    body: [
      'Change your name, profile picture and preferences in Settings, and your goal and plan on the Study Plan page. To change the email address on your account, or anything else you can\'t edit yourself, email us.',
    ],
  },
  {
    id: 'delete',
    title: 'Reset or delete it',
    body: [
      <>{danger} offers two ways to start over. Each asks you to type your username first, and neither can be undone, so download your data before you use one.</>,
      {
        list: [
          <><strong>Reset your AMC progress</strong> deletes every answer, your review log, every mock and logged score, and your study plan. Your account, profile and settings stay.</>,
          <><strong>Delete this account</strong> deletes everything above, your settings and the account itself, and signs you out.</>,
        ],
      },
      'Your posts on the Posts page and problems the AI wrote at your request are shared with every account, so they aren\'t removed with your account. Delete a post yourself from the Posts page, or email us and we will remove your posts or take your username off them.',
    ],
  },
  {
    id: 'requests',
    title: 'Requests, parents and guardians',
    body: [
      <>
        For anything you can't do yourself, such as a copy of information not in the export,
        removing shared content, or objecting to how we use something, email {mail} from the
        address on your account. We will reply within 30 days. A parent or guardian can ask on behalf
        of a child under 18; we may ask for something that shows the account is the child's.
      </>,
    ],
  },
];

export default function YourData() {
  return (
    <LegalDocument
      title="Your Data"
      effective="November 24, 2026"
      intro={['What AMC Guide keeps about you, and how to see, download, correct or delete it, most of it in a couple of clicks.']}
      summary={[
        'We keep your account details, your study record and your settings, on AMC Guide\'s server.',
        'Download all of it as one JSON file from Settings → Data & export.',
        'Reset your progress, or delete your account and everything in it, from Settings → Reset and delete.',
        'Posts you share stay shared until you delete them or ask us to.',
      ]}
      sections={SECTIONS}
    />
  );
}
