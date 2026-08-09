import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { conjugationApi, learnApi } from "../../api/client";
import { LearningHubPage } from "./LearningHubPage";

vi.mock("../../api/client", () => ({
  learnApi: {
    summary: vi.fn(),
    episodes: vi.fn(),
  },
  conjugationApi: {
    summary: vi.fn(),
  },
}));

const mockedApi = vi.mocked(learnApi);
const mockedConjugationApi = vi.mocked(conjugationApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.summary.mockResolvedValue({
    level_band: 3,
    vocabulary: {
      preview: [{ id: 91, word: "호텔", meaning_ja: "ホテル" }],
      due_count: 4,
    },
    grammar: {
      current_episode: 17,
      resume_episode: 17,
      total_episodes: 43,
      completed_episodes: [16],
      due_count: 2,
    },
  });
  mockedApi.episodes.mockResolvedValue([
    {
      ep_no: "EP16",
      title: "過去の連体形",
      order_index: 16,
      youtube_id: null,
      summary: null,
      steps: { video: true, point: true, practice: true },
      status: "completed",
    },
    {
      ep_no: "EP17",
      title: "推測と意志",
      order_index: 17,
      youtube_id: null,
      summary: null,
      steps: { video: false, point: true, practice: false },
      status: "in_progress",
    },
  ]);
  mockedConjugationApi.summary.mockResolvedValue({ due_count: 3, weakest_rule: "ㄷ不規則" });
});

describe("LearningHubPage", () => {
  it("renders all three tracks from the backend summary", async () => {
    render(
      <MemoryRouter>
        <LearningHubPage />
      </MemoryRouter>,
    );

    const vocabularyHeading = await screen.findByRole("heading", { name: "単語トラック" });
    const grammarHeading = screen.getByRole("heading", { name: "文法コース" });
    expect(screen.getByRole("heading", { name: "活用トレーニング" })).toBeInTheDocument();
    expect(screen.getByText("ㄷ不規則を重点練習")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "苦手な形を復習" })).toHaveAttribute(
      "href",
      "/learn/conjugation",
    );
    expect(
      grammarHeading.compareDocumentPosition(vocabularyHeading) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText("TOPIK 3級相当")).toBeInTheDocument();
    expect(screen.getByText("호텔")).toBeInTheDocument();
    expect(screen.getByText("EP17 / 43")).toBeInTheDocument();
    expect(screen.getByText("過去の連体形")).toBeInTheDocument();
    expect(screen.getByText("推測と意志")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "単語を学ぶ" })).toHaveAttribute(
      "href",
      "/study/vocabulary",
    );
    expect(screen.getByRole("link", { name: "EP17からつづける" })).toHaveAttribute(
      "href",
      "/learn/grammar/EP17",
    );
    expect(screen.getByRole("link", { name: "コースを選ぶ" })).toHaveAttribute(
      "href",
      "/learn/grammar",
    );
    expect(screen.getByRole("link", { name: "ホーム" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "記録" })).toHaveAttribute("href", "/records");
    expect(mockedApi.summary).toHaveBeenCalledWith(expect.any(AbortSignal));
    expect(mockedApi.episodes).toHaveBeenCalledWith(expect.any(AbortSignal));
  });

  it("shows a retry action when the hub data fails", async () => {
    mockedApi.summary.mockRejectedValueOnce(new Error("offline"));

    render(
      <MemoryRouter>
        <LearningHubPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "学習データを読み込めませんでした" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "再読み込み" })).toBeInTheDocument();
  });
});
