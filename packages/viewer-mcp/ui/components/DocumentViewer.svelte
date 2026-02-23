<script lang="ts">
import { onMount, onDestroy } from "svelte";
import type { App } from "@modelcontextprotocol/ext-apps";
import type { TextLine, PageData, TooltipState } from "../lib/types";
import { buildPolygonHits, findHitAtImageCoord } from "../lib/geometry";
import { CanvasController } from "../lib/canvas";
import { drawPolygonOverlays } from "../lib/overlays";
import TranscriptionPanel from "./TranscriptionPanel.svelte";
import CanvasToolbar from "./CanvasToolbar.svelte";
import { scheduleContextUpdate, resetContextState } from "../lib/context";
import { POLYGON_DEFAULTS } from "../lib/constants";

interface Props {
  app: App;
  pageData: PageData;
  pageIndex: number;
  totalPages: number;
  pageMetadata: string;
  canFullscreen: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  hasThumbnails: boolean;
  showThumbnails: boolean;
  onToggleThumbnails: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
}

let { app, pageData, pageIndex, totalPages, pageMetadata, canFullscreen, isFullscreen, onToggleFullscreen, hasThumbnails, showThumbnails, onToggleThumbnails, onPrevPage, onNextPage }: Props = $props();

let showNavButtons = $derived(!showThumbnails || !hasThumbnails);

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let tooltip = $state<TooltipState | null>(null);
let highlightedLineId = $state<string | null>(null);
let showPanel = $state(false);
let panelWidth = $state(280);

// Polygon style controls
let polygonColor = $state(POLYGON_DEFAULTS.color);
let polygonThickness = $state(POLYGON_DEFAULTS.thickness);
let polygonOpacity = $state(POLYGON_DEFAULTS.opacity);

let textLines = $derived(pageData?.textLayer?.textLines ?? []);
let hasTextLines = $derived(textLines.length > 0);
let currentPolygons = $derived(textLines.length > 0 ? buildPolygonHits(textLines) : []);

// Canvas element refs
let canvasEl: HTMLCanvasElement;
let containerEl: HTMLDivElement;
let wrapperEl: HTMLDivElement;

let controller: CanvasController;

// ---------------------------------------------------------------------------
// CanvasController callbacks
// ---------------------------------------------------------------------------

/** Draw polygon overlays in image space (called by CanvasController after drawing the image) */
function drawOverlays(ctx: CanvasRenderingContext2D, transform: import("../lib/canvas").Transform) {
  drawPolygonOverlays(
    ctx, transform, currentPolygons,
    { color: polygonColor, thickness: polygonThickness, opacity: polygonOpacity },
    highlightedLineId,
  );
}

/** Handle hover — hit test polygons, set tooltip + highlight, return cursor */
function handleHover(imgX: number, imgY: number, screenX: number, screenY: number): string | null {
  if (!currentPolygons.length) {
    if (tooltip) { tooltip = null; highlightedLineId = null; controller.requestDraw(); }
    return null;
  }

  const hit = findHitAtImageCoord(imgX, imgY, currentPolygons);
  if (hit) {
    // Only show tooltip when panel is closed (panel already shows the text)
    if (!showPanel) {
      tooltip = { text: hit.line.transcription, x: screenX + 15, y: screenY + 15 };
    }
    if (highlightedLineId !== hit.lineId) {
      highlightedLineId = hit.lineId;
      controller.requestDraw();
    }
    return "pointer";
  }

  if (tooltip || highlightedLineId) {
    tooltip = null;
    highlightedLineId = null;
    controller.requestDraw();
  }
  return null;
}

/** Handle click — hit test polygons, update model context */
function handleClick(imgX: number, imgY: number) {
  if (!currentPolygons.length) return;
  const hit = findHitAtImageCoord(imgX, imgY, currentPolygons);
  if (hit) scheduleContextUpdate(getContextState(), hit.line);
}

/** Handle pointer leave — clear tooltip + highlight */
function handlePointerLeave() {
  tooltip = null;
  if (highlightedLineId) {
    highlightedLineId = null;
    controller.requestDraw();
  }
}

// ---------------------------------------------------------------------------
// Transcription panel handlers
// ---------------------------------------------------------------------------

function handlePanelLineHover(lineId: string | null) {
  if (lineId === highlightedLineId) return;
  highlightedLineId = lineId;
  tooltip = null;
  controller?.requestDraw();
}

function handlePanelLineClick(line: TextLine) {
  const centerX = line.hpos + line.width / 2;
  const centerY = line.vpos + line.height / 2;
  if (!controller?.isPointVisible(centerX, centerY)) {
    controller?.centerOn(centerX, centerY);
  }
  scheduleContextUpdate(getContextState(), line);
}

// ---------------------------------------------------------------------------
// Model context helpers
// ---------------------------------------------------------------------------

function getContextState() {
  return {
    app,
    pageIndex,
    totalPages,
    pageMetadata,
    getTextLines: () => pageData?.textLayer?.textLines ?? [],
  };
}

// ---------------------------------------------------------------------------
// Redraw when polygon style changes
// ---------------------------------------------------------------------------

$effect(() => {
  // Subscribe to all three style values
  polygonColor; polygonThickness; polygonOpacity;
  controller?.requestDraw();
});

