<script lang="ts">
import type { TextLine } from "../lib/types";
import { resizeHandle } from "../lib/resize";

type Tab = "transcription" | "info";
type PanelPosition = "right" | "bottom";

interface Props {
  textLines: TextLine[];
  highlightedLineId: string | null;
  documentInfo?: string;
  bildvisningUrl?: string;
  position?: PanelPosition;
  open: boolean;
  width?: number;
  height?: number;
  onWidthChange?: (width: number) => void;
  onLineHover: (id: string | null) => void;
  onLineClick: (line: TextLine) => void;
  onLineDblClick?: (line: TextLine) => void;
  searchMatchIds?: Set<string>;
}

let { textLines, highlightedLineId, documentInfo = "", bildvisningUrl = "", position = "right", open, width = 280, height = 200, onWidthChange, onLineHover, onLineClick, onLineDblClick, searchMatchIds }: Props = $props();

let isBottom = $derived(position === "bottom");

let hasInfo = $derived(!!documentInfo || !!bildvisningUrl);
let hasText = $derived(textLines.length > 0);
let activeTab = $state<Tab>("transcription");

// Default to info tab when there's no text but there is metadata
$effect.pre(() => {
  if (!hasText && hasInfo) activeTab = "info";
});

/** Minimal markdown → HTML for server-generated metadata (bold, headings, paragraphs). */
function renderMarkdown(md: string): string {
  return md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^/, "<p>").replace(/$/, "</p>")
    .replace(/<p><h3>/g, "<h3>").replace(/<\/h3><\/p>/g, "</h3>");
}

let lineEls: HTMLButtonElement[] = [];
let containerEl = $state<HTMLDivElement>(undefined!);
let resizing = $state(false);

