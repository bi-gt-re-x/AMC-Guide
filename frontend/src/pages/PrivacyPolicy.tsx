/**
 * The privacy policy.
 *
 * ## It says what the code does
 *
 * Rewritten on 2026-11-24 for AMC Guide as it is now: a study site for the
 * AMC 10, AMC 12 and AIME. The version before it still described the study
 * tracker this codebase grew out of (tasks, a calendar, a journal), none of
 * which a reader of this site can reach. A policy that describes another
 * product is worse than none. So each section is checkable against the code,
 * and if one of these changes, this page changes with it:
 *
 *   account, email, verification   backend/routes/auth.py, tracking/auth.py
 *   what's stored, and where       data/sql/amc.sql, data/sql/users.sql
 *   what goes to AI providers      backend/amc/ai.py (providers),
 *                                  backend/api/amc_ai.py (what each feature sends)
 *   shared with every account      amc_posts, amc_generated (data/sql/amc.sql)
 *   IP addresses                   middleware/limit.py (memory only)
 *   cookies                        main.py (session, 14 days), routes/theme.py;
 *                                  the full list is pages/CookiePolicy.tsx
 *   export, reset and deletion     ACCOUNT_TABLES in backend/api/settings.py
 *
 * **It is a careful draft, not legal advice**, and should be read by a lawyer
 * before AMC Guide is offered widely. The contact address is utils/contact.ts.
 *
 * The words are data; LegalDocument draws them.
 */
import { Link } from 'react-router-dom';
import { LegalDocument, type LegalSection } from '@/components/LegalDocument';
import { CONTACT_EMAIL } from '@/utils/contact';

const mail = <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>;
const terms = <Link to="/terms-of-service">Terms of Service</Link>;
const cookies = <Link to="/cookie-policy">Cookie Policy</Link>;
const yourData = <Link to="/your-data">Your Data</Link>;

