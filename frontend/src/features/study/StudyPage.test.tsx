import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MotionConfig } from "motion/react";
import type { AnswerResponse, NextResponse } from "../../api/types";
import { studyApi } from "../../api/client";
import { StudyPage } from "./StudyPage";

vi.mock("../../api/client", () => ({
  studyApi: {
    next: vi.fn(),
    answer: vi.fn(),
    due: vi.fn(),
  },
}));

const firstQuestion: NextResponse = {
  mode: "review",
  question: {
    id: 203,
    qtype: "ja_to_word",
    prompt: "みせ【店】",
    choices: ["가게", "가격", "밥", "주인"],
    difficulty: 2,
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
  },
};

const correctResult: AnswerResponse = {
  correct: true,
  correct_answer: "가게",
  explanation: null,
  next_due: "2026-08-10T00:00:00+00:00",
};

const mockedApi = vi.mocked(studyApi);

function renderStudyPage() {
  return render(
    <MotionConfig reducedMotion="always">
      <StudyPage />
    </MotionConfig>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.next.mockResolvedValue(firstQuestion);
  mockedApi.due.mockResolvedValue({ due_count: 12 });
  mockedApi.answer.mockResolvedValue(correctResult);
});

describe("StudyPage API flow", () => {
  it("loads the question and due count from the API", async () => {
    renderStudyPage();

    expect(await screen.findByText("みせ【店】")).toBeInTheDocument();
    expect(screen.getByText("今日の復習 12")).toBeInTheDocument();
    expect(mockedApi.next).toHaveBeenCalledWith(1, expect.any(AbortSignal));
    expect(mockedApi.due).toHaveBeenCalledWith(expect.any(AbortSignal));
  });

  it("submits a selected answer to the API and shows server feedback", async () => {
    const user = userEvent.setup();
    renderStudyPage();

    await user.click(await screen.findByRole("button", { name: "가게" }));
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    expect(mockedApi.answer).toHaveBeenCalledWith({ question_id: 203, answer: "가게" });
    expect(await screen.findByRole("heading", { name: "正解！" })).toBeInTheDocument();
    expect(screen.getByText("가게", { selector: "strong" })).toBeInTheDocument();
  });

  it("shows the correct answer returned by the server after a wrong typed response", async () => {
    const user = userEvent.setup();
    mockedApi.answer.mockResolvedValue({ ...correctResult, correct: false });
    renderStudyPage();

    await user.type(await screen.findByPlaceholderText("韓国語を入力"), "가걔");
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    expect(mockedApi.answer).toHaveBeenCalledWith({ question_id: 203, answer: "가걔" });
    expect(await screen.findByRole("heading", { name: "あと一歩！" })).toBeInTheDocument();
    expect(screen.getByText("가게", { selector: "strong" })).toBeInTheDocument();
  });

  it("requests and renders the next question", async () => {
    const user = userEvent.setup();
    mockedApi.next.mockResolvedValueOnce(firstQuestion).mockResolvedValueOnce(secondQuestion);
    renderStudyPage();

    await user.click(await screen.findByRole("button", { name: "가게" }));
    await user.click(screen.getByRole("button", { name: "答えを確認" }));
    await user.click(await screen.findByRole("button", { name: "次へ" }));

    expect(await screen.findByText("ごはん")).toBeInTheDocument();
    expect(mockedApi.next).toHaveBeenLastCalledWith();
    expect(screen.getByLabelText("2 / 12")).toBeInTheDocument();
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
