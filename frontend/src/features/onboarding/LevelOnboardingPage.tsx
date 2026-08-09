import { useState } from "react";
import { ArrowRight, Check } from "lucide-react";
import { useNavigate } from "react-router";
import { profileApi } from "../../api/client";
import type { LevelBand } from "../../api/types";
import styles from "./LevelOnboardingPage.module.css";

interface LevelOption {
  level: LevelBand;
  label: string;
  description: string;
  topics: [string, string];
  exampleKo: string;
  exampleJa: string;
  conversation: string;
}

const levels: LevelOption[] = [
  {
    level: 1,
    label: "初級・基礎",
    description: "自分のことや、ほしいものを一文ずつ伝えられる",
    topics: ["自分は誰か", "何をくださいと言うか"],
    exampleKo: "저는 유키예요. 일본에서 왔어요. 커피 한 잔 주세요.",
    exampleJa: "私はユキです。日本から来ました。コーヒーを一杯ください。",
    conversation: "相手がゆっくり話し、繰り返しや身振りで助けてくれれば、短いやり取りができます。",
  },
  {
    level: 2,
    label: "初級",
    description: "身近な日常について、短い文をつないで伝えられる",
    topics: ["週末に何をしたか", "明日の予定"],
    exampleKo: "주말에 친구와 영화를 보려고 했는데 표가 없었어요. 그래서 근처에서 밥을 먹었어요.",
    exampleJa: "週末に友だちと映画を見ようとしましたが、チケットがありませんでした。それで近くでご飯を食べました。",
    conversation: "慣れた話題なら会話できます。予想外の質問では、聞き返したり表現を探したりする時間が必要です。",
  },
  {
    level: 3,
    label: "中級",
    description: "経験や考えを、理由や変化と一緒に説明できる",
    topics: ["韓国旅行で困ったこと", "今の仕事を選んだ理由"],
    exampleKo: "한국 드라마를 자막 없이 보고 싶어서 한국어 공부를 시작했어요. 처음에는 발음이 어려웠지만 요즘은 짧은 대화도 조금씩 들려요.",
    exampleJa: "韓国ドラマを字幕なしで見たくて、韓国語の勉強を始めました。最初は発音が難しかったですが、最近は短い会話も少しずつ聞き取れます。",
    conversation: "相手が話す速さを調整し、少し待ってくれれば、日常会話を続けられます。",
  },
  {
    level: 4,
    label: "中上級",
    description: "身近な社会的話題について、比較しながら意見や解決案を伝えられる",
    topics: ["在宅勤務の長所と短所", "日韓の職場文化の違い"],
    exampleKo: "재택근무는 이동 시간을 아낄 수 있다는 장점이 있지만 동료와 소통하기 어렵다는 단점도 있어요. 그래서 중요한 회의는 직접 만나는 편이 좋다고 생각해요.",
    exampleJa: "在宅勤務には移動時間を節約できる長所がありますが、同僚と意思疎通しにくい短所もあります。そのため、大切な会議は直接会うほうがよいと思います。",
    conversation: "相手が慣用表現や話す速さを少し調整すれば、大きな不便なく会話できます。",
  },
  {
    level: 5,
    label: "上級",
    description: "仕事・学業・社会問題について、論点を整理して詳しく説明できる",
    topics: ["プロジェクトの改善策", "少子化の原因と影響"],
    exampleKo: "청년 인구가 줄어드는 현상은 일자리 부족만으로 설명하기 어렵습니다. 주거비와 교육 환경 같은 요인도 함께 고려해야 실효성 있는 대책을 세울 수 있습니다.",
    exampleJa: "若年人口の減少は、雇用不足だけでは説明できません。住居費や教育環境などの要因も併せて考慮してこそ、実効性のある対策を立てられます。",
    conversation: "自然で円滑に意思疎通でき、未知の専門語や慣用語が出たときだけ説明が必要です。",
  },
  {
    level: 6,
    label: "熟達",
    description: "専門的・抽象的な話題でも、前提や含み、細かなニュアンスまで調整して話せる",
    topics: ["利害が対立する提案の調整", "政策の前提への反論"],
    exampleKo: "취지 자체에는 공감합니다. 다만 그 전제가 모든 상황에 그대로 적용된다고 보기는 어렵고, 자칫 예외적인 경우를 배제하는 결과로 이어질 수 있다는 점도 고려해야 합니다.",
    exampleJa: "趣旨そのものには共感します。ただし、その前提がすべての状況に当てはまるとは言い難く、例外的なケースを排除する結果になり得る点も考慮すべきです。",
    conversation: "相手が外国人だと意識して、語彙・速さ・文構造を特別に調整しなくても会話できます。",
  },
];

export function LevelOnboardingPage() {
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
      setError("レベルを保存できませんでした。もう一度お試しください。");
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.pageShell}>
      <section className={styles.surface} aria-labelledby="level-title">
        <span className={styles.step}>はじめの設定 · 1 / 1</span>
        <h1 id="level-title">今の韓国語に近いものは？</h1>
        <p className={styles.intro}>資格の有無ではなく、今できる会話を目安に選んでください。あとから変更できます。</p>

        <fieldset className={styles.levelList}>
          <legend className={styles.srOnly}>韓国語レベル</legend>
          {levels.map((item) => (
            <label key={item.level} className={selected === item.level ? styles.levelSelected : ""}>
              <input
                type="radio"
                name="level"
                value={item.level}
                aria-label={`TOPIK ${item.level}級相当 ${item.label}`}
                checked={selected === item.level}
                onChange={() => setSelected(item.level)}
              />
              <span className={styles.levelNumber}>{item.level}</span>
              <span className={styles.levelCopy}>
                <b>TOPIK {item.level}級相当</b>
                <small>{item.label}</small>
                <span>{item.description}</span>
                <span className={styles.topics}>
                  <span>{item.topics[0]}</span>
                  <span>{item.topics[1]}</span>
                </span>
              </span>
              <span className={styles.check}>{selected === item.level && <Check aria-hidden="true" size={17} />}</span>
              <span className={styles.levelDetail}>
                <span className={styles.detailLabel}>このくらい話せます</span>
                <b lang="ko">{item.exampleKo}</b>
                <span lang="ja">{item.exampleJa}</span>
                <span className={styles.conversation}><b>会話のイメージ</b>{item.conversation}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <div className={styles.actionDock}>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <button
            type="button"
            className={styles.primaryAction}
            disabled={selected === null || submitting}
            onClick={() => void saveLevel()}
          >
            {submitting ? "保存しています…" : selected === null ? "レベルをひとつ選んでください" : `TOPIK ${selected}級相当ではじめる`}
            {selected !== null && !submitting && <ArrowRight aria-hidden="true" size={19} />}
          </button>
        </div>
      </section>
    </main>
  );
}
