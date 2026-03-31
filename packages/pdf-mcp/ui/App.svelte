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
import PdfGallery from "./components/PdfGallery.svelte";
import type { PdfViewerData, GalleryItem } from "./lib/types";
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
let galleryItems = $state<GalleryItem[]>([]);
let galleryLoading = $state(false);
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

  const proxyPath = (sc.proxy_path as string) ?? "";

  viewerData = {
    viewId: scViewId,
    url,
    title,
    sourceUrl,
    currentPage: scCurrentPage,
    totalPages: 0,
    proxyPath,
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

// Load PDF when viewerData URL changes via chunked tool calls.
$effect(() => {
  const url = viewerData?.url;
  if (!url || !app) return;

  // Reset PDF state for new URL
  pdfDocument = null;
  totalPages = 0;
  currentPage = viewerData?.currentPage ?? 1;
  streamingMessage = "Loading PDF...";

  let cancelled = false;

  async function loadViaToolChunks(): Promise<Uint8Array> {
    const chunks: Uint8Array[] = [];
    let offset = 0;

    while (true) {
      if (cancelled) throw new Error("cancelled");

      const result = await app!.callServerTool({
        name: "read_pdf_bytes",
        arguments: { url: url!, offset },
      });

      if (result.isError) {
        const msg = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Failed";
        throw new Error(msg);
      }

      const sc = (result as any).structuredContent as Record<string, unknown>;
      if (!sc?.bytes) throw new Error("Invalid response from read_pdf_bytes");

      const chunkBytes = base64ToUint8Array(sc.bytes as string);
      chunks.push(chunkBytes);
      const totalBytes = (sc.totalBytes as number) ?? 0;
      offset += (sc.byteCount as number) ?? chunkBytes.length;

      if (totalBytes > 0) {
        streamingMessage = `Loading PDF... ${Math.round((offset / totalBytes) * 100)}%`;
      }

      if (!(sc.hasMore as boolean)) break;
    }

    const fullLength = chunks.reduce((sum, c) => sum + c.length, 0);
    const full = new Uint8Array(fullLength);
    let pos = 0;
    for (const chunk of chunks) {
      full.set(chunk, pos);
      pos += chunk.length;
    }
    return full;
  }

  async function loadPdf() {
    try {
      // Load via chunked tool calls (CSP-safe — works in MCP App iframe)
      const pdfBytes = await loadViaToolChunks();
      if (cancelled) return;

      streamingMessage = "Rendering...";
      const doc = await loadPdfFromBytes(pdfBytes);
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

async function handleGallerySelect(item: GalleryItem) {
  if (!app) return;
  isStreaming = true;
  error = null;
  streamingMessage = `Loading "${item.title}"...`;
  try {
    const result = await app.callServerTool({
      name: "display_pdf",
      arguments: { url: item.url, title: item.title },
    });
    if (result.isError) {
      error = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Failed";
    } else {
      const sc = (result as any).structuredContent as Record<string, unknown> | undefined;
      if (sc) {
        lastSeenVersion = 0;
        applyViewerState(sc);
      }
    }
  } catch (err: any) {
    error = `Failed to load PDF: ${err.message ?? err}`;
  }
  isStreaming = false;
}

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

  // Fetch gallery items for the initial view
  galleryLoading = true;
  try {
    const galleryResult = await instance.callServerTool({
      name: "list_pdfs",
      arguments: {},
    });
    const gsc = (galleryResult as any).structuredContent;
    if (gsc?.items) galleryItems = gsc.items;
  } catch { /* gallery fetch failure is non-fatal */ }
  galleryLoading = false;

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
    <div class="loading">
      <div class="spinner"></div>
      <span>Connecting...</span>
    </div>
  {:else if (isStreaming || (hasData && !pdfDocument)) && !error}
    <div class="pdf-loading">
      <div class="pdf-loading-icon">
        <svg width="48" height="56" viewBox="0 0 48 56" fill="none">
          <rect x="2" y="2" width="44" height="52" rx="4" stroke="var(--color-border-primary)" stroke-width="2" fill="var(--color-background-secondary)"/>
          <path d="M12 18h24M12 26h24M12 34h16" stroke="var(--color-border-primary)" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
          <text x="24" y="48" text-anchor="middle" font-size="10" font-weight="700" fill="var(--color-accent)">PDF</text>
        </svg>
      </div>
      <div class="pdf-loading-progress">
        <div class="spinner"></div>
        <span class="pdf-loading-message">{streamingMessage || "Loading PDF..."}</span>
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
      <button class="back-btn" onclick={() => { error = null; viewerData = null; pdfDocument = null; }}>Back to library</button>
    </div>
  {:else}
    <PdfGallery
      items={galleryItems}
      loading={galleryLoading}
      onSelect={handleGallerySelect}
    />
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 0.5rem;
  font-size: var(--font-text-sm-size);
  color: var(--color-text-secondary);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border-primary);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 1.5rem;
}

.pdf-loading-icon {
  opacity: 0.6;
}

.pdf-loading-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pdf-loading-message {
  font-size: var(--font-text-sm-size);
  color: var(--color-text-secondary);
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

.back-btn {
  margin-top: var(--spacing-md);
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-md);
  background: var(--color-background-primary);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: var(--font-text-sm-size);
}

.back-btn:hover {
  background: var(--color-background-secondary);
}
</style>
