import { useEffect, useReducer, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { AlertCircle, Check, RotateCcw, Star, X } from "lucide-react";
import { studyApi } from "../../api/client";
import type { AnswerResponse } from "../../api/types";
import mascotCorrect from "../../assets/mascot/guide-correct.png";
import {
  getCurrentAnswer,
  getInputPlaceholder,
  getQuestionLabel,
  initialStudySessionState,
  studySessionReducer,
} from "./studySession";
import styles from "./StudyPage.module.css";

const DAILY_GOAL = 12;

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function StudyPage() {
  const [state, dispatch] = useReducer(studySessionReducer, initialStudySessionState);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ type: "loadStart" });

    Promise.all([studyApi.next(1, controller.signal), studyApi.due(controller.signal)])
      .then(([next, due]) => {
        dispatch({ type: "loadSuccess", next, dueCount: due.due_count });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          dispatch({ type: "loadFailure", message: "学習データを読み込めませんでした。" });
        }
      });

    return () => controller.abort();
  }, [reloadKey]);

  if (state.phase === "loading") {
    return <LoadingView />;
  }

  if (state.phase === "error") {
    return (
      <StatusView
        title="うまく読み込めませんでした"
        message={state.loadError ?? "通信状況を確認して、もう一度お試しください。"}
        actionLabel="再読み込み"
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
            <img src={mascotCorrect} alt="嬉しそうに応援する学習ガイド" />
          </div>
          <h1 id="complete-title">今日の学習、完了！</h1>
          <p>よく頑張りました。短い積み重ねが、ちゃんと力になります。</p>
          <button
            type="button"
            className={styles.primaryButton}
            onClick={() => setReloadKey((key) => key + 1)}
          >
            <RotateCcw aria-hidden="true" size={20} strokeWidth={2.4} />
            もう一度見る
          </button>
        </section>
      </main>
    );
  }

  const question = state.question;
  if (question === null) return null;

  const currentAnswer = getCurrentAnswer(state);
  const isFeedback = state.phase === "feedback";
  const position = Math.min(state.completedCount + 1, DAILY_GOAL);
  const progress = (position / DAILY_GOAL) * 100;

  async function submitAnswer() {
    const answer = getCurrentAnswer(state);
    if (!answer || state.isSubmitting) return;

    dispatch({ type: "submitStart" });
    try {
      const result = await studyApi.answer({ question_id: question.id, answer });
      dispatch({ type: "submitSuccess", answer, result });

      studyApi
        .due()
        .then((due) => dispatch({ type: "dueUpdated", dueCount: due.due_count }))
        .catch(() => undefined);
    } catch {
      dispatch({ type: "submitFailure", message: "答えを送信できませんでした。もう一度お試しください。" });
    }
  }

  async function loadNextQuestion() {
    if (state.isAdvancing) return;

    dispatch({ type: "nextStart" });
    try {
      const next = await studyApi.next();
      dispatch({ type: "nextSuccess", next });
    } catch {
      dispatch({ type: "nextFailure", message: "次の問題を読み込めませんでした。" });
    }
  }

  return (
    <main className={styles.pageShell}>
      <section className={styles.studySurface} aria-label="韓国語の復習">
        <header className={styles.header}>
          <span className={styles.brand}>kanmanabi</span>
          <span className={styles.dueCount}>今日の復習 {state.dueCount}</span>
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
              <h1>{getQuestionLabel(question)}</h1>
              <span className={styles.difficulty} aria-label={`難易度 ${question.difficulty}`}>
                <Star aria-hidden="true" size={19} fill="currentColor" />
                {question.difficulty}
              </span>
            </div>
            <p className={styles.prompt} lang={question.qtype === "word_to_ja" ? "ko" : "ja"}>
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
          <fieldset className={styles.choices}>
            <legend className={styles.srOnly}>答えを選択</legend>
            {question.choices.map((choice) => {
              const isSelected = state.selectedAnswer === choice;
              const isCorrectChoice = isFeedback && choice === state.result?.correct_answer;
              const isWrongChoice = isFeedback && choice === state.submittedAnswer && !state.result?.correct;
              const classNames = [styles.choice];
              if (isSelected) classNames.push(styles.choiceSelected);
              if (isCorrectChoice) classNames.push(styles.choiceCorrect);
              if (isWrongChoice) classNames.push(styles.choiceWrong);
              if (isFeedback && !isCorrectChoice && !isWrongChoice) classNames.push(styles.choiceMuted);

              return (
                <button
                  key={choice}
                  type="button"
                  className={classNames.join(" ")}
                  onClick={() => dispatch({ type: "select", answer: choice })}
                  disabled={isFeedback || state.isSubmitting}
                  aria-pressed={isSelected}
                >
                  <motion.span animate={{ scale: isSelected ? 1.03 : 1 }}>{choice}</motion.span>
                  {isCorrectChoice ? (
                    <span className={styles.choiceIcon}>
                      <Check aria-hidden="true" size={21} strokeWidth={3} />
                    </span>
                  ) : null}
                  {isWrongChoice ? (
                    <span className={`${styles.choiceIcon} ${styles.choiceIconWrong}`}>
                      <X aria-hidden="true" size={21} strokeWidth={3} />
                    </span>
                  ) : null}
                </button>
              );
            })}
          </fieldset>

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
                <div className={styles.separator} aria-hidden="true">
                  <span />
                  <b>または</b>
                  <span />
                </div>
                <label className={styles.srOnly} htmlFor="typed-answer">
                  {getInputPlaceholder(question)}
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
                  placeholder={getInputPlaceholder(question)}
                  lang={question.qtype === "word_to_ja" ? "ja" : "ko"}
                  autoComplete="off"
                  enterKeyHint="done"
                  disabled={state.isSubmitting}
                />
                {state.operationError ? <InlineError message={state.operationError} /> : null}
                <button
                  type="submit"
                  className={styles.primaryButton}
                  disabled={!currentAnswer || state.isSubmitting}
                >
                  {state.isSubmitting ? "確認中…" : "答えを確認"}
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
        <h2>{result.correct ? "正解！" : "あと一歩！"}</h2>
        <p className={styles.answerPair}>
          <span>{prompt}</span>
          <span aria-hidden="true"> = </span>
          <strong lang="ko">{result.correct_answer}</strong>
        </p>
        {!result.correct ? <p className={styles.encouragement}>ここで覚えれば大丈夫。</p> : null}
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
      {error ? <InlineError message={error} /> : null}
      <button type="button" className={styles.primaryButton} onClick={onNext} disabled={isAdvancing}>
        {isAdvancing ? "読み込み中…" : "次へ"}
      </button>
    </motion.section>
  );
}

function InlineError({ message }: { message: string }) {
  return (
    <p className={styles.inlineError} role="alert">
      <AlertCircle aria-hidden="true" size={17} />
      {message}
    </p>
  );
}

function LoadingView() {
  return (
    <main className={styles.pageShell} aria-busy="true">
      <section className={styles.studySurface} aria-label="学習データを読み込み中">
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
