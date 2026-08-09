import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, Heart, RotateCcw, Search } from "lucide-react";
import { Link } from "react-router";
import { vocabularyApi } from "../../api/client";
import type { LevelBand, VocabularyItem } from "../../api/types";
import { useTranslation } from "react-i18next";
import styles from "./VocabularyBookPage.module.css";

type PagePhase = "loading" | "ready" | "error";

const levels: LevelBand[] = [1, 2, 3, 4, 5, 6];
function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

export function VocabularyBookPage() {
  const { t } = useTranslation();
  const [level, setLevel] = useState<LevelBand>(1);
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [items, setItems] = useState<VocabularyItem[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [phase, setPhase] = useState<PagePhase>("loading");
  const [loadingMore, setLoadingMore] = useState(false);
  // 번역 키를 담는다 — 렌더 시점에 번역해야 언어를 바꿔도 메시지가 따라 바뀐다.
  const [operationError, setOperationError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    vocabularyApi
      .list({ level, q: query, favorite: favoritesOnly, cursor: undefined, signal: controller.signal })
      .then((response) => {
        setItems(response.items);
        setNextCursor(response.next_cursor);
        setPhase("ready");
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setPhase("error");
      });

    return () => controller.abort();
  }, [favoritesOnly, level, query, reloadKey]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextQuery = searchInput.trim();
    setPhase("loading");
    if (nextQuery === query) {
      setReloadKey((key) => key + 1);
    } else {
      setQuery(nextQuery);
    }
  }

  async function loadMore() {
    if (nextCursor === null || loadingMore) return;
    setLoadingMore(true);
    setOperationError(null);
    try {
      const response = await vocabularyApi.list({
        level,
        q: query,
        favorite: favoritesOnly,
        cursor: nextCursor,
      });
      setItems((current) => [...current, ...response.items]);
      setNextCursor(response.next_cursor);
    } catch {
      setOperationError("vocabulary.loadMoreFailed");
    } finally {
      setLoadingMore(false);
    }
  }

  async function toggleFavorite(item: VocabularyItem) {
    const nextFavorite = !item.favorite;
    setOperationError(null);
    try {
      await vocabularyApi.favorite(item.id, nextFavorite);
      setItems((current) =>
        favoritesOnly && !nextFavorite
          ? current.filter((currentItem) => currentItem.id !== item.id)
          : current.map((currentItem) =>
              currentItem.id === item.id
                ? { ...currentItem, favorite: nextFavorite }
                : currentItem,
            ),
      );
    } catch {
      setOperationError("vocabulary.favoriteFailed");
    }
  }

  return (
    <main className={styles.pageShell}>
      <div className={styles.surface}>
        <header className={styles.header}>
          <Link className={styles.backAction} to="/learn" aria-label={t("common.backToLearn")}>
            <ArrowLeft aria-hidden="true" size={22} />
          </Link>
          <div>
            <span className={styles.eyebrow}>VOCABULARY</span>
            <h1>{t("vocabulary.title")}</h1>
          </div>
        </header>

        <section className={styles.controls} aria-label={t("vocabulary.filtersAria")}>
          <div className={styles.levels} aria-label={t("vocabulary.levelsAria")}>
            {levels.map((option) => (
              <button
                key={option}
                type="button"
                className={level === option ? styles.levelCurrent : ""}
                aria-pressed={level === option}
                onClick={() => {
                  if (level !== option) {
                    setPhase("loading");
                    setLevel(option);
                  }
                }}
              >
                {t("common.level", { level: option })}
              </button>
            ))}
          </div>
          <form className={styles.searchForm} role="search" onSubmit={submitSearch}>
            <Search aria-hidden="true" size={19} />
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder={t("vocabulary.searchPlaceholder")}
              aria-label={t("vocabulary.searchAria")}
            />
            <button type="submit">{t("vocabulary.searchButton")}</button>
          </form>
          <button
            type="button"
            className={`${styles.favoriteFilter} ${favoritesOnly ? styles.favoriteFilterCurrent : ""}`}
            aria-pressed={favoritesOnly}
            onClick={() => {
              setPhase("loading");
              setFavoritesOnly((current) => !current);
            }}
          >
            <Heart aria-hidden="true" size={17} fill={favoritesOnly ? "currentColor" : "none"} />
            {t("vocabulary.favoritesOnly")}
          </button>
        </section>

        {phase === "loading" ? (
          <section className={styles.statusSurface} role="status" aria-live="polite">
            <p>{t("vocabulary.loading", { level })}</p>
          </section>
        ) : phase === "error" ? (
          <section className={styles.statusSurface}>
            <h2>{t("vocabulary.loadFailed")}</h2>
            <button
              type="button"
              onClick={() => {
                setPhase("loading");
                setReloadKey((key) => key + 1);
              }}
            >
              <RotateCcw aria-hidden="true" size={18} />
              {t("common.reload")}
            </button>
          </section>
        ) : (
          <section aria-live="polite">
            <div className={styles.resultMeta}>
              <b>{t("common.level", { level })}</b>
              <span>{query ? t("vocabulary.searchResult", { query }) : t("vocabulary.listTitle")}</span>
            </div>
            {items.length === 0 ? (
              <div className={styles.emptyState}>
                <Heart aria-hidden="true" size={24} />
                <p>{favoritesOnly ? t("vocabulary.emptyFavorites") : t("vocabulary.empty")}</p>
              </div>
            ) : (
              <ul className={styles.wordList}>
                {items.map((item) => (
                  <li key={item.id} className={styles.wordItem}>
                    <div className={styles.wordHeading}>
                      <strong lang="ko">{item.word}</strong>
                      {item.hanja && <small>{item.hanja}</small>}
                      <span>{item.pos}</span>
                    </div>
                    <p lang="ja">{item.ja.join(" · ")}</p>
                    {item.guide && <small className={styles.guide} lang="ko">{item.guide}</small>}
                    <span className={`${styles.learningStatus} ${styles[item.status]}`}>
                      {t(`vocabulary.status.${item.status}`)}
                    </span>
                    <button
                      type="button"
                      className={styles.favoriteAction}
                      aria-label={
                        item.favorite
                          ? t("vocabulary.removeFavorite", { word: item.word })
                          : t("vocabulary.addFavorite", { word: item.word })
                      }
                      aria-pressed={item.favorite}
                      onClick={() => void toggleFavorite(item)}
                    >
                      <Heart aria-hidden="true" size={21} fill={item.favorite ? "currentColor" : "none"} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {nextCursor !== null && (
              <button
                type="button"
                className={styles.loadMore}
                disabled={loadingMore}
                onClick={() => void loadMore()}
              >
                {loadingMore ? t("common.loading") : t("vocabulary.loadMore")}
              </button>
            )}
            {operationError && (
              <p className={styles.operationError} role="alert">
                {t(operationError)}
              </p>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
