export type QuestionType = string;
export type StudyTrack = "vocabulary" | "grammar";
export type LevelBand = 1 | 2 | 3 | 4 | 5 | 6;
export type EpisodeStatus = "not_started" | "in_progress" | "completed";
export type EpisodeStep = "video" | "point" | "practice";
export type EpisodeSteps = Record<EpisodeStep, boolean>;
export type EpisodeProgressPatch = Partial<EpisodeSteps>;

export interface Question {
  id: number;
  qtype: QuestionType;
  prompt: string;
  choices: string[];
  difficulty: 1 | 2 | 3;
  track: StudyTrack;
  ep_no: string | null;
}

export type NextMode = "new" | "review" | "done";

export interface NextResponse {
  mode: NextMode;
  question: Question | null;
}

export interface AnswerRequest {
  question_id: number;
  answer: string;
  used_choices: boolean;
}

export interface AnswerResponse {
  correct: boolean;
  correct_answer: string;
  explanation: string | null;
  next_due: string;
}

export interface DueResponse {
  due_count: number;
}

export type ConjugationFormKey = "stem" | "ae" | "eu";

export interface ConjugationDrill {
  id: number;
  word: string;
  meaning_ja: string | null;
  rule: { id: string; label_ja: string };
}

export interface ConjugationNextResponse {
  mode: NextMode;
  drill: ConjugationDrill | null;
}

export interface ConjugationAnswerRequest {
  vocab_id: number;
  stem: string;
  ae: string;
  eu: string;
}

export interface ConjugationFormResult {
  correct: boolean;
  given: string;
  answer: string;
}

export interface ConjugationAnswerResponse {
  results: Record<ConjugationFormKey, ConjugationFormResult>;
  rule: { id: string; label_ja: string; explanation_ja: string };
  contrast: string;
  added_to_review: boolean;
}

export interface ConjugationSummary {
  due_count: number;
  weakest_rule: string | null;
  weakest_rule_id: string | null;
}

export interface UserProfile {
  id: number;
  name: string | null;
  email: string;
  picture: string | null;
  level_band: LevelBand | null;
}

export interface UserProfileUpdate {
  name?: string;
  level_band?: LevelBand;
}

export interface VocabularyPreviewItem {
  id: number;
  word: string;
  meaning_ja: string | null;
}

export interface LearningSummary {
  level_band: LevelBand;
  vocabulary: {
    preview: VocabularyPreviewItem[];
    due_count: number;
  };
  grammar: {
    current_episode: number;
    resume_episode?: number | null;
    total_episodes: number;
    completed_episodes: number[];
    due_count: number;
  };
}

export interface EpisodeSummary {
  ep_no: string;
  title: string;
  order_index: number;
  youtube_id: string | null;
  summary: string | null;
  steps: EpisodeSteps;
  status: EpisodeStatus;
}

export interface EpisodeProgressResponse {
  ep_no: string;
  steps: EpisodeSteps;
  status: EpisodeStatus;
}

export interface GoogleAuthResponse {
  id: number;
  name: string | null;
  email: string;
  picture: string | null;
  level_band: LevelBand | null;
  onboarded: boolean;
}

export type VocabularyStatus = "not_started" | "learning" | "reviewing";

export interface VocabularyItem {
  id: number;
  word: string;
  pos: string | null;
  level_band: LevelBand;
  ja: string[];
  hanja: string | null;
  guide: string | null;
  status: VocabularyStatus;
  favorite: boolean;
}

export interface VocabularyListResponse {
  items: VocabularyItem[];
  next_cursor: number | null;
}

export interface VocabularyFavoriteResponse {
  vocab_id: number;
  favorite: boolean;
}
