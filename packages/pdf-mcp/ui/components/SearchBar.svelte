<script lang="ts">
  import { onMount } from "svelte";

  interface Props {
    searchTerm: string;
    matchCount: number;
    currentMatch: number;
    onNext: () => void;
    onPrev: () => void;
    onClose: () => void;
  }

  let { searchTerm = $bindable(), matchCount, currentMatch, onNext, onPrev, onClose }: Props = $props();

  let inputEl = $state<HTMLInputElement>(undefined!);

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (e.shiftKey) onPrev();
      else onNext();
    }
  }

  onMount(() => {
    inputEl?.focus();
  });
</script>

<div class="search-bar">
  <input
    bind:this={inputEl}
    bind:value={searchTerm}
    class="search-input"
    type="text"
    placeholder="Search..."
    autocomplete="off"
    onkeydown={handleKeydown}
  />
  <span class="search-match-count">
    {#if matchCount > 0}
      {currentMatch + 1} of {matchCount}
    {:else if searchTerm}
      No matches
    {/if}
  </span>
  <button class="search-nav-btn" onclick={onPrev} title="Previous (Shift+Enter)">&#x25B2;</button>
  <button class="search-nav-btn" onclick={onNext} title="Next (Enter)">&#x25BC;</button>
  <button class="search-nav-btn" onclick={onClose} title="Close (Esc)">&#x2715;</button>
</div>

<style>
  .search-bar {
    position: absolute;
    top: 100%;
    right: 8px;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 6px 10px;
    background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
    border: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
    border-radius: var(--border-radius-md, 6px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  }

  .search-input {
    width: 200px;
    padding: 4px 8px;
    border: 1px solid var(--color-border-primary, light-dark(#d4d2cb, #3a3632));
    border-radius: var(--border-radius-sm, 4px);
    background: var(--color-background-secondary, light-dark(#f5f4ed, #201d18));
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
    font: inherit;
    font-size: var(--font-text-sm-size, 0.875rem);
    outline: none;
  }

  .search-input::placeholder {
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
  }

  .search-input:focus {
    border-color: var(--color-accent, #C15F3C);
  }

  .search-match-count {
    font-size: 0.75rem;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    white-space: nowrap;
    min-width: 60px;
    text-align: center;
  }

  .search-nav-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: none;
    border-radius: var(--border-radius-sm, 4px);
    background: none;
    color: var(--color-text-secondary, light-dark(#5c5c5c, #a8a6a3));
    cursor: pointer;
    font-size: 0.75rem;
    transition: background 0.15s, color 0.15s;
  }

  .search-nav-btn:hover {
    background: var(--color-background-tertiary, light-dark(#ebe9e1, #2a2620));
    color: var(--color-text-primary, light-dark(#2c2c2c, #e8e6e3));
  }
</style>
