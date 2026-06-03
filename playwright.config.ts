import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "powershell -ExecutionPolicy Bypass -Command \"Push-Location backend; .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002; Pop-Location\"",
      url: "http://localhost:8002/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command:
        "powershell -ExecutionPolicy Bypass -Command \"$env:NEXT_PUBLIC_API_URL='http://localhost:8002'; pnpm.cmd --filter @rankkit/web dev --hostname localhost --port 3000\"",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
    },
  ],
});
