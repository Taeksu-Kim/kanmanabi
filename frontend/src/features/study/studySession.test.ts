import { describe, expect, it } from "vitest";
import type { Question } from "../../api/types";
import { getInputPlaceholder, getQuestionLabel } from "./studySession";

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

    expect(getQuestionLabel(question)).toBe("正しい答えは？");
    expect(getInputPlaceholder(question)).toBe("答えを入力");
  });
});
