/**
 * Svelte action for drag-resize handles.
 *
 * Attaches pointer events to the element and computes width deltas
 * based on which edge the handle sits on.
 */
interface ResizeHandleOpts {
  edge: "left" | "right";
  min: number;
  max: number;
  onResize: (width: number) => void;
  onResizeStart?: () => void;
  onResizeEnd?: () => void;
}

export function resizeHandle(
  element: HTMLElement,
  opts: ResizeHandleOpts,
): { update(opts: ResizeHandleOpts): void; destroy(): void } {
  let current = opts;
  let dragStartX = 0;
  let dragStartWidth = 0;
  let dragging = false;

  function onPointerDown(e: PointerEvent) {
    e.preventDefault();
    dragging = true;
    dragStartX = e.clientX;
    // Read the parent's computed content width (matches the style:width prop)
    dragStartWidth = parseFloat(getComputedStyle(element.parentElement!).width) || 0;
    element.setPointerCapture(e.pointerId);
    current.onResizeStart?.();
  }

  function onPointerMove(e: PointerEvent) {
    if (!dragging) return;
    const delta =
      current.edge === "right"
        ? e.clientX - dragStartX
        : dragStartX - e.clientX;
    const newWidth = Math.max(current.min, Math.min(current.max, dragStartWidth + delta));
    current.onResize(newWidth);
  }

  function onPointerUp(e: PointerEvent) {
    if (!dragging) return;
    dragging = false;
    element.releasePointerCapture(e.pointerId);
    current.onResizeEnd?.();
  }

  element.addEventListener("pointerdown", onPointerDown);
  element.addEventListener("pointermove", onPointerMove);
  element.addEventListener("pointerup", onPointerUp);

  return {
    update(newOpts) {
      current = newOpts;
    },
    destroy() {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointermove", onPointerMove);
      element.removeEventListener("pointerup", onPointerUp);
    },
  };
}
