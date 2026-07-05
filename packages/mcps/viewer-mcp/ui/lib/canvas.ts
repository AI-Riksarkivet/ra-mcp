/**
 * CanvasController — reusable pan/zoom/transform/draw infrastructure.
 *
 * Owns: transform state, pointer handling (pan + inertia), smooth zoom,
 * ResizeObserver, IntersectionObserver (visibility-aware rendering), RAF scheduling.
 *
 * Domain-specific rendering (e.g. ALTO polygon overlays) is delegated via callbacks.
 */

export interface Transform {
  x: number;
  y: number;
  scale: number;
}

export interface CanvasCallbacks {
  /** Called after the image is drawn — context is still in image-space transform. */
  onAfterDraw?: (ctx: CanvasRenderingContext2D, transform: Transform) => void;
  /** Called on click (non-drag pointer up) with image-space coordinates. */
  onClickImage?: (imgX: number, imgY: number) => void;
  /** Called on hover (non-drag move) with image + screen coords. Return cursor string or null for default "grab". */
  onHoverImage?: (imgX: number, imgY: number, screenX: number, screenY: number) => string | null;
  /** Called when pointer leaves the canvas. */
  onPointerLeave?: () => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MIN_SCALE = 0.1;
const MAX_SCALE = 10;
const ZOOM_SPEED = 0.003;
const ZOOM_LERP = 0.25;
const PAN_FRICTION = 0.92;

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

export class CanvasController {
  transform: Transform = { x: 0, y: 0, scale: 1 };

  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private callbacks: CanvasCallbacks;
  private image: HTMLImageElement | null = null;

  // The coordinate space overlays/hit-testing use — the ALTO page dimensions, which
  // differ from the (downscaled 1500px) IIIF image. The image is drawn stretched to
  // this size so image-space == overlay-space; falls back to the image's own size when
  // there is no text layer.
  private contentWidth = 0;
  private contentHeight = 0;

  // Pointer state for pan + click detection
  private pointerDown: { x: number; y: number; tx: number; ty: number } | null = null;
  private dragged = false;
  private panVelocity = { vx: 0, vy: 0 };
  private lastPointerPos = { x: 0, y: 0, t: 0 };
  private panInertiaId = 0;

  // True during active pan/zoom motion. While interacting, draw() blits only the
  // image (fast) and skips the overlay repaint; overlays are painted once when
  // motion settles. Removes per-frame re-stroking of every ALTO polygon.
  private interacting = false;

  // Smooth zoom animation state
  private targetScale = 1;
  private zoomAnimating = false;
  private zoomCenterX = 0;
  private zoomCenterY = 0;

  // Animation frame handles
  private rafId = 0;
  private zoomRafId = 0;

  // Visibility-aware rendering (pause when off-screen)
  private isVisible = true;
  private pendingDraw = false;

  // Observers
  private resizeObserver: ResizeObserver;
  private visibilityObserver: IntersectionObserver;

  constructor(
    canvas: HTMLCanvasElement,
    container: HTMLElement,
    wrapper: HTMLElement,
    callbacks: CanvasCallbacks = {},
  ) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
    this.callbacks = callbacks;

    this.resizeObserver = new ResizeObserver(() => {
      if (this.image) {
        this.fitToCanvas();
        this.draw();
      }
    });
    this.resizeObserver.observe(container);

