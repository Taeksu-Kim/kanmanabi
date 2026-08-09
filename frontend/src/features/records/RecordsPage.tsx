import { useEffect, useState } from "react";
import { BookOpenCheck, Gauge, Layers3, RotateCcw } from "lucide-react";
import { learnApi } from "../../api/client";
import type { LearningSummary } from "../../api/types";
import { BottomNav } from "../navigation/BottomNav";
import styles from "./RecordsPage.module.css";

export function RecordsPage() {
  const [summary, setSummary] = useState<LearningSummary | null>(null);
  const [failed, setFailed] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    learnApi
      .summary(controller.signal)
      .then(setSummary)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setFailed(true);
      });
    return () => controller.abort();
  }, [reloadKey]);

  if (!summary) {
    return (
      <main className={styles.pageShell}>
        <section className={styles.status} role={failed ? undefined : "status"}>
          <span>kanmanabi</span>
          <h1>{failed ? "記録を読み込めませんでした" : "記録を読み込んでいます…"}</h1>
          {failed && <button type="button" onClick={() => { setSummary(null); setFailed(false); setReloadKey((key) => key + 1); }}><RotateCcw aria-hidden="true" size={18} />再読み込み</button>}
        </section>
      </main>
    );
  }

  const dueTotal = summary.vocabulary.due_count + summary.grammar.due_count;
  const resumeEpisode = summary.grammar.resume_episode ?? summary.grammar.current_episode;

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <div>
            <span>学びの現在地</span>
            <h1>学習記録</h1>
          </div>
          <span className={styles.level}>TOPIK {summary.level_band}級相当</span>
        </header>
        <p className={styles.intro}>いま積み上がっている内容を、トラックごとに確認できます。</p>

        <section className={styles.heroStat} aria-label="文法コースの進捗">
          <span className={styles.statIcon}><BookOpenCheck aria-hidden="true" size={26} /></span>
          <div><small>完了した文法EP</small><strong>{summary.grammar.completed_episodes.length} / {summary.grammar.total_episodes}</strong></div>
          <span className={styles.currentEp}>現在 EP{String(summary.grammar.current_episode).padStart(2, "0")}</span>
          <div className={styles.progressTrack} aria-hidden="true"><span style={{ width: `${Math.min(100, (summary.grammar.completed_episodes.length / summary.grammar.total_episodes) * 100)}%` }} /></div>
        </section>

        <div className={styles.statGrid}>
          <section>
            <span><Gauge aria-hidden="true" size={22} /></span>
            <small>{summary.grammar.resume_episode ? "つづきの文法EP" : "次の文法EP"}</small>
            <strong>EP{String(resumeEpisode).padStart(2, "0")}</strong>
          </section>
          <section>
            <span><Layers3 aria-hidden="true" size={22} /></span>
            <small>今日の復習</small>
            <strong>{dueTotal}問</strong>
          </section>
        </div>

        <section className={styles.breakdown} aria-labelledby="review-breakdown">
          <h2 id="review-breakdown">復習の内訳</h2>
          <div><span>文法</span><b>{summary.grammar.due_count}問</b></div>
          <div><span>単語</span><b>{summary.vocabulary.due_count}問</b></div>
        </section>
      </div>
      <BottomNav current="records" />
    </main>
  );
}
