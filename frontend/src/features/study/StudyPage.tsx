import { useEffect, useReducer, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { AlertCircle, Eye, EyeOff, RotateCcw, Star } from "lucide-react";
import { learnApi, studyApi } from "../../api/client";
import type { AnswerResponse, StudyTrack } from "../../api/types";
import mascotCorrect from "../../assets/mascot/guide-correct.png";
import {
  getCurrentAnswer,
  inputPlaceholderKey,
  questionLabelKey,
  initialStudySessionState,
  studySessionReducer,
} from "./studySession";
import { useTranslation } from "react-i18next";
import styles from "./StudyPage.module.css";

const DAILY_GOAL = 12;

interface StudyPageProps {
  track?: StudyTrack;
  epNo?: string;
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function StudyPage({ track, epNo }: StudyPageProps) {
  const { t } = useTranslation();
  const [state, dispatch] = useReducer(studySessionReducer, initialStudySessionState);
  const [reloadKey, setReloadKey] = useState(0);
  const [visibleChoicesForQuestion, setVisibleChoicesForQuestion] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ type: "loadStart" });

    Promise.all([
      studyApi.next({ level: 1, track, ep_no: epNo, signal: controller.signal }),
      studyApi.due(controller.signal),
    ])
      .then(([next, due]) => {
        dispatch({ type: "loadSuccess", next, dueCount: due.due_count });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          dispatch({ type: "loadFailure", message: "study.loadFailed" });
        }
      });

    return () => controller.abort();
  }, [epNo, reloadKey, track]);

  useEffect(() => {
    if (state.phase === "complete" && track === "grammar" && epNo) {
      learnApi.updateEpisodeProgress(epNo, { practice: true }).catch(() => undefined);
    }
  }, [epNo, state.phase, track]);

  if (state.phase === "loading") {
    return <LoadingView />;
  }

  if (state.phase === "error") {
    return (
      <StatusView
        title={t("study.errorTitle")}
        message={state.loadError ? t(state.loadError) : t("common.retryHint")}
        actionLabel={t("common.reload")}
        onAction={() => setReloadKey((key) => key + 1)}
      />
    );
  }

  if (state.phase === "complete") {
    return (
      <main className={styles.pageShell}>
        <section className={styles.complete} aria-labelledby="complete-title">
          <span className={styles.brand}>kanmanabi</span>
          <div className={styles.completeIllustration}>
            <img src={mascotCorrect} alt={t("study.completeAlt")} />
          </div>
          <h1 id="complete-title">{t("study.completeTitle")}</h1>
          <p>{t("study.completeBody")}</p>
          <button
            type="button"
            className={styles.primaryButton}
            onClick={() => setReloadKey((key) => key + 1)}
          >
            <RotateCcw aria-hidden="true" size={20} strokeWidth={2.4} />
            {t("study.reviewAgain")}
          </button>
        </section>
      </main>
    );
  }

  const question = state.question;
  if (question === null) return null;

  const questionId = question.id;
  const questionKey = `${reloadKey}:${question.id}`;
  const showChoices = visibleChoicesForQuestion === questionKey;
  const currentAnswer = getCurrentAnswer(state);
  const isFeedback = state.phase === "feedback";
  const position = Math.min(state.completedCount + 1, DAILY_GOAL);
  const progress = (position / DAILY_GOAL) * 100;

  async function submitAnswer() {
    const answer = getCurrentAnswer(state);
    if (!answer || state.isSubmitting) return;

    dispatch({ type: "submitStart" });
    try {
      const result = await studyApi.answer({
        question_id: questionId,
        answer,
        used_choices: state.usedChoices,
      });
      dispatch({ type: "submitSuccess", answer, result });

      studyApi
        .due()
        .then((due) => dispatch({ type: "dueUpdated", dueCount: due.due_count }))
        .catch(() => undefined);
    } catch {
      dispatch({ type: "submitFailure", message: "study.submitFailed" });
    }
  }

  async function loadNextQuestion() {
    if (state.isAdvancing) return;

    dispatch({ type: "nextStart" });
    try {
      const next = await studyApi.next({ level: 1, track, ep_no: epNo });
      dispatch({ type: "nextSuccess", next });
    } catch {
      dispatch({ type: "nextFailure", message: "study.nextFailed" });
    }
  }

  return (
    <main className={styles.pageShell}>
      <section className={styles.studySurface} aria-label={t("study.sectionAria")}>
        <header className={styles.header}>
          <span className={styles.brand}>kanmanabi</span>
          <span className={styles.dueCount}>{t("study.dueCount", { count: state.dueCount })}</span>
        </header>

        <div className={styles.progressRow} aria-label={`${position} / ${DAILY_GOAL}`}>
          <div className={styles.progressTrack}>
            <motion.span
              className={styles.progressFill}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            />
            <motion.span
              className={styles.progressStar}
              animate={{ left: `${progress}%` }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <Star aria-hidden="true" size={24} fill="currentColor" strokeWidth={2.1} />
            </motion.span>
          </div>
          <span className={styles.progressText}>
            {position} / {DAILY_GOAL}
          </span>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={question.id}
            className={styles.questionBlock}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.24 }}
          >
            <div className={styles.questionMeta}>
              <div className={styles.questionHeading}>
                <span className={styles.trackBadge}>
                  {question.track === "grammar"
                    ? t("study.grammarTrack", { episode: question.ep_no ? ` · ${question.ep_no}` : "" })
                    : t("study.vocabularyTrack")}
                </span>
                <h1>{t(questionLabelKey(question))}</h1>
              </div>
              <span className={styles.difficulty} aria-label={t("study.difficultyAria", { difficulty: question.difficulty })}>
                <Star aria-hidden="true" size={19} fill="currentColor" />
                {question.difficulty}
              </span>
            </div>
            <p
              className={styles.prompt}
              lang={
                question.qtype === "word_to_ja"
                  ? "ko"
                  : question.qtype === "ja_to_word" || question.qtype === "hanja_to_word"
                    ? "ja"
                    : undefined
              }
            >
              {question.prompt}
            </p>
          </motion.div>
        </AnimatePresence>

        <form
          className={styles.answerForm}
          onSubmit={(event) => {
            event.preventDefault();
            void submitAnswer();
          }}
        >
          <AnimatePresence initial={false}>
            {isFeedback && state.result ? (
              <FeedbackPanel
                key="feedback"
                prompt={question.prompt}
                result={state.result}
                isAdvancing={state.isAdvancing}
                error={state.operationError}
                onNext={() => void loadNextQuestion()}
              />
            ) : (
              <motion.div
                key="answer-input"
                className={styles.recallArea}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.18 }}
              >
                <label className={styles.srOnly} htmlFor="typed-answer">
                  {t(inputPlaceholderKey(question))}
                </label>
                <input
                  id="typed-answer"
                  className={styles.answerInput}
                  value={state.typedAnswer}
                  onChange={(event) => dispatch({ type: "type", answer: event.target.value })}
                  onKeyDown={(event) => {
                    if (event.nativeEvent.isComposing || event.keyCode === 229) {
                      event.preventDefault();
                    }
                  }}
                  placeholder={t(inputPlaceholderKey(question))}
                  lang={
                    question.qtype === "word_to_ja"
                      ? "ja"
                      : question.qtype === "ja_to_word" || question.qtype === "hanja_to_word"
                        ? "ko"
                        : undefined
                  }
                  autoComplete="off"
                  enterKeyHint="done"
                  disabled={state.isSubmitting}
                />
                {question.choices.length > 0 ? (
                  <button
                    type="button"
                    className={styles.choiceToggle}
                    aria-expanded={showChoices}
                    aria-controls="answer-choices"
                    onClick={() =>
                      setVisibleChoicesForQuestion((visibleQuestionKey) => {
                        if (visibleQuestionKey === questionKey) return null;
                        dispatch({ type: "choicesRevealed" });
                        return questionKey;
                      })
                    }
                    disabled={state.isSubmitting}
                  >
                    {showChoices ? (
                      <EyeOff aria-hidden="true" size={18} strokeWidth={2.2} />
                    ) : (
                      <Eye aria-hidden="true" size={18} strokeWidth={2.2} />
                    )}
                    {showChoices ? t("study.hideChoices") : t("study.showChoices")}
                  </button>
                ) : null}
                <AnimatePresence initial={false}>
                  {showChoices && question.choices.length > 0 ? (
                    <motion.fieldset
                      id="answer-choices"
                      className={styles.choices}
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                    >
                      <legend className={styles.srOnly}>{t("study.answerLegend")}</legend>
                      {question.choices.map((choice) => {
                        const isSelected = state.selectedAnswer === choice;

                        return (
                          <button
                            key={choice}
                            type="button"
                            className={`${styles.choice} ${isSelected ? styles.choiceSelected : ""}`}
                            onClick={() => dispatch({ type: "select", answer: choice })}
                            disabled={state.isSubmitting}
                            aria-pressed={isSelected}
                          >
                            <motion.span animate={{ scale: isSelected ? 1.03 : 1 }}>
                              {choice}
                            </motion.span>
                          </button>
                        );
                      })}
                    </motion.fieldset>
                  ) : null}
                </AnimatePresence>
                <p className={styles.choiceHint}>
                  {t("study.inputHint")}
                </p>
                {state.operationError ? <InlineError messageKey={state.operationError} /> : null}
                <button
                  type="submit"
                  className={styles.primaryButton}
                  disabled={!currentAnswer || state.isSubmitting}
                >
                  {state.isSubmitting ? t("study.checking") : t("study.checkAnswer")}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </section>
    </main>
  );
}

