import { useState } from "react";
import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LOCALES, LOCALE_CHOSEN_KEY, LOCALE_LABELS } from "../../i18n";
import type { Locale } from "../../i18n";
import styles from "./LanguageGate.module.css";

/**
 * 첫 방문에 표시 언어를 한 번 확인받는다.
 *
 * 브라우저 언어로 이미 감지해 두었으므로 기본값이 맞는 경우가 많다. 그래도 한 번
 * 명시적으로 보여주는 이유는, 감지가 어긋났을 때(회사 PC의 영어 브라우저 등)
 * 사용자가 바꾸는 방법을 모른 채 헤매지 않게 하기 위함이다.
 * 한 번 고르면 다시 뜨지 않고, 이후에는 화면 우상단 전환 버튼을 쓴다.
 */
export function LanguageGate({ children }: { children: React.ReactNode }) {
  const { t, i18n } = useTranslation();
  const [needsChoice, setNeedsChoice] = useState(
    () => typeof window !== "undefined" && !window.localStorage.getItem(LOCALE_CHOSEN_KEY),
  );

  if (!needsChoice) return <>{children}</>;

  const current = (LOCALES.includes(i18n.resolvedLanguage as Locale)
    ? i18n.resolvedLanguage
    : "ja") as Locale;

  const choose = (next: Locale) => i18n.changeLanguage(next);
  const confirm = () => {
    window.localStorage.setItem(LOCALE_CHOSEN_KEY, "1");
    setNeedsChoice(false);
  };

  return (
    <main className={styles.shell}>
      <section className={styles.card} aria-labelledby="language-gate-title">
        <div className={styles.mark} aria-hidden="true">
          <Languages size={26} strokeWidth={2.2} />
        </div>
        <span className={styles.brand}>kanmanabi</span>
        <h1 id="language-gate-title">{t("language.firstVisitTitle")}</h1>
        <p>{t("language.firstVisitBody")}</p>

        <div className={styles.options} role="radiogroup" aria-labelledby="language-gate-title">
          {LOCALES.map((code) => (
            <button
              key={code}
              type="button"
              role="radio"
              aria-checked={code === current}
              className={code === current ? styles.selected : styles.option}
              onClick={() => choose(code)}
            >
              {LOCALE_LABELS[code]}
            </button>
          ))}
        </div>

        <button type="button" className={styles.confirm} onClick={confirm}>
          {t("language.confirm")}
        </button>
      </section>
    </main>
  );
}
