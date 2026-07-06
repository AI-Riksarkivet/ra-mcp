import { test, expect, type Page } from "@playwright/test";
import { APPS, appUrl, hostUrl } from "./hosts";

/**
 * Runtime harness for the MCP App UIs.
 *
 * The Apps are postMessage-driven: `new App()` from @modelcontextprotocol/ext-apps does a
 * `ui/initialize` JSON-RPC handshake with its host (window.parent) and gets ALL its data
 * from tool calls — so loaded standalone they render nothing. We therefore load the built
 * dist inside an iframe on a mock-host page (written next to the dist so the iframe is
 * same-origin) whose script answers the ext-apps protocol. The mock host and its files live
 * in hosts.ts; the files are created once per run via globalSetup (see playwright.config.ts)
 * so parallel workers never race on them.
 *
 * The mock host reads two page globals so tests can drive it:
 *   window.__toolResponses  : { [toolName]: CallToolResult }  answers to tools/call
 *   window.__pushToolResult(result)                            host→app ui/notifications/tool-result
 */

function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

for (const app of APPS) {
  test.describe(app.name, () => {
    test("bundle loads and mounts without JS errors", async ({ page }) => {
      const errors = collectErrors(page);
      await page.goto(appUrl(app.dist), { waitUntil: "load" });
      await expect(page.locator("#app main")).toBeVisible();
      expect(errors, errors.join("\n")).toEqual([]);
    });

    test("without a host, surfaces a connection error (not an infinite spinner)", async ({ page }) => {
      await page.goto(appUrl(app.dist));
      // The connect() handshake fails with no host; the fix shows an error state rather than
      // hanging on 'Connecting...'.
      await expect(page.locator(".error-state")).toContainText(/connect/i, { timeout: 4000 });
    });

    test("connects through the mock host and renders without errors", async ({ page }, testInfo) => {
      const errors = collectErrors(page);
      await page.goto(hostUrl(app.dist), { waitUntil: "load" });
      const frame = page.frameLocator("#app");
      // Connected: the error state must NOT be present.
      await expect(frame.locator(".error-state")).toHaveCount(0, { timeout: 4000 });
      await expect(frame.locator("main")).toBeVisible();
      expect(errors, errors.join("\n")).toEqual([]);
      await page.screenshot({ path: testInfo.outputPath(`${app.name}-connected.png`) });
    });
  });
}
