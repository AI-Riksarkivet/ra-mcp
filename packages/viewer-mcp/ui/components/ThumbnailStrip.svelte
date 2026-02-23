<script lang="ts">
import { onDestroy } from "svelte";
import { SvelteSet } from "svelte/reactivity";
import type { App } from "@modelcontextprotocol/ext-apps";
import type { ViewerData } from "../lib/types";
import { resizeHandle } from "../lib/resize";
import { parseThumbnailResult } from "../lib/utils";

interface Props {
  app: App;
  data: ViewerData;
  currentPageIndex: number;
  onPageSelect: (index: number) => void;
  width?: number;
  onWidthChange?: (width: number) => void;
}

let { app, data, currentPageIndex, onPageSelect, width = 120, onWidthChange }: Props = $props();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let totalPages = $derived(data.pageUrls.length);

// Cache: page index → thumbnail data URL (capped to limit memory)
const THUMB_CACHE_MAX = 50;
let thumbnailCache = new Map<number, string>();

// Tracks which thumbnails have been rendered (triggers reactivity)
let loadedIndices = new SvelteSet<number>();

// Container ref for scrolling
let containerEl: HTMLDivElement;

// Batch loading state
let pendingIndices = new Set<number>();
let inFlightIndices = new Set<number>();
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let batchInFlight = false;
let batchQueue: number[] = [];
let destroyed = false;

let resizing = $state(false);

// ---------------------------------------------------------------------------
// Virtual list
// ---------------------------------------------------------------------------

const ITEM_HEIGHT = 155;
const BUFFER = 5;

let scrollTop = $state(0);
let containerHeight = $state(0);

let startIndex = $derived(Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER));
let endIndex = $derived(Math.min(totalPages, Math.ceil((scrollTop + containerHeight) / ITEM_HEIGHT) + BUFFER));
let visibleIndices = $derived(Array.from({ length: endIndex - startIndex }, (_, i) => startIndex + i));
let topSpacerHeight = $derived(startIndex * ITEM_HEIGHT);
let bottomSpacerHeight = $derived(Math.max(0, (totalPages - endIndex) * ITEM_HEIGHT));

// RAF-throttled scroll handler
let scrollRafId = 0;

function handleScroll() {
  if (scrollRafId) return;
  scrollRafId = requestAnimationFrame(() => {
    scrollRafId = 0;
    if (!containerEl) return;
    scrollTop = containerEl.scrollTop;
    containerHeight = containerEl.clientHeight;
    triggerThumbnailLoads();
  });
}

function triggerThumbnailLoads() {
  let added = false;
  for (let i = startIndex; i < endIndex; i++) {
    if (!thumbnailCache.has(i) && !inFlightIndices.has(i)) {
      pendingIndices.add(i);
      added = true;
    }
  }
  if (added) scheduleBatch();
}

// ---------------------------------------------------------------------------
// Batch fetching
// ---------------------------------------------------------------------------

async function fetchBatch(indices: number[]) {
  if (indices.length === 0 || destroyed) return;
  batchInFlight = true;

  for (const i of indices) inFlightIndices.add(i);

  try {
    const imageUrls = indices.map(i => data.pageUrls[i].image);
    const result = await app.callServerTool({
      name: "load-thumbnails",
      arguments: {
        image_urls: imageUrls,
        page_indices: indices,
      },
    });

    if (destroyed) return;

    if (!result.isError) {
      const thumbnails = parseThumbnailResult(result);
      for (const thumb of thumbnails) {
        thumbnailCache.set(thumb.index, thumb.dataUrl);
        loadedIndices.add(thumb.index);
      }
      // Evict oldest entries if cache exceeds limit
      while (thumbnailCache.size > THUMB_CACHE_MAX) {
        const oldest = thumbnailCache.keys().next().value!;
        thumbnailCache.delete(oldest);
        loadedIndices.delete(oldest);
      }
    }
  } catch (e) {
    console.error("load-thumbnails failed:", e);
  } finally {
    for (const i of indices) inFlightIndices.delete(i);
    batchInFlight = false;
    if (destroyed) return;
    // Process queued batch if any
    if (batchQueue.length > 0) {
      const next = batchQueue.splice(0, 8);
      fetchBatch(next);
    }
  }
}

function scheduleBatch() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const indices = Array.from(pendingIndices).filter(i => !thumbnailCache.has(i) && !inFlightIndices.has(i));
    pendingIndices.clear();

    if (indices.length === 0) return;

    // Clear stale queue — only current-viewport indices matter
    batchQueue.length = 0;

    // Take first 8 for immediate fetch, queue the rest
    const batch = indices.slice(0, 8);
    const rest = indices.slice(8);

    if (rest.length > 0) {
      batchQueue.push(...rest);
    }

    if (batchInFlight) {
      batchQueue.push(...batch);
    } else {
      fetchBatch(batch);
    }
  }, 300);
}

