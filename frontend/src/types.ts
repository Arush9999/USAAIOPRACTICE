export type User = {
  id: number;
  email: string | null;
  display_name: string;
  theme: "light" | "dark" | "system";
  weekly_hours: number;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Settings = {
  display_name: string;
  weekly_hours: number;
  theme: "light" | "dark" | "system";
};

export type LearnModuleSummary = {
  slug: string;
  title: string;
  summary: string;
  round: number;
  phase: string;
  sequence: number;
  progress: {
    lessons_done: number;
    lessons_total: number;
    checks_correct: number;
    checks_total: number;
    percent: number;
  };
};

export type LearnGroup = {
  round: number;
  phase: string;
  modules: LearnModuleSummary[];
};

export type ContentStep = {
  type: "content";
  slug: string;
  title: string;
  body_markdown: string;
  completed: boolean;
};

export type CheckStep = {
  type: "check";
  public_id: string;
  prompt: string;
  choices: string[];
  difficulty: string;
  subtopic_slug: string;
  completed_correct: boolean;
};

export type LearnStep = ContentStep | CheckStep;

export type LearnModuleDetail = {
  slug: string;
  title: string;
  round: number;
  phase: string;
  steps: LearnStep[];
};

export type PracticeSubtopic = {
  slug: string;
  title: string;
  counts: { easy: number; medium: number; hard: number };
};

export type PracticeTopic = {
  slug: string;
  title: string;
  round: number;
  subtopics: PracticeSubtopic[];
};

export type Question = {
  public_id: string;
  topic_slug: string;
  topic_title: string;
  subtopic_slug?: string;
  qtype: string;
  difficulty: string;
  prompt: string;
  choices: string[];
  hints: string[];
  tags: string[];
  practice_label: string;
};

export type AttemptResult = {
  public_id: string;
  is_correct: boolean;
  submitted: string;
  correct_answer: string;
  explanation: string;
  theory_score: number;
  mastery_status: string;
};
