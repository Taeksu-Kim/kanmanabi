import { useEffect, useReducer, useState } from "react";
import {
  BookOpen,
  Check,
  ChevronRight,
  List,
  Repeat2,
  RotateCcw,
} from "lucide-react";
import { Link } from "react-router";
import { conjugationApi, learnApi } from "../../api/client";
import type { ConjugationSummary, EpisodeSummary, LearningSummary } from "../../api/types";
import { BottomNav } from "../navigation/BottomNav";
import styles from "./LearningHubPage.module.css";

type HubState =
  | { phase: "loading"; summary: null; conjugation: null; episodes: EpisodeSummary[] }
  | { phase: "ready"; summary: LearningSummary; conjugation: ConjugationSummary; episodes: EpisodeSummary[] }
  | { phase: "error"; summary: null; conjugation: null; episodes: EpisodeSummary[] };

type HubAction =
  | { type: "loadStart" }
  | { type: "loadSuccess"; summary: LearningSummary; conjugation: ConjugationSummary; episodes: EpisodeSummary[] }
  | { type: "loadFailure" };

const initialHubState: HubState = { phase: "loading", summary: null, conjugation: null, episodes: [] };

function hubReducer(_state: HubState, action: HubAction): HubState {
  switch (action.type) {
    case "loadStart":
      return initialHubState;
    case "loadSuccess":
      return { phase: "ready", summary: action.summary, conjugation: action.conjugation, episodes: action.episodes };
    case "loadFailure":
      return { phase: "error", summary: null, conjugation: null, episodes: [] };
  }
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function formatEpisodeNo(episode: number) {
  return `EP${String(episode).padStart(2, "0")}`;
}

function getEpisodeNumber(epNo: string) {
  return Number(epNo.replace(/^EP/, ""));
}

function getEpisodePreview(episodes: EpisodeSummary[], currentEpisode: number) {
  if (episodes.length <= 2) return episodes;

  const currentIndex = episodes.findIndex(
    (episode) => getEpisodeNumber(episode.ep_no) === currentEpisode,
  );
  if (currentIndex <= 0) return episodes.slice(0, 2);
  return episodes.slice(currentIndex - 1, currentIndex + 1);
}

export function LearningHubPage() {
  const [state, dispatch] = useReducer(hubReducer, initialHubState);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ type: "loadStart" });

    Promise.all([
      learnApi.summary(controller.signal),
      learnApi.episodes(controller.signal),
      conjugationApi.summary(controller.signal),
    ])
      .then(([summary, episodes, conjugation]) => dispatch({ type: "loadSuccess", summary, episodes, conjugation }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) dispatch({ type: "loadFailure" });
      });

    return () => controller.abort();
  }, [reloadKey]);

  if (state.phase === "loading") {
    return (
      <main className={styles.pageShell}>
        <section className={styles.statusSurface} role="status" aria-live="polite">
          <span className={styles.statusBrand}>kanmanabi</span>
          <h1>学習</h1>
          <p>学習データを読み込んでいます…</p>
        </section>
      </main>
    );
  }

  if (state.phase === "error") {
    return (
      <main className={styles.pageShell}>
        <section className={styles.statusSurface}>
          <span className={styles.statusBrand}>kanmanabi</span>
          <h1>学習データを読み込めませんでした</h1>
          <p>通信状況を確認して、もう一度お試しください。</p>
          <button type="button" className={styles.retryAction} onClick={() => setReloadKey((key) => key + 1)}>
            <RotateCcw aria-hidden="true" size={18} />
            再読み込み
          </button>
        </section>
      </main>
    );
  }

  const { summary, episodes, conjugation } = state;
  const resumeEpisode = summary.grammar.resume_episode ?? summary.grammar.current_episode;
  const resumeEpisodeNo = formatEpisodeNo(resumeEpisode);
  const episodePreview = getEpisodePreview(episodes, resumeEpisode);
  const resumeLabel = summary.grammar.resume_episode
    ? `${resumeEpisodeNo}からつづける`
    : `${resumeEpisodeNo}をはじめる`;

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <h1>学習</h1>
          <span>TOPIK {summary.level_band}級相当</span>
        </header>
        <p className={styles.intro}>今日は何を学びますか？</p>

        <section className={`${styles.track} ${styles.conjugationTrack}`} aria-labelledby="conjugation-track">
          <div className={styles.trackHeader}>
            <span className={styles.trackIcon}>
              <Repeat2 aria-hidden="true" size={25} strokeWidth={2.2} />
            </span>
            <div>
              <h2 id="conjugation-track">活用トレーニング</h2>
              <p>{conjugation.weakest_rule ? `${conjugation.weakest_rule}を重点練習` : "基本の3つの形から"}</p>
            </div>
            {conjugation.due_count > 0 ? <span className={styles.duePill}>復習 {conjugation.due_count}</span> : null}
          </div>
          <div className={styles.conjugationPreview} aria-hidden="true">
            <span>듣</span><span>들어</span><span>들으</span>
          </div>
          <Link className={styles.primaryAction} to="/learn/conjugation">
            {conjugation.due_count > 0 ? "苦手な形を復習" : "活用を練習する"}
          </Link>
        </section>

        <section className={styles.track} aria-labelledby="grammar-track">
          <div className={styles.trackHeader}>
            <span className={styles.trackIcon}>
              <List aria-hidden="true" size={26} strokeWidth={2.2} />
            </span>
            <div>
              <h2 id="grammar-track">文法コース</h2>
              <p>{resumeEpisodeNo} / {summary.grammar.total_episodes}</p>
            </div>
            <span className={styles.duePill}>復習 {summary.grammar.due_count}</span>
          </div>
          <div className={styles.episodeRail}>
            {episodePreview.map((episode) => {
              const episodeNumber = getEpisodeNumber(episode.ep_no);
              const isDone =
                episode.status === "completed" ||
                summary.grammar.completed_episodes.includes(episodeNumber);

              return (
                <div className={styles.episodeNode} key={episode.ep_no}>
                  <span className={`${styles.nodeMarker} ${isDone ? styles.nodeDone : ""}`}>
                    {isDone ? (
                      <Check aria-hidden="true" size={17} strokeWidth={3} />
                    ) : (
                      String(episodeNumber).padStart(2, "0")
                    )}
                  </span>
                  <span><b>{episode.ep_no}</b> {episode.title}</span>
                </div>
              );
            })}
          </div>
          <Link className={styles.primaryAction} to={`/learn/grammar/${resumeEpisodeNo}`}>
            {resumeLabel}
          </Link>
          <Link className={styles.outlineAction} to="/learn/grammar">
            コースを選ぶ
            <ChevronRight aria-hidden="true" size={18} />
          </Link>
        </section>

        <section className={styles.track} aria-labelledby="vocabulary-track">
          <div className={styles.trackHeader}>
            <span className={styles.trackIcon}>
              <BookOpen aria-hidden="true" size={25} strokeWidth={2.2} />
            </span>
            <div>
              <h2 id="vocabulary-track">単語トラック</h2>
              <p>{summary.level_band}級の単語から学習中</p>
            </div>
            <span className={styles.duePill}>復習 {summary.vocabulary.due_count}</span>
          </div>
          <div className={styles.wordRail}>
            {summary.vocabulary.preview.length > 0 ? (
              summary.vocabulary.preview.map((item) => (
                <div className={styles.wordRow} key={item.id}>
                  <strong lang="ko">{item.word}</strong>
                  <span lang="ja">{item.meaning_ja ?? "意味未登録"}</span>
                  <ChevronRight aria-hidden="true" size={19} />
                </div>
              ))
            ) : (
              <p className={styles.emptyRail}>この級の単語はまだありません。</p>
            )}
          </div>
          <Link className={styles.primaryAction} to="/study/vocabulary">
            単語を学ぶ
          </Link>
          <Link className={styles.quietAction} to="/learn/vocabulary">
            単語帳を見る
            <ChevronRight aria-hidden="true" size={18} />
          </Link>
        </section>
      </div>
      <BottomNav current="learn" />
    </main>
  );
}