interface FeedbackPanelProps {
  prompt: string;
  result: AnswerResponse;
  isAdvancing: boolean;
  error: string | null;
  onNext: () => void;
}

function FeedbackPanel({ prompt, result, isAdvancing, error, onNext }: FeedbackPanelProps) {
  const { t } = useTranslation();
  return (
    <motion.section
      className={`${styles.feedback} ${result.correct ? styles.feedbackCorrect : styles.feedbackWrong}`}
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ type: "spring", stiffness: 310, damping: 29 }}
      aria-live="polite"
    >
      <div className={styles.feedbackCopy}>
        <h2>{result.correct ? t("study.correct") : t("study.incorrect")}</h2>
        <p className={styles.answerPair}>
          <span>{prompt}</span>
          <span aria-hidden="true"> = </span>
          <strong lang="ko">{result.correct_answer}</strong>
        </p>
        {!result.correct ? <p className={styles.encouragement}>{t("study.encouragement")}</p> : null}
        {result.explanation ? <p className={styles.explanation}>{result.explanation}</p> : null}
      </div>
      {result.correct ? (
        <motion.div
          className={styles.mascot}
          initial={{ opacity: 0, y: 12, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay: 0.08, duration: 0.28 }}
        >
          <img src={mascotCorrect} alt="" />
        </motion.div>
      ) : null}
      {error ? <InlineError messageKey={error} /> : null}
      <button type="button" className={styles.primaryButton} onClick={onNext} disabled={isAdvancing}>
        {isAdvancing ? t("common.loading") : t("study.next")}
      </button>
    </motion.section>
  );
}

