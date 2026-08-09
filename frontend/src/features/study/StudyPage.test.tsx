import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MotionConfig } from "motion/react";
import type { AnswerResponse, NextResponse } from "../../api/types";
import { learnApi, studyApi } from "../../api/client";
import { StudyPage } from "./StudyPage";

vi.mock("../../api/client", () => ({
  studyApi: {
    next: vi.fn(),
    answer: vi.fn(),
    due: vi.fn(),
  },
  learnApi: {
    updateEpisodeProgress: vi.fn(),
  },
}));

const firstQuestion: NextResponse = {
  mode: "review",
  question: {
    id: 203,
    qtype: "ja_to_word",
    prompt: "みせ【店】",
    choices: ["가게", "가격", "밥", "주인"],
    difficulty: 3,
    track: "vocabulary",
    ep_no: null,
  },
};

const secondQuestion: NextResponse = {
  mode: "new",
  question: {
    id: 204,
    qtype: "ja_to_word",
    prompt: "ごはん",
    choices: ["물", "밥", "빵", "집"],
    difficulty: 1,
    track: "vocabulary",
    ep_no: null,
  },
};

const grammarQuestion: NextResponse = {
  mode: "new",
  question: {
    id: 301,
    qtype: "particle_iga",
    prompt: "약사( )",
    choices: ["이", "가"],
    difficulty: 1,
    track: "grammar",
    ep_no: "EP01",
  },
};

const correctResult: AnswerResponse = {
  correct: true,
  correct_answer: "가게",
  explanation: null,
  next_due: "2026-08-10T00:00:00+00:00",
};

const mockedApi = vi.mocked(studyApi);
const mockedLearnApi = vi.mocked(learnApi);

function renderStudyPage(track: "vocabulary" | "grammar" = "vocabulary", epNo?: string) {
  return render(
    <MotionConfig reducedMotion="always">
      <StudyPage track={track} epNo={epNo} />
    </MotionConfig>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.next.mockResolvedValue(firstQuestion);
  mockedApi.due.mockResolvedValue({ due_count: 12 });
  mockedApi.answer.mockResolvedValue(correctResult);
  mockedLearnApi.updateEpisodeProgress.mockResolvedValue({
    ep_no: "EP01",
    steps: { video: false, point: false, practice: true },
    status: "in_progress",
  });
});

describe("StudyPage API flow", () => {
  it("loads the question and due count from the API", async () => {
    renderStudyPage();

    expect(await screen.findByText("みせ【店】")).toBeInTheDocument();
    expect(screen.getByText("今日の復習 12")).toBeInTheDocument();
    expect(screen.getByLabelText("難易度 3")).toBeInTheDocument();
    expect(screen.getByText("単語")).toBeInTheDocument();
    expect(mockedApi.next).toHaveBeenCalledWith({
      level: 1,
      track: "vocabulary",
      signal: expect.any(AbortSignal),
    });
    expect(mockedApi.due).toHaveBeenCalledWith(expect.any(AbortSignal));
  });

  it("requests and identifies a grammar-track question", async () => {
    mockedApi.next.mockResolvedValue(grammarQuestion);
    renderStudyPage("grammar", "EP01");

    expect(await screen.findByText("약사( )")).toBeInTheDocument();
    expect(screen.getByText("文法 · EP01")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("答えを入力")).toBeInTheDocument();
    expect(mockedApi.next).toHaveBeenCalledWith({
      level: 1,
      track: "grammar",
      ep_no: "EP01",
      signal: expect.any(AbortSignal),
    });
  });

  it("submits a selected answer to the API and shows server feedback", async () => {
    const user = userEvent.setup();
    renderStudyPage();

    await screen.findByText("みせ【店】");
    expect(screen.queryByRole("button", { name: "가게" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "選択肢を見る" }));
    await user.click(screen.getByRole("button", { name: "가게" }));
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    expect(mockedApi.answer).toHaveBeenCalledWith({
      question_id: 203,
      answer: "가게",
      used_choices: true,
    });
    expect(await screen.findByRole("heading", { name: "正解！" })).toBeInTheDocument();
    expect(screen.getByText("가게", { selector: "strong" })).toBeInTheDocument();
  });

  it("remembers that choices were revealed even after hiding them", async () => {
    const user = userEvent.setup();
    renderStudyPage();

    await screen.findByText("みせ【店】");
    await user.click(screen.getByRole("button", { name: "選択肢を見る" }));
    expect(screen.getByRole("button", { name: "가격" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "選択肢を隠す" }));
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "가격" })).not.toBeInTheDocument();
    });
    await user.type(screen.getByPlaceholderText("韓国語を入力"), "가게");
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    expect(mockedApi.answer).toHaveBeenCalledWith({
      question_id: 203,
      answer: "가게",
      used_choices: true,
    });
  });

  it("shows the correct answer returned by the server after a wrong typed response", async () => {
    const user = userEvent.setup();
    mockedApi.answer.mockResolvedValue({ ...correctResult, correct: false });
    renderStudyPage();

    await user.type(await screen.findByPlaceholderText("韓国語を入力"), "가걔");
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    expect(mockedApi.answer).toHaveBeenCalledWith({
      question_id: 203,
      answer: "가걔",
      used_choices: false,
    });
    expect(await screen.findByRole("heading", { name: "あと一歩！" })).toBeInTheDocument();
    expect(screen.getByText("가게", { selector: "strong" })).toBeInTheDocument();
  });

  it("requests and renders the next question", async () => {
    const user = userEvent.setup();
    mockedApi.next.mockResolvedValueOnce(firstQuestion).mockResolvedValueOnce(secondQuestion);
    renderStudyPage();

    await screen.findByText("みせ【店】");
    await user.click(screen.getByRole("button", { name: "選択肢を見る" }));
    await user.click(screen.getByRole("button", { name: "가게" }));
    await user.click(screen.getByRole("button", { name: "答えを確認" }));
    await user.click(await screen.findByRole("button", { name: "次へ" }));

    expect(await screen.findByText("ごはん")).toBeInTheDocument();
    expect(mockedApi.next).toHaveBeenLastCalledWith({
      level: 1,
      track: "vocabulary",
      ep_no: undefined,
    });
    expect(screen.getByLabelText("2 / 12")).toBeInTheDocument();
  });

  it("marks grammar practice complete when the episode session is finished", async () => {
    const user = userEvent.setup();
    mockedApi.next
      .mockResolvedValueOnce(grammarQuestion)
      .mockResolvedValueOnce({ mode: "done", question: null });
    renderStudyPage("grammar", "EP01");

    await user.type(await screen.findByPlaceholderText("答えを入力"), "이");
    await user.click(screen.getByRole("button", { name: "答えを確認" }));
    await user.click(await screen.findByRole("button", { name: "次へ" }));

    expect(await screen.findByRole("heading", { name: "今日の学習、完了！" })).toBeInTheDocument();
    await waitFor(() => {
      expect(mockedLearnApi.updateEpisodeProgress).toHaveBeenCalledWith("EP01", {
        practice: true,
      });
    });
  });

  it("offers a retry when the initial API load fails", async () => {
    const user = userEvent.setup();
    mockedApi.next.mockRejectedValueOnce(new Error("offline"));
    renderStudyPage();

    expect(await screen.findByRole("heading", { name: "うまく読み込めませんでした" })).toBeInTheDocument();
    mockedApi.next.mockResolvedValueOnce(firstQuestion);
    await user.click(screen.getByRole("button", { name: "再読み込み" }));

    expect(await screen.findByText("みせ【店】")).toBeInTheDocument();
  });
});
