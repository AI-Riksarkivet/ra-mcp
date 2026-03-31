<script lang="ts">
  import type { GalleryItem } from "../lib/types";

  interface Props {
    items: GalleryItem[];
    loading: boolean;
    onSelect: (item: GalleryItem) => void;
  }

  let { items, loading, onSelect }: Props = $props();
</script>

<div class="gallery">
  <div class="gallery-header">
    <h2 class="gallery-title">PDF Library</h2>
    <p class="gallery-subtitle">Select a document to view</p>
  </div>

  {#if loading}
    <div class="gallery-loading">
      <div class="spinner"></div>
      <span>Loading library...</span>
    </div>
  {:else if items.length === 0}
    <div class="gallery-empty">No documents available</div>
  {:else}
    <div class="gallery-grid">
      {#each items as item (item.url)}
        <button class="gallery-card" onclick={() => onSelect(item)}>
          <div class="card-icon">
            <svg width="40" height="48" viewBox="0 0 40 48" fill="none">
              <rect x="1" y="1" width="38" height="46" rx="3" stroke="currentColor" stroke-width="1.5" fill="var(--color-background-secondary)"/>
              <path d="M10 14h20M10 20h20M10 26h14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>
              <text x="20" y="40" text-anchor="middle" font-size="8" font-weight="600" fill="var(--color-accent)">PDF</text>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-title">{item.title}</span>
            {#if item.description}
              <span class="card-description">{item.description}</span>
            {/if}
            {#if item.category}
              <span class="card-badge">{item.category}</span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .gallery {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
    height: 100%;
  }

  .gallery-header {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  .gallery-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }

  .gallery-subtitle {
    font-size: 0.9rem;
    color: var(--color-text-secondary);
    margin: 0.25rem 0 0;
  }

  .gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
    width: 100%;
  }

  .gallery-card {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--color-border-primary);
    border-radius: var(--border-radius-lg);
    background: var(--color-background-primary);
    padding: 1rem;
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s, box-shadow 0.15s;
    font-family: inherit;
    font-size: inherit;
    color: inherit;
  }

  .gallery-card:hover {
    border-color: var(--color-accent);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .gallery-card:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 2px var(--claude-selection);
  }

  .card-icon {
    display: flex;
    justify-content: center;
    margin-bottom: 0.75rem;
    color: var(--color-text-secondary);
  }

  .card-body {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .card-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--color-text-primary);
  }

  .card-description {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-badge {
    display: inline-block;
    font-size: 0.7rem;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    background: var(--color-background-tertiary);
    color: var(--color-text-secondary);
    margin-top: 0.25rem;
    align-self: flex-start;
  }

  .gallery-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: var(--color-text-secondary);
    padding: 3rem;
  }

  .spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--color-border-primary);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .gallery-empty {
    text-align: center;
    padding: 3rem;
    color: var(--color-text-secondary);
  }
</style>
