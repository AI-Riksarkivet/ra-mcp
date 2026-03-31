<script lang="ts">
import { onDestroy } from "svelte";
import { SvelteMap, SvelteSet } from "svelte/reactivity";
import type { PDFDocumentProxy, OutlineItem } from "../lib/pdf-engine";
import { getOutline, renderThumbnail } from "../lib/pdf-engine";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  pdfDocument: PDFDocumentProxy;
  currentPage: number;
  totalPages: number;
  onPageSelect: (page: number) => void;
}

let { pdfDocument, currentPage, totalPages, onPageSelect }: Props = $props();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let mode = $state<"outline" | "thumbnails">("thumbnails");
let outline = $state<OutlineItem[] | null>(null);
let outlineLoading = $state(false);
let thumbnailCache = new SvelteMap<number, string>();
let scrollContainer = $state<HTMLDivElement>(undefined!);

// Track in-flight thumbnail renders to avoid duplicate work
let thumbInFlight = new SvelteSet<number>();
let destroyed = false;

// ---------------------------------------------------------------------------
// Fetch outline when pdfDocument changes
// ---------------------------------------------------------------------------

let prevDoc: PDFDocumentProxy | null = null;

$effect(() => {
  const doc = pdfDocument;
  if (!doc || doc === prevDoc) return;
  prevDoc = doc;

  outlineLoading = true;
  outline = null;
  thumbnailCache.clear();
  thumbInFlight.clear();

  let cancelled = false;

  (async () => {
    try {
      const result = await getOutline(doc);
      if (cancelled) return;
      outline = result;
      if (result) {
        mode = "outline";
        console.log("[TocPanel] Outline loaded:", result.length, "top-level items");
      } else {
        mode = "thumbnails";
        console.log("[TocPanel] No outline found, showing thumbnails");
      }
    } catch (err) {
      console.error("[TocPanel] outline fetch error:", err);
      if (!cancelled) {
        outline = null;
        mode = "thumbnails";
      }
    } finally {
      if (!cancelled) outlineLoading = false;
    }
  })();

  return () => { cancelled = true; };
});

// ---------------------------------------------------------------------------
// Thumbnail lazy loading
// ---------------------------------------------------------------------------

const THUMB_HEIGHT = 140;
const BUFFER = 2;

let scrollTop = $state(0);
let containerHeight = $state(0);

let visibleStart = $derived(Math.max(1, Math.floor(scrollTop / THUMB_HEIGHT) + 1 - BUFFER));
let visibleEnd = $derived(Math.min(totalPages, Math.ceil((scrollTop + containerHeight) / THUMB_HEIGHT) + BUFFER));

// RAF-throttled scroll handler
let scrollRafId = 0;

function handleScroll() {
  if (scrollRafId) return;
  scrollRafId = requestAnimationFrame(() => {
    scrollRafId = 0;
    if (!scrollContainer) return;
    scrollTop = scrollContainer.scrollTop;
    containerHeight = scrollContainer.clientHeight;
  });
}

// Load thumbnails for visible range
$effect(() => {
  if (mode !== "thumbnails" || !pdfDocument) return;

  const start = visibleStart;
  const end = visibleEnd;
  const doc = pdfDocument;

  for (let pageNum = start; pageNum <= end; pageNum++) {
    if (thumbnailCache.has(pageNum) || thumbInFlight.has(pageNum)) continue;
    thumbInFlight.add(pageNum);

    renderThumbnail(doc, pageNum, 120).then((dataUrl) => {
      if (!destroyed) {
        thumbnailCache.set(pageNum, dataUrl);
      }
    }).catch((err) => {
      console.error(`[TocPanel] thumbnail render error (page ${pageNum}):`, err);
    }).finally(() => {
      thumbInFlight.delete(pageNum);
    });
  }
});

// ---------------------------------------------------------------------------
// Initialize container dimensions + ResizeObserver
// ---------------------------------------------------------------------------

let resizeObserver: ResizeObserver | null = null;

$effect(() => {
  if (!scrollContainer) return;

  scrollTop = scrollContainer.scrollTop;
  containerHeight = scrollContainer.clientHeight;

  resizeObserver = new ResizeObserver(() => {
    if (!scrollContainer) return;
    containerHeight = scrollContainer.clientHeight;
  });
  resizeObserver.observe(scrollContainer);

  return () => {
    resizeObserver?.disconnect();
    resizeObserver = null;
  };
});

