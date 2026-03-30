<script lang="ts">
import { onMount } from "svelte";
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";

import PdfViewer from "./components/PdfViewer.svelte";
import type { PdfViewerData } from "./lib/types";
import type { PDFDocumentProxy } from "./lib/pdf-engine";
import { loadPdfFromBytes } from "./lib/pdf-engine";
import { base64ToUint8Array } from "./lib/annotations";
import { ZOOM } from "./lib/constants";

let app = $state<App | null>(null);
let hostContext = $state<McpUiHostContext | undefined>();
let viewerData = $state.raw<PdfViewerData | null>(null);
let error = $state<string | null>(null);
let isStreaming = $state(false);
let streamingMessage = $state("");
let pdfDocument = $state.raw<PDFDocumentProxy | null>(null);
let currentPage = $state(1);
let totalPages = $state(0);
let scale = $state(ZOOM.default);
let searchTerm = $state("");

let isFullscreen = $derived(hostContext?.displayMode === "fullscreen");
let canFullscreen = $derived(hostContext?.availableDisplayModes?.includes("fullscreen") ?? false);
let hasData = $derived(viewerData !== null && viewerData.url.length > 0);

let lastSeenVersion = 0;
let viewId = $state("");

function applyViewerState(sc: Record<string, unknown>) {
  const url = (sc.url as string) ?? "";
  const title = (sc.title as string) ?? "Document";
  const sourceUrl = (sc.source_url as string) ?? "";
  const scViewId = (sc.view_id as string) ?? "";
  const version = (sc.version as number) ?? 0;
  const requestFullscreen = (sc.request_fullscreen as boolean) ?? false;
  const scCurrentPage = (sc.current_page as number) ?? 1;

  if (!url) return;

  if (version > 0 && version <= lastSeenVersion) return;
  lastSeenVersion = version;
  if (scViewId) viewId = scViewId;

  if (requestFullscreen && app && !isFullscreen && window.innerWidth >= 640) {
    app.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
  }

  // If same URL, just update navigation state
  if (viewerData && viewerData.url === url) {
    if (scCurrentPage !== viewerData.currentPage) {
      currentPage = scCurrentPage;
      viewerData = { ...viewerData, currentPage: scCurrentPage };
    }
    return;
  }

  viewerData = {
    viewId: scViewId,
    url,
    title,
    sourceUrl,
    currentPage: scCurrentPage,
    totalPages: 0,
  };
}

// Apply host theme
$effect(() => {
  if (hostContext?.theme) applyDocumentTheme(hostContext.theme);
  if (hostContext?.styles?.variables) applyHostStyleVariables(hostContext.styles.variables);
  if (hostContext?.styles?.css?.fonts) applyHostFonts(hostContext.styles.css.fonts);
});

// Send size when not fullscreen
$effect(() => {
  if (!app || isFullscreen) return;
  app.sendSizeChanged({ height: 600 });
});

// Load PDF bytes when viewerData URL changes
$effect(() => {
  const url = viewerData?.url;
  if (!url || !app) return;

  // Reset PDF state for new URL
  pdfDocument = null;
  totalPages = 0;
  currentPage = viewerData?.currentPage ?? 1;
  streamingMessage = `Loading PDF...`;

  let cancelled = false;

  async function loadPdf() {
    const chunks: Uint8Array[] = [];
    let offset = 0;
    let totalBytes = 0;

    try {
      while (true) {
        if (cancelled) return;

        const result = await app!.callServerTool({
          name: "read_pdf_bytes",
          arguments: { url: url!, offset },
        });

        if (result.isError) {
          error = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Failed to load PDF";
          return;
        }

        const sc = (result as any).structuredContent as Record<string, unknown> | undefined;
        if (!sc || !sc.bytes) {
          error = "Invalid response from read_pdf_bytes";
          return;
        }

        const chunkBytes = base64ToUint8Array(sc.bytes as string);
        chunks.push(chunkBytes);
        totalBytes = (sc.totalBytes as number) ?? 0;
        offset += (sc.byteCount as number) ?? chunkBytes.length;

        const progress = totalBytes > 0 ? Math.round((offset / totalBytes) * 100) : 0;
        streamingMessage = `Loading PDF... ${progress}%`;

        if (!(sc.hasMore as boolean)) break;
      }

      if (cancelled) return;

      // Combine chunks
      const fullLength = chunks.reduce((sum, c) => sum + c.length, 0);
      const fullBytes = new Uint8Array(fullLength);
      let pos = 0;
      for (const chunk of chunks) {
        fullBytes.set(chunk, pos);
        pos += chunk.length;
      }

      // Load with pdf.js
      const doc = await loadPdfFromBytes(fullBytes);
      if (cancelled) return;

      pdfDocument = doc;
      totalPages = doc.numPages;
      streamingMessage = "";
    } catch (err: any) {
      if (!cancelled) {
        error = `Failed to load PDF: ${err.message ?? err}`;
      }
    }
  }

  loadPdf();

  return () => {
    cancelled = true;
  };
});

