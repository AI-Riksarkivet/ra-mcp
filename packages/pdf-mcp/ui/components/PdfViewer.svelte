<script lang="ts">
import { onMount, onDestroy } from "svelte";
import { SvelteMap } from "svelte/reactivity";
import type { App } from "@modelcontextprotocol/ext-apps";
import type { PDFDocumentProxy, PDFPageProxy } from "../lib/pdf-engine";
import type { PdfCommand, TrackedAnnotation } from "../lib/types";
import {
  renderPage,
  buildTextLayer,
  extractPageText,
  searchPageText,
} from "../lib/pdf-engine";
import { scheduleContextUpdate, resetContextState } from "../lib/context";
import { ZOOM } from "../lib/constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  app: App;
  pdfDocument: PDFDocumentProxy;
  title: string;
  currentPage: number;
  totalPages: number;
  scale: number;
  searchTerm: string;
  canFullscreen: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  viewId: string;
}

let {
  app,
  pdfDocument,
  title,
  currentPage = $bindable(),
  totalPages,
  scale = $bindable(),
  searchTerm = $bindable(),
  canFullscreen,
  isFullscreen,
  onToggleFullscreen,
  viewId,
}: Props = $props();

// ---------------------------------------------------------------------------
// Element refs
// ---------------------------------------------------------------------------

let canvasEl = $state<HTMLCanvasElement>(undefined!);
let textLayerEl = $state<HTMLDivElement>(undefined!);
let containerEl = $state<HTMLDivElement>(undefined!);

// ---------------------------------------------------------------------------
// Local state
// ---------------------------------------------------------------------------

let searchOpen = $state(false);
let searchMatchCount = $state(0);
let searchCurrentMatch = $state(0);
let searchRects = $state<DOMRect[]>([]);
let annotationMap = new SvelteMap<string, TrackedAnnotation>();
let showAnnotationPanel = $state(false);
let loading = $state(false);

// Writable derived: tracks currentPage, can be overridden by user input
let pageInputValue = $derived(currentPage);

// Highlight layer dimensions (set during page render)
let highlightWidth = $state(0);
let highlightHeight = $state(0);

// ---------------------------------------------------------------------------
// Derived state
// ---------------------------------------------------------------------------

let zoomLabel = $derived(Math.round(scale * 100));
let hasAnnotations = $derived(annotationMap.size > 0);
let searchMatchLabel = $derived(
  searchMatchCount > 0
    ? `${searchCurrentMatch + 1}/${searchMatchCount}`
    : "No matches",
);

// ---------------------------------------------------------------------------
// Page rendering
// ---------------------------------------------------------------------------

let currentPageProxy = $state<PDFPageProxy | null>(null);
let renderGeneration = 0;

$effect(() => {
  const page = currentPage;
  const s = scale;

  if (!pdfDocument || !canvasEl || !textLayerEl) return;

  loading = true;
  const gen = ++renderGeneration;

  (async () => {
    try {
      const pageProxy = await pdfDocument.getPage(page);
      if (gen !== renderGeneration) return;

      currentPageProxy = pageProxy;

      await renderPage(pageProxy, canvasEl, s);
      if (gen !== renderGeneration) return;

      await buildTextLayer(pageProxy, textLayerEl, s);
      if (gen !== renderGeneration) return;

      // Size the highlight layer to match the viewport
      const viewport = pageProxy.getViewport({ scale: s });
      highlightWidth = viewport.width;
      highlightHeight = viewport.height;

      // Extract text and update context
      const pageText = await extractPageText(pageProxy);
      if (gen !== renderGeneration) return;

      scheduleContextUpdate({
        app,
        title,
        currentPage: page,
        totalPages,
        pageText,
        searchTerm: searchTerm || undefined,
        searchMatchCount: searchMatchCount || undefined,
      });
    } catch (err) {
      if (gen === renderGeneration) {
        console.error("[PdfViewer] render error:", err);
      }
    } finally {
      if (gen === renderGeneration) {
        loading = false;
      }
    }
  })();
});

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

