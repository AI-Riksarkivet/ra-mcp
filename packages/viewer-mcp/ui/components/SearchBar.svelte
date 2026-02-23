<script lang="ts">
import { onMount } from "svelte";

interface Props {
  searchTerm: string;
  matchCount: number;
  activeMatchIndex: number;
  rightOffset?: number;
  onSearchTermChange: (term: string) => void;
  onPrevMatch: () => void;
  onNextMatch: () => void;
  onClose: () => void;
  globalTotalMatches?: number;
  globalSearchLoading?: boolean;
}

let { searchTerm, matchCount, activeMatchIndex, rightOffset = 0, onSearchTermChange, onPrevMatch, onNextMatch, onClose, globalTotalMatches = 0, globalSearchLoading = false }: Props = $props();

let inputEl: HTMLInputElement;

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") {
    e.preventDefault();
    onClose();
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (e.shiftKey) onPrevMatch();
    else onNextMatch();
  }
}

onMount(() => {
  inputEl?.focus();
});
</script>

<div class="search-bar" style:right="{rightOffset + 8}px">
  <div class="search-input-wrapper">
    <svg class="search-icon" width="12" height="12" viewBox="0 0 16 16" fill="none">
      <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M10.5 10.5L14.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <input
      bind:this={inputEl}
      type="text"
      placeholder="Search text..."
      value={searchTerm}
      oninput={(e) => onSearchTermChange((e.target as HTMLInputElement).value)}
      onkeydown={handleKeydown}
    />
  </div>
  {#if searchTerm}
    <span class="match-info">
      {#if matchCount > 0}
        {activeMatchIndex + 1}/{matchCount}
      {:else}
        No matches
      {/if}
      {#if globalSearchLoading}
        <span class="global-loading" title="Searching all pages...">...</span>
      {:else if globalTotalMatches > 0}
        <span class="global-total" title="Total matches across all pages">&middot; {globalTotalMatches} total</span>
      {/if}
    </span>
    <button class="search-btn" onclick={onPrevMatch} disabled={matchCount === 0 && globalTotalMatches === 0} title="Previous (Shift+Enter)">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M8 7L5 3L2 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
    <button class="search-btn" onclick={onNextMatch} disabled={matchCount === 0 && globalTotalMatches === 0} title="Next (Enter)">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 3L5 7L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
  {/if}
  <button class="search-btn close-btn" onclick={onClose} title="Close (Escape)">
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 2L8 8M8 2L2 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
  </button>
</div>

<style>
.search-bar {
  position: absolute;
  top: 8px;
  z-index: 16;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  border-radius: var(--border-radius-md, 6px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: right 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  border-radius: var(--border-radius-sm, 4px);
  padding: 2px 6px;
}

.search-icon {
  color: var(--color-text-tertiary, light-dark(#999, #666));
  flex-shrink: 0;
}

.search-input-wrapper input {
  border: none;
  outline: none;
  background: none;
  font: inherit;
  font-size: var(--font-text-sm-size, 0.875rem);
  color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  width: 120px;
  padding: 2px 0;
}

.search-input-wrapper input::placeholder {
  color: var(--color-text-tertiary, light-dark(#999, #666));
}

.match-info {
  font-size: 0.7rem;
  color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  white-space: nowrap;
  min-width: 40px;
  text-align: center;
}

.search-btn {
  display: flex;
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
  transition: background 0.1s, color 0.1s;
}

.search-btn:hover:not(:disabled) {
  background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
  color: var(--color-text-primary, light-dark(#1a1815, #e8e6e3));
}

.search-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.global-loading {
  letter-spacing: 1px;
  animation: pulse-dots 1s infinite;
}

.global-total {
  opacity: 0.7;
}

@keyframes pulse-dots {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
</style>
