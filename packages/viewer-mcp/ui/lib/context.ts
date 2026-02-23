/**
 * Model context updates — sends page/selection info to the MCP host.
 */
import type { App } from "@modelcontextprotocol/ext-apps";
import type { TextLine } from "./types";

export interface ContextState {
  app: App;
  pageIndex: number;
  totalPages: number;
  pageMetadata: string;
  getTextLines: () => TextLine[];
}

let timer: ReturnType<typeof setTimeout> | null = null;
let lastSentContext = "";

export function scheduleContextUpdate(state: ContextState, selectedLine?: TextLine) {
  if (timer) clearTimeout(timer);
  const delay = selectedLine ? 0 : 500;
  timer = setTimeout(() => sendContextUpdate(state, selectedLine), delay);
}

async function sendContextUpdate(state: ContextState, selectedLine?: TextLine) {
  const { app, pageIndex, totalPages, pageMetadata } = state;
  if (!app) return;
  const caps = app.getHostCapabilities();
  if (!caps?.updateModelContext) return;

  const page = pageIndex + 1;
  const lines = state.getTextLines();
  const fullText = lines.map(l => `[${l.id}] ${l.transcription}`).join("\n");

  const parts = [`Document viewer: page ${page}/${totalPages} (page_index=${pageIndex})`];
  if (pageMetadata) parts.push(`Page metadata: ${pageMetadata}`);
  if (selectedLine) parts.push(`User selected text (${selectedLine.id}): "${selectedLine.transcription}"`);
  parts.push(fullText ? `Page transcription (line IDs for highlight-region tool):\n${fullText}` : "(no transcribed text on this page)");

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

/** Reset dedup state (e.g. when the component unmounts / remounts) */
export function resetContextState() {
  if (timer) clearTimeout(timer);
  timer = null;
  lastSentContext = "";
}
