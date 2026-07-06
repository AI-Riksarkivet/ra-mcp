import { test, expect, type Page } from "@playwright/test";
import { pathToFileURL, fileURLToPath } from "node:url";
import fs from "node:fs";
import path from "node:path";

// This project is ESM ("type": "module"), where the CommonJS `__dirname` global
// does not exist — derive it from import.meta.url instead.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Runtime harness for the MCP App UIs.
 *
 * The Apps are postMessage-driven: `new App()` from @modelcontextprotocol/ext-apps does a
 * `ui/initialize` JSON-RPC handshake with its host (window.parent) and gets ALL its data
 * from tool calls — so loaded standalone they render nothing. We therefore load the built
 * dist inside an iframe on a mock-host page (written next to the dist so the iframe is
 * same-origin) whose script answers the ext-apps protocol.
 *
 * The mock host reads two page globals so tests can drive it:
 *   window.__toolResponses  : { [toolName]: CallToolResult }  answers to tools/call
 *   window.__pushToolResult(result)                            host→app ui/notifications/tool-result
 */

const APPS = [
  { name: "viewer", dist: path.resolve(__dirname, "../src/ra_mcp_viewer_mcp/dist") },
  { name: "pdf", dist: path.resolve(__dirname, "../../pdf-mcp/src/ra_mcp_pdf_mcp/dist") },
];

const HOST_HTML = `<!doctype html><html><body style="margin:0">
<iframe id="app" src="mcp-app.html" style="width:900px;height:640px;border:0"></iframe>
<script>
  window.__toolResponses = window.__toolResponses || {};
  const iframe = document.getElementById("app");
  const reply = (id, result) => iframe.contentWindow.postMessage({ jsonrpc: "2.0", id, result }, "*");
  window.__pushToolResult = (result) =>
    iframe.contentWindow.postMessage({ jsonrpc: "2.0", method: "ui/notifications/tool-result", params: result }, "*");
  window.addEventListener("message", (e) => {
    const m = e.data;
    if (!m || m.jsonrpc !== "2.0" || typeof m.id === "undefined" || !m.method) return;
    if (m.method === "ui/initialize") {
      reply(m.id, {
        protocolVersion: m.params.protocolVersion,
        hostInfo: { name: "MockHost", version: "1.0.0" },
        hostCapabilities: {},
        hostContext: { displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"] },
      });
    } else if (m.method === "ui/request-display-mode") {
      reply(m.id, { displayMode: m.params?.mode ?? "inline" });
    } else if (m.method === "tools/call") {
      reply(m.id, window.__toolResponses[m.params?.name] ?? { content: [], structuredContent: {} });
    } else {
      reply(m.id, {}); // ack everything else so nothing hangs
    }
  });
</script></body></html>`;

const appUrl = (dist: string) => pathToFileURL(path.join(dist, "mcp-app.html")).href;
const hostUrl = (dist: string) => pathToFileURL(path.join(dist, "_e2e_host.html")).href;

test.beforeAll(() => {
  for (const app of APPS) {
    const appFile = path.join(app.dist, "mcp-app.html");
    if (!fs.existsSync(appFile)) throw new Error(`${app.name} dist not built (${appFile}) — run \`make build-ui\` first`);
    fs.writeFileSync(path.join(app.dist, "_e2e_host.html"), HOST_HTML);
  }
});

test.afterAll(() => {
  for (const app of APPS) fs.rmSync(path.join(app.dist, "_e2e_host.html"), { force: true });
});

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
