import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { vocabularyApi } from "../../api/client";
import { VocabularyBookPage } from "./VocabularyBookPage";

vi.mock("../../api/client", () => ({
  vocabularyApi: {
    list: vi.fn(),
    favorite: vi.fn(),
  },
}));

const mockedApi = vi.mocked(vocabularyApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.list.mockResolvedValue({
    items: [
      {
        id: 1,
        word: "가게",
        pos: "명사",
        level_band: 1,
        ja: ["みせ【店】", "しょうてん【商店】"],
        hanja: null,
        guide: "가게에 가다",
        status: "learning",
        favorite: false,
      },
    ],
    next_cursor: 3,
  });
  mockedApi.favorite.mockResolvedValue({ vocab_id: 1, favorite: true });
});

describe("VocabularyBookPage", () => {
  it("shows level vocabulary and loads the next cursor", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <VocabularyBookPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "単語帳" })).toBeInTheDocument();
    expect(screen.getByText("가게")).toBeInTheDocument();
    expect(screen.getByText("学習中")).toBeInTheDocument();
    expect(mockedApi.list).toHaveBeenCalledWith({
      level: 1,
      q: "",
      favorite: false,
      cursor: undefined,
      signal: expect.any(AbortSignal),
    });

    mockedApi.list.mockResolvedValueOnce({
      items: [
        {
          id: 4,
          word: "가구",
          pos: "명사",
          level_band: 1,
          ja: ["かぐ【家具】"],
          hanja: "家具",
          guide: null,
          status: "not_started",
          favorite: false,
        },
      ],
      next_cursor: null,
    });
    await user.click(screen.getByRole("button", { name: "さらに見る" }));

    expect(await screen.findByText("가구")).toBeInTheDocument();
    expect(mockedApi.list).toHaveBeenLastCalledWith({
      level: 1,
      q: "",
      favorite: false,
      cursor: 3,
    });
  });

  it("applies level, search, and favorite controls", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <VocabularyBookPage />
      </MemoryRouter>,
    );
    await screen.findByText("가게");

    await user.click(screen.getByRole("button", { name: "3級" }));
    expect(mockedApi.list).toHaveBeenLastCalledWith({
      level: 3,
      q: "",
      favorite: false,
      cursor: undefined,
      signal: expect.any(AbortSignal),
    });

    await user.type(screen.getByRole("searchbox"), "学校");
    await user.click(screen.getByRole("button", { name: "検索" }));
    expect(mockedApi.list).toHaveBeenLastCalledWith({
      level: 3,
      q: "学校",
      favorite: false,
      cursor: undefined,
      signal: expect.any(AbortSignal),
    });

    await user.click(screen.getByRole("button", { name: "가게をお気に入りに追加" }));
    expect(mockedApi.favorite).toHaveBeenCalledWith(1, true);
    expect(screen.getByRole("button", { name: "가게のお気に入りを解除" })).toBeInTheDocument();
  });
});
