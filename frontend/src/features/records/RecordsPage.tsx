import { useEffect, useState } from "react";
import { BookOpenCheck, Gauge, Layers3, RotateCcw } from "lucide-react";
import { learnApi } from "../../api/client";
import type { LearningSummary } from "../../api/types";
import { BottomNav } from "../navigation/BottomNav";
import { useTranslation } from "react-i18next";
import styles from "./RecordsPage.module.css";

export function RecordsPage() {
  const { t } = useTranslation();
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
          <h1>{failed ? t("records.loadFailed") : t("records.loading")}</h1>
          {failed && <button type="button" onClick={() => { setSummary(null); setFailed(false); setReloadKey((key) => key + 1); }}><RotateCcw aria-hidden="true" size={18} />{t("common.reload")}</button>}
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
            <span>{t("records.eyebrow")}</span>
            <h1>{t("records.title")}</h1>
          </div>
          <span className={styles.level}>{t("common.topikLevel", { level: summary.level_band })}</span>
        </header>
        <p className={styles.intro}>{t("records.intro")}</p>

        <section className={styles.heroStat} aria-label={t("records.grammarProgressAria")}>
          <span className={styles.statIcon}><BookOpenCheck aria-hidden="true" size={26} /></span>
          <div><small>{t("records.completedEpisodes")}</small><strong>{summary.grammar.completed_episodes.length} / {summary.grammar.total_episodes}</strong></div>
          <span className={styles.currentEp}>{t("records.currentEpisode", { ep: `EP${String(summary.grammar.current_episode).padStart(2, "0")}` })}</span>
          <div className={styles.progressTrack} aria-hidden="true"><span style={{ width: `${Math.min(100, (summary.grammar.completed_episodes.length / summary.grammar.total_episodes) * 100)}%` }} /></div>
        </section>

        <div className={styles.statGrid}>
          <section>
            <span><Gauge aria-hidden="true" size={22} /></span>
            <small>{summary.grammar.resume_episode ? t("records.resumeLabel") : t("records.nextLabel")}</small>
            <strong>EP{String(resumeEpisode).padStart(2, "0")}</strong>
          </section>
          <section>
            <span><Layers3 aria-hidden="true" size={22} /></span>
            <small>{t("records.todayReview")}</small>
            <strong>{t("common.questionCount", { count: dueTotal })}</strong>
          </section>
        </div>

        <section className={styles.breakdown} aria-labelledby="review-breakdown">
          <h2 id="review-breakdown">{t("records.breakdown")}</h2>
          <div><span>{t("common.grammar")}</span><b>{t("common.questionCount", { count: summary.grammar.due_count })}</b></div>
          <div><span>{t("common.vocabulary")}</span><b>{t("common.questionCount", { count: summary.vocabulary.due_count })}</b></div>
        </section>
      </div>
      <BottomNav current="records" />
    </main>
  );
}