/** 상태에는 번역 키가 담기므로 렌더 시점에 번역한다(언어를 바꾸면 표시 중인 메시지도 따라 바뀐다). */
function InlineError({ messageKey }: { messageKey: string }) {
  const { t } = useTranslation();
  return (
    <p className={styles.inlineError} role="alert">
      <AlertCircle aria-hidden="true" size={17} />
      {t(messageKey)}
    </p>
  );
}

function LoadingView() {
  const { t } = useTranslation();
  return (
    <main className={styles.pageShell} aria-busy="true">
      <section className={styles.studySurface} aria-label={t("study.loadingAria")}>
        <header className={styles.header}>
          <span className={styles.brand}>kanmanabi</span>
          <span className={`${styles.skeleton} ${styles.skeletonShort}`} />
        </header>
        <div className={`${styles.skeleton} ${styles.skeletonProgress}`} />
        <div className={`${styles.skeleton} ${styles.skeletonLabel}`} />
        <div className={`${styles.skeleton} ${styles.skeletonPrompt}`} />
        <div className={styles.loadingChoices}>
          {Array.from({ length: 4 }, (_, index) => (
            <span key={index} className={`${styles.skeleton} ${styles.skeletonChoice}`} />
          ))}
        </div>
      </section>
    </main>
  );
}

interface StatusViewProps {
  title: string;
  message: string;
  actionLabel: string;
  onAction: () => void;
}

function StatusView({ title, message, actionLabel, onAction }: StatusViewProps) {
  return (
    <main className={styles.pageShell}>
      <section className={styles.statusView} aria-labelledby="status-title">
        <span className={styles.brand}>kanmanabi</span>
        <AlertCircle aria-hidden="true" className={styles.statusIcon} size={34} />
        <h1 id="status-title">{title}</h1>
        <p>{message}</p>
        <button type="button" className={styles.primaryButton} onClick={onAction}>
          {actionLabel}
        </button>
      </section>
    </main>
  );
}
