<script lang="ts">
  import { SvelteMap } from "svelte/reactivity";
  import type { TrackedAnnotation, PdfAnnotationDef } from "../lib/types";
  import { defaultColor } from "../lib/annotations";

  interface Props {
    annotations: Map<string, TrackedAnnotation>;
    currentPage: number;
    onSelect: (id: string) => void;
    onRemove: (id: string) => void;
    onClose: () => void;
  }

  let { annotations, currentPage, onSelect, onRemove, onClose }: Props = $props();

  let openSection: string | null = $state(null);

  let byPage: SvelteMap<number, TrackedAnnotation[]> = $derived.by(() => {
    const map = new SvelteMap<number, TrackedAnnotation[]>();
    for (const tracked of annotations.values()) {
      const page = tracked.def.page;
      let list = map.get(page);
      if (!list) {
        list = [];
        map.set(page, list);
      }
      list.push(tracked);
    }
    return map;
  });

  let sortedPages: number[] = $derived([...byPage.keys()].sort((a, b) => a - b));

  function getColor(def: PdfAnnotationDef): string {
    return def.color ?? defaultColor(def.type);
  }
</script>

<div class="annotation-panel floating">
  <div class="annotation-panel-header">
    <span class="annotation-panel-title">Annotations ({annotations.size})</span>
    <button class="annotation-panel-close" onclick={onClose}>&#x2715;</button>
  </div>
  <div class="annotation-panel-list">
    {#each sortedPages as pageNum (pageNum)}
      {@const sectionKey = `page-${pageNum}`}
      {@const isOpen = openSection === sectionKey}
      {@const pageAnnotations = byPage.get(pageNum) ?? []}
      <div
        class="annotation-section-header"
        class:open={isOpen}
        class:current-page={pageNum === currentPage}
        onclick={() => { openSection = isOpen ? null : sectionKey }}
        role="button"
        tabindex="0"
        onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openSection = isOpen ? null : sectionKey; } }}
      >
        <span>Page {pageNum} ({pageAnnotations.length})</span>
        <span class="annotation-section-chevron">{isOpen ? '\u25BC' : '\u25B6'}</span>
      </div>
      {#if isOpen}
        <div class="annotation-section-body open">
          {#each pageAnnotations as tracked (tracked.def.id)}
            <div
              class="annotation-card"
              onclick={() => onSelect(tracked.def.id)}
              role="button"
              tabindex="0"
              onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(tracked.def.id); } }}
            >
              <div class="annotation-card-row">
                <div class="annotation-card-swatch" style:background={getColor(tracked.def)}></div>
                <span class="annotation-card-type">{tracked.def.type}</span>
                {#if 'content' in tracked.def && tracked.def.content}
                  <span class="annotation-card-preview">{tracked.def.content}</span>
                {/if}
                <button
                  class="annotation-card-delete"
                  onclick={(e) => { e.stopPropagation(); onRemove(tracked.def.id); }}
                  title="Remove annotation"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                    <path d="M2 3h8M4.5 3V2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 .5.5v1M5 5.5v3M7 5.5v3M3 3l.5 7a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1L9 3" />
                  </svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {/each}
  </div>
</div>

<style>
  .annotation-panel.floating {
    position: absolute;
    top: 48px;
    right: 8px;
    z-index: 20;
    width: 260px;
    max-height: 60%;
    display: flex;
    flex-direction: column;
    background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
    border: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
    border-radius: var(--border-radius-md, 6px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    overflow: hidden;
  }

  .annotation-panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
    cursor: grab;
    flex-shrink: 0;
  }

  .annotation-panel-title {
    font-size: var(--font-text-sm-size, 0.875rem);
    font-weight: 600;
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  }

  .annotation-panel-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border: none;
    border-radius: var(--border-radius-sm, 4px);
    background: none;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    cursor: pointer;
    font-size: 0.8rem;
    transition: background 0.15s, color 0.15s;
  }

  .annotation-panel-close:hover {
    background: var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620));
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  }

  .annotation-panel-list {
    overflow-y: auto;
    flex: 1;
  }

  .annotation-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;
  }

  .annotation-section-header:hover {
    background: var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620));
  }

  .annotation-section-header.open {
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  }

  .annotation-section-header.current-page {
    border-left: 2px solid var(--color-accent, #C15F3C);
  }

  .annotation-section-chevron {
    font-size: 0.6rem;
  }

  .annotation-section-body.open {
    padding: 4px 0;
  }

  .annotation-card {
    padding: 6px 12px;
    cursor: pointer;
    transition: background 0.1s;
  }

  .annotation-card:hover {
    background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  }

  .annotation-card-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .annotation-card-swatch {
    width: 10px;
    height: 10px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .annotation-card-type {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    flex-shrink: 0;
  }

  .annotation-card-preview {
    font-size: 0.75rem;
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    min-width: 0;
  }

  .annotation-card-delete {
    display: none;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    padding: 0;
    border: none;
    border-radius: var(--border-radius-sm, 4px);
    background: none;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    cursor: pointer;
    flex-shrink: 0;
    margin-left: auto;
    transition: background 0.15s, color 0.15s;
  }

  .annotation-card:hover .annotation-card-delete {
    display: flex;
  }

  .annotation-card-delete:hover {
    background: var(--color-background-danger, light-dark(#fef2f2, #2d1515));
    color: var(--color-text-danger, light-dark(#b91c1c, #f87171));
  }
</style>
