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

// A full first-page render — the path the smoke tests above don't reach: the real
// image-load $effect in DocumentViewer + CanvasController.setImage. Deliver a one-page view
// (as view_document would) plus a load_page response carrying a decodable image, then assert
// the scan actually paints and the loading spinner is not left stuck. (This is positive
// coverage of the render pipeline; it does NOT reproduce the reported first-image race, which
// is timing-dependent and does not trigger headless — the controller-ordering fix in
// DocumentViewer closes that race, but a headless test can't force it.)
test("viewer renders the first page image without leaving the spinner stuck", async ({ page }) => {
  const viewerDist = APPS.find((a) => a.name === "viewer")!.dist;
  // 1x1 red PNG — decodes almost instantly, maximising the controller-vs-decode race.
  const RED_PNG =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

  await page.addInitScript((img) => {
    (window as unknown as { __toolResponses: Record<string, unknown> }).__toolResponses = {
      load_page: {
        content: [],
        structuredContent: { page: { index: 0, imageDataUrl: img, textLayer: { textLines: [], pageWidth: 100, pageHeight: 100 } } },
      },
    };
  }, RED_PNG);

  await page.goto(hostUrl(viewerDist), { waitUntil: "load" });
  const frame = page.frameLocator("#app");
  await expect(frame.locator("main")).toBeVisible();

  // Deliver the initial one-page view exactly as view_document's tool result would.
  await page.evaluate(() => {
    (window as unknown as { __pushToolResult: (r: unknown) => void }).__pushToolResult({
      isError: false,
      content: [],
      structuredContent: {
        view_id: "e2e-first-image",
        image_urls: ["https://example.test/p1.jpg"],
        text_layer_urls: [""],
        page_numbers: [1],
        bildvisning_urls: [""],
        document_info: "",
        highlight_term: "",
        reference_code: "SE/RA/TEST/1",
        version: 1,
        go_to_page: -1,
        request_fullscreen: false,
      },
    });
  });

  await expect(frame.locator("canvas")).toBeVisible({ timeout: 5000 });
  await expect(frame.locator(".canvas-spinner")).toHaveCount(0, { timeout: 5000 }); // not stuck loading
  await expect(frame.locator(".canvas-status--error")).toHaveCount(0);

  // Definitive proof the scan actually painted: the canvas has non-transparent pixels.
  const painted = await frame.locator("canvas").evaluate((el: HTMLCanvasElement) => {
    const ctx = el.getContext("2d");
    if (!ctx || !el.width || !el.height) return false;
    const { data } = ctx.getImageData(0, 0, el.width, el.height);
    for (let i = 3; i < data.length; i += 4) if (data[i] !== 0) return true; // any pixel with alpha > 0
    return false;
  });
  expect(painted, "canvas should have painted the page image").toBe(true);
});