const SECTIONS: LegalSection[] = [
  {
    id: 'scope',
    title: 'Who we are and what this covers',
    body: [
      <>
        AMC Guide ("we", "us" or "our") is a study site for the American Mathematics Competitions:
        the AMC 10, AMC 12 and AIME. This Privacy Policy explains what personal information we
        collect when you use the AMC Guide website and web app (the "Service"), how we use it, who
        we share it with, how long we keep it, and the choices you have. It's part of our {terms}.
      </>,
      <>
        For the purposes of data protection laws such as the GDPR, AMC Guide is the "controller" of
        your personal information. You can reach us at {mail}.
      </>,
    ],
  },
  {
    id: 'you-give',
    title: 'Information you give us',
    body: [
      { sub: 'When you make an account' },
      {
        list: [
          <><strong>Name and email address.</strong> Your email confirms your account, lets you sign in and receives account emails. Your name is used to greet you.</>,
          <><strong>Username.</strong> How your account is known inside AMC Guide. It's shown next to anything you choose to share on the Posts page.</>,
          <><strong>Password.</strong> Stored only as a salted, one-way hash (PBKDF2). Nobody, including us, can read your password from it.</>,
          <><strong>Google sign-in.</strong> If it's offered and you choose it, Google sends us your name and email address and confirms the address is yours. We never see your Google password.</>,
        ],
      },
      { sub: 'As you study' },
      {
        list: [
          <><strong>Your answers:</strong> each answer you give, whether it was right, how long you took and where you answered it (practice, review, a set or a timed contest).</>,
          <><strong>Your review log:</strong> the problems you missed and when each comes back.</>,
          <><strong>Mock contests and past papers:</strong> timed sittings in progress, finished sittings and their scores, scores you log yourself, and which papers you've unlocked.</>,
          <><strong>Your study plan:</strong> the contest, date, goal score and hours you choose, how strong you say you are in each subject, and anything you add about your experience, past scores, resources or constraints.</>,
          <><strong>Settings and profile:</strong> your theme, display preferences and profile picture.</>,
          <><strong>What you share:</strong> problems and solutions you post on the Posts page, and problems you ask the AI to write.</>,
        ],
      },
    ],
  },
  {
    id: 'automatic',
    title: 'Information collected automatically',
    body: [
      {
        list: [
          <><strong>Cookies.</strong> Two: one that keeps you signed in and one that remembers your light or dark theme. There are no advertising or analytics cookies. Our {cookies} lists them.</>,
          <><strong>IP addresses.</strong> Used only to limit repeated sign-in attempts, held in the server's memory for a short time and never written to the database.</>,
          <><strong>Server logs.</strong> Like any web server, ours records requests (the page asked for, the time and the result) to keep the Service running and find faults.</>,
        ],
      },
      'We don\'t use advertising networks, tracking pixels or third-party analytics, and we don\'t follow you across other websites.',
    ],
  },
  {
    id: 'use',
    title: 'How we use your information',
    body: [
      {
        list: [
          'To run your account and sign you in.',
          'To grade your answers, schedule your reviews, work out your level and predicted scores, and build your study plan and practice sets.',
          'To send account emails, such as the link that confirms your address. We don\'t send marketing email.',
          'To keep the Service secure and stop abuse, such as password guessing.',
          'To find and fix problems with the Service.',
        ],
      },
      'We don\'t sell your personal information, rent it, or use it for advertising.',
    ],
  },
  {
    id: 'legal-bases',
    title: 'Our legal bases',
    body: [
      'Where laws like the GDPR apply, we rely on: performing our agreement with you (running your account and the features you use); our legitimate interests (keeping the Service secure and working); your consent, where we ask for it; and legal obligations, where we have them.',
    ],
  },
  {
    id: 'ai',
    title: 'AI features',
    body: [
      'Some features send information to an AI provider to write a response. Each runs only when you press its button.',
      {
        list: [
          <><strong>Hints:</strong> the problem, and its reference solution so the hint points the right way.</>,
          <><strong>Explain my mistake:</strong> the problem, the right answer, the answer you gave and the reference solution.</>,
          <><strong>The AI coach</strong> (on Analytics and the Study Plan): a summary of your results (accuracy and timing by topic, recent scores, predicted scores) and your study plan, including anything you typed into the plan form.</>,
          <><strong>Writing new problems:</strong> the contest, topic and difficulty you choose, and the problem you started from for "More like this".</>,
        ],
      },
      'We never send your email address, your password or your name. The providers we use are Google (Gemini), xAI (Grok) and Groq, depending on which is available. Each handles what we send under its own terms for developers, which limit how it may be used.',
      'Answers are saved so the same request isn\'t sent twice. A hint for a problem is saved without your account attached and can be shown to anyone who asks for the same hint. Problems the AI writes for you are added to the shared problem bank, which every account can see.',
    ],
  },
  {
    id: 'sharing',
    title: 'Who can see your information',
    body: [
      {
        list: [
          <><strong>Other users</strong> see only what you post on the Posts page, with your username. Your answers, scores, reviews and plan are never shown to anyone else, and AMC Guide never ranks you against other people.</>,
          <><strong>Service providers</strong> who help us run AMC Guide: our hosting and database, Google (sign-in, sending email and the site's fonts) and the AI providers in section 6. They may use your information only to provide their service to us.</>,
          <><strong>The law.</strong> We will share information if the law requires it, or to protect someone's safety or the Service from abuse.</>,
          <><strong>A change of ownership.</strong> If AMC Guide is ever transferred to someone else, your information would go with it under this policy, and we would tell you first.</>,
        ],
      },
    ],
  },
  {
    id: 'retention',
    title: 'How long we keep it',
    body: [
      'We keep your account and study record for as long as you have an account. Resetting your AMC progress in Settings deletes your answers, review log, mock scores and study plan straight away. Deleting your account deletes all of that and the account itself.',
      'What you shared stays shared: a post on the Posts page and a problem the AI wrote at your request remain after your account is gone, because others may be using them. Email us and we will remove your posts or take your username off them.',
    ],
  },
  {
    id: 'security',
    title: 'Security',
    body: [
      'Passwords are stored only as salted hashes. The session cookie is signed so it can\'t be forged, can\'t be read by the page\'s scripts, and is sent only over a secure connection on the live site. Sign-in attempts are rate-limited.',
      'No system is perfectly secure. If we learn of a breach that affects your information, we will tell you and, where the law requires it, the authorities.',
    ],
  },
  {
    id: 'rights',
    title: 'Your choices and rights',
    body: [
      <>
        You can see, download, correct and delete your information at any time. Our {yourData}{' '}
        page explains how. Depending on where you live, you may also have the right to object to or
        restrict how we use it, to withdraw consent you gave, and to complain to your data protection
        authority. Email {mail} for anything you can't do in Settings, and we will reply within 30 days.
      </>,
    ],
  },
  {
    id: 'children',
    title: 'Children and students',
    body: [
      'AMC Guide is for students preparing for contests, and many of them are under 18. You must be 13 or older to make an account, and under 18 you need the permission of a parent or guardian. We don\'t knowingly collect information from children under 13. If you believe a child under 13 has made an account, email us and we will delete it.',
      'Parents and guardians can ask us to see, export or delete their child\'s information at the address below.',
    ],
  },
  {
    id: 'transfers',
    title: 'Where your information is processed',
    body: [
      'AMC Guide\'s servers and the providers in section 7 may be in a different country from you, including the United States. When we move personal information from the EEA, the UK or Switzerland to another country, we rely on the safeguards the law allows, such as the Standard Contractual Clauses in our providers\' terms.',
    ],
  },
  {
    id: 'changes',
    title: 'Changes to this policy',
    body: [
      'We will post any change to this policy on this page with a new effective date. If a change affects what we collect, how we use it or who we share it with, we will tell you in the app before it takes effect and, where the law requires it, ask for your consent.',
    ],
  },
  {
    id: 'contact',
    title: 'Contact',
    body: [
      <>
        Questions, requests or complaints about privacy? Email {mail}. Parents and guardians can
        use the same address.
      </>,
    ],
  },
];

export default function PrivacyPolicy() {
  return (
    <LegalDocument
      title="Privacy Policy"
      effective="November 24, 2026"
      intro={[
        'This policy explains what AMC Guide collects, why, who sees it, and what you can do about it, in words as plain as we can manage.',
      ]}
      summary={[
        'We keep your name, email, a hashed password, and your study record: answers, reviews, mock scores and your plan.',
        'We use it only to run AMC Guide for you. No ads, no selling, no tracking across sites.',
        'Hints, explanations and the AI coach send the problem, your answer or a summary of your results to an AI provider. Never your name, email or password.',
        'Only what you post on the Posts page is visible to other people.',
        'Download, reset or delete everything from Settings, any time.',
        'AMC Guide is for people 13 and older, with a parent\'s OK under 18.',
      ]}
      sections={SECTIONS}
    />
  );
}
