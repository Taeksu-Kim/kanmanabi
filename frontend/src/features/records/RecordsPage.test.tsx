import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { learnApi } from "../../api/client";
import { RecordsPage } from "./RecordsPage";

vi.mock("../../api/client", () => ({
  learnApi: { summary: vi.fn() },
}));

const mockedApi = vi.mocked(learnApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.summary.mockResolvedValue({
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
});

describe("RecordsPage", () => {
  it("shows the progress that the backend currently provides", async () => {
    render(
      <MemoryRouter>
        <RecordsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "学習記録" })).toBeInTheDocument();
    expect(screen.getByText("TOPIK 3級相当")).toBeInTheDocument();
    expect(screen.getByText("3 / 43")).toBeInTheDocument();
    expect(screen.getByText("EP17")).toBeInTheDocument();
    expect(screen.getByText("6問")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ホーム" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "学習" })).toHaveAttribute("href", "/learn");
    expect(mockedApi.summary).toHaveBeenCalledWith(expect.any(AbortSignal));
  });
});
