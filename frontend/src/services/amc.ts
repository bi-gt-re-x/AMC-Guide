/**
 * The AMC prep API (backend/api/amc.py): dashboard, problems, review, topics,
 * contests, study plan, analytics and search. Every call is for the signed-in account.
 */
import { del, get, post, put } from './api';

export type Level = 'AMC 10' | 'AMC 12' | 'AIME';
export type Status = 'new' | 'solved' | 'missed' | 'review';
export type CategoryId = 'algebra' | 'number-theory' | 'counting' | 'geometry' | 'misc';

export interface ProblemSummary {
  id: string;
  level: Level;
  topic: string;
  topic_name: string;
  category: CategoryId;
  difficulty: number;
  /** AMC Guide's 1-12 rating: the AoPS competition rating times 2. */
  rating?: number | null;
  technique_name: string;
  preview: string;
  source: string;
  /** A compact label, such as M10-2·5. */
  short?: string;
  /** The contest it first appears in, and its number there. */
  contest_id?: string | null;
  number?: number | null;
  status: Status;
  attempts: number;
}

export interface Source {
  contest: string;
  name: string;
  number: number;
}

export interface Problem {
  id: string;
  level: Level;
  topic: string;
  topic_name: string;
  category: CategoryId;
  category_name: string;
  also: { id: string; name: string }[];
  technique: string;
  technique_name: string;
  difficulty: number;
  /** AMC Guide's 1-12 rating: the AoPS rating times 2 (an AMC 10 #1 is 2, the hardest AIME problem 12). */
  rating?: number | null;
  /** The AoPS competition rating it comes from. */
  aops?: number | null;
  statement: string;
  choices: string[] | null;
  format: 'choice' | 'integer';
  sources: Source[];
  /** An imported official problem (backend/amc/official.py). */
  official?: boolean;
  /** Whether a worked solution exists, said before it is revealed. Official
   *  problems have one when AMC Guide has written it (backend/amc/official_solutions.py). */
  has_solution?: boolean;
  /** A drawn figure (`<svg ...>`), Asymptote source, 'image', or '' when there is no diagram. */
  diagram?: string;
  /** The problem's page on the AoPS wiki (official problems only). */
  aops_url?: string | null;
  /** Written by the AI and kept after an independent second solve agreed. */
  ai?: boolean;
  answer?: string | number;
  /** Numbered steps; null for an official problem AMC Guide has not written up. */
  solution?: string[] | null;
  insight?: string | null;
  trap?: string | null;
}

export interface ReviewItem extends ProblemSummary {
  stage: number;
  due: string;
  review_status: 'active' | 'mastered';
  note: string;
  misses: number;
  overdue: boolean;
  is_due: boolean;
  /** Its topic: problems missed first time, and tried, by this account. */
  topic_missed: number;
  topic_tried: number;
}

export interface Category {
  id: CategoryId;
  name: string;
  color: string;
  blurb: string;
  problems: number;
  attempted: number;
  solved: number;
  accuracy: number | null;
}

export interface TopicStats {
  problems: number;
  attempted: number;
  solved: number;
  first_right: number;
  review: number;
  accuracy: number | null;
  mastery: number;
}

/** One problem as a pill: a short label, coloured by status. */
export interface Pill {
  id: string;
  short: string;
  difficulty: number;
  rating?: number | null;
  status: Status;
  /** Full source and a preview, for the tooltip. */
  title: string;
}

export interface StrategyGroup {
  id: string;
  name: string;
  idea: string;
  pills: Pill[];
}

export interface StrategyFamily {
  id: string;
  name: string;
  color: string;
  blurb: string;
  problems: number;
  solved: number;
  techniques: (StrategyGroup & { solved: number; topics: { id: string; name: string }[] })[];
}

export interface Topic extends TopicStats {
  id: string;
  category: CategoryId;
  name: string;
  weight: number;
  levels: Level[];
  summary: string;
  ideas: string[];
  /** The Ideas card: what to do, when, and a worked example (backend/amc/ideas.py). */
  playbook?: PlaybookMove[];
  /** The mistake that costs the most points on this topic. */
  trap?: string;
  pills?: Pill[];
}

export interface PlaybookMove {
  move: string;
  when: string;
  example: string;
}

/** A problem on a topic page's strategy list: a pill plus what the row shows. */
export interface TopicRow extends Pill {
  source: string;
  statement: string;
}

