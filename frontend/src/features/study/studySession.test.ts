import i18n from "i18next";
import { describe, expect, it } from "vitest";
import type { Question } from "../../api/types";
import { inputPlaceholderKey, questionLabelKey } from "./studySession";

describe("study question copy", () => {
  it("uses neutral copy for a grammar qtype that the frontend does not know", () => {
    const question: Question = {
      id: 301,
      qtype: "particle_iga",
      prompt: "약사( )",
      choices: ["이", "가"],
      difficulty: 1,
      track: "grammar",
      ep_no: "EP01",
    };

    // 프론트가 모르는 qtype이면 중립 문구 키로 떨어진다
    expect(questionLabelKey(question)).toBe("study.prompt.default");
    expect(inputPlaceholderKey(question)).toBe("study.placeholder.default");
    expect(i18n.t(questionLabelKey(question))).toBe("正しい答えは？");
  });

  it("translates the neutral copy for each locale", async () => {
    const question: Question = {
      id: 302,
      qtype: "nuance_go_seo",
      prompt: "밥을 먹( ) 학교에 가요.",
      choices: ["고", "어서"],
      difficulty: 3,
      track: "grammar",
      ep_no: "EP30",
    };

    await i18n.changeLanguage("ko");
    expect(i18n.t(questionLabelKey(question))).toBe("올바른 답은?");
    await i18n.changeLanguage("ja");
    expect(i18n.t(questionLabelKey(question))).toBe("正しい答えは？");
  });
});
