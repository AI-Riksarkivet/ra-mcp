import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// This project is ESM ("type": "module"), where the CommonJS `__dirname` global
// does not exist — derive it from import.meta.url instead.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const APPS = [
  { name: "viewer", dist: path.resolve(__dirname, "../src/ra_mcp_viewer_mcp/dist") },
  { name: "pdf", dist: path.resolve(__dirname, "../../pdf-mcp/src/ra_mcp_pdf_mcp/dist") },
];

// Mock MCP host page: iframes the built app and answers the ext-apps postMessage
// protocol (ui/initialize handshake, tools/call, display-mode) so the App mounts.
export const HOST_HTML = `<!doctype html><html><body style="margin:0">
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

export const appUrl = (dist: string) => pathToFileURL(path.join(dist, "mcp-app.html")).href;
export const hostUrl = (dist: string) => pathToFileURL(path.join(dist, "_e2e_host.html")).href;

// Write/remove the mock-host file next to each built app. These run ONCE per
// test run via Playwright globalSetup/globalTeardown — never per-worker — so a
// worker's teardown can't delete a file another parallel worker still needs.
export function writeHostFiles(): void {
  for (const app of APPS) {
    const appFile = path.join(app.dist, "mcp-app.html");
    if (!fs.existsSync(appFile)) throw new Error(`${app.name} dist not built (${appFile}) — run \`make build-ui\` first`);
    fs.writeFileSync(path.join(app.dist, "_e2e_host.html"), HOST_HTML);
  }
}

export function removeHostFiles(): void {
  for (const app of APPS) fs.rmSync(path.join(app.dist, "_e2e_host.html"), { force: true });
}
