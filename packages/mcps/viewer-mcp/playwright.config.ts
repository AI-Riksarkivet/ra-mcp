import { defineConfig, devices } from "@playwright/test";

// Runtime smoke/render harness for the MCP App UIs. Loads the built dist/mcp-app.html in
// headless chromium under a mock MCP host (see e2e/apps.spec.ts) — the only way to exercise
// the bundle end-to-end, since the Apps are postMessage-driven and render nothing standalone.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  // Write/remove the shared mock-host files once for the whole run (not per
  // worker), so parallel workers can't race on them (see e2e/hosts.ts).
  globalSetup: "./e2e/global-setup.ts",
  globalTeardown: "./e2e/global-teardown.ts",
  use: { ...devices["Desktop Chrome"] },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