/** One problem of a posted test: its text, choices, answer and solution. */
export interface PostProblem {
  statement: string;
  /** Five choices for the AMC; null for an AIME problem. */
  choices: string[] | null;
  /** A letter A-E, or the AIME integer. */
  answer: string;
  solution: string;
}

/**
 * Something posted by hand (backend/amc/posts.py): one problem with its answer
 * and solution, or a whole test whose `problems` carry theirs and whose `key`
 * is the answer key.
 */
export interface Post extends PostProblem {
  id: string;
  kind: 'problem' | 'test';
  author: string;
  level: Level;
  title: string;
  /** A test's problems, in order; null for a single problem. */
  problems: PostProblem[] | null;
  /** A test's answers, in order; null for a single problem. */
  key: string[] | null;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
}

export interface PostDraft extends PostProblem {
  kind?: 'problem' | 'test';
  level: Level;
  title: string;
  problems?: PostProblem[] | null;
}

/** One of the up-to-three problems a topic page suggests doing next. */
export interface NextPick extends ProblemSummary {
  kind: 'retry' | 'next' | 'stretch';
  reason: string;
}

export interface MockBrief {
  id: string;
  contest_id: string;
  name: string;
  level: Level | '';
  kind: 'mock' | 'logged';
  score: number;
  correct: number;
  wrong: number;
  blank: number;
  seconds: number;
  note: string;
  at: string;
  max?: number;
  /** Read against the paper's real results (backend/amc/results.py); null for a mock set. */
  standing?: Standing | null;
}

/** A score read against the official paper it was sat on. */
export interface Standing {
  score: number;
  /** Under that year's scoring (a blank was 2.5 until 2006). */
  scored_as: number;
  /** The same result on a typical recent paper, where 100 (AMC 10) / 85 (AMC 12) qualifies. */
  adjusted: number;
  /** About what share of the real field it beat, 0-100. */
  percentile: number | null;
  /** "Top N%". */
  top: number | null;
  floor: number | null;
  vs_floor: number | null;
  award: string;
  mean: number | null;
  students: number | null;
}

/** One official paper's published results. */
export interface PaperResults {
  mean?: number;
  median?: number;
  floor?: number;
  floor_pct?: number;
  top25?: number;
  top10?: number;
  hr?: number;
  top2_5?: number;
  dhr?: number;
  students?: number;
  top5?: number;
  top1?: number;
  usamo?: number | Record<string, number>;
  usajmo?: number | Record<string, number>;
  blank_points: number;
}

export interface TodayItem {
  key: string;
  label: string;
  /** One line under the label: how big, how fast, and why. */
  detail?: string;
  /** About how long it takes. */
  minutes?: number;
  to: string;
  done: boolean;
  progress?: number;
  goal?: number;
}

/** How a topic is trained, from its kind of weakness (backend/amc/planning.py). */
export type StudyMode = 'learn' | 'accuracy' | 'timed' | 'mixed' | 'spaced' | 'practice';
export type WeaknessKindId = 'conceptual' | 'execution' | 'speed' | 'recognition' | 'retention';

/** One of the five difficulty levels, and a practice mix across them. */
export interface DifficultyLevel { level: number; name: string; means: string; ratings: number[]; top: number; typical: number }
export type DifficultyMix = { level: number; share: number }[];
export interface DifficultyPlan { ceiling: number; mix: DifficultyMix; levels: DifficultyLevel[] }

/** One line of the Analytics summary: a label, one value, a short note. */
export interface Takeaway {
  id: 'projected' | 'level' | 'next' | 'weakness';
  label: string;
  value: string;
  note: string;
  tone: '' | 'good' | 'warn' | 'bad';
  to?: string;
  mix?: DifficultyMix;
}

/** A topic's handpicked practice set (backend/amc/practice.py). */
export interface PracticeSetPayload {
  topic: { id: string; name: string; category: CategoryId };
  mode: StudyMode;
  title: string;
  instructions: string;
  seconds: number | null;
  hide_topic: boolean;
  level: Level;
  mix: DifficultyMix;
  suggested: StudyMode;
  modes: { id: StudyMode; title: string }[];
  problems: (ProblemSummary & { level_of: number })[];
}

/** One topic's study priority: expected points from studying it, and why. */
export interface StudyPriority {
  id: string;
  name: string;
  category: CategoryId;
  priority: number;
  /** About how many points a few weeks on it would add. */
  gain: number;
  factors: {
    frequency: number; share: number; mastery: number | null; answered: number; right: number;
    level: number | null; feasibility: number; recency: number; days_since: number | null;
    importance: number; builds: number;
  };
  kinds: Partial<Record<WeaknessKindId, { score: number; evidence: string; count: number }>>;
  kind: WeaknessKindId | null;
  mode: StudyMode;
  mode_label: string;
  why: string;
  /** What difficulty to practise it at. */
  mix: DifficultyMix;
}

