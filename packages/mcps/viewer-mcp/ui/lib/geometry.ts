/**
 * Pure geometry helpers for ALTO polygon hit-testing and coordinate transforms.
 */

import type { TextLine } from "./types";

/** Parsed polygon ready for hit-testing */
export interface PolygonHit {
  lineId: string;
  points: number[];
  /** Axis-aligned bounds [minX, minY, maxX, maxY] derived from `points` — used to cheaply
   *  reject a point before the O(vertices) ray-cast on the hover hot path. */
  bbox: [number, number, number, number];
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
    // Bounding-box reject first: this runs on every hover mousemove over a page with
    // hundreds of lines, and the AABB test (4 comparisons) rejects almost all of them
    // without paying for the ray-cast.
    const [minX, minY, maxX, maxY] = p.bbox;
    if (imgX < minX || imgX > maxX || imgY < minY || imgY > maxY) continue;
    if (pointInPolygon(imgX, imgY, p.points)) return p;
  }
  return null;
}

/** Compute axis-aligned bounds [minX, minY, maxX, maxY] from flat [x,y,...] points. */
function pointsBBox(points: number[]): [number, number, number, number] {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (let i = 0; i < points.length; i += 2) {
    const x = points[i], y = points[i + 1];
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  return [minX, minY, maxX, maxY];
}

/** Build PolygonHit array from ALTO text lines (filters lines with <6 polygon points) */
export function buildPolygonHits(textLines: TextLine[]): PolygonHit[] {
  const hits: PolygonHit[] = [];
  for (const line of textLines) {
    const points = parsePolygonPoints(line.polygon);
    if (points.length >= 6) {
      hits.push({ lineId: line.id, points, bbox: pointsBBox(points), line });
    }
  }
  return hits;
}
