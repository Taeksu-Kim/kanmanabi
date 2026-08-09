import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";

const dist = new URL("../dist/", import.meta.url).pathname;
const contentTypes: Record<string, string> = {
  ".css": "text/css",
  ".html": "text/html",
  ".js": "text/javascript",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

const question = {
  mode: "review",
  question: {
    id: 203,
    qtype: "ja_to_word",
    prompt: "みせ【店】",
    choices: ["가게", "가격", "밥", "주인"],
    difficulty: 2,
    track: "vocabulary",
    ep_no: null,
  },
};

const grammarQuestion = {
  mode: "new",
  question: {
    id: 301,
    qtype: "particle_iga",
    prompt: "약사( )",
    choices: ["이", "가"],
    difficulty: 1,
    track: "grammar",
    ep_no: "EP01",
  },
};

const learningSummary = {
  level_band: 3,
  vocabulary: {
    preview: [
      { id: 91, word: "호텔", meaning_ja: "ホテル" },
      { id: 92, word: "예약", meaning_ja: "予約" },
    ],
    due_count: 4,
  },
  grammar: {
    current_episode: 17,
    resume_episode: 17,
    total_episodes: 43,
    completed_episodes: [16],
    due_count: 2,
  },
};

const episodes = [
  {
    ep_no: "EP16",
    title: "過去の連体形",
    order_index: 16,
    youtube_id: null,
    summary: "過去の出来事を名詞につなげる",
    steps: { video: true, point: true, practice: true },
    status: "completed",
  },
  {
    ep_no: "EP17",
    title: "推測と意志",
    order_index: 17,
    youtube_id: null,
    summary: "これからの意志や推測を伝える",
    steps: { video: false, point: true, practice: false },
    status: "in_progress",
  },
  {
    ep_no: "EP18",
    title: "理由を伝える",
    order_index: 18,
    youtube_id: null,
    summary: null,
    steps: { video: false, point: false, practice: false },
    status: "not_started",
  },
];

test.beforeEach(async ({ page }) => {
  // 첫 방문 언어 확인 화면을 건너뛴다. 언어 게이트 자체는 별도 테스트에서 확인한다.
  // 첫 방문 언어 확인 화면만 건너뛴다. 언어 자체는 강제하지 않는다 —
  // 여기서 locale까지 고정하면 페이지를 이동할 때마다 되돌아가 전환 테스트가 깨진다.
  // 브라우저 언어(en-US)는 미지원이라 fallbackLng(ja)가 적용된다.
  await page.addInitScript(() => {
    window.localStorage.setItem("kanmanabi.localeChosen", "1");
  });
  await page.route("https://accounts.google.com/gsi/client", async (route) => {
    await route.fulfill({
      contentType: "text/javascript",
      body: `window.google={accounts:{id:{initialize(options){window.__googleCallback=options.callback},renderButton(parent){const button=document.createElement('button');button.textContent='Google でログイン';button.addEventListener('click',()=>window.__googleCallback({credential:'e2e-google-jwt'}));parent.append(button)}}}};`,
    });
  });
  await page.route("http://app.local/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/study/next") {
      if (url.searchParams.get("track") === "grammar") {
        const epNo = url.searchParams.get("ep_no") ?? "EP01";
        return route.fulfill({
          json: {
            ...grammarQuestion,
            question: { ...grammarQuestion.question, ep_no: epNo },
          },
        });
      }
      return route.fulfill({ json: question });
    }
    if (url.pathname === "/api/study/due") return route.fulfill({ json: { due_count: 12 } });
    if (url.pathname === "/api/learn/summary") {
      return route.fulfill({ json: learningSummary });
    }
    if (url.pathname === "/api/conjugation/summary") {
      return route.fulfill({
        json: { due_count: 2, weakest_rule: "ㄷ不規則", weakest_rule_id: "irregular_ㄷ" },
      });
    }
    if (url.pathname === "/api/conjugation/next") {
      return route.fulfill({
        json: {
          mode: "review",
          drill: { id: 77, word: "듣다", meaning_ja: "聞く", rule: { id: "irregular_ㄷ", label_ja: "ㄷ不規則" } },
        },
      });
    }
    if (url.pathname === "/api/conjugation/answer") {
      return route.fulfill({
        json: {
          results: {
            stem: { correct: true, given: "듣", answer: "듣" },
            ae: { correct: false, given: "듣어", answer: "들어" },
            eu: { correct: false, given: "듣으", answer: "들으" },
          },
          rule: { id: "irregular_ㄷ", label_ja: "ㄷ不規則", explanation_ja: "母音の前ではㄷがㄹに変わります。" },
          contrast: "듣고 / 들어요 / 들으면",
          added_to_review: true,
        },
      });
    }
    if (url.pathname === "/api/episodes") return route.fulfill({ json: episodes });
    if (url.pathname === "/api/episodes/EP17/progress") {
      return route.fulfill({
        json: {
          ep_no: "EP17",
          steps: { video: false, point: true, practice: true },
          status: "in_progress",
        },
      });
    }
    if (url.pathname === "/api/auth/google") {
      return route.fulfill({
        json: {
          id: 7,
          name: "Yuki",
          email: "yuki@example.com",
          picture: null,
          level_band: null,
          onboarded: false,
        },
      });
    }
    if (url.pathname === "/api/me" && route.request().method() === "GET") {
      return route.fulfill({
        json: {
          id: 7,
          name: "Yuki",
          email: "yuki@example.com",
          picture: null,
          level_band: 3,
        },
      });
    }
    if (url.pathname === "/api/me" && route.request().method() === "PATCH") {
      return route.fulfill({
        json: {
          id: 7,
          name: "Yuki",
          email: "yuki@example.com",
          picture: null,
          level_band: 2,
        },
      });
    }
    if (url.pathname === "/api/vocab") {
      return route.fulfill({
        json: {
          items: [
            {
              id: 1,
              word: "가게",
              pos: "명사",
              level_band: Number(url.searchParams.get("level") ?? 1),
              ja: ["みせ【店】", "しょうてん【商店】"],
              hanja: null,
              guide: "가게에 가다",
              status: "learning",
              favorite: false,
            },
          ],
          next_cursor: null,
        },
      });
    }
    if (url.pathname === "/api/vocab/1/favorite") {
      return route.fulfill({ json: { vocab_id: 1, favorite: route.request().method() === "PUT" } });
    }
    if (url.pathname === "/api/study/answer") {
      return route.fulfill({
        json: {
          correct: true,
          correct_answer: "가게",
          explanation: null,
          next_due: "2026-08-10T00:00:00+00:00",
        },
      });
    }

    const assetPath = url.pathname.startsWith("/assets/") ? url.pathname.slice(1) : "index.html";
    return route.fulfill({
      body: await readFile(join(dist, assetPath)),
      contentType: contentTypes[extname(assetPath)] ?? "application/octet-stream",
    });
  });
});

