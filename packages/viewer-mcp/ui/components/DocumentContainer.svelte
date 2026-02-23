<script lang="ts">
import { onDestroy } from "svelte";
import { LRUCache } from "lru-cache";
import type { App } from "@modelcontextprotocol/ext-apps";
import type { ViewerData, PageData } from "../lib/types";
import { parsePageResult } from "../lib/utils";
import DocumentViewer from "./DocumentViewer.svelte";
import ThumbnailStrip from "./ThumbnailStrip.svelte";

interface Props {
  app: App;
  data: ViewerData;
  canFullscreen: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}

let { app, data, canFullscreen, isFullscreen, onToggleFullscreen }: Props = $props();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let currentPageIndex = $state(0);
let totalPages = $derived(data.pageUrls.length);
let hasThumbnails = $derived(data.pageUrls.length > 1);
let showThumbnails = $state(true);
let currentPageMetadata = $derived(data.pageMetadata[currentPageIndex] ?? "");
let thumbnailStripWidth = $state(120);

// Client-side page cache with LRU eviction (max 10 entries ≈ 40 MB worst-case)
let pageCache = new LRUCache<number, PageData>({ max: 10 });
let inFlight = new Map<number, Promise<PageData | null>>();
let currentPage = $state<PageData | null>(null);

function handlePageSelect(index: number) {
  currentPageIndex = index;
}

function handlePrevPage() {
  if (currentPageIndex > 0) currentPageIndex--;
}

function handleNextPage() {
  if (currentPageIndex < totalPages - 1) currentPageIndex++;
}

function handleKeydown(e: KeyboardEvent) {
  if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

  if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
    e.preventDefault();
    handlePrevPage();
  } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
    e.preventDefault();
    handleNextPage();
  }
}

// ---------------------------------------------------------------------------
// Page fetching + caching
// ---------------------------------------------------------------------------

/** Fetch page text layer from server (image loads directly via URL) */
function fetchPageData(index: number): Promise<PageData | null> {
  if (index < 0 || index >= totalPages) return Promise.resolve(null);
  if (pageCache.has(index)) return Promise.resolve(pageCache.get(index)!);
  if (inFlight.has(index)) return inFlight.get(index)!;

  const promise = (async (): Promise<PageData | null> => {
    try {
      const urls = data.pageUrls[index];
      const result = await app.callServerTool({
        name: "load-page",
        arguments: {
          image_url: urls.image,
          text_layer_url: urls.textLayer,
          page_index: index,
        },
      });

      if (result.isError) {
        const errText = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Unknown error";
        console.error("load-page error:", errText);
        return null;
      }

      const page = parsePageResult(result);
      if (page) {
        pageCache.set(index, page);
        return page;
      }
    } catch (e) {
      console.error("load-page failed:", e);
    } finally {
      inFlight.delete(index);
    }
    return null;
  })();

  inFlight.set(index, promise);
  return promise;
}

/** Fetch and set current page — use cache or fetch text layer via callServerTool */
async function fetchAndRenderPage(index: number) {
  if (index < 0 || index >= totalPages) return;

  // Check cache first — instant render, no server call
  const cached = pageCache.get(index);
  if (cached) {
    currentPage = cached;
    prefetchAdjacentPages(index);
    return;
  }

  const page = await fetchPageData(index);
  if (page && currentPageIndex === index) {
    currentPage = page;
    prefetchAdjacentPages(index);
  }
}

/** Prefetch text layer for adjacent pages so navigation feels instant */
function prefetchAdjacentPages(index: number) {
  const neighbors = [index - 1, index + 1];
  for (const n of neighbors) {
    if (n >= 0 && n < totalPages && !pageCache.has(n)) {
      // Fire and forget — don't await, don't block rendering
      fetchPageData(n);
    }
  }
}

// ---------------------------------------------------------------------------
// Watch page index changes
// ---------------------------------------------------------------------------

onDestroy(() => {
  pageCache.clear();
  inFlight.clear();
});

let lastRenderedIndex = -1;
$effect(() => {
  const idx = currentPageIndex;
  if (idx !== lastRenderedIndex) {
    lastRenderedIndex = idx;
    fetchAndRenderPage(idx);
  }
});
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="split-layout" tabindex="-1" onkeydown={handleKeydown}>
  {#if hasThumbnails}
    <div class="thumbnail-wrapper" class:collapsed={!showThumbnails} style:width="{showThumbnails ? thumbnailStripWidth : 0}px" style:min-width="{showThumbnails ? thumbnailStripWidth : 0}px">
      <ThumbnailStrip
        {app}
        {data}
        {currentPageIndex}
        onPageSelect={handlePageSelect}
        width={thumbnailStripWidth}
        onWidthChange={(w) => thumbnailStripWidth = w}
      />
    </div>
  {/if}
  {#if currentPage}
    <DocumentViewer
      {app}
      pageData={currentPage}
      pageIndex={currentPageIndex}
      {totalPages}
      pageMetadata={currentPageMetadata}
      {canFullscreen}
      {isFullscreen}
      {onToggleFullscreen}
      {hasThumbnails}
      {showThumbnails}
      onToggleThumbnails={() => showThumbnails = !showThumbnails}
      onPrevPage={handlePrevPage}
      onNextPage={handleNextPage}
    />
  {:else}
    <div class="page-loading">
      <div class="page-loading-shimmer"></div>
    </div>
  {/if}
</div>

<style>
.split-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
  gap: 0;
}

.split-layout:focus {
  outline: none;
}

.thumbnail-wrapper {
  overflow: hidden;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.thumbnail-wrapper.collapsed {
  width: 0;
  min-width: 0;
}

.page-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  border-radius: var(--border-radius-md, 6px);
}

.page-loading-shimmer {
  width: 60%;
  height: 80%;
  border-radius: var(--border-radius-md, 6px);
  background: linear-gradient(90deg, var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620)) 25%, var(--color-background-secondary, light-dark(#f5f4ed, #201d18)) 50%, var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620)) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
