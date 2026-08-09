export type QuestionType = "word_to_ja" | "ja_to_word" | "hanja_to_word";

export interface Question {
  id: number;
  qtype: QuestionType;
  prompt: string;
  choices: string[];
  difficulty: 1 | 2;
}

export type NextMode = "new" | "review" | "done";

export interface NextResponse {
  mode: NextMode;
  question: Question | null;
}

export interface AnswerRequest {
  question_id: number;
  answer: string;
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
