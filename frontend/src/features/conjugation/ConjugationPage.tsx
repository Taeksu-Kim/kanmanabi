import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Check, ChevronRight, RotateCcw } from "lucide-react";
import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { conjugationApi } from "../../api/client";
import type {
  ConjugationAnswerResponse,
  ConjugationDrill,
  ConjugationFormKey,
} from "../../api/types";
import styles from "./ConjugationPage.module.css";

type Answers = Record<ConjugationFormKey, string>;
const EMPTY_ANSWERS: Answers = { stem: "", ae: "", eu: "" };

function ResultValue({ result }: { result: ConjugationAnswerResponse["results"][ConjugationFormKey] }) {
  const { t } = useTranslation();
  if (result.correct) {
    return <><strong lang="ko">{result.answer}</strong><Check aria-label={t("conjugation.correct")} size={21} /></>;
  }
  return (
    <span className={styles.correction}>
      <del lang="ko">{result.given || t("conjugation.unanswered")}</del>
      <strong lang="ko">{result.answer}</strong>
      <span>{t("conjugation.corrected")}</span>
    </span>
  );
}

export function ConjugationPage() {
  const { t } = useTranslation();
  const fields: Array<{ key: ConjugationFormKey; label: string; suffix: string }> = [
    { key: "stem", label: t("conjugation.forms.stem"), suffix: "＋고 있어요" },
    { key: "ae", label: t("conjugation.forms.ae"), suffix: "＋요" },
    { key: "eu", label: t("conjugation.forms.eu"), suffix: "＋면" },
  ];
  const [drill, setDrill] = useState<ConjugationDrill | null>(null);
  const [answers, setAnswers] = useState<Answers>(EMPTY_ANSWERS);
  const [result, setResult] = useState<ConjugationAnswerResponse | null>(null);
  const [position, setPosition] = useState(1);
  const [phase, setPhase] = useState<"loading" | "ready" | "submitting" | "done" | "error">("loading");
  const firstInput = useRef<HTMLInputElement>(null);

  const loadNext = (advance = false) => {
    if (advance && position >= 10) {
      setPhase("done");
      return null;
    }
    const controller = new AbortController();
    setPhase("loading");
    setResult(null);
    setAnswers(EMPTY_ANSWERS);
    if (advance) setPosition((current) => current + 1);
    conjugationApi.next(1, controller.signal)
      .then((response) => {
        setDrill(response.drill);
        setPhase(response.drill ? "ready" : "done");
      })
      .catch(() => setPhase("error"));
    return controller;
  };

  useEffect(() => {
    const controller = new AbortController();
    conjugationApi.next(1, controller.signal)
      .then((response) => {
        setDrill(response.drill);
        setPhase(response.drill ? "ready" : "done");
      })
      .catch(() => setPhase("error"));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (phase === "ready" && !result) firstInput.current?.focus();
  }, [phase, result, drill]);

  const submit = async () => {
    if (!drill || phase !== "ready") return;
    setPhase("submitting");
    try {
      const response = await conjugationApi.answer({ vocab_id: drill.id, ...answers });
      setResult(response);
      setPhase("ready");
    } catch {
      setPhase("error");
    }
  };

  if (phase === "loading") return <main className={styles.centerState} role="status">{t("conjugation.loading")}</main>;
  if (phase === "error") return <main className={styles.centerState}><p>{t("conjugation.loadFailed")}</p><button onClick={() => loadNext()}><RotateCcw size={18} />{t("common.reload")}</button></main>;
  if (phase === "done" || !drill) return <main className={styles.centerState}><h1>{t("conjugation.complete")}</h1><Link to="/learn">{t("common.backToLearn")}</Link></main>;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/learn" aria-label={t("common.backToLearn")}><ArrowLeft size={27} /></Link>
        <h1>{t("conjugation.title")}</h1>
        <span>{position} / 10</span>
      </header>
      <div className={styles.progress} aria-label={t("conjugation.progress", { position, total: 10 })}><span style={{ width: `${position * 10}%` }} /></div>

      <section className={styles.task} aria-labelledby="drill-word">
        <h2 id="drill-word" lang="ko">{drill.word}</h2>
        <p lang="ja">{drill.meaning_ja ?? t("hub.missingMeaning")}</p>
        {!result ? <h3>{t("conjugation.instruction")}</h3> : null}

        <div className={styles.formRows}>
          {fields.map((field, index) => (
            <label className={styles.formRow} key={field.key}>
              <span className={styles.formLabel}><b>{field.label}</b><small lang="ko">{field.suffix}</small></span>
              {result ? (
                <span className={`${styles.resultBox} ${result.results[field.key].correct ? styles.correct : styles.corrected}`}>
                  <ResultValue result={result.results[field.key]} />
                </span>
              ) : (
                <input
                  ref={index === 0 ? firstInput : undefined}
                  lang="ko"
                  autoComplete="off"
                  spellCheck={false}
                  enterKeyHint={index === fields.length - 1 ? "done" : "next"}
                  value={answers[field.key]}
                  onChange={(event) => setAnswers((current) => ({ ...current, [field.key]: event.target.value }))}
                  onKeyDown={(event) => { if (event.key === "Enter" && index === fields.length - 1) void submit(); }}
                />
              )}
            </label>
          ))}
        </div>

        {result ? (
          <div className={styles.feedback} aria-live="polite">
            <h3>{t(`conjugation.rules.${result.rule.id}.label`, { defaultValue: result.rule.label_ja })}</h3>
            <p>{t(`conjugation.rules.${result.rule.id}.explanation`, { defaultValue: result.rule.explanation_ja })}</p>
            <strong lang="ko">{result.contrast}</strong>
          </div>
        ) : (
          <details className={styles.help}>
            <summary>{t("conjugation.showHelp")} <ChevronRight size={17} /></summary>
            <p>{t("conjugation.help")}</p>
          </details>
        )}
      </section>

      <div className={styles.actions}>
        {result?.added_to_review ? <p><Check size={18} />{t("conjugation.addedToReview", { rule: t(`conjugation.rules.${result.rule.id}.label`, { defaultValue: result.rule.label_ja }) })}</p> : null}
        {result ? (
          <><button type="button" onClick={() => loadNext(true)}>{t("conjugation.next")}</button><button className={styles.quiet} type="button" onClick={() => { setResult(null); setAnswers(EMPTY_ANSWERS); }}>{t("conjugation.retry")}</button></>
        ) : (
          <button type="button" disabled={phase === "submitting" || Object.values(answers).every((value) => !value.trim())} onClick={() => void submit()}>
            {phase === "submitting" ? t("conjugation.checking") : t("conjugation.check")}
          </button>
        )}
      </div>
    </main>
  );
}
