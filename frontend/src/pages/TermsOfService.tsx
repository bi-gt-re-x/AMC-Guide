/**
 * The terms of service.
 *
 * Rewritten in full on 2026-10-17; on 2026-11-24 the sections on what the
 * Service is, your content, AI and study habits were brought up to date for the
 * contest-prep site (they still described the old tracker's tasks and
 * calendar), and a section on contest problems and the MAA was added.
 *
 * The earlier version was nine short
 * sections; this one covers what a hosted app with accounts, AI features and
 * an audience of students needs to say: who may sign up (13 and up, with a
 * parent's OK under 18), one account per email, what the AI features are and
 * aren't, acceptable use, ownership of what people write, termination,
 * warranties, liability, disputes and changes.
 *
 * Every factual claim matches the code, as the privacy policy's do (see the
 * note at the top of PrivacyPolicy.tsx). **It is a careful draft, not legal
 * advice**, and should be read by a lawyer before AMC Guide is offered widely.
 *
 * The words are data; LegalDocument draws them.
 */
import { Link } from 'react-router-dom';
import { LegalDocument, type LegalSection } from '@/components/LegalDocument';
import { CONTACT_EMAIL } from '@/utils/contact';

const mail = <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>;
const privacy = <Link to="/privacy-policy">Privacy Policy</Link>;