// Auto-scroll to highlighted line when changed externally (from canvas hover)
$effect(() => {
  const id = highlightedLineId;
  if (!id || !containerEl || !open) return;
  const idx = textLines.findIndex(l => l.id === id);
  if (idx >= 0 && lineEls[idx]) {
    const el = lineEls[idx];
    const containerRect = containerEl.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    if (elRect.top < containerRect.top || elRect.bottom > containerRect.bottom) {
      el.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }
});
</script>

<div class="panel" class:open class:resizing class:bottom={isBottom} style:width={isBottom ? undefined : `${width}px`} style:height={isBottom ? `${height}px` : undefined}>
  {#if !isBottom}
    <div
      class="resize-handle"
      use:resizeHandle={{ edge: 'left', min: 200, max: 500, onResize: (w) => onWidthChange?.(w), onResizeStart: () => resizing = true, onResizeEnd: () => resizing = false }}
    ></div>
  {/if}

  {#if hasInfo}
    <div class="tab-bar">
      <button class="tab" class:active={activeTab === "transcription"} onclick={() => activeTab = "transcription"}>Text</button>
      <button class="tab" class:active={activeTab === "info"} onclick={() => activeTab = "info"}>Info</button>
    </div>
  {/if}

  {#if activeTab === "transcription"}
    <div class="panel-lines" bind:this={containerEl}>
      {#each textLines as line, i (line.id)}
        <button
          class="line-item"
          class:highlighted={line.id === highlightedLineId}
          class:search-match={searchMatchIds?.has(line.id)}
          bind:this={lineEls[i]}
          onpointerenter={() => onLineHover(line.id)}
          onpointerleave={() => onLineHover(null)}
          onclick={() => onLineClick(line)}
          ondblclick={() => onLineDblClick?.(line)}
        >
          <span class="line-text">{line.transcription}</span>
          {#if line.confidence != null}
            <span
              class="confidence-badge"
              class:low={line.confidence < 0.7}
              class:medium={line.confidence >= 0.7 && line.confidence < 0.9}
              class:high={line.confidence >= 0.9}
              title={line.confidence.toFixed(2)}
            >{line.confidence.toFixed(2)}</span>
          {/if}
        </button>
      {/each}
      {#if textLines.length === 0}
        <div class="no-lines">No transcribed text on this page</div>
      {/if}
    </div>
  {:else}
    <div class="panel-info">
      {#if documentInfo}
        <div class="info-content">{@html renderMarkdown(documentInfo)}</div>
      {/if}
      {#if bildvisningUrl}
        <a class="bildvisning-link" href={bildvisningUrl} target="_blank" rel="noopener">Open in Riksarkivet viewer</a>
      {/if}
      {#if !documentInfo && !bildvisningUrl}
        <div class="no-lines">No document information available</div>
      {/if}
    </div>
  {/if}
</div>

<style>
/* ------------------------------------------------------------------ */
/* Panel container                                                     */
/* ------------------------------------------------------------------ */

.panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  border-left: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.04);
  z-index: 10;
  transform: translateX(100%);
  pointer-events: none;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  -webkit-font-smoothing: antialiased;
}

.panel.resizing { transition: none; }
.panel.open { transform: translateX(0); pointer-events: auto; }

/* Bottom sheet mode (mobile) */
.panel.bottom {
  position: relative;
  top: auto;
  right: auto;
  bottom: auto;
  width: 100% !important;
  flex-shrink: 0;
  border-left: none;
  border-top: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
  transform: none;
  pointer-events: auto;
  border-radius: 0;
}

.panel.bottom:not(.open) {
  display: none;
}

/* ------------------------------------------------------------------ */
/* Resize handle                                                       */
/* ------------------------------------------------------------------ */

.resize-handle {
  position: absolute;
  top: 0;
  left: -4px;
  bottom: 0;
  width: 8px;
  cursor: col-resize;
  z-index: 11;
}

.resize-handle::after {
  content: "";
  position: absolute;
  top: 0;
  left: 3px;
  bottom: 0;
  width: 2px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.15s ease;
}

.resize-handle:hover::after,
.panel.resizing .resize-handle::after {
  background: var(--color-accent, #c15f3c);
  opacity: 0.5;
}

/* ------------------------------------------------------------------ */
/* Tab bar                                                             */
/* ------------------------------------------------------------------ */

.tab-bar {
  display: flex;
  gap: 1px;
  padding: 0 0.75rem;
  border-bottom: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  flex-shrink: 0;
  background: var(--color-background-secondary, light-dark(#f5f5f0, #1e1b17));
}

.tab {
  flex: 1;
  padding: 0.5rem 0.75rem;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.tab:hover {
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
}

.tab.active {
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  border-bottom-color: var(--color-accent, #c15f3c);
  font-weight: 600;
}

/* ------------------------------------------------------------------ */
/* Transcription lines                                                 */
/* ------------------------------------------------------------------ */

.panel-lines {
  flex: 1;
  overflow-y: auto;
  padding: 0.375rem 0 0.375rem 0;
}

.line-item {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
  width: 100%;
  padding: 0.375rem 0.75rem;
  font: inherit;
  font-size: var(--font-text-sm-size, 0.875rem);
  line-height: 1.6;
  text-align: left;
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  background: none;
  border: none;
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
}

.line-item:hover {
  background: light-dark(rgba(0, 0, 0, 0.03), rgba(255, 255, 255, 0.04));
}

.line-item.highlighted {
  background: var(--claude-selection, rgba(193, 95, 60, 0.12));
  border-left-color: var(--color-accent, #c15f3c);
}

.line-item.search-match {
  border-left-color: light-dark(#d97706, #f59e0b);
  background: light-dark(rgba(245, 158, 11, 0.06), rgba(245, 158, 11, 0.08));
}

.line-item.search-match.highlighted {
  background: light-dark(rgba(245, 158, 11, 0.14), rgba(245, 158, 11, 0.18));
}

.line-text {
  flex: 1;
  min-width: 0;
}

/* ------------------------------------------------------------------ */
/* Confidence badges                                                   */
/* ------------------------------------------------------------------ */

.confidence-badge {
  flex-shrink: 0;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.125rem 0.3125rem;
  border-radius: 0.25rem;
  line-height: 1;
  letter-spacing: 0.02em;
}

.confidence-badge.high {
  color: light-dark(#15803d, #86efac);
  background: light-dark(rgba(21, 128, 61, 0.08), rgba(134, 239, 172, 0.1));
}

.confidence-badge.medium {
  color: light-dark(#a16207, #fcd34d);
  background: light-dark(rgba(161, 98, 7, 0.08), rgba(252, 211, 77, 0.1));
}

.confidence-badge.low {
  color: light-dark(#dc2626, #fca5a5);
  background: light-dark(rgba(220, 38, 38, 0.08), rgba(252, 165, 165, 0.1));
}

/* ------------------------------------------------------------------ */
/* Info panel                                                          */
/* ------------------------------------------------------------------ */

.panel-info {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  font-size: var(--font-text-sm-size, 0.875rem);
  line-height: 1.65;
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
}

.panel-info :global(h3) {
  margin: 0 0 0.75rem 0;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.panel-info :global(p) {
  margin: 0 0 0.625rem 0;
}

.panel-info :global(strong) {
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  font-weight: 500;
  font-size: 0.75rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.bildvisning-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.75rem;
  padding: 0.4375rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-accent, #c15f3c);
  text-decoration: none;
  border: 1px solid light-dark(rgba(0, 0, 0, 0.1), rgba(255, 255, 255, 0.1));
  border-radius: 0.5rem;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.bildvisning-link:hover {
  background: light-dark(rgba(0, 0, 0, 0.03), rgba(255, 255, 255, 0.05));
  border-color: var(--color-accent, #c15f3c);
}

/* ------------------------------------------------------------------ */
/* Empty state                                                         */
/* ------------------------------------------------------------------ */

.no-lines {
  padding: 2rem 1rem;
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  font-size: var(--font-text-sm-size, 0.875rem);
  text-align: center;
  line-height: 1.5;
}
</style>
