import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import ja from "./ja.json";
import ko from "./ko.json";

export const LOCALES = ["ja", "ko"] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_LABELS: Record<Locale, string> = {
  ja: "日本語",
  ko: "한국어",
};

export const LOCALE_STORAGE_KEY = "kanmanabi.locale";
/** 언어를 명시적으로 고른 적이 있는지 — 첫 방문 안내를 한 번만 띄우기 위해 쓴다. */
export const LOCALE_CHOSEN_KEY = "kanmanabi.localeChosen";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ja: { translation: ja },
      ko: { translation: ko },
    },
    // 서비스의 주 사용자는 일본인 학습자다. 감지에 실패하거나 지원하지 않는
    // 언어(영어 등)면 일본어로 떨어뜨린다.
    fallbackLng: "ja",
    supportedLngs: LOCALES,
    nonExplicitSupportedLngs: true,   // ko-KR → ko 로 인식
    detection: {
      // 저장된 선택이 최우선. 없으면 브라우저 언어를 본다.
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LOCALE_STORAGE_KEY,
      caches: ["localStorage"],
    },
    interpolation: { escapeValue: false },   // React가 이미 이스케이프한다
  });

function syncDocumentLanguage() {
  if (typeof document === "undefined") return;

  const locale = LOCALES.includes(i18n.resolvedLanguage as Locale)
    ? (i18n.resolvedLanguage as Locale)
    : "ja";
  document.documentElement.lang = locale;
  document.title = i18n.t("meta.title");
  document.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute(
    "content",
    i18n.t("meta.description"),
  );
}

syncDocumentLanguage();
i18n.on("languageChanged", syncDocumentLanguage);

export default i18n;