const SECTIONS: LegalSection[] = [
  {
    id: 'agreement',
    title: 'Agreeing to these terms',
    body: [
      <>
        These Terms of Service (the "Terms") are a binding agreement between you and the people
        who run AMC Guide ("AMC Guide", "we", "us" or "our"). They cover your use of the AMC Guide website,
        web app and every feature and service in it (together, the "Service"). Our {privacy}{' '}
        explains how we handle your information, and it's part of these Terms.
      </>,
      'By creating an account, checking the box at sign-up, or using the Service in any way, you confirm that you have read these Terms, understand them, and agree to them. If you don\'t agree, don\'t use the Service.',
      'If you use the Service on behalf of a school, club or other organization, you confirm that you are allowed to accept these Terms for it, and "you" includes that organization.',
    ],
  },
  {
    id: 'eligibility',
    title: 'Who can use AMC Guide',
    body: [
      {
        list: [
          <><strong>You must be at least 13 years old.</strong> AMC Guide isn't meant for children under 13, and we don't knowingly let them make accounts. If we learn that an account belongs to someone under 13, we will delete it.</>,
          <><strong>If you're under 18</strong> (or under the age of majority where you live), you may only use AMC Guide with the permission of a parent or legal guardian, who must read and agree to these Terms for you. If you're a parent or guardian and you allow your child to use AMC Guide, you agree to these Terms for them and are responsible for their use of it.</>,
          'You must not be barred from using services like this one under the laws that apply to you.',
          'If your country sets a higher age for agreeing to online services or to the handling of personal data, that higher age applies to you.',
        ],
      },
    ],
  },
  {
    id: 'accounts',
    title: 'Your account',
    body: [
      {
        list: [
          <><strong>Accurate details.</strong> Give your real name and an email address you own and can read. Keep them up to date.</>,
          <><strong>Confirm your email.</strong> We send a confirmation link to the address you sign up with. Until you follow it, some parts of the Service may be limited, and we may delete accounts that are never confirmed.</>,
          <><strong>One account per email.</strong> Each email address, and each inbox, can belong to only one AMC Guide account. Variations that reach the same inbox (for example adding "+something" before the @, or moving the dots in a Gmail address) count as the same address.</>,
          <><strong>A strong password, kept secret.</strong> New passwords must meet the rules shown on the sign-up form. Don't share your password or use one you use anywhere else. We will never ask for your password by email.</>,
          <><strong>Your responsibility.</strong> You are responsible for everything that happens under your account, unless it happened because of our own failure to protect it. If you think someone else has used your account, tell us right away at {mail}.</>,
          <><strong>One person, one account.</strong> Accounts are personal. Don't sell, transfer or lend yours, and don't make accounts with automated tools.</>,
          <><strong>Signing in with Google.</strong> If you sign in with Google, Google's own terms also apply to that sign-in, and we receive only what Google shares with us (your name and email address).</>,
        ],
      },
    ],
  },
  {
    id: 'service',
    title: 'What AMC Guide provides',
    body: [
      'AMC Guide is a study site for the AMC 10, AMC 12 and AIME. It gives you practice problems tagged by topic and technique, a review log that brings your misses back on a schedule, timed mock contests, past official papers, a study plan to contest day, analytics and a predicted score, and AI hints, explanations and coaching.',
      'AMC Guide is free. There are no paid plans, subscriptions, ads or in-app purchases. If we ever introduce paid features, we will tell you first, and nothing you already have will be charged for without your clear agreement.',
      'AMC Guide is still being built. We may add, change, limit or remove features at any time, including how ratings, levels, predicted scores and study plans are worked out. We will try to give notice of changes that matter.',
    ],
  },
  {
    id: 'content',
    title: 'Your content',
    body: [
      '"Your content" means what you put into AMC Guide: your answers, your study plan and what you tell it about yourself, the scores you log, your settings, and anything you post on the Posts page.',
      {
        list: [
          <><strong>You own it.</strong> We don't claim ownership of your content.</>,
          <><strong>The permission you give us.</strong> So that we can run the Service, you give us a worldwide, non-exclusive, royalty-free license to store, copy, process and display your content, only as needed to provide, protect and improve the Service. This includes sending parts of it to the AI providers described in our {privacy} when you use a feature that needs them. This license ends when you delete the content or your account, except for what you chose to share.</>,
          <><strong>What you share.</strong> A post on the Posts page is visible to every account, with your username. By posting, you let other users read and practise it, and let us keep showing it after your account is deleted unless you ask us to remove it. Post only problems and solutions you wrote yourself or are allowed to share, and credit the source.</>,
          <><strong>Your responsibility for it.</strong> You confirm that you have the right to put your content into AMC Guide and that it doesn't break any law or anyone else's rights.</>,
          <><strong>Private by design.</strong> Apart from your posts, your content isn't shown to other users, and AMC Guide never ranks or compares you against other people.</>,
        ],
      },
    ],
  },
  {
    id: 'contest-problems',
    title: 'Contest problems and the MAA',
    body: [
      'The AMC 10, AMC 12 and AIME are run by the Mathematical Association of America (MAA). AMC and AIME problems are © the MAA, and AMC Guide is not affiliated with, sponsored by or endorsed by the MAA.',
      'Official problems appear in AMC Guide for personal study, each with a link to its source. AMC Guide\'s mock and step problems, and the worked solutions it writes, are original.',
      'Ratings, predicted scores and study plans are AMC Guide\'s own estimates. They aren\'t official scores, cutoffs or results, and they don\'t predict how you will do on contest day.',
    ],
  },
  {
    id: 'ai',
    title: 'AI features',
    body: [
      'Some features use artificial intelligence: hints, "Explain my mistake", the AI coach, and new problems written on request. Each runs only when you ask for it.',
      {
        list: [
          <><strong>It can be wrong.</strong> AI output is generated automatically. A hint can mislead, an explanation can contain an error, and a written problem can be flawed even after it is checked. Use your own judgment, and check against the reference solution.</>,
          <><strong>Not professional advice.</strong> Nothing AMC Guide produces is academic, legal, medical or other professional advice.</>,
          <><strong>Don't misuse it.</strong> Don't try to make the AI features produce harmful, illegal or abusive content, or get around their limits.</>,
          <><strong>Usage limits.</strong> AI features cost money to run, so each account has a daily limit, and we may change or switch them off.</>,
        ],
      },
    ],
  },
  {
    id: 'wellbeing',
    title: 'Contests, honesty and study habits',
    body: [
      'Use AMC Guide to prepare, never during a real contest. Using it, or any outside help, while sitting an official AMC or AIME breaks the MAA\'s rules.',
      'Study plans suggest hours and pacing; you decide what\'s right for you. Take breaks and sleep. Scores and streaks are there to help, and if tracking starts to feel stressful, step back.',
    ],
  },
  {
    id: 'acceptable-use',
    title: 'Acceptable use',
    body: [
      'You agree to use the Service only for lawful purposes and in line with these Terms. You must not:',
      {
        list: [
          'Access, or try to access, anyone else\'s account or data, or any part of the Service you aren\'t allowed into.',
          'Probe, scan or test the Service for weaknesses, or get around any security, rate limit or access control, unless we have given you written permission as part of a security report.',
          'Overload, crash or interfere with the Service, including through denial-of-service attacks, scripts or bots that send excessive requests.',
          'Copy, scrape or harvest content or data from the Service with automated tools.',
          'Upload viruses, malware or any code meant to cause harm.',
          'Use the Service to store or share anything illegal, or anything that infringes someone else\'s intellectual property, privacy or other rights.',
          'Use the Service to harass, threaten, bully or harm anyone.',
          'Pretend to be someone else, or give false information to make an account.',
          'Make more than one account per person, or make accounts for others without their permission.',
          'Reverse engineer, decompile or try to extract the source code of the Service, except where the law allows it despite this limit.',
          'Resell, rent or offer the Service to others as your own product.',
          'Help or encourage anyone else to do any of these things.',
        ],
      },
      'If you find a security problem, please tell us privately at the address in the Contact section instead of using it. We appreciate responsible reports.',
    ],
  },
  {
    id: 'ownership',
    title: 'Our property',
    body: [
      'The Service, including its name, logo, design, software, text, graphics, original problems and solutions, and everything else we provide (but not your content, and not the MAA\'s problems), belongs to us or to the people who license it to us, and is protected by copyright, trademark and other laws.',
      'We give you a personal, limited, non-exclusive, non-transferable, revocable license to use the Service for your own study, as these Terms allow. Nothing in these Terms gives you any other right to our property, and you may not use our name or logo without our written permission.',
    ],
  },
  {
    id: 'feedback',
    title: 'Feedback',
    body: [
      'If you send us ideas, suggestions or other feedback, you agree that we may use them freely to improve AMC Guide, without owing you anything. We are grateful for them all the same.',
    ],
  },
  {
    id: 'third-parties',
    title: 'Other services and links',
    body: [
      'The Service relies on, and links to, services run by others: Google for sign-in, sending email and fonts; AI providers for some features; and outside websites such as the AoPS wiki, where official problems and their discussions live. Their own terms and privacy policies apply to your use of them. We aren\'t responsible for their content, availability or practices.',
    ],
  },
  {
    id: 'availability',
    title: 'Availability and changes',
    body: [
      'We work to keep the Service running, but we don\'t promise it will always be available, fast, secure or free of errors. It may be down for maintenance, updates or reasons beyond our control.',
      'We may stop offering the Service, or any part of it, at any time. If we plan to shut the whole Service down, we will try to give you at least 30 days\' notice in the app or by email so you can export your data.',
    ],
  },
  {
    id: 'termination',
    title: 'Ending your use of AMC Guide',
    body: [
      {
        list: [
          <><strong>You can leave any time.</strong> Delete your account in Settings, under Reset and delete. Deleting is permanent and can't be undone.</>,
          <><strong>We may suspend or close accounts</strong> that break these Terms, put other people or the Service at risk, are never confirmed, have been inactive for a long time, or that the law requires us to close. Where it's reasonable and allowed, we will tell you first and give you a chance to fix the problem or export your data.</>,
          <><strong>What happens after.</strong> When an account is closed, your right to use the Service ends and we delete your content as our {privacy} describes. The sections of these Terms that by their nature should continue (such as ownership, disclaimers, limits on liability and disputes) still apply.</>,
        ],
      },
    ],
  },
  {
    id: 'warranties',
    title: 'Disclaimer of warranties',
    body: [
      <>
        <strong>
          The Service is provided "as is" and "as available". To the fullest extent the law
          allows, we make no warranties or promises of any kind, express or implied, including
          any warranty of merchantability, fitness for a particular purpose, title,
          non-infringement, accuracy, or that the Service will be uninterrupted, secure or free
          of errors, or that your data will never be lost.
        </strong>
      </>,
      'Some places don\'t allow certain warranties to be excluded. If you live in one, the exclusions above apply only as far as your local law allows.',
    ],
  },
  {
    id: 'liability',
    title: 'Limits on liability',
    body: [
      <>
        <strong>
          To the fullest extent the law allows, AMC Guide and the people who build and run it will
          not be liable for any indirect, incidental, special, consequential or punitive damages,
          or for any loss of data, progress, scores, grades, opportunities, profits or
          goodwill, arising from or related to your use of, or inability to use, the Service,
          even if we were told such damages were possible.
        </strong>
      </>,
      <>
        <strong>
          Our total liability for all claims related to the Service is limited to the greater of
          (a) the amount you paid us to use the Service in the 12 months before the claim, or
          (b) 50 US dollars.
        </strong>{' '}
        Because AMC Guide is free, that is normally 50 US dollars.
      </>,
      'Nothing in these Terms limits liability that the law doesn\'t allow to be limited, such as liability for fraud, for death or personal injury caused by negligence, or your rights as a consumer that can\'t be waived.',
    ],
  },
  {
    id: 'indemnity',
    title: 'Your responsibility to us',
    body: [
      'To the extent the law allows, you agree to defend and compensate AMC Guide and the people who run it for any claims, losses and reasonable costs (including legal fees) that come from your content, your breach of these Terms, or your misuse of the Service. We will tell you about any such claim and let you take part in responding to it.',
    ],
  },
  {
    id: 'disputes',
    title: 'Disputes and governing law',
    body: [
      <>
        <strong>Talk to us first.</strong> If you have a problem with AMC Guide, email {mail} and
        describe it. Most problems can be solved this way. Please give us 30 days to try before
        starting any formal claim, and we will do the same for you.
      </>,
      'These Terms are governed by the laws of the United States and of the state in which AMC Guide\'s operator lives, without regard to conflict-of-law rules. Any claim that isn\'t resolved informally will be brought in the state or federal courts serving that location, or in a small claims court where you live if your claim qualifies.',
      'If you live in the European Union, the United Kingdom or another place whose consumer laws give you the right to bring a claim in your own country\'s courts, or to the protection of its mandatory laws, nothing in these Terms takes that right away.',
    ],
  },
  {
    id: 'changes',
    title: 'Changes to these terms',
    body: [
      'We may update these Terms from time to time, for example when we add features or when the law changes. The latest version will always be on this page, with its effective date at the top.',
      'If a change is significant, we will tell you in the app (and by email if it affects your rights in an important way) at least 14 days before it takes effect, unless the change is needed sooner for legal or security reasons. If you keep using the Service after a change takes effect, you accept the new Terms. If you don\'t accept them, stop using the Service and delete your account.',
    ],
  },
  {
    id: 'general',
    title: 'General',
    body: [
      {
        list: [
          <><strong>Entire agreement.</strong> These Terms and the {privacy} are the whole agreement between you and us about the Service.</>,
          <><strong>Severability.</strong> If any part of these Terms can't be enforced, the rest still applies, and the part that can't be enforced is changed only as much as needed to make it enforceable.</>,
          <><strong>No waiver.</strong> If we don't enforce part of these Terms right away, we still have the right to enforce it later.</>,
          <><strong>Transfer.</strong> You can't transfer these Terms or your account to anyone else. We may transfer them as part of a merger, sale or reorganization, and the Terms will continue to protect you.</>,
          <><strong>Events beyond our control.</strong> We aren't responsible for delays or failures caused by things we can't reasonably control, such as outages of the services we rely on, natural disasters or changes in the law.</>,
          <><strong>Language.</strong> These Terms are written in English. If they are translated, the English version is the one that applies.</>,
        ],
      },
    ],
  },
  {
    id: 'contact',
    title: 'Contact',
    body: [
      <>
        Questions about these Terms, reports of a problem with an account, or a security report?
        Email {mail}. Parents and guardians can use the same address.
      </>,
    ],
  },
];

export default function TermsOfService() {
  return (
    <LegalDocument
      title="Terms of Service"
      effective="November 24, 2026"
      intro={[
        'Please read these Terms carefully. They explain the rules for using AMC Guide, what you can expect from us, what we expect from you, and the limits on our responsibility.',
      ]}
      summary={[
        'You need to be 13 or older, and under 18 you need a parent or guardian\'s OK.',
        'One account per person and per email address. Keep your password to yourself.',
        'What you put in AMC Guide is yours. Only your Posts are visible to others.',
        'AMC and AIME problems are © the MAA. AMC Guide isn\'t affiliated with the MAA.',
        'AI hints and explanations can be wrong. Ratings and predicted scores are estimates.',
        'Prepare here; never use AMC Guide during a real contest.',
        'Don\'t break, overload or try to get into anything that isn\'t yours.',
        'AMC Guide is free and provided as is, and our liability is limited.',
        'You can delete your account any time in Settings.',
      ]}
      sections={SECTIONS}
    />
  );
}
