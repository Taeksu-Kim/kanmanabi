import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { profileApi } from "../../api/client";
import { LevelOnboardingPage } from "./LevelOnboardingPage";

vi.mock("../../api/client", () => ({
  profileApi: { update: vi.fn() },
}));

const mockedApi = vi.mocked(profileApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.update.mockResolvedValue({
    id: 7,
    name: "Yuki",
    email: "yuki@example.com",
    picture: null,
    level_band: 2,
  });
});

describe("LevelOnboardingPage", () => {
  it("shows every level detail at once so the learner only taps to select", () => {
    render(
      <MemoryRouter>
        <LevelOnboardingPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("週末に何をしたか")).toBeInTheDocument();
    expect(screen.getByText("明日の予定")).toBeInTheDocument();
    expect(
      screen.getByText(
        "주말에 친구와 영화를 보려고 했는데 표가 없었어요. 그래서 근처에서 밥을 먹었어요.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "週末に友だちと映画を見ようとしましたが、チケットがありませんでした。それで近くでご飯を食べました。",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/予想外の質問では/)).toBeInTheDocument();
    expect(screen.getByText(/취지 자체에는 공감합니다/)).toBeInTheDocument();
    expect(screen.getAllByText("このくらい話せます")).toHaveLength(6);
  });

  it("saves the selected self-assessed level and enters the learning hub", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/onboarding/level"]}>
        <Routes>
          <Route path="/onboarding/level" element={<LevelOnboardingPage />} />
          <Route path="/learn" element={<h1>学習ハブ</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("radio", { name: /TOPIK 2級相当/ }));
    await user.click(screen.getByRole("button", { name: "TOPIK 2級相当ではじめる" }));

    expect(mockedApi.update).toHaveBeenCalledWith({ level_band: 2 });
    expect(await screen.findByRole("heading", { name: "学習ハブ" })).toBeInTheDocument();
  });
});