/** One kind of weakness, the topics showing it, and how to train it. */
export interface WeaknessKind {
  id: WeaknessKindId;
  name: string;
  mode: StudyMode;
  means: string;
  approach: string;
  count: number;
  topics: { id: string; name: string; category: CategoryId; evidence: string; score: number }[];
}

export interface PlanWeek {
  number: number;
  start: string;
  end: string;
  phase: 'Foundations' | 'Core' | 'Contest mode' | 'Taper';
  note: string;
  focus: { id: string; name: string; category: CategoryId; mode?: StudyMode; mode_label?: string; gain?: number;
           mix?: DifficultyMix; reason?: string }[];
  problems: number;
  mock: boolean;
  mock_done: boolean;
  current: boolean;
  past: boolean;
  /** Distinct problems answered that week; on past weeks and this one only. */
  answered?: number;
}

export interface Dashboard {
  stats: {
    solved: number;
    attempted: number;
    total: number;
    accuracy: number | null;
    streak: number;
    due: number;
    in_review: number;
    mastered: number;
    minutes: number;
    mocks: number;
  };
  target: Level;
  goal: number;
  /** Null until `projection_min` problems have been answered. */
  projected: Record<Level, number | null>;
  projection_min: number;
  categories: Category[];
  weakest: {
    id: string; name: string; category: CategoryId; mastery: number; accuracy: number | null;
    attempted: number; first_right: number;
  }[];
  next_problem: ProblemSummary | null;
  performance: RecentPerformance;
  plan: null | {
    target: Level;
    exam_date: string;
    goal_score: number;
    days_left: number;
    week: PlanWeek | null;
    today: TodayItem[];
  };
  last_mock: MockBrief | null;
}

export interface PerformanceWindow {
  answered: number;
  correct: number;
  accuracy: number | null;
  revealed: number;
  minutes: number;
  avg_seconds: number | null;
  days: number;
  hardest: { id: string; rating: number; short: string } | null;
}

export interface ScorePoint {
  id: string;
  contest_id: string;
  name: string;
  level: Level | '';
  kind: 'mock' | 'logged';
  score: number;
  max: number | null;
  at: string;
  /** The score on a typical recent paper; the score itself for a mock set. */
  adjusted: number;
  top: number | null;
  floor: number | null;
  vs_floor: number | null;
  award: string;
}

export interface Note {
  tone: 'up' | 'down' | 'flat';
  text: string;
}

/** The dashboard's recent performance: this week against last. */
export interface RecentPerformance {
  this_week: PerformanceWindow;
  last_week: PerformanceWindow;
  days: { date: string; answered: number; correct: number }[];
  mocks: ScorePoint[];
  notes: Note[];
}

export interface RatingRow {
  rating: number;
  attempted: number;
  first_right: number;
  accuracy: number | null;
  avg_seconds: number | null;
}

export interface ContestGuide {
  level: Level;
  count: number;
  minutes: number;
  max: number;
  scoring: string;
  who: string;
  format: string;
  qualify: string;
  sections: { range: string; rating: string; minutes: number; what: string }[];
  shares: { id: string; name: string; share: number }[];
  measured: null | { papers: number; problems: number; shares: Record<string, number> };
  bands: { last: number; rating: number }[];
  key_topics: { id: string; name: string; category: string }[];
}

/** One week of the analytics page's performance chart (backend/amc/insights.py `weekly`). */
export interface PerformanceWeek {
  start: string;
  answered: number;
  correct: number;
  accuracy: number | null;
  minutes: number;
  days: number;
  by_category: Partial<Record<CategoryId, number>>;
  /** Mean 1-12 rating of the problems answered that week. */
  avg_rating: number | null;
  /** The week's best contest score as a share of the paper's maximum. */
  score_share: number | null;
}

/** Points lost in recent timed sittings, by topic (backend/amc/mockscore.py). */
export interface MockMistakes {
  sittings: number;
  lost: number;
  topics: { id: string; name: string; category: CategoryId; wrong: number; blank: number; missed: number;
            asked: number; lost: number; per_sitting: number; problems: string[] }[];
}