test("home, grammar-first learning hub, and records are connected", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /Yukiさん/ })).toBeVisible();
  await expect(page.getByText("今日の復習 6問")).toBeVisible();
  await expect(page.getByRole("link", { name: /復習をはじめる/ })).toHaveAttribute(
    "href",
    "/review",
  );

  await page.getByRole("link", { name: "学習", exact: true }).click();
  await expect(page).toHaveURL("/learn");
  const grammarTop = await page.getByRole("heading", { name: "文法コース" }).evaluate((node) => node.getBoundingClientRect().top);
  const vocabularyTop = await page.getByRole("heading", { name: "単語トラック" }).evaluate((node) => node.getBoundingClientRect().top);
  expect(grammarTop).toBeLessThan(vocabularyTop);

  await page.getByRole("link", { name: "EP17からつづける" }).click();
  await expect(page).toHaveURL("/learn/grammar/EP17");
  await expect(page.getByRole("heading", { name: "推測と意志" })).toBeVisible();
  await page.goto("/learn");

  await page.getByRole("link", { name: "記録", exact: true }).click();
  await expect(page).toHaveURL("/records");
  await expect(page.getByRole("heading", { name: "学習記録" })).toBeVisible();
  await expect(page.getByText("1 / 43")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("learning hub opens typed recall without overlapping optional choices", async ({ page }) => {
  await page.goto("/learn");

  await expect(page.getByRole("heading", { name: "単語トラック" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "文法コース" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);

  await page.getByRole("link", { name: "単語を学ぶ" }).click();
  await expect(page.getByText("みせ【店】", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "가게" })).toHaveCount(0);

  await page.getByRole("button", { name: "選択肢を見る" }).click();
  const choiceBox = await page.getByRole("button", { name: "가격" }).boundingBox();
  const hintBox = await page
    .getByText("しっかり覚えたい時は入力、迷った時は選択肢を表示")
    .boundingBox();

  expect(choiceBox).not.toBeNull();
  expect(hintBox).not.toBeNull();
  expect(choiceBox!.y + choiceBox!.height).toBeLessThanOrEqual(hintBox!.y);

  await page.getByRole("button", { name: "選択肢を隠す" }).click();
  await page.getByRole("textbox").fill("가게");
  const answerRequest = page.waitForRequest("**/api/study/answer");
  await page.getByRole("button", { name: "答えを確認" }).click();
  expect((await answerRequest).postDataJSON()).toMatchObject({
    question_id: 203,
    answer: "가게",
    used_choices: true,
  });
});

test("conjugation track records and corrects three forms on mobile", async ({ page }) => {
  await page.goto("/learn");
  await expect(page.getByRole("heading", { name: "活用トレーニング" })).toBeVisible();
  await page.getByRole("link", { name: "苦手な形を復習" }).click();
  await expect(page).toHaveURL("/learn/conjugation");
  await expect(page.getByRole("heading", { name: "듣다" })).toBeVisible();
  if (process.env.CAPTURE_CONJUGATION) {
    await page.screenshot({ path: "/tmp/conjugation-question.png", fullPage: true });
  }

  const inputs = page.getByRole("textbox");
  await inputs.nth(0).fill("듣");
  await inputs.nth(1).fill("듣어");
  await inputs.nth(2).fill("듣으");
  await page.getByRole("button", { name: "答えを確認" }).click();

  await expect(page.getByText("들어", { exact: true })).toBeVisible();
  await expect(page.getByText("들으", { exact: true })).toBeVisible();
  await expect(page.getByText("ㄷ不規則を復習に追加しました")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  if (process.env.CAPTURE_CONJUGATION) {
    await page.screenshot({ path: "/tmp/conjugation-result.png", fullPage: true });
  }
});

test("conjugation training keeps the same mobile flow in Korean", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("kanmanabi.locale", "ko");
    window.localStorage.setItem("kanmanabi.localeChosen", "1");
  });
  await page.goto("/learn/conjugation");
  await expect(page.getByRole("heading", { name: "활용 훈련" })).toBeVisible();
  await expect(page.getByText("세 가지 형태로 바꿔 보세요")).toBeVisible();
  if (process.env.CAPTURE_CONJUGATION) {
    await page.screenshot({ path: "/tmp/conjugation-question-ko.png", fullPage: true });
  }

  const inputs = page.getByRole("textbox");
  await inputs.nth(0).fill("듣");
  await inputs.nth(1).fill("듣어");
  await inputs.nth(2).fill("듣으");
  await page.getByRole("button", { name: "답 확인하기" }).click();

  await expect(page.getByRole("heading", { name: "ㄷ 불규칙" })).toBeVisible();
  await expect(page.getByText("모음 앞에서 ㄷ이 ㄹ로 바뀝니다.")).toBeVisible();
  await expect(page.getByText("ㄷ 불규칙을(를) 복습에 추가했습니다")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  if (process.env.CAPTURE_CONJUGATION) {
    await page.screenshot({ path: "/tmp/conjugation-result-ko.png", fullPage: true });
  }
});

test("grammar course continues from the selected episode", async ({ page }) => {
  await page.goto("/learn");

  await page.getByRole("link", { name: "コースを選ぶ" }).click();
  await expect(page).toHaveURL("/learn/grammar");
  await expect(page.getByRole("heading", { name: "文法コース" })).toBeVisible();
  await expect(page.getByText("学習中")).toBeVisible();

  await page.getByRole("link", { name: /EP17/ }).click();
  await expect(page).toHaveURL("/learn/grammar/EP17");
  await expect(page.getByRole("heading", { name: "推測と意志" })).toBeVisible();
  await page.getByRole("link", { name: "練習をはじめる" }).click();
  await expect(page).toHaveURL("/study/grammar/EP17");
  await expect(page.getByText("文法 · EP17")).toBeVisible();
});

test("Google login sends a new learner through level onboarding", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "韓国語を、今日から少しずつ。" })).toBeVisible();
  await page.getByRole("button", { name: "Google でログイン" }).click();
  await expect(page).toHaveURL("/onboarding/level");
  await expect(page.getByText("このくらい話せます")).toHaveCount(6);
  await expect(page.getByText(/취지 자체에는 공감합니다/)).toBeVisible();

  await page.getByRole("radio", { name: /TOPIK 2級相当/ }).click();
  await page.getByRole("button", { name: "TOPIK 2級相当ではじめる" }).click();
  await expect(page).toHaveURL("/learn");
  await expect(page.getByRole("heading", { name: "単語トラック" })).toBeVisible();
});

