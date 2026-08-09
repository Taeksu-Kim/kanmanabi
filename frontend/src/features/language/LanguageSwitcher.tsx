import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LOCALES, LOCALE_CHOSEN_KEY, LOCALE_LABELS } from "../../i18n";
import type { Locale } from "../../i18n";
import styles from "./LanguageSwitcher.module.css";

interface LanguageSwitcherProps {
  /** floating: 화면 우상단 고정 / inline: 흐름 안에 배치 */
  variant?: "floating" | "inline";
}

/** 언어 전환. 어느 화면에서도 같은 위치에 있어야 찾기 쉬우므로 기본은 고정 배치다. */
export function LanguageSwitcher({ variant = "floating" }: LanguageSwitcherProps) {
  const { t, i18n } = useTranslation();
  const current = (LOCALES.includes(i18n.resolvedLanguage as Locale)
    ? i18n.resolvedLanguage
    : "ja") as Locale;

  const change = (next: Locale) => {
    i18n.changeLanguage(next);
    // 한 번이라도 직접 고르면 첫 방문 안내를 다시 띄우지 않는다.
    window.localStorage.setItem(LOCALE_CHOSEN_KEY, "1");
  };

  return (
    <div
      className={variant === "floating" ? styles.floating : styles.inline}
      role="group"
      aria-label={t("language.label")}
    >
      <Languages aria-hidden="true" size={16} className={styles.icon} />
      {LOCALES.map((code) => (
        <button
          key={code}
          type="button"
          className={code === current ? styles.active : styles.option}
          aria-pressed={code === current}
          aria-label={t("language.switchTo", { name: LOCALE_LABELS[code] })}
          onClick={() => change(code)}
        >
          {LOCALE_LABELS[code]}
        </button>
      ))}
    </div>
  );
}
