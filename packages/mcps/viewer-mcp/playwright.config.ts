import { defineConfig, devices } from "@playwright/test";

// Runtime smoke/render harness for the MCP App UIs. Loads the built dist/mcp-app.html in
// headless chromium under a mock MCP host (see e2e/apps.spec.ts) — the only way to exercise
// the bundle end-to-end, since the Apps are postMessage-driven and render nothing standalone.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  use: { ...devices["Desktop Chrome"] },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