// ---------------------------------------------------------------------------
// Auto-scroll to active thumbnail
// ---------------------------------------------------------------------------

$effect(() => {
  const idx = currentPageIndex;
  if (!containerEl || containerHeight === 0) return;
  const itemTop = idx * ITEM_HEIGHT;
  const itemBottom = itemTop + ITEM_HEIGHT;
  const visTop = containerEl.scrollTop;
  const visBottom = visTop + containerHeight;
  if (itemTop < visTop || itemBottom > visBottom) {
    const target = itemTop - containerHeight / 2 + ITEM_HEIGHT / 2;
    containerEl.scrollTo({ top: Math.max(0, target), behavior: "smooth" });
  }
});

// ---------------------------------------------------------------------------
// Initialize container dimensions + ResizeObserver
// ---------------------------------------------------------------------------

let resizeObserver: ResizeObserver | null = null;

$effect(() => {
  if (!containerEl) return;

  // Set initial values
  scrollTop = containerEl.scrollTop;
  containerHeight = containerEl.clientHeight;
  triggerThumbnailLoads();

  resizeObserver = new ResizeObserver(() => {
    if (!containerEl) return;
    containerHeight = containerEl.clientHeight;
  });
  resizeObserver.observe(containerEl);

  return () => {
    resizeObserver?.disconnect();
    resizeObserver = null;
  };
});

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onDestroy(() => {
  destroyed = true;
  if (debounceTimer) clearTimeout(debounceTimer);
  if (scrollRafId) cancelAnimationFrame(scrollRafId);
  batchQueue.length = 0;
  pendingIndices.clear();
});

function getThumbnailUrl(index: number): string | null {
  if (loadedIndices.has(index)) {
    return thumbnailCache.get(index) ?? null;
  }
  return null;
}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="thumbnail-strip" class:resizing bind:this={containerEl} style:width="{width}px" style:min-width="{width}px" onscroll={handleScroll}>
  <div
    class="resize-handle"
    use:resizeHandle={{ edge: 'right', min: 80, max: 250, onResize: (w) => onWidthChange?.(w), onResizeStart: () => resizing = true, onResizeEnd: () => resizing = false }}
  ></div>
  <div style:height="{topSpacerHeight}px" style:flex-shrink="0"></div>
  {#each visibleIndices as i (i)}
    {@const thumbUrl = getThumbnailUrl(i)}
    <div
      class="thumbnail-slot"
      class:active={i === currentPageIndex}
    >
      <button
        class="thumbnail-inner"
        onclick={() => onPageSelect(i)}
      >
        {#if thumbUrl}
          <img
            src={thumbUrl}
            alt="Page {i + 1}"
            class="thumbnail-img"
          />
        {:else}
          <div class="thumbnail-placeholder">
            <span class="placeholder-text">{i + 1}</span>
          </div>
        {/if}
      </button>
    </div>
  {/each}
  <div style:height="{bottomSpacerHeight}px" style:flex-shrink="0"></div>
</div>

<style>
.thumbnail-strip {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs, 0.25rem);
  padding: var(--spacing-xs, 0.25rem);
  background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  border-right: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  border-radius: var(--border-radius-lg, 10px) 0 0 var(--border-radius-lg, 10px);
  position: relative;
}

.resize-handle {
  position: absolute;
  top: 0;
  right: -3px;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 11;
}

.resize-handle::after {
  content: "";
  position: absolute;
  top: 0;
  right: 2px;
  bottom: 0;
  width: 2px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.15s;
}

.resize-handle:hover::after,
.thumbnail-strip.resizing .resize-handle::after {
  background: var(--color-accent, #c15f3c);
  opacity: 0.4;
}

.thumbnail-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.thumbnail-inner {
  width: calc(100% - 16px);
  min-height: 80px;
  border: 2px solid transparent;
  border-radius: var(--border-radius-md, 6px);
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  padding: 0;
  font: inherit;
  color: inherit;
  text-align: inherit;
  display: block;
}

.thumbnail-slot.active .thumbnail-inner {
  border-color: var(--color-accent, #c15f3c);
  box-shadow: 0 0 0 2px rgba(193, 95, 60, 0.3);
}

.thumbnail-inner:hover {
  border-color: var(--color-accent, #c15f3c);
}

.thumbnail-img {
  width: 100%;
  height: 120px;
  object-fit: contain;
  display: block;
}

.thumbnail-placeholder {
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620));
}

.placeholder-text {
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  opacity: 0.6;
}
</style>
