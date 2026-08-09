# Study mobile flow — v2

Status: approved for the first POC study-loop implementation.

## Surfaces

- [`study-mobile-question-v2.png`](./study-mobile-question-v2.png) — active,
  unanswered dual-input question.
- [`study-mobile-correct-v2.png`](./study-mobile-correct-v2.png) — the same
  question immediately after a correct answer.
- Mascot reference: [`mascot-character-sheet-v3.png`](./mascot-character-sheet-v3.png).

Both concepts use a 390×844 target proportion; generated source size is 853×1844.

## Locked visible copy for review

- `kanmanabi`
- `今日の復習 12`
- `3 / 12`
- `★ 2`
- `韓国語では？`
- `みせ【店】`
- `가게`, `가격`, `밥`, `주인`
- `または`
- `韓国語を入力`
- `答えを確認`
- correct state: `正解！`, `みせ【店】 = 가게`, `次へ`

## Question-screen generation prompt

Create a complete high-fidelity 390×844 mobile study-question screen for
kanmanabi, a POC Korean-learning web app for beginner Japanese learners. It should
feel psychologically close, friendly, adult, and worth opening daily while clearly
remaining focused study. Use a compact brand/review header, slim progress bar,
question label and difficulty, one large prompt, four tactile one-column choices,
an understated `または` separator, text input, and full-width answer action. Keep
everything visible without scrolling and omit the mascot before submission.

Use background `#F7FAF8`, surface `#FFFFFF`, ink `#19352A`, leaf green `#2F8F68`,
strong green `#207653`, mint `#E9F7EF`, border `#DCE8E1`, and a tiny reward-yellow
`#F4C95D` progress marker. Use modern Japanese/Korean rounded sans typography,
14–16px corners, at least 44px touch targets, and a subtle 2–3px bottom edge to
make choices and the main action feel tappable. Keep UI text and controls
code-native. Avoid cream, bright lime, blue-primary styling, exam sheets, fintech
forms, thin-outline-only buttons, nested cards, illustration, mascot, fake metrics,
bottom navigation, gradients, glow, and extra copy.

## Correct-state edit prompt

Use the question concept as the exact UI edit target and mascot v3 as the identity
reference. Preserve the shell, header, progress, prompt, typography, palette, and
component geometry. Mark `가게` correct with mint fill, strong green edge, and a
check icon; de-emphasize the other answers. Replace the separator/input/action
region with an anchored pale-mint feedback panel containing `正解！`,
`みせ【店】 = 가게`, the joyful mascot at roughly 100–140 CSS pixels, and a
full-width `次へ` action. Keep text primary and use only a few tiny yellow/mint
accents. Suggest a short upward panel slide and small mascot settle motion, with a
reduced-motion fallback. Avoid a full celebration page, mascot dominance, XP,
coins, hearts, fake rewards, speech bubbles, gradients, and extra copy.

## Review notes

- The green tactile controls fix the formal exam/fintech feeling of v1.
- The active state keeps the mascot out of the learner's focal path.
- The feedback state introduces the mascot only after commitment and keeps the
  answer text visually primary.
- Before implementation, validate whether the progress star and feedback-panel
  height feel appropriately restrained; then derive the incorrect state in the
  same component family.
