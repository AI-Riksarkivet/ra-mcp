<script lang="ts">
import { onDestroy } from "svelte";
import { SvelteMap } from "svelte/reactivity";
import type { App } from "@modelcontextprotocol/ext-apps";
import type { PDFDocumentProxy, PDFPageProxy } from "../lib/pdf-engine";
import type { TrackedAnnotation } from "../lib/types";
import {
  renderPage,
  buildTextLayer,
  extractPageText,
  searchPageText,
} from "../lib/pdf-engine";
import { scheduleContextUpdate, resetContextState } from "../lib/context";
import { ZOOM } from "../lib/constants";
import TocPanel from "./TocPanel.svelte";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  app: App;
  pdfDocument: PDFDocumentProxy;
  pdfUrl: string;
  title: string;
  currentPage: number;
  totalPages: number;
  scale: number;
  searchTerm: string;
  canFullscreen: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  onBackToGallery: () => void;
  viewId: string;
}

let {
  app,
  pdfDocument,
  pdfUrl,
  title,
  currentPage = $bindable(),
  totalPages,
  scale = $bindable(),
  searchTerm = $bindable(),
  canFullscreen,
  isFullscreen,
  onToggleFullscreen,
  onBackToGallery,
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
let tocOpen = $state(true);
let searchMatchCount = $state(0);
let searchCurrentMatch = $state(0);
let searchRects = $state<DOMRect[]>([]);
let annotationMap = new SvelteMap<string, TrackedAnnotation>();
let showAnnotationPanel = $state(false);
let loading = $state(false);

// Cross-page search
let globalSearchResults = $state<{ pageNum: number; count: number }[]>([]);
let globalSearchTotal = $derived(globalSearchResults.reduce((s, r) => s + r.count, 0));
let globalSearchPages = $derived(globalSearchResults.length);
let globalSearchLoading = $state(false);

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
let searchMatchLabel = $derived.by(() => {
  if (globalSearchLoading) return "Searching...";
  if (searchMatchCount > 0) {
    const pageLabel = `${searchCurrentMatch + 1}/${searchMatchCount} on this page`;
    if (globalSearchTotal > 0) {
      return `${pageLabel} | ${globalSearchTotal} on ${globalSearchPages} page${globalSearchPages > 1 ? "s" : ""}`;
    }
    return pageLabel;
  }
  if (globalSearchTotal > 0) {
    return `${globalSearchTotal} on ${globalSearchPages} page${globalSearchPages > 1 ? "s" : ""} (not on this page)`;
  }
  return searchTerm ? "No matches" : "";
});

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

// Cross-page search: uses server-side pymupdf via search_pdf tool (fast).
let globalSearchCancelFn: (() => void) | null = null;

function startGlobalSearch() {
  if (!searchTerm || !app || !pdfUrl) return;
  if (globalSearchCancelFn) globalSearchCancelFn();

  globalSearchLoading = true;
  globalSearchResults = [];
  let cancelled = false;
  globalSearchCancelFn = () => { cancelled = true; };

  (async () => {
    try {
      const result = await app.callServerTool({
        name: "search_pdf",
        arguments: { url: pdfUrl, term: searchTerm },
      });

      if (cancelled) return;

      if (result.isError) {
        console.error("[PdfViewer] server search error:", result.content);
        return;
      }

      const sc = (result as any).structuredContent as Record<string, unknown>;
      if (sc?.pageMatches && Array.isArray(sc.pageMatches)) {
        globalSearchResults = sc.pageMatches as { pageNum: number; count: number }[];
      }
    } catch (err) {
      console.error("[PdfViewer] global search error:", err);
    } finally {
      if (!cancelled) globalSearchLoading = false;
      globalSearchCancelFn = null;
    }
  })();
}

// Clear global results when search term changes
$effect(() => {
  searchTerm; // track dependency
  globalSearchResults = [];
  globalSearchLoading = false;
  if (globalSearchCancelFn) {
    globalSearchCancelFn();
    globalSearchCancelFn = null;
  }
});

// Navigate to next/prev page with matches
function searchNextPage() {
  if (globalSearchResults.length === 0) return;
  const next = globalSearchResults.find((r) => r.pageNum > currentPage);
  if (next) {
    currentPage = next.pageNum;
  } else {
    // Wrap around to first match
    currentPage = globalSearchResults[0].pageNum;
  }
}

function searchPrevPage() {
  if (globalSearchResults.length === 0) return;
  const prev = [...globalSearchResults].reverse().find((r) => r.pageNum < currentPage);
  if (prev) {
    currentPage = prev.pageNum;
  } else {
    // Wrap around to last match
    currentPage = globalSearchResults[globalSearchResults.length - 1].pageNum;
  }
}

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

function fitToWidth() {
  if (!pdfDocument || !containerEl) return;
  pdfDocument.getPage(currentPage).then((page) => {
    const viewport = page.getViewport({ scale: 1 });
    const containerWidth = containerEl.clientWidth - 48; // padding
    const tocWidth = tocOpen ? 160 : 0;
    const availableWidth = containerWidth - tocWidth;
    if (availableWidth > 0 && viewport.width > 0) {
      scale = Math.max(ZOOM.min, Math.min(ZOOM.max, availableWidth / viewport.width));
    }
  });
}

// Auto-fit on mount
$effect(() => {
  if (pdfDocument && containerEl) {
    // Fit on first load
    fitToWidth();
  }
});

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
// Lifecycle
// ---------------------------------------------------------------------------

// No command polling — model commands (navigate, search, highlight) go through
// state updates via get_pdf_state polling in App.svelte (every 2-10s with backoff),
// same pattern as viewer-mcp. This avoids the hundreds of overlapping long-poll
// requests that the command queue pattern caused over remote HTTP.

onDestroy(() => {
  resetContextState();
});
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="viewer" bind:this={containerEl} onkeydown={handleKeydown} tabindex="-1">
  <div class="viewer-layout">
    {#if tocOpen}
      <TocPanel
        {pdfDocument}
        {currentPage}
        {totalPages}
        onPageSelect={(p) => currentPage = p}
      />
    {/if}

    <div class="viewer-body">
      <!-- Floating page nav (top-left) -->
      <div class="page-overlay top-left">
        <button class="overlay-btn" onclick={prevPage} disabled={currentPage <= 1} aria-label="Previous page">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M8 2L4 6L8 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div class="page-indicator">
          <input
            type="number"
            class="page-input"
            value={pageInputValue}
            min={1}
            max={totalPages}
            onchange={goToPageInput}
            aria-label="Page number"
          />
          <span class="page-total">/{totalPages}</span>
        </div>
        <button class="overlay-btn" onclick={nextPage} disabled={currentPage >= totalPages} aria-label="Next page">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4 2L8 6L4 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        {#if loading}
          <div class="loading-dot"></div>
        {/if}
      </div>

      <!-- Floating toolbar (top-right, vertical) -->
      <div class="floating-toolbar">
        <button class="toolbar-btn" onclick={onBackToGallery} title="Back to library" aria-label="Back to library">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 2L2 8L6 14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 8H14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
        <button class="toolbar-btn" class:active={searchOpen} onclick={toggleSearch} title="Search (Ctrl+F)" aria-label="Toggle search">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/><path d="M10.5 10.5L14.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
        <button class="toolbar-btn" class:active={tocOpen} onclick={() => tocOpen = !tocOpen} title="Toggle sidebar" aria-label="Toggle sidebar">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M2 3h12M2 8h8M2 13h10"/></svg>
        </button>
        <button class="toolbar-btn" onclick={zoomOut} disabled={scale <= ZOOM.min} title="Zoom out" aria-label="Zoom out">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
        <button class="toolbar-btn" onclick={zoomIn} disabled={scale >= ZOOM.max} title="Zoom in" aria-label="Zoom in">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 3v8M3 7h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
        {#if canFullscreen}
          <button class="toolbar-btn" onclick={onToggleFullscreen} title={isFullscreen ? "Exit fullscreen (Esc)" : "Enter fullscreen"} aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}>
            {#if isFullscreen}
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M5 1H1v4M15 1h-4M1 15h4M11 15h4v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1 1l4.5 4.5M15 1l-4.5 4.5M1 15l4.5-4.5M15 15l-4.5-4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            {:else}
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M1 5V1h4M11 1h4v4M15 11v4h-4M5 15H1v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1 1l4.5 4.5M15 1l-4.5 4.5M1 15l4.5-4.5M15 15l-4.5-4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            {/if}
          </button>
        {/if}
      </div>

      <!-- Floating search bar (below toolbar, top-right) -->
      {#if searchOpen}
        <div class="floating-search">
          <div class="search-input-wrapper">
            <svg class="search-icon" width="12" height="12" viewBox="0 0 16 16" fill="none"><circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/><path d="M10.5 10.5L14.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            <input
              bind:value={searchTerm}
              type="text"
              placeholder="Search..."
              aria-label="Search text in PDF"
            />
          </div>
          {#if searchTerm}
            <span class="match-info">{searchMatchLabel}</span>
            <button class="search-nav-btn" onclick={searchPrev} disabled={searchMatchCount === 0} title="Previous match" aria-label="Previous match">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 7L5 3L8 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
            <button class="search-nav-btn" onclick={searchNext} disabled={searchMatchCount === 0} title="Next match" aria-label="Next match">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 3L5 7L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
            <span class="search-divider"></span>
            {#if globalSearchLoading}
              <span class="match-info">Searching...</span>
            {:else if globalSearchPages > 0}
              <button class="search-nav-btn" onclick={searchPrevPage} title="Previous page with matches" aria-label="Previous page with matches">
                <svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M4 1L1 5L4 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1 5H11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
              <button class="search-nav-btn" onclick={searchNextPage} title="Next page with matches" aria-label="Next page with matches">
                <svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M8 1L11 5L8 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 5H1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
            {:else}
              <button class="search-all-btn" onclick={startGlobalSearch} title="Search all {totalPages} pages" aria-label="Search all pages">
                All pages
              </button>
            {/if}
          {/if}
          <button class="search-nav-btn close-btn" onclick={toggleSearch} title="Close (Esc)" aria-label="Close search">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 2L8 8M8 2L2 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
      {/if}

      <!-- Canvas + overlays -->
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
</div>

<style>
/* Viewer root */
.viewer {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--color-background-primary);
  outline: none;
}

.viewer-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Viewer body (canvas area, positioned for floating overlays) */
.viewer-body {
  flex: 1;
  position: relative;
  overflow: auto;
  display: flex;
  justify-content: center;
  background: var(--color-background-tertiary);
}

/* Floating page nav (top-left) */
.page-overlay {
  position: absolute;
  z-index: 15;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 6px;
  background: var(--color-background-primary);
  border-radius: var(--border-radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.page-overlay.top-left {
  top: 8px;
  left: 8px;
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: var(--border-radius-sm);
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}

.overlay-btn:hover:not(:disabled) {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
}

.overlay-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.page-indicator {
  display: flex;
  align-items: center;
  gap: 1px;
}

.page-input {
  width: 36px;
  padding: 2px 4px;
  border: none;
  border-radius: var(--border-radius-sm);
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
  font-size: 0.8rem;
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}

.page-input::-webkit-outer-spin-button,
.page-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-input:focus {
  outline: 1px solid var(--color-accent);
}

.page-total {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* Floating toolbar (top-right, vertical column) */
.floating-toolbar {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 15;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: var(--border-radius-sm);
  background: var(--color-background-primary);
  color: var(--color-text-secondary);
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.toolbar-btn:hover:not(:disabled) {
  opacity: 1;
}

.toolbar-btn.active {
  opacity: 1;
  background: var(--color-accent);
  color: #fff;
}

.toolbar-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

/* Floating search bar (top-right, below toolbar) */
.floating-search {
  position: absolute;
  top: 8px;
  right: 44px;
  z-index: 16;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  background: var(--color-background-primary);
  border-radius: var(--border-radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--color-background-secondary);
  border-radius: var(--border-radius-sm);
  padding: 2px 6px;
}

.search-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
  opacity: 0.5;
}

.search-input-wrapper input {
  border: none;
  outline: none;
  background: none;
  font: inherit;
  font-size: var(--font-text-sm-size);
  color: var(--color-text-primary);
  width: 120px;
  padding: 2px 0;
}

.search-input-wrapper input::placeholder {
  color: var(--color-text-secondary);
  opacity: 0.6;
}

.match-info {
  font-size: 0.65rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
  min-width: 30px;
  text-align: center;
}

.search-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: var(--border-radius-sm);
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}

.search-nav-btn:hover:not(:disabled) {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
}

.search-nav-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.search-divider {
  width: 1px;
  height: 14px;
  background: var(--color-border-primary);
  flex-shrink: 0;
}

.search-all-btn {
  padding: 2px 8px;
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-sm);
  background: none;
  color: var(--color-text-secondary);
  font-size: 0.65rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.1s, color 0.1s;
}

.search-all-btn:hover {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
}

/* Canvas + page rendering */
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

/* Text layer (PDF.js text selection) */
.text-layer {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  opacity: 0.2;
  line-height: 1;
  text-size-adjust: none;
  forced-color-adjust: none;
  transform-origin: 0 0;
  z-index: 2;
}

.text-layer :global(:is(span, br)) {
  color: transparent;
  position: absolute;
  white-space: pre;
  cursor: text;
  transform-origin: 0% 0%;
}

.text-layer > :global(:not(.markedContent)),
.text-layer :global(.markedContent span:not(.markedContent)) {
  z-index: 1;
  font-size: calc(var(--scale-factor, 1) * var(--font-height, 0));
  transform: rotate(var(--rotate, 0deg)) scaleX(var(--scale-x, 1));
}

.text-layer :global(.markedContent) {
  display: contents;
}

.text-layer :global(::selection) {
  background: var(--selection-bg);
}

.text-layer > :global(span) {
  pointer-events: all;
}

/* Highlight layer (search results) */
.highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 3;
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

@media (prefers-color-scheme: dark) {
  .search-highlight {
    background: rgba(255, 255, 0, 0.3);
    mix-blend-mode: screen;
  }
  .search-highlight.current {
    background: rgba(255, 165, 0, 0.5);
    mix-blend-mode: screen;
  }
}
</style>