export interface Analytics {
  /** Topics by expected score gain, and the kinds of weakness (backend/amc/planning.py). */
  priorities: StudyPriority[];
  /** Where timed sittings lose points: the top of the Weaknesses card. */
  mock_mistakes?: MockMistakes;
  kinds: WeaknessKind[];
  difficulty?: DifficultyPlan;
  /** The page in four lines, shown first. */
  takeaways?: Takeaway[];
  target: Level;
  goal: number;
  has_plan: boolean;
  exam_date: string | null;
  days_left: number | null;
  hours: number | null;
  performance: {
    attempted: number;
    solved: number;
    accuracy: number | null;
    avg_seconds: number | null;
    minutes: number;
    active_days: number;
    projected: Record<Level, number | null>;
    projection_min: number;
    categories: Category[];
    ratings: RatingRow[];
    ceiling: number | null;
    weeks: PerformanceWeek[];
    topics: {
      id: string; name: string; category: string; weight: number; levels: Level[];
      attempted: number; problems: number; accuracy: number | null; mastery: number; review: number;
    }[];
    recovery: { missed_first: number; recovered: number; open: number; revealed: number };
    mocks: ScorePoint[];
  };
  contests: Record<Level, ContestGuide>;
  prepare: {
    goal: number;
    right_needed: number;
    split: string;
    need_rating: number | null;
    ceiling: number | null;
    reach: string;
    gap: number | null;
    focus: { id: string; name: string; category: string; weight: number; mastery: number; accuracy: number | null }[];
    steps: { title: string; body: string; to: string }[];
    week: { what: string; hours: number }[];
    phase: null | { name: string; weeks: number; text: string };
  };
}

export interface ProblemFilters {
  level?: string;
  category?: string;
  topic?: string;
  difficulty?: string;
  status?: string;
  technique?: string;
  q?: string;
  sort?: string;
  source?: string;
  /** Whole rating steps, comma separated: "3" covers 3 and 3.5. */
  rating?: string;
  /** Problem number within its contest, a past paper's year, or a mock contest id. */
  number?: string;
  year?: string;
  mock?: string;
}

export interface ProblemList {
  problems: ProblemSummary[];
  total: number;
  counts: Record<Status, number>;
  /** Problems in each whole rating step, "1" to "10". */
  rating_counts: Record<string, number>;
  kinds: Record<'summit' | 'step' | 'official' | 'ai', number>;
  mocks: { id: string; name: string; level: Level; family: 'summit' | 'step'; set: number | null }[];
  years: { year: number; count: number }[];
  families: { id: string; name: string; techniques: { id: string; name: string }[] }[];
  official: number;
  topics: { id: string; name: string; category: CategoryId }[];
  categories: Category[];
  techniques: { id: string; name: string }[];
}

export interface ProblemDetail {
  problem: Problem;
  status: Status;
  attempts: { answer: string; correct: boolean; at: string; source: string; seconds: number }[];
  review: ReviewItem | null;
  related: ProblemSummary[];
  /** The topic Previous and Next walk, when the problem was opened from one. */
  topic?: string | null;
  prev: string | null;
  next: string | null;
  /** Where it sits in the filtered list it was opened from, if it was. */
  position?: { at: number; of: number } | null;
}

export interface AttemptReply {
  correct: boolean;
  given: string;
  problem: Problem;
  review: { stage: number; due: string; status: string } | null;
  moved: boolean;
}

export interface ReviewQueue {
  due: ReviewItem[];
  upcoming: ReviewItem[];
  mastered: ReviewItem[];
  forecast: { date: string; count: number }[];
  by_topic: { name: string; count: number }[];
  intervals: number[];
}

/** One problem in the weak-topics bank, with the topic that put it there. */
export interface WeakProblem extends ProblemSummary {
  weak_topic: string;
  weak_topic_name: string;
  /** The modelled chance of a first-try right answer (backend/amc/smart.py). */
  chance: number;
}

/** Twelve problems from the weakest topics (backend/amc/weak.py). */
export interface WeakBank {
  target: Level;
  mocks: boolean;
  draw: number;
  size: number;
  topics: {
    id: string; name: string; attempted: number; first_right: number;
    /** Problems in the topic got wrong first time. */
    missed: number;
    accuracy: number | null; in_review: number; picked: number;
  }[];
  problems: WeakProblem[];
  pool: { official: number; mock: number };
}

export interface Format {
  count: number;
  minutes: number;
  max: number;
  scoring: string;
}

