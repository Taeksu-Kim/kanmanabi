import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { learnApi } from "../../api/client";
import { GrammarCoursePage } from "./GrammarCoursePage";

vi.mock("../../api/client", () => ({
  learnApi: {
    episodes: vi.fn(),
  },
}));

const mockedApi = vi.mocked(learnApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.episodes.mockResolvedValue([
    {
      ep_no: "EP01",
      title: "これ・この",
      order_index: 1,
      youtube_id: null,
      summary: "ものを指す基本表現",
      steps: { video: true, point: true, practice: true },
      status: "completed",
    },
    {
      ep_no: "EP02",
      title: "私・あなた・우리",
      order_index: 2,
      youtube_id: null,
      summary: null,
      steps: { video: false, point: true, practice: false },
      status: "in_progress",
    },
    {
      ep_no: "EP03",
      title: "名前の呼び方",
      order_index: 3,
      youtube_id: null,
      summary: null,
      steps: { video: false, point: false, practice: false },
      status: "not_started",
    },
  ]);
});

describe("GrammarCoursePage", () => {
  it("renders the episode path and links each episode to its grammar session", async () => {
    render(
      <MemoryRouter>
        <GrammarCoursePage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "文法コース" })).toBeInTheDocument();
    expect(screen.getByText("これ・この")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
    expect(screen.getByText("学習中")).toBeInTheDocument();
    expect(screen.getByText("未開始")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /EP02/ })).toHaveAttribute(
      "href",
      "/learn/grammar/EP02",
    );
    expect(mockedApi.episodes).toHaveBeenCalledWith(expect.any(AbortSignal));
  });
});
