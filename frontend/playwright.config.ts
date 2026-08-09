import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

const configuredBrowser = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
const systemBrowser = "/usr/bin/google-chrome";
const executablePath = configuredBrowser ?? (existsSync(systemBrowser) ? systemBrowser : undefined);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://app.local",
    browserName: "chromium",
    viewport: { width: 390, height: 844 },
    reducedMotion: "no-preference",
    launchOptions: executablePath
      ? { executablePath, args: ["--no-sandbox", "--disable-dev-shm-usage"] }
      : undefined,
  },
});