export interface MockContest extends Format {
  id: string;
  name: string;
  level: Level;
  blurb: string;
  /** 'summit': the five full sets per contest; 'step': the original warm-up mocks. */
  family: 'summit' | 'step';
  set: number | null;
  attempts: number;
  best: number | null;
  /** Mean rating of its problems against a real paper's, on the 1-12 scale. */
  difficulty?: MockDifficulty | null;
}

export interface MockDifficulty {
  average: number;
  real: number;
  /** Negative: plays easier than a real paper. */
  vs_real: number;
}

/** How a mock compares with a real paper, in words. */
export function versusReal(d: MockDifficulty | null | undefined, level: Level): string {
  if (!d) return '';
  if (Math.abs(d.vs_real) < 0.3) return `About as hard as a real ${level}`;
  const step = Math.abs(d.vs_real).toFixed(1);
  const points = step === '1.0' ? 'point' : 'points';
  return d.vs_real < 0
    ? `Plays about ${step} ${points} easier than a real ${level}`
    : `Plays about ${step} ${points} harder than a real ${level}`;
}

export interface PastContest extends Format {
  id: string;
  name: string;
  year: number;
  level: Level;
  paper: string;
  season: string;
  problems_url: string;
  answers_url: string;
  logged?: MockBrief | null;
  /** How many of its problems have been imported (count = all of them). */
  imported?: number;
  /** How many of its problems have an AMC Guide write-up. */
  written?: number;
  /** Scores logged or sittings taken on it, and the best of them. */
  sittings?: number;
  best?: number | null;
}

export interface ContestList {
  mocks: MockContest[];
  years: { year: number; contests: PastContest[] }[];
  history: MockBrief[];
  formats: Record<Level, Format>;
  imported: number;
  /** Whether this account may import papers (only `temu`). */
  can_import: boolean;
}

/** How a problem of a paper stands: right first time, right after a miss, missed and still open, or untouched. */
export type ContestProgress = 'first' | 'fixed' | 'open' | 'new';

/** One line of an official paper's answer key, with AMC Guide's write-up when there is one. */
export interface KeyRow {
  number: number;
  id: string;
  answer: string;
  solution: string[] | null;
  insight: string | null;
  trap: string | null;
}

export interface ContestDetail {
  contest: (MockContest & { kind: 'mock' }) | (Omit<PastContest, 'imported'> & { kind: 'past'; imported: boolean });
  problems: (Problem & { number: number; status: Status; progress: ContestProgress })[];
  history: MockBrief[];
  /** Whether this account may import or remove the paper (only `temu`). */
  can_import: boolean;
  /** An official paper this account unlocked by hand before sitting it. */
  unlocked?: boolean;
  /** The timed sitting in progress on this paper, kept on the account. */
  sitting?: SittingState | null;
  /** How the paper went for real: mean, AIME floor, honor rolls (official papers). */
  results?: PaperResults | null;
  /** An official paper only part brought in: the numbers of the problems that
   *  are (each can be practised; the paper is sat once all of them are in). */
  partial?: number[];
}

/** A timed contest in progress, as the server keeps it (table `amc_sittings`). */
export interface SittingState {
  /** Seconds of contest time used so far: only time spent on the sitting page. */
  used: number;
  answers: Record<string, string>;
  flags: number[];
  started_at?: string;
  updated_at?: string;
}

export interface MockRow {
  number: number;
  problem_id: string;
  given: string;
  answer: string | number;
  result: 'correct' | 'wrong' | 'blank';
  topic: string;
  topic_name: string;
  difficulty: number;
  rating?: number | null;
  statement: string;
  solution: string[] | null;
  insight: string | null;
  trap: string | null;
  choices: string[] | null;
  diagram: string;
}

export interface MockResult {
  result: MockBrief & Format;
  contest: { id: string; name: string; level: Level; official: boolean };
  rows: MockRow[];
  report: {
    topics: { topic: string; name: string; total: number; correct: number; lost: number }[];
    bands: { label: string; correct: number; total: number; lost: number }[];
  };
  attempts: MockBrief[];
}

export type SubjectStrength = 'weak' | 'ok' | 'strong';

export interface PlanDetails {
  experience?: 'first' | 'taken' | 'qualified';
  /** School grade, '6'-'12' or 'Other'. */
  grade?: string;
  last_score?: number;
  days_per_week?: number;
  strong?: string[];
  weak?: string[];
  /** How strong they feel in each subject, and anything more on it (both optional). */
  subjects?: Partial<Record<CategoryId, SubjectStrength>>;
  subject_notes?: Partial<Record<CategoryId, string>>;
  resources?: string;
  notes?: string;
}

