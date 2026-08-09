import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import i18n from "i18next";
import { afterEach, describe, expect, it } from "vitest";
import { LOCALE_CHOSEN_KEY } from "../../i18n";
import { LanguageGate } from "./LanguageGate";
import { LanguageSwitcher } from "./LanguageSwitcher";

afterEach(async () => {
  window.localStorage.clear();
  await i18n.changeLanguage("ja");
});

describe("language switching", () => {
  it("switches the whole UI language and remembers the choice", async () => {
    render(<LanguageSwitcher />);

    await userEvent.click(screen.getByRole("button", { name: /한국어/ }));
    expect(i18n.resolvedLanguage).toBe("ko");
    expect(i18n.t("nav.home")).toBe("홈");
    expect(document.documentElement.lang).toBe("ko");
    expect(document.title).toBe("kanmanabi — 매일 익히는 한국어");

    await userEvent.click(screen.getByRole("button", { name: /日本語/ }));
    expect(i18n.resolvedLanguage).toBe("ja");
    expect(i18n.t("nav.home")).toBe("ホーム");
    expect(document.documentElement.lang).toBe("ja");
  });

  it("marks the active language for assistive tech", async () => {
    render(<LanguageSwitcher />);
    expect(screen.getByRole("button", { name: /日本語/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /한국어/ })).toHaveAttribute("aria-pressed", "false");
  });
});

describe("first visit language gate", () => {
  it("asks once, then gets out of the way", async () => {
    const { unmount } = render(
      <LanguageGate>
        <p>app</p>
      </LanguageGate>,
    );

    // 처음에는 앱 대신 언어 확인 화면이 보인다
    expect(screen.queryByText("app")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /この言語ではじめる|이 언어로 시작하기/ }));
    expect(screen.getByText("app")).toBeInTheDocument();
    unmount();

    // 한 번 고르면 다시 묻지 않는다
    expect(window.localStorage.getItem(LOCALE_CHOSEN_KEY)).toBe("1");
    render(
      <LanguageGate>
        <p>app</p>
      </LanguageGate>,
    );
    expect(screen.getByText("app")).toBeInTheDocument();
  });
});
