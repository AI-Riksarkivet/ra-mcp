<script lang="ts">
import PolygonStylePopover from "./PolygonStylePopover.svelte";
import { POLYGON_DEFAULTS } from "../lib/constants";

interface Props {
  showTranscription: boolean;
  hasTranscription: boolean;
  canFullscreen: boolean;
  isFullscreen: boolean;
  hasThumbnails: boolean;
  showThumbnails: boolean;
  rightOffset?: number;
  onToggleTranscription: () => void;
  onResetView: () => void;
  onToggleFullscreen: () => void;
  onToggleThumbnails: () => void;
  polygonColor?: string;
  polygonThickness?: number;
  polygonOpacity?: number;
  onPolygonStyleChange?: (key: string, value: string | number) => void;
  onToggleSearch?: () => void;
  showHighlights?: boolean;
  onToggleHighlights?: (v: boolean) => void;
}

let {
  showTranscription,
  hasTranscription,
  canFullscreen,
  isFullscreen,
  hasThumbnails,
  showThumbnails,
  rightOffset = 0,
  onToggleTranscription,
  onResetView,
  onToggleFullscreen,
  onToggleThumbnails,
  polygonColor = POLYGON_DEFAULTS.color,
  polygonThickness = POLYGON_DEFAULTS.thickness,
  polygonOpacity = POLYGON_DEFAULTS.opacity,
  onPolygonStyleChange,
  onToggleSearch,
  showHighlights,
  onToggleHighlights,
}: Props = $props();

let showPopover = $state(false);
</script>

<div class="toolbar" style:right="{rightOffset + 8}px">
  {#if hasTranscription && onToggleSearch}
    <button
      class="toolbar-btn"
      onclick={onToggleSearch}
      title="Search text (Ctrl+F)"
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10.5 10.5L14.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  {/if}

  {#if hasTranscription}
    <button
      class="toolbar-btn"
      class:active={showTranscription}
      onclick={onToggleTranscription}
      title={showTranscription ? "Hide transcription" : "Show transcription"}
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  {/if}

  {#if hasThumbnails}
    <button
      class="toolbar-btn"
      class:active={showThumbnails}
      onclick={onToggleThumbnails}
      title={showThumbnails ? "Hide pages" : "Show pages"}
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <rect x="1" y="1" width="4" height="5" rx="0.5" stroke="currentColor" stroke-width="1.3"/>
        <rect x="1" y="8.5" width="4" height="5" rx="0.5" stroke="currentColor" stroke-width="1.3"/>
        <path d="M8 3h7M8 7h5M8 11h6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
    </button>
  {/if}

  <button
    class="toolbar-btn"
    onclick={onResetView}
    title="Reset view"
  >
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path d="M1 8a7 7 0 0 1 13-3.5M15 8a7 7 0 0 1-13 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M14 1v4h-4M2 15v-4h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>

  <!-- Polygon style settings -->
  <div class="popover-anchor">
    <button
      class="toolbar-btn"
      class:active={showPopover}
      onclick={() => showPopover = !showPopover}
      title="Overlay style"
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M12.5 1.5l2 2-9 9L2 14l1.5-3.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M10.5 3.5l2 2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
    </button>

    {#if showPopover}
      <PolygonStylePopover
        color={polygonColor}
        thickness={polygonThickness}
        opacity={polygonOpacity}
        onChange={(key, value) => onPolygonStyleChange?.(key, value)}
        onClose={() => showPopover = false}
        {showHighlights}
        {onToggleHighlights}
      />
    {/if}
  </div>

  {#if canFullscreen}
    <button
      class="toolbar-btn"
      onclick={onToggleFullscreen}
      title={isFullscreen ? "Exit fullscreen (Esc)" : "Enter fullscreen"}
    >
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

<style>
.toolbar {
  position: absolute;
  top: 8px;
  z-index: 15;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: right 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: var(--border-radius-sm, 4px);
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}

.toolbar-btn:hover {
  opacity: 1;
}

.toolbar-btn.active {
  opacity: 1;
  background: var(--color-accent, #c15f3c);
  color: #fff;
}

.popover-anchor {
  position: relative;
}
</style>