$effect(() => {
  const query = searchTerm;
  const s = scale;
  const pageProxy = currentPageProxy;

  if (!pageProxy) {
    searchRects = [];
    searchMatchCount = 0;
    searchCurrentMatch = 0;
    return;
  }

  if (!query) {
    searchRects = [];
    searchMatchCount = 0;
    searchCurrentMatch = 0;
    return;
  }

  const gen = renderGeneration;

  (async () => {
    try {
      const result = await searchPageText(pageProxy, query, s);
      if (gen !== renderGeneration) return;

      searchRects = result.rects;
      searchMatchCount = result.count;
      if (searchCurrentMatch >= result.count) {
        searchCurrentMatch = 0;
      }
    } catch (err) {
      console.error("[PdfViewer] search error:", err);
    }
  })();
});

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function prevPage() {
  if (currentPage > 1) currentPage--;
}

function nextPage() {
  if (currentPage < totalPages) currentPage++;
}

function goToPageInput(e: Event) {
  const input = e.target as HTMLInputElement;
  const val = Math.max(1, Math.min(totalPages, parseInt(input.value, 10) || 1));
  currentPage = val;
}

// ---------------------------------------------------------------------------
// Zoom
// ---------------------------------------------------------------------------

function zoomIn() {
  scale = Math.min(ZOOM.max, scale + ZOOM.step);
}

function zoomOut() {
  scale = Math.max(ZOOM.min, scale - ZOOM.step);
}

// ---------------------------------------------------------------------------
// Search bar
// ---------------------------------------------------------------------------

function toggleSearch() {
  searchOpen = !searchOpen;
  if (!searchOpen) {
    searchTerm = "";
    searchCurrentMatch = 0;
  }
}

function searchPrev() {
  if (searchMatchCount === 0) return;
  searchCurrentMatch =
    (searchCurrentMatch - 1 + searchMatchCount) % searchMatchCount;
}

function searchNext() {
  if (searchMatchCount === 0) return;
  searchCurrentMatch = (searchCurrentMatch + 1) % searchMatchCount;
}

// ---------------------------------------------------------------------------
// Keyboard navigation
// ---------------------------------------------------------------------------

function handleKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement) return;

  switch (e.key) {
    case "ArrowLeft":
      e.preventDefault();
      prevPage();
      break;
    case "ArrowRight":
      e.preventDefault();
      nextPage();
      break;
    case "f":
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        toggleSearch();
      }
      break;
  }
}

// ---------------------------------------------------------------------------
// Command polling
// ---------------------------------------------------------------------------

let pollTimer: ReturnType<typeof setInterval> | null = null;

async function pollCommands() {
  if (!app) return;

  try {
    const result = await app.callServerTool("poll_pdf_commands", {
      view_id: viewId,
    });
    if (!result?.content?.length) return;

    const text = result.content[0];
    if (typeof text === "object" && "text" in text) {
      const commands: PdfCommand[] = JSON.parse(text.text);
      for (const cmd of commands) {
        processCommand(cmd);
      }
    }
  } catch {
    // Server may not support this tool yet -- silently skip
  }
}

