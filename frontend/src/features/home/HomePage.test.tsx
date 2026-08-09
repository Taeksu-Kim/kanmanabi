import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { learnApi, profileApi } from "../../api/client";
import { HomePage } from "./HomePage";

vi.mock("../../api/client", () => ({
  profileApi: { me: vi.fn() },
  learnApi: { summary: vi.fn(), episodes: vi.fn() },
}));

const mockedProfileApi = vi.mocked(profileApi);
const mockedLearnApi = vi.mocked(learnApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedProfileApi.me.mockResolvedValue({
    id: 7,
    name: "Yuki",
    email: "yuki@example.com",
    picture: null,
    level_band: 3,
  });
  mockedLearnApi.summary.mockResolvedValue({
    level_band: 3,
    vocabulary: { preview: [], due_count: 4 },
    grammar: {
      current_episode: 17,
      resume_episode: 17,
      total_episodes: 43,
      completed_episodes: [1, 2, 3],
      due_count: 2,
    },
  });
  mockedLearnApi.episodes.mockResolvedValue([
    {
      ep_no: "EP17",
      title: "推測と意志",
      order_index: 17,
      youtube_id: "video17",
      summary: "話し手の予想と意志を区別します。",
      steps: { video: true, point: false, practice: false },
      status: "in_progress",
    },
  ]);
});

describe("HomePage", () => {
  it("shows a real home dashboard with review and grammar continuation", async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /Yukiさん/ })).toBeInTheDocument();
    expect(screen.getByText("今日の復習 6問")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /復習をはじめる/ })).toHaveAttribute(
      "href",
      "/review",
    );
    expect(screen.getByText("EP17 · 推測と意志")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "EP17からつづける" })).toHaveAttribute(
      "href",
      "/learn/grammar/EP17",
    );
    expect(screen.getByRole("link", { name: "学習" })).toHaveAttribute("href", "/learn");
    expect(screen.getByRole("link", { name: "記録" })).toHaveAttribute("href", "/records");
    expect(mockedProfileApi.me).toHaveBeenCalledWith(expect.any(AbortSignal));
    expect(mockedLearnApi.summary).toHaveBeenCalledWith(expect.any(AbortSignal));
    expect(mockedLearnApi.episodes).toHaveBeenCalledWith(expect.any(AbortSignal));
  });
});
