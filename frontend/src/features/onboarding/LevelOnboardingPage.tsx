import { useState } from "react";
import { ArrowRight, Check } from "lucide-react";
import { useNavigate } from "react-router";
import { profileApi } from "../../api/client";
import type { LevelBand } from "../../api/types";
import { useTranslation } from "react-i18next";
import styles from "./LevelOnboardingPage.module.css";

interface LevelOption {
  level: LevelBand;
  /** 학습 대상인 한국어 예문은 언어와 무관하게 고정. 나머지 설명은 i18n 사전에 있다. */
  exampleKo: string;
}

const levels: LevelOption[] = [
  {
    level: 1,
    exampleKo: "저는 유키예요. 일본에서 왔어요. 커피 한 잔 주세요.",
  },
  {
    level: 2,
    exampleKo: "주말에 친구와 영화를 보려고 했는데 표가 없었어요. 그래서 근처에서 밥을 먹었어요.",
  },
  {
    level: 3,
    exampleKo: "한국 드라마를 자막 없이 보고 싶어서 한국어 공부를 시작했어요. 처음에는 발음이 어려웠지만 요즘은 짧은 대화도 조금씩 들려요.",
  },
  {
    level: 4,
    exampleKo: "재택근무는 이동 시간을 아낄 수 있다는 장점이 있지만 동료와 소통하기 어렵다는 단점도 있어요. 그래서 중요한 회의는 직접 만나는 편이 좋다고 생각해요.",
  },
  {
    level: 5,
    exampleKo: "청년 인구가 줄어드는 현상은 일자리 부족만으로 설명하기 어렵습니다. 주거비와 교육 환경 같은 요인도 함께 고려해야 실효성 있는 대책을 세울 수 있습니다.",
  },
  {
    level: 6,
    exampleKo: "취지 자체에는 공감합니다. 다만 그 전제가 모든 상황에 그대로 적용된다고 보기는 어렵고, 자칫 예외적인 경우를 배제하는 결과로 이어질 수 있다는 점도 고려해야 합니다.",
  },
];

export function LevelOnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<LevelBand | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function saveLevel() {
    if (selected === null || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await profileApi.update({ level_band: selected });
      navigate("/learn", { replace: true });
    } catch {
      setError("onboarding.saveFailed");
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.pageShell}>
      <section className={styles.surface} aria-labelledby="level-title">
        <span className={styles.step}>{t("onboarding.step")}</span>
        <h1 id="level-title">{t("onboarding.title")}</h1>
        <p className={styles.intro}>{t("onboarding.intro")}</p>

        <fieldset className={styles.levelList}>
          <legend className={styles.srOnly}>{t("onboarding.legend")}</legend>
          {levels.map((item) => (
            <label key={item.level} className={selected === item.level ? styles.levelSelected : ""}>
              <input
                type="radio"
                name="level"
                value={item.level}
                aria-label={`${t("onboarding.submit", { level: item.level })} ${t(`onboarding.levels.${item.level}.label`)}`}
                checked={selected === item.level}
                onChange={() => setSelected(item.level)}
              />
              <span className={styles.levelNumber}>{item.level}</span>
              <span className={styles.levelCopy}>
                <b>{t("onboarding.levelTitle", { level: item.level })}</b>
                <small>{t(`onboarding.levels.${item.level}.label`)}</small>
                <span>{t(`onboarding.levels.${item.level}.description`)}</span>
                <span className={styles.topics}>
                  <span>{t(`onboarding.levels.${item.level}.topics.0`)}</span>
                  <span>{t(`onboarding.levels.${item.level}.topics.1`)}</span>
                </span>
              </span>
              <span className={styles.check}>{selected === item.level && <Check aria-hidden="true" size={17} />}</span>
              <span className={styles.levelDetail}>
                <span className={styles.detailLabel}>{t("onboarding.detailLabel")}</span>
                <b lang="ko">{item.exampleKo}</b>
                <span>{t(`onboarding.levels.${item.level}.example`)}</span>
                <span className={styles.conversation}><b>{t("onboarding.conversationLabel")}</b>{t(`onboarding.levels.${item.level}.conversation`)}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <div className={styles.actionDock}>
          {error && <p className={styles.error} role="alert">{t(error)}</p>}
          <button
            type="button"
            className={styles.primaryAction}
            disabled={selected === null || submitting}
            onClick={() => void saveLevel()}
          >
            {submitting ? t("onboarding.saving") : selected === null ? t("onboarding.selectPrompt") : t("onboarding.submit", { level: selected })}
            {selected !== null && !submitting && <ArrowRight aria-hidden="true" size={19} />}
          </button>
        </div>
      </section>
    </main>
  );
}
