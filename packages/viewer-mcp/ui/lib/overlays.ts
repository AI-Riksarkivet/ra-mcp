/**
 * Polygon overlay drawing — pure functions, no Svelte dependencies.
 */

import type { PolygonHit } from "./geometry";
import type { Transform } from "./canvas";

export interface PolygonStyle {
  color: string;
  thickness: number;
  opacity: number;
}

export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Draw polygon overlays on a canvas context (already transformed to image space).
 */
export function drawPolygonOverlays(
  ctx: CanvasRenderingContext2D,
  transform: Transform,
  polygons: PolygonHit[],
  style: PolygonStyle,
  hoveredLineId: string | null,
): void {
  if (polygons.length === 0) return;

  // Pre-compute all RGBA strings once per frame (not per polygon)
  const fillNormal = hexToRgba(style.color, style.opacity);
  const fillHover = hexToRgba(style.color, Math.min(1, style.opacity * 2));
  const strokeNormal = hexToRgba(style.color, Math.min(1, style.opacity * 5));
  const strokeHover = hexToRgba(style.color, 1);
  const lineWidthNormal = style.thickness / transform.scale;
  const lineWidthHover = (style.thickness + 1) / transform.scale;

  for (const p of polygons) {
    const isHovered = p.lineId === hoveredLineId;

    ctx.beginPath();
    ctx.moveTo(p.points[0], p.points[1]);
    for (let i = 2; i < p.points.length; i += 2) {
      ctx.lineTo(p.points[i], p.points[i + 1]);
    }
    ctx.closePath();

    ctx.fillStyle = isHovered ? fillHover : fillNormal;
    ctx.fill();
    ctx.strokeStyle = isHovered ? strokeHover : strokeNormal;
    ctx.lineWidth = isHovered ? lineWidthHover : lineWidthNormal;
    ctx.stroke();
  }
}
