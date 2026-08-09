import { useEffect, useState } from "react";
import { ArrowRight, BookMarked, ChevronRight, RotateCcw, Sparkles } from "lucide-react";
import { Link } from "react-router";
import { learnApi, profileApi } from "../../api/client";
import type { EpisodeSummary, LearningSummary, UserProfile } from "../../api/types";
import { BottomNav } from "../navigation/BottomNav";
import { useTranslation } from "react-i18next";
import styles from "./HomePage.module.css";

type HomeState =
  | { phase: "loading" }
  | { phase: "error" }
  | { phase: "ready"; profile: UserProfile; summary: LearningSummary; episode: EpisodeSummary | null };

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function episodeNumber(epNo: string) {
  return Number(epNo.replace(/^EP/, ""));
}

export function HomePage() {
  const { t } = useTranslation();
  const [state, setState] = useState<HomeState>({ phase: "loading" });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    Promise.all([
      profileApi.me(controller.signal),
      learnApi.summary(controller.signal),
      learnApi.episodes(controller.signal),
    ])
      .then(([profile, summary, episodes]) => {
        const resumeEpisode = summary.grammar.resume_episode ?? summary.grammar.current_episode;
        const episode =
          episodes.find((item) => episodeNumber(item.ep_no) === resumeEpisode) ?? null;
        setState({ phase: "ready", profile, summary, episode });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setState({ phase: "error" });
      });

    return () => controller.abort();
  }, [reloadKey]);

  if (state.phase !== "ready") {
    return (
      <main className={styles.pageShell}>
        <section className={styles.status} role={state.phase === "loading" ? "status" : undefined}>
          <span>kanmanabi</span>
          <h1>{state.phase === "loading" ? t("home.loading") : t("home.loadFailed")}</h1>
          {state.phase === "error" && (
            <button type="button" onClick={() => { setState({ phase: "loading" }); setReloadKey((key) => key + 1); }}>
              <RotateCcw aria-hidden="true" size={18} />
              {t("common.reload")}
            </button>
          )}
        </section>
      </main>
    );
  }

  const { profile, summary, episode } = state;
  const dueTotal = summary.vocabulary.due_count + summary.grammar.due_count;
  const resumeEpisode = summary.grammar.resume_episode ?? summary.grammar.current_episode;
  const resumeEpisodeNo = `EP${String(resumeEpisode).padStart(2, "0")}`;
  const resumeLabel = summary.grammar.resume_episode
    ? t("home.resumeEpisode", { ep: resumeEpisodeNo })
    : t("home.startEpisode", { ep: resumeEpisodeNo });

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <span className={styles.brand}>kanmanabi</span>
          <span className={styles.level}>{t("common.topikLevel", { level: summary.level_band })}</span>
        </header>

        <section className={styles.welcome}>
          <span className={styles.eyebrow}>{t("home.eyebrow")}</span>
          <h1>{profile.name ? t("home.welcomeNamed", { name: profile.name }) : t("home.welcome")}</h1>
          <p>{t("home.intro")}</p>
        </section>

        <section className={styles.reviewCard} aria-labelledby="review-title">
          <span className={styles.reviewIcon}><Sparkles aria-hidden="true" size={24} /></span>
          <div>
            <span className={styles.cardLabel}>{t("home.menuLabel")}</span>
            <h2 id="review-title">{t("home.reviewCount", { count: dueTotal })}</h2>
            <p>{t("common.grammar")} {summary.grammar.due_count} · {t("common.vocabulary")} {summary.vocabulary.due_count}</p>
          </div>
          <Link to="/review">
            {t("home.startReview")}
            <ArrowRight aria-hidden="true" size={19} />
          </Link>
        </section>

        <section className={styles.section} aria-labelledby="continue-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.cardLabel}>{t("home.grammarCourse")}</span>
              <h2 id="continue-title">{t("home.continueTitle")}</h2>
            </div>
            <span>{resumeEpisodeNo} / {summary.grammar.total_episodes}</span>
          </div>
          <div className={styles.lessonRow}>
            <span className={styles.lessonNumber}>{String(resumeEpisode).padStart(2, "0")}</span>
            <div>
              <strong>{resumeEpisodeNo} · {episode?.title ?? t("home.nextEpisode")}</strong>
              <p>{episode?.summary ?? t("home.stepHint")}</p>
            </div>
          </div>
          <Link className={styles.outlineAction} to={`/learn/grammar/${resumeEpisodeNo}`}>
            {resumeLabel}
            <ChevronRight aria-hidden="true" size={19} />
          </Link>
        </section>

        <Link className={styles.wordShortcut} to="/study/vocabulary">
          <span><BookMarked aria-hidden="true" size={22} /></span>
          <div><b>{t("home.newWords")}</b><small>{t("home.wordTrackOf", { level: summary.level_band })}</small></div>
          <ChevronRight aria-hidden="true" size={20} />
        </Link>
      </div>
      <BottomNav current="home" />
    </main>
  );
}
