import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { conjugationApi } from "../../api/client";
import { ConjugationPage } from "./ConjugationPage";

vi.mock("../../api/client", () => ({
  conjugationApi: { next: vi.fn(), answer: vi.fn() },
}));

const mockedApi = vi.mocked(conjugationApi);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.next.mockResolvedValue({
    mode: "new",
    drill: { id: 7, word: "듣다", meaning_ja: "聞く", rule: { id: "irregular_ㄷ", label_ja: "ㄷ不規則" } },
  });
  mockedApi.answer.mockResolvedValue({
    results: {
      stem: { correct: true, given: "듣", answer: "듣" },
      ae: { correct: false, given: "듣어", answer: "들어" },
      eu: { correct: false, given: "듣으", answer: "들으" },
    },
    rule: { id: "irregular_ㄷ", label_ja: "ㄷ不規則", explanation_ja: "母音の前ではㄷがㄹに変わります。" },
    contrast: "듣고 / 들어요 / 들으면",
    added_to_review: true,
  });
});

describe("ConjugationPage", () => {
  it("submits three forms and shows per-form correction feedback", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><ConjugationPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "듣다" })).toBeInTheDocument();
    const inputs = screen.getAllByRole("textbox");
    await user.type(inputs[0], "듣");
    await user.type(inputs[1], "듣어");
    await user.type(inputs[2], "듣으");
    await user.click(screen.getByRole("button", { name: "答えを確認" }));

    await waitFor(() => expect(mockedApi.answer).toHaveBeenCalledWith({
      vocab_id: 7, stem: "듣", ae: "듣어", eu: "듣으",
    }));
    expect(screen.getByText("들어")).toBeInTheDocument();
    expect(screen.getByText("들으")).toBeInTheDocument();
    expect(screen.getByText("듣고 / 들어요 / 들으면")).toBeInTheDocument();
    expect(screen.getByText("ㄷ不規則を復習に追加しました")).toBeInTheDocument();
  });
});