// ---------------------------------------------------------------------------
// Find closest outline item to current page (for highlighting)
// ---------------------------------------------------------------------------

function flattenOutline(items: OutlineItem[]): OutlineItem[] {
  const result: OutlineItem[] = [];
  for (const item of items) {
    result.push(item);
    if (item.items.length > 0) {
      result.push(...flattenOutline(item.items));
    }
  }
  return result;
}

let activeOutlinePageNum = $derived.by(() => {
  if (!outline) return null;
  const flat = flattenOutline(outline);
  let closest: number | null = null;
  for (const item of flat) {
    if (item.pageNum !== null && item.pageNum <= currentPage) {
      if (closest === null || item.pageNum > closest) {
        closest = item.pageNum;
      }
    }
  }
  return closest;
});

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onDestroy(() => {
  destroyed = true;
  if (scrollRafId) cancelAnimationFrame(scrollRafId);
  thumbInFlight.clear();
});
</script>

<div class="toc-panel">
  <div class="toc-tabs">
    {#if outline}
      <button class="toc-tab" class:active={mode === "outline"} onclick={() => mode = "outline"}>
        Outline
      </button>
    {/if}
    <button class="toc-tab" class:active={mode === "thumbnails"} onclick={() => mode = "thumbnails"}>
      Pages
    </button>
  </div>

  <div class="toc-content" bind:this={scrollContainer} onscroll={handleScroll}>
    {#if outlineLoading}
      <div class="loading-message">Loading...</div>
    {:else if mode === "outline" && outline}
      {#each outline as item (item.title)}
        {@render outlineNode(item, 0)}
      {/each}
    {:else}
      {#each Array(totalPages) as _, i (i)}
        {@const pageNum = i + 1}
        <button
          class="thumb-item"
          class:active={pageNum === currentPage}
          onclick={() => onPageSelect(pageNum)}
        >
          {#if thumbnailCache.has(pageNum)}
            <img src={thumbnailCache.get(pageNum)} alt="Page {pageNum}" class="thumb-img" />
          {:else}
            <div class="thumb-placeholder"></div>
          {/if}
          <span class="thumb-label">{pageNum}</span>
        </button>
      {/each}
    {/if}
  </div>
</div>

{#snippet outlineNode(item: OutlineItem, depth: number)}
  <button
    class="outline-item"
    class:active={item.pageNum === activeOutlinePageNum}
    style:padding-left="{12 + depth * 16}px"
    onclick={() => { if (item.pageNum) onPageSelect(item.pageNum) }}
    disabled={!item.pageNum}
  >
    {item.title}
  </button>
  {#if item.items.length > 0}
    {#each item.items as child (child.title)}
      {@render outlineNode(child, depth + 1)}
    {/each}
  {/if}
{/snippet}

<style>
.toc-panel {
  width: 160px;
  display: flex;
  flex-direction: column;
  background: var(--color-background-primary);
  border-right: 1px solid var(--color-border-primary);
  flex-shrink: 0;
  overflow: hidden;
}

.toc-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.toc-tab {
  flex: 1;
  padding: 0.4rem;
  font-size: 0.75rem;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.toc-tab.active {
  color: var(--color-text-primary);
  border-bottom: 2px solid var(--color-accent);
}

.toc-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem;
}

.loading-message {
  padding: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-align: center;
}

/* Outline items */

.outline-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: none;
  padding: 0.35rem 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-primary);
  cursor: pointer;
  border-radius: var(--border-radius-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.outline-item:hover {
  background: var(--color-background-secondary);
}

.outline-item.active {
  color: var(--color-accent);
  font-weight: 600;
}

.outline-item:disabled {
  opacity: 0.5;
  cursor: default;
}

/* Thumbnail items */

.thumb-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  padding: 0.3rem;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--border-radius-md);
  width: 100%;
}

.thumb-item:hover {
  background: var(--color-background-secondary);
}

.thumb-item.active {
  outline: 2px solid var(--color-accent);
  outline-offset: -2px;
}

.thumb-img {
  width: 100%;
  border-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.thumb-placeholder {
  width: 100%;
  aspect-ratio: 3 / 4;
  background: var(--color-background-tertiary);
  border-radius: 2px;
}

.thumb-label {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
}
</style>
