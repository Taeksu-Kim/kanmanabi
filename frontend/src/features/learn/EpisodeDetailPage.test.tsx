import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { learnApi } from "../../api/client";
import { EpisodeDetailPage } from "./EpisodeDetailPage";

vi.mock("../../api/client", () => ({
  learnApi: {
    episodes: vi.fn(),
    openEpisode: vi.fn(),
    updateEpisodeProgress: vi.fn(),
  },
}));

const mockedApi = vi.mocked(learnApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.episodes.mockResolvedValue([
    {
      ep_no: "EP17",
      title: "推測と意志",
      order_index: 17,
      youtube_id: null,
      summary: "これからの意志や推測を伝える",
      steps: { video: false, point: false, practice: false },
      status: "not_started",
    },
  ]);
  mockedApi.updateEpisodeProgress.mockResolvedValue({
    ep_no: "EP17",
    steps: { video: false, point: true, practice: false },
    status: "in_progress",
  });
  mockedApi.openEpisode.mockResolvedValue({
    ep_no: "EP17",
    steps: { video: false, point: false, practice: false },
    status: "not_started",
  });
});

describe("EpisodeDetailPage", () => {
  it("shows the three-step path and updates the point step", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/learn/grammar/EP17"]}>
        <Routes>
          <Route path="/learn/grammar/:epNo" element={<EpisodeDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "推測と意志" })).toBeInTheDocument();
    await waitFor(() => expect(mockedApi.openEpisode).toHaveBeenCalledWith("EP17"));
    expect(screen.getByText("動画で学ぶ")).toBeInTheDocument();
    expect(screen.getByText("ポイントを読む")).toBeInTheDocument();
    expect(screen.getByText("文法練習")).toBeInTheDocument();
    expect(screen.getByText("動画は準備中です")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "ポイントを確認済みにする" }));
    expect(mockedApi.updateEpisodeProgress).toHaveBeenCalledWith("EP17", { point: true });
    expect(await screen.findByText("確認済み")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "練習をはじめる" })).toHaveAttribute(
      "href",
      "/study/grammar/EP17",
    );
  });

  it("embeds the episode video when the backend provides a YouTube id", async () => {
    mockedApi.episodes.mockResolvedValueOnce([
      {
        ep_no: "EP17",
        title: "推測と意志",
        order_index: 17,
        youtube_id: "HHK9QpOalcI",
        summary: null,
        steps: { video: false, point: false, practice: false },
        status: "not_started",
      },
    ]);

    render(
      <MemoryRouter initialEntries={["/learn/grammar/EP17"]}>
        <Routes>
          <Route path="/learn/grammar/:epNo" element={<EpisodeDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByTitle("EP17 推測と意志")).toHaveAttribute(
      "src",
      "https://www.youtube-nocookie.com/embed/HHK9QpOalcI",
    );
    expect(screen.getByRole("button", { name: "動画を見終えた" })).toBeInTheDocument();
  });
});