export interface PlanSettings {
  target: Level;
  exam_date: string;
  goal_score: number;
  hours: number;
  details?: PlanDetails;
}

/** The AI coach's plan (backend/amc/coach.py). */
export interface CoachPlan {
  summary: string;
  starting_point: string;
  /** Three to five tasks for the current week (older plans have none). */
  this_week?: string[];
  phases: { name: string; weeks: string; goal: string; focus_topics: string[]; routine: string }[];
  weekly_schedule: { day: string; task: string; minutes: number }[];
  milestones: { week: number; target: string }[];
  focus_order: string[];
  tips: string[];
  questions: string[];
}

export interface PlanPayload {
  plan: null | (PlanSettings & {
    days_left: number;
    created_at: string;
    updated_at: string;
    details: PlanDetails;
    coach: CoachPlan | null;
    coach_at: string;
    coach_by: string;
  });
  /** Whether an AI model is configured, and which one. */
  ai: { available: boolean; label: string };
  weeks?: PlanWeek[];
  today?: TodayItem[];
  projected?: number | null;
  coverage?: { id: string; name: string; category: CategoryId; mastery: number; weight: number; attempted?: number }[];
  priorities?: StudyPriority[];
  kinds?: WeaknessKind[];
  difficulty?: DifficultyPlan;
  /** Where the student starts against the goal, from their scores and answers. */
  start?: {
    current: number | null; from: string; goal: number; gap: number | null; weeks: number | null;
    per_week: number | null; stage: 'far' | 'near' | 'there' | 'unknown'; summary: string;
  };
  defaults: { dates: Record<Level, string>; goals: Record<Level, number> };
  /** Where the student is working now, which the plan is built from. */
  level?: PlanLevel;
}

export interface PlanLevel {
  level: number;
  name: string;
  means: string;
  /** Distinct problems answered: how much the level rests on. */
  measured: number;
  goal_level: number;
  goal_name: string;
  mix: DifficultyMix;
  recent: { answered: number; right: number; accuracy: number | null };
  before: { answered: number; right: number; accuracy: number | null };
  pace: { per_week: number; planned: number } | null;
}

// ---------------------------------------------------------------------------
// Smart insights and the AI layer (backend/amc/smart.py, backend/api/amc_ai.py)
// ---------------------------------------------------------------------------
export interface AIStatus {
  available: boolean;
  provider: string;
  label: string;
  used_today: number;
  limit: number;
  setup: string;
}

export interface ContestForecast {
  expected: number;
  low: number;
  high: number;
  target: number | null;
  chance: number | null;
  reach: number;
  count: number;
  /** Expected score working through the paper at the student's own pace, in the time limit. */
  timed: number;
  /** The last problem reached in the time limit at that pace. */
  reached: number;
  /** Points the clock costs: untimed minus timed. */
  speed_cost: number;
}

export interface TopicAbility {
  id: string;
  name: string;
  category: CategoryId;
  weight: number;
  answered: number;
  right: number;
  theta: number | null;
  se: number | null;
  relevant: boolean;
  priority: number;
  /** Points on the student's contest from bringing this topic up to their level. */
  points: number;
}

export interface PatternRow {
  kind: 'careless' | 'slow' | 'rushed' | 'revealed' | 'pressure';
  count: number;
  text: string;
  problems: { id: string; short: string; topic: string; rating: number }[];
}

export interface SmartStats {
  level: Level;
  goal: number;
  answered: number;
  confident: boolean;
  theta: number;
  se: number;
  band: string;
  contests: Record<Level, ContestForecast>;
  topics: TopicAbility[];
  techniques: { id: string; name: string; answered: number; theta: number }[];
  focus: TopicAbility[];
  strong: TopicAbility[];
  patterns: PatternRow[];
  trend: { week_end: string; answered: number; theta: number | null }[];
  mocks: null | { taken: number; scores: { contest: string; score: number; at: string }[]; blank_rate: number | null; by_fifth: (number | null)[] };
  next_problems: { id: string; short: string; topic: string; topic_name: string; rating: number; chance: number }[];
  review_due: number;
  /** Seconds the student takes on a first try: at their level, two points easier, two harder; contest pace. */
  pace: { timed_answers: number; at_level: number; easy: number; hard: number; contest: number };
  /** Timed mocks against what the model expects for those exact papers. */
  mock_check: null | { taken: number; gap: number; recent: { contest: string; score: number; expected: number }[] };
}

