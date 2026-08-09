import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Check, ChevronRight, RotateCcw } from "lucide-react";
import { Link } from "react-router";
import { conjugationApi } from "../../api/client";
import type {
  ConjugationAnswerResponse,
  ConjugationDrill,
  ConjugationFormKey,
} from "../../api/types";
import styles from "./ConjugationPage.module.css";

const FIELDS: Array<{ key: ConjugationFormKey; label: string; suffix: string }> = [
  { key: "stem", label: "語幹（다を取る）", suffix: "＋고 있어요" },
  { key: "ae", label: "아/어形", suffix: "＋요" },
  { key: "eu", label: "(으)形", suffix: "＋면" },
];

type Answers = Record<ConjugationFormKey, string>;
const EMPTY_ANSWERS: Answers = { stem: "", ae: "", eu: "" };

function ResultValue({ result }: { result: ConjugationAnswerResponse["results"][ConjugationFormKey] }) {
  if (result.correct) {
    return <><strong lang="ko">{result.answer}</strong><Check aria-label="正解" size={21} /></>;
  }
  return (
    <span className={styles.correction}>
      <del lang="ko">{result.given || "未回答"}</del>
      <strong lang="ko">{result.answer}</strong>
      <span>修正</span>
    </span>
  );
}

export function ConjugationPage() {
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

  if (phase === "loading") return <main className={styles.centerState} role="status">活用問題を準備しています…</main>;
  if (phase === "error") return <main className={styles.centerState}><p>問題を読み込めませんでした。</p><button onClick={() => loadNext()}><RotateCcw size={18} />もう一度</button></main>;
  if (phase === "done" || !drill) return <main className={styles.centerState}><h1>今日の練習は完了です</h1><Link to="/learn">学習に戻る</Link></main>;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Link to="/learn" aria-label="学習に戻る"><ArrowLeft size={27} /></Link>
        <h1>活用トレーニング</h1>
        <span>{position} / 10</span>
      </header>
      <div className={styles.progress} aria-label={`進捗 ${position} / 10`}><span style={{ width: `${position * 10}%` }} /></div>

      <section className={styles.task} aria-labelledby="drill-word">
        <h2 id="drill-word" lang="ko">{drill.word}</h2>
        <p lang="ja">{drill.meaning_ja ?? "意味未登録"}</p>
        {!result ? <h3>3つの形に変えてください</h3> : null}

        <div className={styles.formRows}>
          {FIELDS.map((field, index) => (
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
                  enterKeyHint={index === FIELDS.length - 1 ? "done" : "next"}
                  value={answers[field.key]}
                  onChange={(event) => setAnswers((current) => ({ ...current, [field.key]: event.target.value }))}
                  onKeyDown={(event) => { if (event.key === "Enter" && index === FIELDS.length - 1) void submit(); }}
                />
              )}
            </label>
          ))}
        </div>

        {result ? (
          <div className={styles.feedback} aria-live="polite">
            <h3>{result.rule.label_ja}</h3>
            <p>{result.rule.explanation_ja}</p>
            <strong lang="ko">{result.contrast}</strong>
          </div>
        ) : (
          <details className={styles.help}>
            <summary>形の説明を見る <ChevronRight size={17} /></summary>
            <p>後ろに付く表現を手がかりに、三つの基本形を作ります。</p>
          </details>
        )}
      </section>

      <div className={styles.actions}>
        {result?.added_to_review ? <p><Check size={18} />{result.rule.label_ja}を復習に追加しました</p> : null}
        {result ? (
          <><button type="button" onClick={() => loadNext(true)}>次の問題へ</button><button className={styles.quiet} type="button" onClick={() => { setResult(null); setAnswers(EMPTY_ANSWERS); }}>もう一度解く</button></>
        ) : (
          <button type="button" disabled={phase === "submitting" || Object.values(answers).every((value) => !value.trim())} onClick={() => void submit()}>
            {phase === "submitting" ? "確認しています…" : "答えを確認"}
          </button>
        )}
      </div>
    </main>
  );
}
