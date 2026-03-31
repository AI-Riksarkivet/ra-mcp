/**
 * Model context updates — sends page/selection info to the MCP host.
 */
import type { App } from "@modelcontextprotocol/ext-apps";

export interface PdfContextState {
  app: App;
  title: string;
  currentPage: number;
  totalPages: number;
  pageText?: string;
  searchTerm?: string;
  searchMatchCount?: number;
  globalSearchTotal?: number;
  globalSearchPages?: number;
  selectedText?: string;
}

let timer: ReturnType<typeof setTimeout> | null = null;
let lastSentContext = "";

export function scheduleContextUpdate(state: PdfContextState) {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => sendContextUpdate(state), 500);
}

async function sendContextUpdate(state: PdfContextState) {
  const { app, title, currentPage, totalPages } = state;
  if (!app) return;
  const caps = app.getHostCapabilities();
  if (!caps?.updateModelContext) return;

  const parts = [`PDF viewer | "${title}" | Page ${currentPage}/${totalPages}`];

  if (state.selectedText) {
    parts.push(`Selected text: "${state.selectedText}"`);
  }
  if (state.searchTerm) {
    let searchInfo = `Search: "${state.searchTerm}" (${state.searchMatchCount ?? 0} matches on this page)`;
    if (state.globalSearchTotal) {
      searchInfo += ` | ${state.globalSearchTotal} total matches across ${state.globalSearchPages} pages`;
    }
    parts.push(searchInfo);
  }
  if (state.pageText) {
    parts.push(`\nPage content:\n${state.pageText}`);
  }

  const text = parts.join("\n");
  if (text === lastSentContext) return;
  lastSentContext = text;

  try {
    await app.updateModelContext({
      content: [{ type: "text", text }],
    });
  } catch (e) {
    console.error("[updateModelContext]", e);
  }
}

export function resetContextState() {
  if (timer) clearTimeout(timer);
  timer = null;
  lastSentContext = "";
}
