import { useEffect, useState } from "react";
import { ArrowLeft, Check, CirclePlay, FileText, PencilLine, RotateCcw } from "lucide-react";
import { Link, useParams } from "react-router";
import { learnApi } from "../../api/client";
import type { EpisodeStep, EpisodeSummary } from "../../api/types";
import styles from "./EpisodeDetailPage.module.css";

type PagePhase = "loading" | "ready" | "error" | "not_found";

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function EpisodeDetailPage() {
  const { epNo } = useParams();
  const [episode, setEpisode] = useState<EpisodeSummary | null>(null);
  const [phase, setPhase] = useState<PagePhase>("loading");
  const [updating, setUpdating] = useState<EpisodeStep | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    learnApi
      .episodes(controller.signal)
      .then((episodes) => {
        const selected = episodes.find((item) => item.ep_no === epNo) ?? null;
        setEpisode(selected);
        setPhase(selected ? "ready" : "not_found");
        if (selected) learnApi.openEpisode(selected.ep_no).catch(() => undefined);
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setPhase("error");
      });
    return () => controller.abort();
  }, [epNo, reloadKey]);

  async function toggleStep(step: EpisodeStep) {
    if (!episode || updating) return;
    setUpdating(step);
    setOperationError(null);
    try {
      const progress = await learnApi.updateEpisodeProgress(episode.ep_no, {
        [step]: !episode.steps[step],
      });
      setEpisode((current) =>
        current ? { ...current, steps: progress.steps, status: progress.status } : current,
      );
    } catch {
      setOperationError("進み具合を保存できませんでした。もう一度お試しください。");
    } finally {
      setUpdating(null);
    }
  }

  if (phase === "loading") {
    return <StatusPage message="エピソードを読み込んでいます…" />;
  }

  if (phase === "error") {
    return (
      <StatusPage
        title="エピソードを読み込めませんでした"
        message="通信状況を確認して、もう一度お試しください。"
        onRetry={() => {
          setPhase("loading");
          setReloadKey((key) => key + 1);
        }}
      />
    );
  }

  if (phase === "not_found" || !episode) {
    return <StatusPage title="エピソードが見つかりません" message="コースから別のエピソードを選んでください。" />;
  }

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <Link className={styles.backAction} to="/learn/grammar" aria-label="文法コースに戻る">
            <ArrowLeft aria-hidden="true" size={22} />
          </Link>
          <span>{episode.ep_no}</span>
        </header>

        <section className={styles.intro}>
          <h1>{episode.title}</h1>
          <p>{episode.summary ?? "このエピソードの文法を、3つのステップで学びます。"}</p>
        </section>

        <ol className={styles.stepPath} aria-label="エピソードの学習ステップ">
          <li className={episode.steps.video ? styles.stepDone : ""}>
            <StepMarker number={1} done={episode.steps.video} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <CirclePlay aria-hidden="true" size={21} />
                <h2>動画で学ぶ</h2>
              </div>
              {episode.youtube_id ? (
                <>
                  <div className={styles.videoFrame}>
                    <iframe
                      src={`https://www.youtube-nocookie.com/embed/${episode.youtube_id}`}
                      title={`${episode.ep_no} ${episode.title}`}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                  <StepButton
                    done={episode.steps.video}
                    pending={updating === "video"}
                    activeLabel="動画を見終えた"
                    doneLabel="視聴済み"
                    onClick={() => void toggleStep("video")}
                  />
                </>
              ) : (
                <p className={styles.unavailable}>動画は準備中です</p>
              )}
            </div>
          </li>

          <li className={episode.steps.point ? styles.stepDone : ""}>
            <StepMarker number={2} done={episode.steps.point} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <FileText aria-hidden="true" size={21} />
                <h2>ポイントを読む</h2>
              </div>
              <p>{episode.summary ?? "日本語との違いと、使う場面を確認しましょう。"}</p>
              <StepButton
                done={episode.steps.point}
                pending={updating === "point"}
                activeLabel="ポイントを確認済みにする"
                doneLabel="確認済み"
                onClick={() => void toggleStep("point")}
              />
            </div>
          </li>

          <li className={episode.steps.practice ? styles.stepDone : ""}>
            <StepMarker number={3} done={episode.steps.practice} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <PencilLine aria-hidden="true" size={21} />
                <h2>文法練習</h2>
              </div>
              <p>選択肢に頼らず、習った表現を自分で思い出してみましょう。</p>
              <Link className={styles.practiceAction} to={`/study/grammar/${episode.ep_no}`}>
                {episode.steps.practice ? "もう一度練習する" : "練習をはじめる"}
              </Link>
            </div>
          </li>
        </ol>

        {operationError && <p className={styles.operationError} role="alert">{operationError}</p>}
      </div>
    </main>
  );
}

function StepMarker({ number, done }: { number: number; done: boolean }) {
  return <span className={styles.marker}>{done ? <Check aria-hidden="true" size={18} strokeWidth={3} /> : number}</span>;
}

interface StepButtonProps {
  done: boolean;
  pending: boolean;
  activeLabel: string;
  doneLabel: string;
  onClick: () => void;
}

function StepButton({ done, pending, activeLabel, doneLabel, onClick }: StepButtonProps) {
  return (
    <button type="button" className={styles.stepAction} disabled={pending} onClick={onClick}>
      {pending ? "保存中…" : done ? doneLabel : activeLabel}
    </button>
  );
}

function StatusPage({ title, message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return (
    <main className={styles.pageShell}>
      <section className={styles.statusSurface} role={title ? undefined : "status"}>
        {title && <h1>{title}</h1>}
        <p>{message}</p>
        {onRetry && (
          <button type="button" onClick={onRetry}>
            <RotateCcw aria-hidden="true" size={18} />
            再読み込み
          </button>
        )}
      </section>
    </main>
  );
}