function processCommand(cmd: PdfCommand) {
  switch (cmd.type) {
    case "navigate":
      currentPage = Math.max(1, Math.min(totalPages, cmd.page));
      break;
    case "search":
      searchTerm = cmd.query;
      searchOpen = !!cmd.query;
      break;
    case "zoom":
      scale = Math.max(ZOOM.min, Math.min(ZOOM.max, cmd.scale));
      break;
    case "add_annotations":
      for (const ann of cmd.annotations) {
        annotationMap.set(ann.id, { def: ann, elements: [] });
      }
      break;
    case "remove_annotations":
      for (const id of cmd.ids) {
        annotationMap.delete(id);
      }
      break;
    case "highlight_text":
      if (cmd.query) {
        searchTerm = cmd.query;
        searchOpen = true;
      }
      break;
    default:
      break;
  }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMount(() => {
  pollTimer = setInterval(pollCommands, 200);
});

onDestroy(() => {
  if (pollTimer) clearInterval(pollTimer);
  resetContextState();
});
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="viewer" bind:this={containerEl} onkeydown={handleKeydown} tabindex="-1">
  <!-- Toolbar -->
  <div class="toolbar">
    <div class="toolbar-left">
      <span class="pdf-title" title={title}>{title}</span>
      {#if loading}
        <div class="loading-indicator">
          <svg class="spinner" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="28" stroke-dashoffset="8" stroke-linecap="round"/>
          </svg>
        </div>
      {/if}
    </div>

    <div class="toolbar-center">
      <button class="nav-btn" onclick={prevPage} disabled={currentPage <= 1} aria-label="Previous page">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M8 2L4 6L8 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="page-nav">
        <input
          type="number"
          class="page-input"
          value={pageInputValue}
          min={1}
          max={totalPages}
          onchange={goToPageInput}
          aria-label="Page number"
        />
        <span class="total-pages">of {totalPages}</span>
      </div>
      <button class="nav-btn" onclick={nextPage} disabled={currentPage >= totalPages} aria-label="Next page">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M4 2L8 6L4 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <div class="toolbar-right">
      <button class="zoom-btn" onclick={zoomOut} disabled={scale <= ZOOM.min} aria-label="Zoom out">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 7h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </button>
      <span class="zoom-level">{zoomLabel}%</span>
      <button class="zoom-btn" onclick={zoomIn} disabled={scale >= ZOOM.max} aria-label="Zoom in">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 3v8M3 7h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </button>

      <button class="search-btn" class:active={searchOpen} onclick={toggleSearch} aria-label="Toggle search">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
          <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M10.5 10.5L14.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>

      {#if canFullscreen}
        <button class="fullscreen-btn" onclick={onToggleFullscreen} aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}>
          {#if isFullscreen}
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M5 1H1v4M15 1h-4M1 15h4M11 15h4v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M1 1l4.5 4.5M15 1l-4.5 4.5M1 15l4.5-4.5M15 15l-4.5-4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          {:else}
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M1 5V1h4M11 1h4v4M15 11v4h-4M5 15H1v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M1 1l4.5 4.5M15 1l-4.5 4.5M1 15l4.5-4.5M15 15l-4.5-4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          {/if}
        </button>
      {/if}
    </div>
  </div>

  <!-- Search bar -->
  {#if searchOpen}
    <div class="search-bar">
      <input
        bind:value={searchTerm}
        class="search-input"
        placeholder="Search..."
        aria-label="Search text in PDF"
      />
      <span class="search-match-count">{searchMatchLabel}</span>
      <button class="search-nav-btn" onclick={searchPrev} disabled={searchMatchCount === 0} aria-label="Previous match">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 7L5 3L8 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <button class="search-nav-btn" onclick={searchNext} disabled={searchMatchCount === 0} aria-label="Next match">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 3L5 7L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <button class="search-close-btn" onclick={toggleSearch} aria-label="Close search">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2 2L8 8M8 2L2 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
  {/if}

  <!-- Canvas + overlays -->
  <div class="viewer-body">
    <div class="canvas-container">
      <div class="page-wrapper">
        <canvas bind:this={canvasEl}></canvas>
        <div
          class="highlight-layer"
          style:width="{highlightWidth}px"
          style:height="{highlightHeight}px"
        >
          {#each searchRects as rect, i (i)}
            <div
              class="search-highlight"
              class:current={i === searchCurrentMatch}
              style:left="{rect.x}px"
              style:top="{rect.y}px"
              style:width="{rect.width}px"
              style:height="{rect.height}px"
            ></div>
          {/each}
        </div>
        <div bind:this={textLayerEl} class="text-layer"></div>
      </div>
    </div>
  </div>
</div>

<style>
/* ------------------------------------------------------------------ */
/* Viewer root                                                         */
/* ------------------------------------------------------------------ */

.viewer {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--color-background-primary);
  outline: none;
}

/* ------------------------------------------------------------------ */
/* Toolbar                                                             */
/* ------------------------------------------------------------------ */

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  min-height: 48px;
  padding: 0 var(--spacing-md);
  background: var(--color-background-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  gap: var(--spacing-sm);
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.toolbar-left {
  flex: 1;
  min-width: 0;
}

.toolbar-center {
  flex: 0 0 auto;
}

.toolbar-right {
  flex: 1;
  min-width: 0;
  justify-content: flex-end;
}

.pdf-title {
  font-size: var(--font-text-sm-size);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ------------------------------------------------------------------ */
/* Toolbar buttons                                                     */
/* ------------------------------------------------------------------ */

.nav-btn,
.zoom-btn,
.search-btn,
.fullscreen-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-sm);
  background: var(--color-background-primary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.nav-btn:hover:not(:disabled),
.zoom-btn:hover:not(:disabled),
.search-btn:hover:not(:disabled),
.fullscreen-btn:hover:not(:disabled) {
  background: var(--color-background-tertiary);
  color: var(--color-text-primary);
}

.nav-btn:disabled,
.zoom-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.search-btn.active {
  background: var(--color-accent);
  color: var(--color-text-on-accent);
  border-color: var(--color-accent);
}

/* ------------------------------------------------------------------ */
/* Page navigation input                                               */
/* ------------------------------------------------------------------ */

.page-nav {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.page-input {
  width: 50px;
  height: 28px;
  padding: 0 var(--spacing-xs);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-sm);
  background: var(--color-background-primary);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-text-sm-size);
  text-align: center;
  -moz-appearance: textfield;
}

.page-input::-webkit-outer-spin-button,
.page-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-input:focus {
  outline: 2px solid var(--color-accent);
  outline-offset: -1px;
}

.total-pages {
  font-size: var(--font-text-sm-size);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* ------------------------------------------------------------------ */
/* Zoom label                                                          */
/* ------------------------------------------------------------------ */

.zoom-level {
  min-width: 42px;
  text-align: center;
  font-size: var(--font-text-sm-size);
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* ------------------------------------------------------------------ */
/* Search bar                                                          */
/* ------------------------------------------------------------------ */

.search-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-background-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  justify-content: flex-end;
}

.search-input {
  width: 200px;
  height: 28px;
  padding: 0 var(--spacing-sm);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-sm);
  background: var(--color-background-primary);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  font-size: var(--font-text-sm-size);
}

.search-input:focus {
  outline: 2px solid var(--color-accent);
  outline-offset: -1px;
}

.search-match-count {
  font-size: var(--font-text-sm-size);
  color: var(--color-text-secondary);
  white-space: nowrap;
  min-width: 70px;
  text-align: center;
}

.search-nav-btn,
.search-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-sm);
  background: var(--color-background-primary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.search-nav-btn:hover:not(:disabled),
.search-close-btn:hover {
  background: var(--color-background-tertiary);
  color: var(--color-text-primary);
}

.search-nav-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

/* ------------------------------------------------------------------ */
/* Viewer body (canvas area)                                           */
/* ------------------------------------------------------------------ */

.viewer-body {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  background: var(--color-background-tertiary);
}

.canvas-container {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: var(--spacing-lg);
  min-height: 100%;
}

.page-wrapper {
  position: relative;
  box-shadow: 0 2px 12px var(--shadow-page-color);
  border-radius: 2px;
  background: white;
  line-height: 0;
}

.page-wrapper canvas {
  display: block;
}

/* ------------------------------------------------------------------ */
/* Text layer (PDF.js text selection)                                   */
/* ------------------------------------------------------------------ */

.text-layer {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 2;
  overflow: hidden;
  opacity: 0.25;
  line-height: 1;
}

.text-layer :global(span) {
  position: absolute;
  white-space: pre;
  color: transparent;
  pointer-events: all;
}

.text-layer :global(span)::selection {
  background: var(--selection-bg);
}

.text-layer :global(br) {
  display: none;
}

/* ------------------------------------------------------------------ */
/* Highlight layer (search results)                                    */
/* ------------------------------------------------------------------ */

.highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.search-highlight {
  position: absolute;
  background: rgba(255, 255, 0, 0.4);
  mix-blend-mode: multiply;
  border-radius: 2px;
}

.search-highlight.current {
  background: rgba(255, 165, 0, 0.6);
}
</style>
