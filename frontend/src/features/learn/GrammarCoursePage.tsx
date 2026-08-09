import { useEffect, useReducer, useState } from "react";
import { ArrowLeft, Check, ChevronRight, RotateCcw } from "lucide-react";
import { Link } from "react-router";
import { learnApi } from "../../api/client";
import type { EpisodeStatus, EpisodeSummary } from "../../api/types";
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

const statusLabels: Record<EpisodeStatus, string> = {
  completed: "完了",
  in_progress: "学習中",
  not_started: "未開始",
};

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
          <Link className={styles.backAction} to="/learn" aria-label="学習に戻る">
            <ArrowLeft aria-hidden="true" size={22} />
          </Link>
          <div>
            <span className={styles.eyebrow}>GRAMMAR PATH</span>
            <h1>文法コース</h1>
          </div>
        </header>

        {state.phase === "loading" ? (
          <section className={styles.statusSurface} role="status" aria-live="polite">
            <p>コースを読み込んでいます…</p>
          </section>
        ) : state.phase === "error" ? (
          <section className={styles.statusSurface}>
            <h2>コースを読み込めませんでした</h2>
            <p>通信状況を確認して、もう一度お試しください。</p>
            <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
              <RotateCcw aria-hidden="true" size={18} />
              再読み込み
            </button>
          </section>
        ) : (
          <>
            <div className={styles.courseSummary}>
              <p>短いエピソードを順番に進めて、使える文法を増やしましょう。</p>
              <span>{state.episodes.length} エピソード</span>
            </div>

            <ol className={styles.episodePath} aria-label="文法エピソード一覧">
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
                        <span>{statusLabels[episode.status]}</span>
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