test("vocabulary book filters by level and searches Japanese meanings", async ({ page }) => {
  await page.goto("/learn");

  await page.getByRole("link", { name: "単語帳を見る" }).click();
  await expect(page).toHaveURL("/learn/vocabulary");
  await expect(page.getByRole("heading", { name: "単語帳" })).toBeVisible();
  await expect(page.getByText("学習中")).toBeVisible();

  await page.getByRole("button", { name: "3級" }).click();
  await page.getByRole("searchbox").fill("学校");
  const searchRequest = page.waitForRequest(
    (request) => request.url().includes("/api/vocab?") && request.url().includes("q=%E5%AD%A6%E6%A0%A1"),
  );
  await page.getByRole("button", { name: "検索" }).click();
  const searchUrl = new URL((await searchRequest).url());
  expect(searchUrl.searchParams.get("level")).toBe("3");
  expect(searchUrl.searchParams.get("q")).toBe("学校");

  await page.getByRole("button", { name: "가게をお気に入りに追加" }).click();
  await expect(page.getByRole("button", { name: "가게のお気に入りを解除" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("grammar session identifies its episode and safely renders an unknown qtype", async ({ page }) => {
  await page.goto("/study/grammar");

  await expect(page.getByText("文法 · EP01")).toBeVisible();
  await expect(page.getByRole("heading", { name: "正しい答えは？" })).toBeVisible();
  await expect(page.getByPlaceholder("答えを入力")).toBeVisible();
});

test("first visit asks for a display language before showing the app", async ({ page }) => {
  // addInitScript는 페이지 이동마다 실행되므로, 이 테스트 안에서는 이동하지 않는다.
  await page.addInitScript(() => window.localStorage.removeItem("kanmanabi.localeChosen"));
  await page.goto("/learn");

  await expect(page.getByRole("heading", { name: "表示言語" })).toBeVisible();
  await page.getByRole("radio", { name: "한국어" }).click();
  await page.getByRole("button", { name: "이 언어로 시작하기" }).click();

  // 앱 전체가 한국어로 뜬다
  await expect(page.getByRole("heading", { name: "문법 코스" })).toBeVisible();
  await expect(page.getByRole("link", { name: "홈" })).toBeVisible();
});

test("language switcher is available on every screen and survives reloads", async ({ page }) => {
  await page.goto("/records");
  await expect(page.getByText("学びの現在地")).toBeVisible();

  // 전환 버튼의 aria-label은 현재 UI 언어로 렌더된다(일본어 화면이면 "한국어に切り替える").
  // 언어에 상관없이 잡히도록 언어명으로 부분 매칭한다.
  await page.getByRole("button", { name: /한국어/ }).click();
  await expect(page.getByText("학습 현재 위치")).toBeVisible();
  await expect(page.getByRole("heading", { name: "학습 기록" })).toBeVisible();
  await expect(page.getByText("TOPIK 3급 수준")).toBeVisible();
  await expect(page).toHaveTitle("kanmanabi — 매일 익히는 한국어");
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");

  // 다른 화면으로 이동해도 유지된다
  await page.goto("/learn");
  await expect(page.getByRole("heading", { name: "학습", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "문법 코스" })).toBeVisible();
  await expect(page.getByText("복습 2")).toBeVisible();

  // 새로고침해도 마지막 선택이 남는다
  await page.reload();
  await expect(page.getByRole("heading", { name: "문법 코스" })).toBeVisible();
});
