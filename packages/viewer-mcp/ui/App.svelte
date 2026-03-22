<script lang="ts">
import { onMount } from "svelte";
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";

import DocumentContainer from "./components/DocumentContainer.svelte";
import type { ViewerData } from "./lib/types";
import { HIGHLIGHT_DEFAULTS } from "./lib/constants";

const CARD_HEIGHT = 300;
const VIEWER_HEIGHT = 550;

let app = $state<App | null>(null);
let hostContext = $state<McpUiHostContext | undefined>();
let viewerData = $state.raw<ViewerData | null>(null);
let error = $state<string | null>(null);
let isStreaming = $state(false);
let streamingMessage = $state("");
let isFullscreen = $derived(hostContext?.displayMode === "fullscreen");
let canFullscreen = $derived(hostContext?.availableDisplayModes?.includes("fullscreen") ?? false);
let hasData = $derived(viewerData && viewerData.pageUrls.length > 0);
let isCardState = $derived((!hasData && !isStreaming) || !!error || !app);

// Tracked separately from hostContext to avoid feedback loops in the sizing effect
let containerDims = $state<Record<string, number> | undefined>();
let lastSentHeight = 0;
let lastSeenVersion = 0;

function urlsChanged(newImageUrls: string[]): boolean {
  if (!viewerData) return true;
  if (viewerData.pageUrls.length !== newImageUrls.length) return true;
  return viewerData.pageUrls.some((p, i) => p.image !== newImageUrls[i]);
}

/** Apply server state from ontoolresult or poll. Skips unchanged versions. */
function applyViewerState(sc: Record<string, unknown>) {
  const imageUrls = sc.image_urls as string[] | undefined;
  const textLayerUrls = sc.text_layer_urls as string[] | undefined;
  const highlightTerm = (sc.highlight_term as string) ?? "";
  const version = (sc.version as number) ?? 0;

  if (!imageUrls || !textLayerUrls || imageUrls.length === 0 || imageUrls.length !== textLayerUrls.length) {
    return;
  }

  if (version > 0 && version <= lastSeenVersion) return;
  lastSeenVersion = version;

  if (!urlsChanged(imageUrls)) {
    if (viewerData && viewerData.highlightTerm !== highlightTerm) {
      viewerData = { ...viewerData, highlightTerm, highlightTermColor: HIGHLIGHT_DEFAULTS.color };
    }
    return;
  }

  viewerData = {
    pageUrls: imageUrls.map((image, i) => ({ image, textLayer: textLayerUrls[i] })),
    pageMetadata: Array.from({ length: imageUrls.length }, () => ""),
    highlightTerm,
    highlightTermColor: HIGHLIGHT_DEFAULTS.color,
  };
}

$effect(() => {
  if (hostContext?.theme) applyDocumentTheme(hostContext.theme);
  if (hostContext?.styles?.variables) applyHostStyleVariables(hostContext.styles.variables);
  if (hostContext?.styles?.css?.fonts) applyHostFonts(hostContext.styles.css.fonts);
});

$effect(() => {
  if (!app) return;

  if (isFullscreen) {
    document.documentElement.style.height = "100vh";
    return;
  }

  const desired = (isCardState && !isStreaming) ? CARD_HEIGHT : VIEWER_HEIGHT;

  if (containerDims && "height" in containerDims) {
    document.documentElement.style.height = "100vh";
    return;
  }

  const maxH = containerDims?.maxHeight;
  const targetHeight = maxH ? Math.min(desired, maxH) : desired;
  if (targetHeight === lastSentHeight) return;

  document.documentElement.style.height = "";
  const timerId = setTimeout(() => {
    lastSentHeight = targetHeight;
    app?.sendSizeChanged({ height: targetHeight });
  }, 50);
  return () => clearTimeout(timerId);
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
    { name: "Document Viewer", version: "1.0.0" },
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
    const refCode = args?.reference_code as string ?? "";
    const pages = args?.pages as string ?? "";
    streamingMessage = refCode ? `Loading ${refCode} pages ${pages}...` : "Loading document...";
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
    if (params.containerDimensions !== undefined) {
      containerDims = params.containerDimensions as Record<string, number> | undefined;
    }
  };

  await instance.connect();
  app = instance;
  hostContext = instance.getHostContext();
  containerDims = hostContext?.containerDimensions as Record<string, number> | undefined;
  instance.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});

  let pollId: ReturnType<typeof setInterval> | null = null;

  function startPolling() {
    if (pollId) return;
    pollId = setInterval(async () => {
      try {
        const result = await instance.callServerTool({ name: "get_viewer_state", arguments: {} });
        if (result.isError) return;
        const sc = (result as any).structuredContent as Record<string, unknown> | undefined;
        if (sc) applyViewerState(sc);
      } catch { /* poll failure is non-fatal */ }
    }, 2000);
  }

  return () => {
    if (pollId) clearInterval(pollId);
  };
});
</script>

<svelte:document onkeydown={handleKeydown} />

<main
  class="main"
  class:card-state={isCardState}
  class:fullscreen={isFullscreen}
  style:padding-top={hostContext?.safeAreaInsets?.top ? `${hostContext.safeAreaInsets.top}px` : undefined}
  style:padding-right={hostContext?.safeAreaInsets?.right ? `${hostContext.safeAreaInsets.right}px` : undefined}
  style:padding-bottom={hostContext?.safeAreaInsets?.bottom ? `${hostContext.safeAreaInsets.bottom}px` : undefined}
  style:padding-left={hostContext?.safeAreaInsets?.left ? `${hostContext.safeAreaInsets.left}px` : undefined}
>
  {#if !app}
    <div class="loading">Connecting...</div>
  {:else if isStreaming && !viewerData}
    <div class="skeleton">
      <div class="skeleton-strip">
        {#each Array(4) as _, i (i)}
          <div class="skeleton-thumb"></div>
        {/each}
      </div>
      <div class="skeleton-viewer">
        <div class="skeleton-shimmer"></div>
        {#if streamingMessage}
          <span class="skeleton-message">{streamingMessage}</span>
        {/if}
      </div>
    </div>
  {:else if viewerData && hasData && !error}
    <DocumentContainer
      app={app}
      data={viewerData}
      {canFullscreen}
      {isFullscreen}
      onToggleFullscreen={toggleFullscreen}
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
  position: relative;
  width: 100%;
  height: 100%;
  padding: var(--spacing-sm, 0.5rem);
  display: flex;
  flex-direction: column;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  border-radius: var(--border-radius-lg, 10px);
  border: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  overflow: hidden;
}

.main.fullscreen {
  border-radius: 0;
  border: none;
}

.main.card-state {
  justify-content: center;
  align-items: center;
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
.skeleton-strip {
  width: 120px;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs, 0.25rem);
  padding: var(--spacing-xs, 0.25rem);
  background: var(--color-background-secondary, #f5f5f5);
  border-right: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  border-radius: var(--border-radius-lg, 10px) 0 0 var(--border-radius-lg, 10px);
}
.skeleton-thumb {
  width: 100px;
  height: 120px;
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