async function toggleFullscreen() {
  if (!app) return;
  try {
    await app.requestDisplayMode({ mode: isFullscreen ? "inline" : "fullscreen" });
  } catch (err) {
    console.error("Failed to change display mode:", err);
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape" && isFullscreen) toggleFullscreen();
}

onMount(async () => {
  const instance = new App(
    { name: "PDF Viewer", version: "1.0.0" },
    { availableDisplayModes: ["inline", "fullscreen"] },
    { autoResize: false },
  );

  instance.ontoolinputpartial = () => {
    if (!viewerData) isStreaming = true;
  };

  instance.ontoolinput = (params) => {
    const args = params.arguments as Record<string, unknown>;
    isStreaming = true;
    error = null;
    const title = (args?.title as string) ?? "";
    streamingMessage = title ? `Loading "${title}"...` : "Loading PDF...";
  };

  instance.ontoolresult = (result) => {
    isStreaming = false;
    if (result.isError) {
      error = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Unknown error";
      return;
    }
    const sc = result.structuredContent as Record<string, unknown> | undefined;
    if (sc) {
      lastSeenVersion = 0;
      applyViewerState(sc);
      startPolling();
    }
  };

  instance.ontoolcancelled = (params) => {
    isStreaming = false;
    error = `Cancelled: ${params.reason}`;
  };

  instance.onerror = (err) => {
    console.error("App error:", err);
    error = err.message;
  };

  instance.onhostcontextchanged = (params) => {
    hostContext = { ...hostContext, ...params };
  };

  instance.onteardown = async () => {
    stopPolling();
    return {};
  };

  await instance.connect();
  app = instance;
  hostContext = instance.getHostContext();
  if (window.innerWidth >= 640) {
    instance.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
  }

  // Polling for server-initiated state changes
  let pollTimer: ReturnType<typeof setTimeout> | null = null;
  let pollInterval = 2000;
  let pollActive = true;
  const POLL_MIN = 2000;
  const POLL_MAX = 10000;

  function schedulePoll() {
    if (!pollActive) return;
    pollTimer = setTimeout(async () => {
      if (!viewId || !pollActive) { schedulePoll(); return; }
      try {
        const prevVersion = lastSeenVersion;
        const result = await instance.callServerTool({
          name: "get_pdf_state",
          arguments: { view_id: viewId },
        });
        if (!result.isError) {
          const sc = (result as any).structuredContent as Record<string, unknown> | undefined;
          if (sc) applyViewerState(sc);
        }
        pollInterval = lastSeenVersion > prevVersion
          ? POLL_MIN
          : Math.min(pollInterval + 1000, POLL_MAX);
      } catch { /* poll failure is non-fatal */ }
      schedulePoll();
    }, pollInterval);
  }

  function startPolling() {
    if (pollTimer) return;
    pollActive = true;
    pollInterval = POLL_MIN;
    schedulePoll();
  }

  function stopPolling() {
    pollActive = false;
    if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
  }

  return () => {
    stopPolling();
  };
});
</script>

<svelte:document onkeydown={handleKeydown} />

<main
  class="main"
  style:padding-top={hostContext?.safeAreaInsets?.top ? `${hostContext.safeAreaInsets.top}px` : undefined}
  style:padding-right={hostContext?.safeAreaInsets?.right ? `${hostContext.safeAreaInsets.right}px` : undefined}
  style:padding-bottom={hostContext?.safeAreaInsets?.bottom ? `${hostContext.safeAreaInsets.bottom}px` : undefined}
  style:padding-left={hostContext?.safeAreaInsets?.left ? `${hostContext.safeAreaInsets.left}px` : undefined}
>
  {#if !app}
    <div class="loading">Connecting...</div>
  {:else if isStreaming && !hasData}
    <div class="skeleton">
      <div class="skeleton-sidebar">
        {#each Array(6) as _, i (i)}
          <div class="skeleton-page-thumb"></div>
        {/each}
      </div>
      <div class="skeleton-viewer">
        <div class="skeleton-shimmer"></div>
        {#if streamingMessage}
          <span class="skeleton-message">{streamingMessage}</span>
        {/if}
      </div>
    </div>
  {:else if hasData && !pdfDocument}
    <div class="skeleton">
      <div class="skeleton-sidebar">
        {#each Array(6) as _, i (i)}
          <div class="skeleton-page-thumb"></div>
        {/each}
      </div>
      <div class="skeleton-viewer">
        <div class="skeleton-shimmer"></div>
        {#if streamingMessage}
          <span class="skeleton-message">{streamingMessage}</span>
        {/if}
      </div>
    </div>
  {:else if hasData && pdfDocument && !error}
    <PdfViewer
      {app}
      {pdfDocument}
      title={viewerData?.title ?? "Document"}
      bind:currentPage
      {totalPages}
      bind:scale
      bind:searchTerm
      {canFullscreen}
      {isFullscreen}
      onToggleFullscreen={toggleFullscreen}
      viewId={viewId}
    />
  {:else if error}
    <div class="error-state">
      <h2>Error</h2>
      <p>{error}</p>
    </div>
  {/if}
</main>

<style>
.main {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  font-size: 1rem;
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
}

.skeleton {
  display: flex;
  flex: 1;
  gap: 0;
  min-height: 400px;
}

.skeleton-sidebar {
  width: 100px;
  min-width: 100px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs, 0.25rem);
  padding: var(--spacing-xs, 0.25rem);
  background: var(--color-background-secondary, #f5f5f5);
  border-right: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  border-radius: var(--border-radius-lg, 10px) 0 0 var(--border-radius-lg, 10px);
}

.skeleton-page-thumb {
  width: 80px;
  height: 100px;
  border-radius: var(--border-radius-md, 6px);
  background: linear-gradient(90deg, var(--color-background-tertiary, #eee) 25%, var(--color-background-secondary, #f5f5f5) 50%, var(--color-background-tertiary, #eee) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  margin: 0 auto;
}

.skeleton-viewer {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md, 0.75rem);
  background: var(--color-background-secondary, #f5f5f5);
  border-radius: 0 var(--border-radius-lg, 10px) var(--border-radius-lg, 10px) 0;
}

.skeleton-message {
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
}

.skeleton-shimmer {
  width: 60%;
  height: 80%;
  border-radius: var(--border-radius-md, 6px);
  background: linear-gradient(90deg, var(--color-background-tertiary, #eee) 25%, var(--color-background-secondary, #f5f5f5) 50%, var(--color-background-tertiary, #eee) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.error-state {
  text-align: center;
  padding: var(--spacing-lg, 1.5rem);
  background: var(--color-background-danger, light-dark(#fef2f2, #2d1515));
  border-radius: var(--border-radius-lg, 10px);
  border: 1px solid var(--color-border-danger, light-dark(#fca5a5, #7f1d1d));
}

.error-state h2 {
  margin: 0 0 var(--spacing-sm, 0.5rem) 0;
  font-size: 1.25rem;
  color: var(--color-text-danger, #b91c1c);
}

.error-state p {
  margin: var(--spacing-sm, 0.5rem) 0;
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
}
</style>
