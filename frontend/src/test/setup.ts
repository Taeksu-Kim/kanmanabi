// i18n을 먼저 초기화한다. 하지 않으면 컴포넌트가 번역 키를 그대로 렌더한다.
// jsdom의 navigator.language는 보통 en-US라 fallbackLng(ja)가 적용된다.
import "../i18n";

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