// ---------------------------------------------------------------------------
// Watch pageData changes — load image and set on controller
// ---------------------------------------------------------------------------

$effect(() => {
  const pd = pageData;

  highlightedLineId = null;
  tooltip = null;

  const img = new Image();
  let cancelled = false;

  img.onload = () => {
    if (cancelled) return;
    if (controller) {
      controller.setImage(img);
      scheduleContextUpdate(getContextState());
    }
  };
  img.onerror = () => {
    if (cancelled) return;
    console.error("Failed to load page image");
  };
  img.src = pd.imageDataUrl;

  return () => {
    cancelled = true;
    img.onload = null;
    img.onerror = null;
    img.src = "";
  };
});

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

// Canvas event wrappers — delegate to controller (created in onMount)
function onPointerDown(e: PointerEvent) { controller?.handlePointerDown(e); }
function onPointerMove(e: PointerEvent) { controller?.handlePointerMove(e); }
function onPointerUp(e: PointerEvent) { controller?.handlePointerUp(e); }
function onPointerLeave() { controller?.handlePointerLeave(); }
function onWheel(e: WheelEvent) { controller?.handleWheel(e); }

onMount(() => {
  controller = new CanvasController(canvasEl, containerEl, wrapperEl, {
    onAfterDraw: drawOverlays,
    onClickImage: handleClick,
    onHoverImage: handleHover,
    onPointerLeave: handlePointerLeave,
  });
});

onDestroy(() => {
  controller?.destroy();
  resetContextState();
});
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="viewer-wrapper" bind:this={wrapperEl}>
  <!-- Canvas -->
  <div class="canvas-container" bind:this={containerEl}>
    <canvas
      bind:this={canvasEl}
      style="cursor: grab"
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      onpointerup={onPointerUp}
      onpointerleave={onPointerLeave}
      onwheel={onWheel}
    ></canvas>
    <div class="top-left-info">
      {#if showNavButtons}
        <button class="nav-btn" disabled={pageIndex <= 0} onclick={onPrevPage} aria-label="Previous page">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 3L5 7L9 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      {/if}
      <div class="page-indicator">{pageIndex + 1}/{totalPages}</div>
      {#if showNavButtons}
        <button class="nav-btn" disabled={pageIndex >= totalPages - 1} onclick={onNextPage} aria-label="Next page">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 3L9 7L5 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      {/if}
      {#if pageMetadata}
        <div class="page-info">{pageMetadata}</div>
      {/if}
    </div>

    <CanvasToolbar
      showTranscription={showPanel}
      hasTranscription={hasTextLines}
      {canFullscreen}
      {isFullscreen}
      {hasThumbnails}
      {showThumbnails}
      rightOffset={showPanel ? panelWidth : 0}
      onToggleTranscription={() => showPanel = !showPanel}
      onResetView={() => controller?.resetView()}
      {onToggleFullscreen}
      {onToggleThumbnails}
      {polygonColor}
      {polygonThickness}
      {polygonOpacity}
      onPolygonStyleChange={(key, value) => {
        if (key === 'color') polygonColor = value as string;
        else if (key === 'thickness') polygonThickness = value as number;
        else if (key === 'opacity') polygonOpacity = value as number;
      }}
    />

    {#if hasTextLines}
      <TranscriptionPanel
        {textLines}
        {highlightedLineId}
        open={showPanel}
        width={panelWidth}
        onWidthChange={(w) => panelWidth = w}
        onLineHover={handlePanelLineHover}
        onLineClick={handlePanelLineClick}
      />
    {/if}
  </div>
</div>

<!-- Tooltip -->
{#if tooltip && tooltip.x > 0}
  <div class="tooltip" style:left="{tooltip.x}px" style:top="{tooltip.y}px">
    {tooltip.text}
  </div>
{/if}

<style>
.viewer-wrapper {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  overflow: hidden;
  position: relative;
  border-radius: var(--border-radius-md, 6px);
}
.canvas-container canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.top-left-info {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  pointer-events: none;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
}

.nav-btn {
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: var(--border-radius-sm, 4px);
  background: light-dark(rgba(0, 0, 0, 0.1), rgba(255, 255, 255, 0.1));
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.nav-btn:hover:not(:disabled) {
  background: light-dark(rgba(0, 0, 0, 0.2), rgba(255, 255, 255, 0.2));
  color: var(--color-text-primary, light-dark(#1a1815, #e8e6e3));
}
.nav-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.page-indicator,
.page-info {
  background: light-dark(rgba(0, 0, 0, 0.1), rgba(255, 255, 255, 0.1));
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  padding: 2px 8px;
  border-radius: var(--border-radius-sm, 4px);
  font-size: var(--font-text-xs-size, 0.75rem);
  white-space: nowrap;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tooltip {
  position: fixed;
  background: var(--color-tooltip-background, light-dark(rgba(44, 44, 44, 0.95), rgba(232, 230, 227, 0.95)));
  color: var(--color-tooltip-text, light-dark(#faf9f5, #1a1815));
  padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 0.75rem);
  border-radius: var(--border-radius-md, 6px);
  font-size: var(--font-text-sm-size, 0.875rem);
  pointer-events: none;
  z-index: 1000;
  max-width: 300px;
  word-wrap: break-word;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
