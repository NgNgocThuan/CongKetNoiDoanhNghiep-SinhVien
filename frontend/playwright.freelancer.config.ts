import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: process.env.FREELANCER_LIVE_TEST
    ? "freelancer-live.spec.ts"
    : "freelancer.spec.ts",
  workers: 1,
  timeout: 35_000,
  use: {
    baseURL: "http://127.0.0.1:5188",
    ...devices["Desktop Chrome"],
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    trace: "retain-on-failure",
  },
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report/freelancer", open: "never" }],
  ],
  webServer: {
    command: "npm run dev -- --port 5188",
    url: "http://127.0.0.1:5188",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