    // Pause canvas rendering when scrolled out of view
    this.visibilityObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        this.isVisible = entry.isIntersecting;
        if (this.isVisible && this.pendingDraw) {
          this.pendingDraw = false;
          this.requestDraw();
        }
      }
    });
    this.visibilityObserver.observe(wrapper);
  }

  // -------------------------------------------------------------------------
  // Public API
  // -------------------------------------------------------------------------

  /**
   * Set the page image. `contentWidth`/`contentHeight` are the ALTO page dimensions
   * (the coordinate space of the polygon overlays and hit-testing); pass 0 to use the
   * image's own pixel size. The image is drawn stretched to that content size so the
   * overlays — which are in native ALTO coordinates — line up with the scan.
   */
  setImage(img: HTMLImageElement, contentWidth = 0, contentHeight = 0): void {
    this.image = img;
    this.contentWidth = contentWidth > 0 ? contentWidth : img.naturalWidth;
    this.contentHeight = contentHeight > 0 ? contentHeight : img.naturalHeight;
    this.fitToCanvas();
    this.draw();
  }

  /** Check if an image-space point is within the visible canvas area. */
  isPointVisible(imgX: number, imgY: number, margin = 50): boolean {
    if (!this.canvas) return false;
    const screenX = imgX * this.transform.scale + this.transform.x;
    const screenY = imgY * this.transform.scale + this.transform.y;
    const cw = this.canvas.clientWidth;
    const ch = this.canvas.clientHeight;
    return screenX >= margin && screenX <= cw - margin &&
           screenY >= margin && screenY <= ch - margin;
  }

  /** Reset the view to fit the image in the canvas. */
  resetView(): void {
    this.fitToCanvas();
    this.draw();
  }

  /** Pan so that the given image-space point is centered on the canvas. */
  centerOn(imgX: number, imgY: number): void {
    if (!this.canvas) return;
    const cw = this.canvas.clientWidth;
    const ch = this.canvas.clientHeight;
    this.transform.x = cw / 2 - imgX * this.transform.scale;
    this.transform.y = ch / 2 - imgY * this.transform.scale;
    this.targetScale = this.transform.scale;
    this.draw();
  }

  /** Zoom and pan so the given image-space rectangle fills the viewport with padding. */
  zoomToRect(x: number, y: number, w: number, h: number, padding = 40): void {
    if (!this.canvas) return;
    const cw = this.canvas.clientWidth;
    const ch = this.canvas.clientHeight;
    const scaleX = (cw - padding * 2) / w;
    const scaleY = (ch - padding * 2) / h;
    const scale = Math.min(scaleX, scaleY);
    const cx = x + w / 2;
    const cy = y + h / 2;
    this.transform.scale = scale;
    this.transform.x = cw / 2 - cx * scale;
    this.transform.y = ch / 2 - cy * scale;
    this.targetScale = scale;
    this.draw();
  }

  requestDraw(): void {
    if (!this.isVisible) {
      this.pendingDraw = true;
      return;
    }
    if (!this.rafId) {
      this.rafId = requestAnimationFrame(() => {
        this.rafId = 0;
        this.draw();
      });
    }
  }

  destroy(): void {
    this.resizeObserver.disconnect();
    this.visibilityObserver.disconnect();
    if (this.rafId) cancelAnimationFrame(this.rafId);
    if (this.panInertiaId) cancelAnimationFrame(this.panInertiaId);
    if (this.zoomRafId) cancelAnimationFrame(this.zoomRafId);
    this.zoomAnimating = false;
    this.image = null;
  }

  // -------------------------------------------------------------------------
  // Event handlers — bind these to canvas events in the component
  // -------------------------------------------------------------------------

  handlePointerDown = (e: PointerEvent): void => {
    if (e.button !== 0) return;
    // Cancel any ongoing inertia animation
    if (this.panInertiaId) {
      cancelAnimationFrame(this.panInertiaId);
      this.panInertiaId = 0;
    }
    this.pointerDown = {
      x: e.clientX,
      y: e.clientY,
      tx: this.transform.x,
      ty: this.transform.y,
    };
    this.dragged = false;
    this.panVelocity = { vx: 0, vy: 0 };
    this.lastPointerPos = { x: e.clientX, y: e.clientY, t: performance.now() };
    this.canvas.setPointerCapture(e.pointerId);
  };

  handlePointerMove = (e: PointerEvent): void => {
    if (this.pointerDown) {
      const dx = e.clientX - this.pointerDown.x;
      const dy = e.clientY - this.pointerDown.y;
      if (dx * dx + dy * dy > 9) this.dragged = true;
      this.transform.x = this.pointerDown.tx + dx;
      this.transform.y = this.pointerDown.ty + dy;

      // Track velocity for inertia
      const now = performance.now();
      const dt = now - this.lastPointerPos.t;
      if (dt > 0) {
        this.panVelocity.vx = (e.clientX - this.lastPointerPos.x) / dt;
        this.panVelocity.vy = (e.clientY - this.lastPointerPos.y) / dt;
      }
      this.lastPointerPos = { x: e.clientX, y: e.clientY, t: now };

      this.interacting = true;
      this.requestDraw();
      return;
    }

    // Hover — delegate to callback. getBoundingClientRect() (a forced layout
    // reflow) is read here only, NOT on the pan-drag hot path above where its
    // result would be discarded.
    if (this.callbacks.onHoverImage) {
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const imgX = (cx - this.transform.x) / this.transform.scale;
      const imgY = (cy - this.transform.y) / this.transform.scale;
      const cursor = this.callbacks.onHoverImage(imgX, imgY, e.clientX, e.clientY);
      this.canvas.style.cursor = cursor ?? "grab";
    }
  };

  handlePointerUp = (e: PointerEvent): void => {
    if (!this.pointerDown) return;
    const wasDrag = this.dragged;
    this.pointerDown = null;
    this.canvas.releasePointerCapture(e.pointerId);

    if (wasDrag) {
      // Apply inertia if velocity is meaningful; otherwise settle now (repaint overlays).
      const speed = Math.sqrt(this.panVelocity.vx ** 2 + this.panVelocity.vy ** 2);
      if (speed > 0.1) {
        this.applyPanInertia();
      } else {
        this.settle();
      }
      return;
    }

    // Click — repaint overlays (a sub-threshold move may have suppressed them),
    // then delegate to callback.
    this.settle();
    if (this.callbacks.onClickImage) {
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const imgX = (cx - this.transform.x) / this.transform.scale;
      const imgY = (cy - this.transform.y) / this.transform.scale;
      this.callbacks.onClickImage(imgX, imgY);
    }
  };

  handlePointerLeave = (): void => {
    this.callbacks.onPointerLeave?.();
  };

  handleWheel = (e: WheelEvent): void => {
    e.preventDefault();
    const rect = this.canvas.getBoundingClientRect();
    this.zoomCenterX = e.clientX - rect.left;
    this.zoomCenterY = e.clientY - rect.top;

    // Normalize deltaY across input devices:
    // - Mouse wheel: deltaMode=0 (pixels), large values (~100)
    // - Trackpad pinch: deltaMode=0 (pixels), small values (~1-10)
    // - Old-style wheel: deltaMode=1 (lines)
    let delta = -e.deltaY;
    if (e.deltaMode === 1) delta *= 20; // line mode -> approximate pixels

    const factor = Math.exp(delta * ZOOM_SPEED);
    this.targetScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, this.targetScale * factor));

    this.interacting = true;
    if (!this.zoomAnimating) {
      this.zoomAnimating = true;
      this.animateZoom();
    }
  };

  // -------------------------------------------------------------------------
  // Private
  // -------------------------------------------------------------------------

  private draw(): void {
    if (!this.canvas || !this.image) return;
    const ctx = this.ctx;

    const dpr = window.devicePixelRatio || 1;
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;

    if (this.canvas.width !== w * dpr || this.canvas.height !== h * dpr) {
      this.canvas.width = w * dpr;
      this.canvas.height = h * dpr;
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    ctx.save();
    ctx.translate(this.transform.x, this.transform.y);
    ctx.scale(this.transform.scale, this.transform.scale);

    ctx.drawImage(this.image, 0, 0, this.contentWidth, this.contentHeight);

    // Let the component draw overlays (polygons, etc.) in image space — but skip
    // them during active motion; they are repainted once when motion settles.
    if (!this.interacting) {
      this.callbacks.onAfterDraw?.(ctx, this.transform);
    }

    ctx.restore();
  }

  /** End an interaction and repaint once with overlays. */
  private settle(): void {
    this.interacting = false;
    this.draw();
  }

  private fitToCanvas(): void {
    if (!this.image || !this.canvas) return;
    const cw = this.canvas.clientWidth;
    const ch = this.canvas.clientHeight;
    if (cw === 0 || ch === 0) return;
    const padding = 8;
    const scaleX = (cw - padding * 2) / this.contentWidth;
    const scaleY = (ch - padding * 2) / this.contentHeight;
    // Allow scaling UP to fill the canvas, not just down
    this.transform.scale = Math.min(scaleX, scaleY);
    this.transform.x = (cw - this.contentWidth * this.transform.scale) / 2;
    this.transform.y = (ch - this.contentHeight * this.transform.scale) / 2;
    // Sync smooth zoom target so next scroll starts from fitted scale
    this.targetScale = this.transform.scale;
  }

  private applyPanInertia(): void {
    const step = () => {
      this.panVelocity.vx *= PAN_FRICTION;
      this.panVelocity.vy *= PAN_FRICTION;

      const speed = Math.sqrt(this.panVelocity.vx ** 2 + this.panVelocity.vy ** 2);
      if (speed < 0.02) {
        this.panInertiaId = 0;
        this.settle();
        return;
      }

      // velocity is px/ms, multiply by ~16ms frame time
      this.transform.x += this.panVelocity.vx * 16;
      this.transform.y += this.panVelocity.vy * 16;
      this.draw();
      this.panInertiaId = requestAnimationFrame(step);
    };

    this.panInertiaId = requestAnimationFrame(step);
  }

  private animateZoom = (): void => {
    if (!this.zoomAnimating) return;

    const diff = this.targetScale - this.transform.scale;

    // Close enough — snap and stop
    if (Math.abs(diff) < 0.001) {
      this.interacting = false; // so the final applyZoom draw repaints overlays
      this.applyZoom(this.targetScale);
      this.zoomAnimating = false;
      this.zoomRafId = 0;
      return;
    }

    const newScale = this.transform.scale + diff * ZOOM_LERP;
    this.applyZoom(newScale);

    this.zoomRafId = requestAnimationFrame(this.animateZoom);
  };

  private applyZoom(newScale: number): void {
    const clamped = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
    const ratio = clamped / this.transform.scale;
    this.transform.x = this.zoomCenterX - (this.zoomCenterX - this.transform.x) * ratio;
    this.transform.y = this.zoomCenterY - (this.zoomCenterY - this.transform.y) * ratio;
    this.transform.scale = clamped;
    this.draw(); // Draw immediately inside animation loop (no RAF scheduling needed)
  }
}
