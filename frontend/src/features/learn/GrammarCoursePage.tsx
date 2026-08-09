import { useEffect, useReducer, useState } from "react";
import { ArrowLeft, Check, ChevronRight, RotateCcw } from "lucide-react";
import { Link } from "react-router";
import { learnApi } from "../../api/client";
import type { EpisodeSummary } from "../../api/types";
import { useTranslation } from "react-i18next";
import styles from "./GrammarCoursePage.module.css";

type CourseState =
  | { phase: "loading"; episodes: EpisodeSummary[] }
  | { phase: "ready"; episodes: EpisodeSummary[] }
  | { phase: "error"; episodes: EpisodeSummary[] };

type CourseAction =
  | { type: "loadStart" }
  | { type: "loadSuccess"; episodes: EpisodeSummary[] }
  | { type: "loadFailure" };

const initialState: CourseState = { phase: "loading", episodes: [] };

function courseReducer(_state: CourseState, action: CourseAction): CourseState {
  switch (action.type) {
    case "loadStart":
      return initialState;
    case "loadSuccess":
      return { phase: "ready", episodes: action.episodes };
    case "loadFailure":
      return { phase: "error", episodes: [] };
  }
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function GrammarCoursePage() {
  const { t } = useTranslation();
  const [state, dispatch] = useReducer(courseReducer, initialState);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ type: "loadStart" });

    learnApi
      .episodes(controller.signal)
      .then((episodes) => dispatch({ type: "loadSuccess", episodes }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) dispatch({ type: "loadFailure" });
      });

    return () => controller.abort();
  }, [reloadKey]);

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <Link className={styles.backAction} to="/learn" aria-label={t("common.backToLearn")}>
            <ArrowLeft aria-hidden="true" size={22} />
          </Link>
          <div>
            <span className={styles.eyebrow}>GRAMMAR PATH</span>
            <h1>{t("course.title")}</h1>
          </div>
        </header>

        {state.phase === "loading" ? (
          <section className={styles.statusSurface} role="status" aria-live="polite">
            <p>{t("course.loading")}</p>
          </section>
        ) : state.phase === "error" ? (
          <section className={styles.statusSurface}>
            <h2>{t("course.loadFailed")}</h2>
            <p>{t("common.retryHint")}</p>
            <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
              <RotateCcw aria-hidden="true" size={18} />
              {t("common.reload")}
            </button>
          </section>
        ) : (
          <>
            <div className={styles.courseSummary}>
              <p>{t("course.intro")}</p>
              <span>{t("course.episodeCount", { count: state.episodes.length })}</span>
            </div>

            <ol className={styles.episodePath} aria-label={t("course.listAria")}>
              {state.episodes.map((episode) => (
                <li key={episode.ep_no} className={styles.episodeItem}>
                  <Link
                    className={`${styles.episodeLink} ${styles[episode.status]}`}
                    to={`/learn/grammar/${episode.ep_no}`}
                  >
                    <span className={styles.marker}>
                      {episode.status === "completed" ? (
                        <Check aria-hidden="true" size={18} strokeWidth={3} />
                      ) : (
                        String(episode.order_index).padStart(2, "0")
                      )}
                    </span>
                    <span className={styles.episodeCopy}>
                      <span className={styles.episodeMeta}>
                        <b>{episode.ep_no}</b>
                        <span>{t(`course.status.${episode.status}`)}</span>
                      </span>
                      <strong>{episode.title}</strong>
                      {episode.summary && <small>{episode.summary}</small>}
                    </span>
                    <ChevronRight aria-hidden="true" className={styles.chevron} size={20} />
                  </Link>
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </main>
  );
}