export interface Diagnosis {
  headline: string;
  diagnosis: string;
  strengths: string[];
  weaknesses: string[];
  this_week: { action: string; why: string; minutes: number; topic: string; topic_name: string }[];
  contest_strategy: string;
}

export interface InsightsPayload {
  stats: SmartStats;
  ai: AIStatus;
  diagnosis: Diagnosis | null;
  diagnosis_at: string | null;
}

export interface Explanation {
  likely_mistake: string;
  habit: string;
  right_approach: string;
  given: string;
}

export interface ImportBatch {
  url: string;
  label: string;
  contests: string[];
}

export interface BundleRow {
  id: string;
  name: string;
  problems: number;
  count: number;
  answers: number;
  complete: boolean;
  diagrams: number;
  issues: string[];
  saved: boolean;
}

export interface ImportPreview {
  preview: {
    number: number;
    statement: string;
    choices: string[] | null;
    diagram: boolean;
    topic: string;
    answer: string | number | null;
  }[];
  issues: string[];
  saved: boolean;
  count: number;
  diagrams: number;
  /** Every problem and answer found: it can be saved (missing choices are only a warning). */
  complete?: boolean;
}

export interface SearchResults {
  query: string;
  problems: { id: string; level: Level; topic_name: string; difficulty: number; rating?: number | null; preview: string; source: string }[];
  topics: { id: string; name: string; summary: string; category_name: string }[];
  contests: { id: string; name: string; level: Level; kind: 'mock' | 'past' }[];
  pages: { name: string; to: string }[];
}

