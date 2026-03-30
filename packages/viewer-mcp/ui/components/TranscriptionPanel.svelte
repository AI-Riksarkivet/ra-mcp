<script lang="ts">
import type { TextLine } from "../lib/types";
import { resizeHandle } from "../lib/resize";

type Tab = "transcription" | "info";

interface Props {
  textLines: TextLine[];
  highlightedLineId: string | null;
  documentInfo?: string;
  bildvisningUrl?: string;
  open: boolean;
  width?: number;
  onWidthChange?: (width: number) => void;
  onLineHover: (id: string | null) => void;
  onLineClick: (line: TextLine) => void;
  searchMatchIds?: Set<string>;
}

let { textLines, highlightedLineId, documentInfo = "", bildvisningUrl = "", open, width = 280, onWidthChange, onLineHover, onLineClick, searchMatchIds }: Props = $props();

let activeTab = $state<Tab>("transcription");
let hasInfo = $derived(!!documentInfo || !!bildvisningUrl);

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
let containerEl: HTMLDivElement;
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

<div class="panel" class:open class:resizing style:width="{width}px">
  <div
    class="resize-handle"
    use:resizeHandle={{ edge: 'left', min: 200, max: 500, onResize: (w) => onWidthChange?.(w), onResizeStart: () => resizing = true, onResizeEnd: () => resizing = false }}
  ></div>

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
.panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  border-left: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
  transform: translateX(100%);
  pointer-events: none;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
}

.panel.resizing {
  transition: none;
}

.panel.open {
  transform: translateX(0);
  pointer-events: auto;
}

.resize-handle {
  position: absolute;
  top: 0;
  left: -3px;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 11;
}

.resize-handle::after {
  content: "";
  position: absolute;
  top: 0;
  left: 2px;
  bottom: 0;
  width: 2px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.15s;
}

.resize-handle:hover::after,
.panel.resizing .resize-handle::after {
  background: var(--color-accent, #c15f3c);
  opacity: 0.4;
}

.panel-lines {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-xs, 0.25rem) 0 var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
}

.line-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  width: 100%;
  padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
  font: inherit;
  font-size: var(--font-text-sm-size, 0.875rem);
  line-height: 1.5;
  text-align: left;
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  background: none;
  border: none;
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s;
}

.line-text {
  flex: 1;
  min-width: 0;
}

.confidence-badge {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 3px;
  line-height: 1.3;
  opacity: 0.7;
}

.confidence-badge.high {
  color: light-dark(#15803d, #86efac);
  background: light-dark(rgba(21, 128, 61, 0.1), rgba(134, 239, 172, 0.1));
}

.confidence-badge.medium {
  color: light-dark(#a16207, #fcd34d);
  background: light-dark(rgba(161, 98, 7, 0.1), rgba(252, 211, 77, 0.1));
}

.confidence-badge.low {
  color: light-dark(#dc2626, #fca5a5);
  background: light-dark(rgba(220, 38, 38, 0.1), rgba(252, 165, 165, 0.1));
}

.line-item:hover,
.line-item.highlighted {
  background: var(--claude-selection, rgba(193, 95, 60, 0.19));
  border-left-color: var(--color-accent, #c15f3c);
}

.line-item.search-match {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
}

.line-item.search-match.highlighted {
  background: rgba(245, 158, 11, 0.18);
}

.no-lines {
  padding: var(--spacing-lg, 1.5rem) var(--spacing-md, 1rem);
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  font-size: var(--font-text-sm-size, 0.875rem);
  font-style: italic;
  text-align: center;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  flex-shrink: 0;
}

.tab {
  flex: 1;
  padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
  font: inherit;
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
}

.tab.active {
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  border-bottom-color: var(--color-accent, #c15f3c);
}

.panel-info {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md, 0.75rem) var(--spacing-md, 0.75rem);
  font-size: var(--font-text-sm-size, 0.875rem);
  line-height: 1.6;
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
}

.panel-info :global(h3) {
  margin: 0 0 var(--spacing-sm, 0.5rem) 0;
  font-size: 1rem;
  font-weight: 600;
}

.panel-info :global(p) {
  margin: 0 0 var(--spacing-sm, 0.5rem) 0;
}

.panel-info :global(strong) {
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  font-weight: 500;
}

.bildvisning-link {
  display: inline-block;
  margin-top: var(--spacing-sm, 0.5rem);
  padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-accent, #c15f3c);
  text-decoration: none;
  border: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
  border-radius: var(--border-radius-md, 6px);
  transition: background 0.15s;
}

.bildvisning-link:hover {
  background: var(--claude-selection, rgba(193, 95, 60, 0.19));
}
</style>
