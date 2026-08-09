import type { AnswerResponse, NextMode, NextResponse, Question } from "../../api/types";

export type SessionPhase = "loading" | "answering" | "feedback" | "complete" | "error";

export interface StudySessionState {
  phase: SessionPhase;
  mode: NextMode | null;
  question: Question | null;
  dueCount: number;
  completedCount: number;
  selectedAnswer: string;
  typedAnswer: string;
  submittedAnswer: string;
  result: AnswerResponse | null;
  loadError: string | null;
  operationError: string | null;
  isSubmitting: boolean;
  isAdvancing: boolean;
  usedChoices: boolean;
}

export type StudySessionAction =
  | { type: "loadStart" }
  | { type: "loadSuccess"; next: NextResponse; dueCount: number }
  | { type: "loadFailure"; message: string }
  | { type: "select"; answer: string }
  | { type: "type"; answer: string }
  | { type: "choicesRevealed" }
  | { type: "submitStart" }
  | { type: "submitSuccess"; answer: string; result: AnswerResponse }
  | { type: "submitFailure"; message: string }
  | { type: "nextStart" }
  | { type: "nextSuccess"; next: NextResponse }
  | { type: "nextFailure"; message: string }
  | { type: "dueUpdated"; dueCount: number };

export const initialStudySessionState: StudySessionState = {
  phase: "loading",
  mode: null,
  question: null,
  dueCount: 0,
  completedCount: 0,
  selectedAnswer: "",
  typedAnswer: "",
  submittedAnswer: "",
  result: null,
  loadError: null,
  operationError: null,
  isSubmitting: false,
  isAdvancing: false,
  usedChoices: false,
};

export function getCurrentAnswer(state: StudySessionState) {
  return state.typedAnswer.trim() || state.selectedAnswer;
}

function nextQuestionState(
  state: StudySessionState,
  next: NextResponse,
  completedCount: number,
): StudySessionState {
  if (next.mode === "done" || next.question === null) {
    return {
      ...state,
      phase: "complete",
      mode: "done",
      question: null,
      completedCount,
      isAdvancing: false,
      operationError: null,
    };
  }

  return {
    ...state,
    phase: "answering",
    mode: next.mode,
    question: next.question,
    completedCount,
    selectedAnswer: "",
    typedAnswer: "",
    submittedAnswer: "",
    result: null,
    operationError: null,
    isSubmitting: false,
    isAdvancing: false,
    usedChoices: false,
  };
}

export function studySessionReducer(
  state: StudySessionState,
  action: StudySessionAction,
): StudySessionState {
  switch (action.type) {
    case "loadStart":
      return { ...initialStudySessionState, dueCount: state.dueCount };
    case "loadSuccess":
      return nextQuestionState(
        { ...state, dueCount: action.dueCount, loadError: null },
        action.next,
        0,
      );
    case "loadFailure":
      return { ...state, phase: "error", loadError: action.message };
    case "select":
      if (state.phase !== "answering" || state.isSubmitting) return state;
      return { ...state, selectedAnswer: action.answer, typedAnswer: "", operationError: null };
    case "type":
      if (state.phase !== "answering" || state.isSubmitting) return state;
      return { ...state, typedAnswer: action.answer, selectedAnswer: "", operationError: null };
    case "choicesRevealed":
      if (state.phase !== "answering") return state;
      return { ...state, usedChoices: true };
    case "submitStart":
      if (state.phase !== "answering") return state;
      return { ...state, isSubmitting: true, operationError: null };
    case "submitSuccess":
      return {
        ...state,
        phase: "feedback",
        submittedAnswer: action.answer,
        result: action.result,
        isSubmitting: false,
        operationError: null,
      };
    case "submitFailure":
      return { ...state, isSubmitting: false, operationError: action.message };
    case "nextStart":
      if (state.phase !== "feedback") return state;
      return { ...state, isAdvancing: true, operationError: null };
    case "nextSuccess":
      return nextQuestionState(state, action.next, state.completedCount + 1);
    case "nextFailure":
      return { ...state, isAdvancing: false, operationError: action.message };
    case "dueUpdated":
      return { ...state, dueCount: action.dueCount };
  }
}

/** qtype은 DB에 48종이 있고 계속 늘어난다. 사전에 없는 유형은 중립 문구로 폴백한다. */
export function questionLabelKey(question: Question) {
  switch (question.qtype) {
    case "word_to_ja":
      return "study.prompt.word_to_ja";
    case "ja_to_word":
      return "study.prompt.ja_to_word";
    case "hanja_to_word":
      return "study.prompt.hanja_to_word";
    default:
      return "study.prompt.default";
  }
}

export function inputPlaceholderKey(question: Question) {
  switch (question.qtype) {
    case "word_to_ja":
      return "study.placeholder.ja";
    case "ja_to_word":
    case "hanja_to_word":
      return "study.placeholder.ko";
    default:
      return "study.placeholder.default";
  }
}