export const amc = {
  dashboard: () => get<Dashboard>('/api/amc/dashboard'),
  analytics: () => get<Analytics>('/api/amc/analytics'),
  topicSet: (topic: string, mode: string) =>
    get<PracticeSetPayload>(`/api/amc/topics/${encodeURIComponent(topic)}/set?mode=${encodeURIComponent(mode)}`),
  insights: () => get<InsightsPayload>('/api/amc/insights'),
  diagnose: (refresh = false) =>
    post<{ diagnosis: Diagnosis; at: string; cached: boolean }>('/api/amc/insights/ai', { refresh }),
  aiStatus: () => get<AIStatus>('/api/amc/ai/status'),
  hint: (id: string, level: number) =>
    post<{ hint: string; level: number }>(`/api/amc/ai/hint/${encodeURIComponent(id)}`, { level }),
  explain: (id: string) => post<Explanation>(`/api/amc/ai/explain/${encodeURIComponent(id)}`, {}),
  posts: (level = '', kind = '') =>
    get<{ posts: Post[]; levels: Level[] }>('/api/amc/posts', { ...(level ? { level } : {}), ...(kind ? { kind } : {}) }),
  parseTest: (level: Level, problems: string, key: string) =>
    post<{ problems: PostProblem[]; issues: string[] }>('/api/amc/posts/parse', { level, problems, key }),
  createPost: (draft: PostDraft) => post<{ post: Post }>('/api/amc/posts', draft),
  editPost: (id: string, draft: PostDraft) => put<{ post: Post }>(`/api/amc/posts/${encodeURIComponent(id)}`, draft),
  deletePost: (id: string) => del<object>(`/api/amc/posts/${encodeURIComponent(id)}`),
  splitChoices: (statement: string) =>
    post<{ statement: string; choices: string[] }>('/api/amc/posts/split', { statement }),
  createProblem: (body: { like?: string; level?: string; topic?: string; technique?: string; rating?: number }) =>
    post<{ id: string }>('/api/amc/ai/create', body),
  problems: (filters: ProblemFilters) => get<ProblemList>('/api/amc/problems', { ...filters }),
  /**
   * One problem. `walk` says which list its Previous and Next step through:
   * `{ topic }` from a topic, `{ list: '1', ...filters }` from the Problems
   * page (the filtered list, in its order), nothing for the problem's own paper.
   */
  problem: (id: string, walk: Record<string, string> = {}) =>
    get<ProblemDetail>(`/api/amc/problems/${encodeURIComponent(id)}`, walk),
  attempt: (id: string, answer: string, seconds: number, source: 'practice' | 'review' = 'practice') =>
    post<AttemptReply>(`/api/amc/problems/${encodeURIComponent(id)}/attempt`, { answer, seconds, source }),
  reveal: (id: string) => post<{ problem: Problem }>(`/api/amc/problems/${encodeURIComponent(id)}/reveal`),
  review: () => get<ReviewQueue>('/api/amc/review'),
  weakBank: (mocks: boolean, draw = 0) =>
    get<WeakBank>('/api/amc/review/weak', { mocks: mocks ? 1 : 0, draw }),
  addReview: (id: string) => post<object>(`/api/amc/review/${encodeURIComponent(id)}`),
  removeReview: (id: string) => del<object>(`/api/amc/review/${encodeURIComponent(id)}`),
  noteReview: (id: string, note: string) => post<object>(`/api/amc/review/${encodeURIComponent(id)}/note`, { note }),
  topics: () => get<{ categories: (Category & { topics: Topic[] })[] }>('/api/amc/topics'),
  topic: (id: string) =>
    get<{
      topic: Topic & { category_name: string };
      problems: ProblemSummary[];
      siblings: { id: string; name: string }[];
      techniques: { id: string; name: string; count: number }[];
      by_strategy: (Omit<StrategyGroup, 'pills'> & { pills: TopicRow[] })[];
      next: NextPick[];
    }>(`/api/amc/topics/${encodeURIComponent(id)}`),
  strategies: () => get<{ families: StrategyFamily[]; untagged: number }>('/api/amc/strategies'),
  contests: () => get<ContestList>('/api/amc/contests'),
  contest: (id: string) => get<ContestDetail>(`/api/amc/contests/${encodeURIComponent(id)}`),
  contestKey: (id: string) => get<{ key: KeyRow[]; written: number }>(`/api/amc/contests/${encodeURIComponent(id)}/key`),
  submit: (id: string, answers: Record<string, string>, seconds: number) =>
    post<{ id: string }>(`/api/amc/contests/${encodeURIComponent(id)}/submit`, { answers, seconds }),
  saveSitting: (id: string, sitting: Pick<SittingState, 'used' | 'answers' | 'flags'>) =>
    put<{ sitting: SittingState }>(`/api/amc/contests/${encodeURIComponent(id)}/sitting`, sitting),
  discardSitting: (id: string) => del<object>(`/api/amc/contests/${encodeURIComponent(id)}/sitting`),
  unlock: (id: string, on: boolean) =>
    put<{ unlocked: boolean }>(`/api/amc/contests/${encodeURIComponent(id)}/unlock`, { on }),
  mock: (id: string) => get<MockResult>(`/api/amc/mocks/${encodeURIComponent(id)}`),
  deleteMock: (id: string) => del<object>(`/api/amc/mocks/${encodeURIComponent(id)}`),
  importContest: (id: string, problems: string, key: string, save: boolean) =>
    post<ImportPreview>(`/api/amc/contests/${encodeURIComponent(id)}/import`, { problems, key, save }),
  removeImport: (id: string) => del<object>(`/api/amc/contests/${encodeURIComponent(id)}/import`),
  importBatches: () => get<{ batches: ImportBatch[]; missing: number; total: number }>('/api/amc/official/batches'),
  importBundle: (text: string, save: boolean) =>
    post<{ contests: BundleRow[]; saved: number }>('/api/amc/official/import', { text, save }),
  logScore: (id: string, score: number, note: string) =>
    post<object>(`/api/amc/contests/${encodeURIComponent(id)}/log`, { score, note }),
  plan: () => get<PlanPayload>('/api/amc/plan'),
  savePlan: (settings: PlanSettings) => put<PlanPayload>('/api/amc/plan', settings),
  clearPlan: () => del<object>('/api/amc/plan'),
  check: (key: string, done: boolean) => post<PlanPayload>('/api/amc/plan/check', { key, done }),
  coach: (answers: Record<string, string> = {}) =>
    post<PlanPayload>('/api/amc/plan/coach', { answers }, undefined),
  search: (q: string, limit = 20) => get<SearchResults>('/api/amc/search', { q, limit }),
};

/** Fired when an answer, a mock or a plan change moves the dashboard's numbers. */
/** The top of AMC Guide's rating scale (backend/amc/scale.py): the AoPS rating times 2, so 12 is the hardest AIME problem. */
export const RATING_TOP = 12;

export const AMC_CHANGED = 'summit:amc-changed';

export function announceAmcChanged(): void {
  window.dispatchEvent(new Event(AMC_CHANGED));
}

export const CATEGORY_TONE: Record<CategoryId, string> = {
  algebra: 'blue',
  'number-theory': 'amber',
  counting: 'green',
  geometry: 'rose',
  misc: 'slate',
};

export function pct(value: number | null | undefined): string {
  return value == null ? '—' : `${Math.round(value * 100)}%`;
}

export function shortDate(iso: string): string {
  const d = new Date(`${iso.slice(0, 10)}T12:00:00`);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
