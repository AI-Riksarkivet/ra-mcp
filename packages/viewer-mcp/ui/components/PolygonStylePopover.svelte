<script lang="ts">
import { onMount, onDestroy } from "svelte";

const SWATCHES = [
  "#c15f3c", // terracotta
  "#3b82f6", // blue
  "#10b981", // green
  "#f59e0b", // amber
  "#8b5cf6", // purple
  "#ef4444", // red
] as const;

interface Props {
  color: string;
  thickness: number;
  opacity: number;
  onChange: (key: string, value: string | number) => void;
  onClose: () => void;
}

let { color, thickness, opacity, onChange, onClose }: Props = $props();

let popoverEl: HTMLDivElement;

function onWindowClick(e: MouseEvent) {
  const target = e.target as Node;
  if (popoverEl && !popoverEl.contains(target)) {
    onClose();
  }
}

onMount(() => {
  window.addEventListener('click', onWindowClick, true);
});
onDestroy(() => {
  window.removeEventListener('click', onWindowClick, true);
});
</script>

<div class="style-popover" bind:this={popoverEl}>
  <div class="popover-section">
    <span class="popover-label">Color</span>
    <div class="swatches">
      {#each SWATCHES as swatch (swatch)}
        <button
          class="swatch"
          class:selected={color === swatch}
          style:background={swatch}
          onclick={() => onChange('color', swatch)}
          title={swatch}
        ></button>
      {/each}
    </div>
  </div>
  <div class="popover-section">
    <span class="popover-label">Thickness</span>
    <input
      type="range"
      min="0.5"
      max="5"
      step="0.5"
      value={thickness}
      oninput={(e) => onChange('thickness', parseFloat((e.target as HTMLInputElement).value))}
    />
  </div>
  <div class="popover-section">
    <span class="popover-label">Opacity</span>
    <input
      type="range"
      min="0.02"
      max="0.5"
      step="0.02"
      value={opacity}
      oninput={(e) => onChange('opacity', parseFloat((e.target as HTMLInputElement).value))}
    />
  </div>
</div>

<style>
.style-popover {
  position: absolute;
  right: 100%;
  top: 0;
  margin-right: 6px;
  width: 160px;
  padding: 8px;
  background: var(--color-background-primary, light-dark(#faf9f5, #1a1815));
  border-radius: var(--border-radius-md, 6px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 20;
}

.popover-section {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.popover-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-tertiary, light-dark(#999, #666));
}

.swatches {
  display: flex;
  gap: 4px;
}

.swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
  transition: border-color 0.15s;
}

.swatch:hover {
  border-color: var(--color-text-tertiary, light-dark(#999, #666));
}

.swatch.selected {
  border-color: var(--color-text-primary, light-dark(#1a1815, #faf9f5));
  box-shadow: 0 0 0 1.5px var(--color-background-primary, light-dark(#faf9f5, #1a1815));
}

.style-popover input[type="range"] {
  width: 100%;
  height: 4px;
  accent-color: var(--color-accent, #c15f3c);
  cursor: pointer;
}
</style>
