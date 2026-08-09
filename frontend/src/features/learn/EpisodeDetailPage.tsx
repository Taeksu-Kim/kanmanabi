import { useEffect, useState } from "react";
import { ArrowLeft, Check, CirclePlay, FileText, PencilLine, RotateCcw } from "lucide-react";
import { Link, useParams } from "react-router";
import { learnApi } from "../../api/client";
import type { EpisodeStep, EpisodeSummary } from "../../api/types";
import { useTranslation } from "react-i18next";
import styles from "./EpisodeDetailPage.module.css";

type PagePhase = "loading" | "ready" | "error" | "not_found";

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function EpisodeDetailPage() {
  const { t } = useTranslation();
  const { epNo } = useParams();
  const [episode, setEpisode] = useState<EpisodeSummary | null>(null);
  const [phase, setPhase] = useState<PagePhase>("loading");
  const [updating, setUpdating] = useState<EpisodeStep | null>(null);
  // 번역 키를 담는다 — 렌더 시점에 번역해야 언어를 바꿔도 메시지가 따라 바뀐다.
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
      setOperationError("episode.saveFailed");
    } finally {
      setUpdating(null);
    }
  }

  if (phase === "loading") {
    return <StatusPage message={t("episode.loading")} />;
  }

  if (phase === "error") {
    return (
      <StatusPage
        title={t("episode.loadFailed")}
        message={t("common.retryHint")}
        onRetry={() => {
          setPhase("loading");
          setReloadKey((key) => key + 1);
        }}
      />
    );
  }

  if (phase === "not_found" || !episode) {
    return <StatusPage title={t("episode.notFound")} message={t("episode.notFoundHint")} />;
  }

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <Link className={styles.backAction} to="/learn/grammar" aria-label={t("episode.backToCourse")}>
            <ArrowLeft aria-hidden="true" size={22} />
          </Link>
          <span>{episode.ep_no}</span>
        </header>

        <section className={styles.intro}>
          <h1>{episode.title}</h1>
          <p>{episode.summary ?? t("episode.defaultSummary")}</p>
        </section>

        <ol className={styles.stepPath} aria-label={t("episode.stepsAria")}>
          <li className={episode.steps.video ? styles.stepDone : ""}>
            <StepMarker number={1} done={episode.steps.video} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <CirclePlay aria-hidden="true" size={21} />
                <h2>{t("episode.videoTitle")}</h2>
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
                    activeLabel={t("episode.videoDone")}
                    doneLabel={t("episode.videoDoneLabel")}
                    onClick={() => void toggleStep("video")}
                  />
                </>
              ) : (
                <p className={styles.unavailable}>{t("episode.videoUnavailable")}</p>
              )}
            </div>
          </li>

          <li className={episode.steps.point ? styles.stepDone : ""}>
            <StepMarker number={2} done={episode.steps.point} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <FileText aria-hidden="true" size={21} />
                <h2>{t("episode.pointTitle")}</h2>
              </div>
              <p>{episode.summary ?? t("episode.pointSummary")}</p>
              <StepButton
                done={episode.steps.point}
                pending={updating === "point"}
                activeLabel={t("episode.pointDone")}
                doneLabel={t("episode.pointDoneLabel")}
                onClick={() => void toggleStep("point")}
              />
            </div>
          </li>

          <li className={episode.steps.practice ? styles.stepDone : ""}>
            <StepMarker number={3} done={episode.steps.practice} />
            <div className={styles.stepContent}>
              <div className={styles.stepHeading}>
                <PencilLine aria-hidden="true" size={21} />
                <h2>{t("episode.practiceTitle")}</h2>
              </div>
              <p>{t("episode.practiceHint")}</p>
              <Link className={styles.practiceAction} to={`/study/grammar/${episode.ep_no}`}>
                {episode.steps.practice ? t("episode.practiceAgain") : t("episode.practiceStart")}
              </Link>
            </div>
          </li>
        </ol>

        {operationError && <p className={styles.operationError} role="alert">{t(operationError)}</p>}
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
  const { t } = useTranslation();
  return (
    <main className={styles.pageShell}>
      <section className={styles.statusSurface} role={title ? undefined : "status"}>
        {title && <h1>{title}</h1>}
        <p>{message}</p>
        {onRetry && (
          <button type="button" onClick={onRetry}>
            <RotateCcw aria-hidden="true" size={18} />
            {t("common.reload")}
          </button>
        )}
      </section>
    </main>
  );
}
