/**
 * Pure geometry helpers for ALTO polygon hit-testing and coordinate transforms.
 */

import type { TextLine } from "./types";

/** Parsed polygon ready for hit-testing */
export interface PolygonHit {
  lineId: string;
  points: number[];
  line: TextLine;
}

/** Parse ALTO polygon "x1,y1 x2,y2 ..." into flat [x1,y1,x2,y2,...] */
export function parsePolygonPoints(polygon: string): number[] {
  const pts: number[] = [];
  for (const pair of polygon.trim().split(/\s+/)) {
    const [x, y] = pair.split(",").map(Number);
    if (!isNaN(x) && !isNaN(y)) pts.push(x, y);
  }
  return pts;
}

/** Ray-casting point-in-polygon test */
export function pointInPolygon(px: number, py: number, pts: number[]): boolean {
  let inside = false;
  for (let i = 0, j = pts.length - 2; i < pts.length; j = i, i += 2) {
    const xi = pts[i], yi = pts[i + 1];
    const xj = pts[j], yj = pts[j + 1];
    if (yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/** Find which polygon (text line) contains the given image-space coordinate */
export function findHitAtImageCoord(
  imgX: number,
  imgY: number,
  polygons: PolygonHit[],
): PolygonHit | null {
  for (const p of polygons) {
    if (pointInPolygon(imgX, imgY, p.points)) return p;
  }
  return null;
}

/** Build PolygonHit array from ALTO text lines (filters lines with <6 polygon points) */
export function buildPolygonHits(textLines: TextLine[]): PolygonHit[] {
  const hits: PolygonHit[] = [];
  for (const line of textLines) {
    const points = parsePolygonPoints(line.polygon);
    if (points.length >= 6) {
      hits.push({ lineId: line.id, points, line });
    }
  }
  return hits;
}
