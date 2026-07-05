import { describe, it, expect } from "vitest";
import {
  parsePolygonPoints,
  pointInPolygon,
  buildPolygonHits,
  findHitAtImageCoord,
} from "./geometry";
import type { TextLine } from "./types";

function line(id: string, polygon: string, bbox?: Partial<TextLine>): TextLine {
  return { id, polygon, transcription: id, hpos: 0, vpos: 0, width: 0, height: 0, ...bbox };
}

describe("parsePolygonPoints", () => {
  it("parses 'x,y x,y' pairs into a flat [x,y,...] array", () => {
    expect(parsePolygonPoints("10,20 30,40 50,60")).toEqual([10, 20, 30, 40, 50, 60]);
  });

  it("tolerates extra whitespace and skips malformed pairs", () => {
    expect(parsePolygonPoints("  10,20   bad 30,40  ")).toEqual([10, 20, 30, 40]);
  });
});

describe("pointInPolygon", () => {
  const square = [0, 0, 100, 0, 100, 100, 0, 100];

  it("is true strictly inside", () => {
    expect(pointInPolygon(50, 50, square)).toBe(true);
  });

  it("is false clearly outside", () => {
    expect(pointInPolygon(150, 50, square)).toBe(false);
    expect(pointInPolygon(50, 150, square)).toBe(false);
  });
});

describe("buildPolygonHits", () => {
  it("keeps lines with >=6 points and derives the bbox from the points", () => {
    const hits = buildPolygonHits([
      line("a", "0,0 100,0 100,50 0,50"), // 8 coords
      line("b", "0,0 10,0"), // 4 coords -> filtered out
    ]);
    expect(hits.map((h) => h.lineId)).toEqual(["a"]);
    // bbox is [minX, minY, maxX, maxY] computed from the polygon, not the (0-defaulted) hpos/width.
    expect(hits[0].bbox).toEqual([0, 0, 100, 50]);
  });

  it("computes the bbox as the true extent of arbitrary points", () => {
    const [h] = buildPolygonHits([line("z", "30,10 90,25 70,80 20,60")]);
    expect(h.bbox).toEqual([20, 10, 90, 80]);
  });
});

describe("findHitAtImageCoord (bbox-reject fast path)", () => {
  const hits = buildPolygonHits([
    line("top", "0,0 100,0 100,50 0,50"),
    line("bottom", "0,60 100,60 100,110 0,110"),
  ]);

  it("returns the polygon that contains the point", () => {
    expect(findHitAtImageCoord(50, 25, hits)?.lineId).toBe("top");
    expect(findHitAtImageCoord(50, 80, hits)?.lineId).toBe("bottom");
  });

  it("returns null in the gap between polygons", () => {
    expect(findHitAtImageCoord(50, 55, hits)).toBeNull();
  });

  it("returns null far outside every bbox", () => {
    expect(findHitAtImageCoord(500, 500, hits)).toBeNull();
  });

  it("the bbox reject never changes the result vs a pure ray-cast scan", () => {
    // Cross-check the optimized path against a brute-force pointInPolygon scan over a
    // grid, so the AABB pre-reject can't silently drop a real hit.
    const brute = (x: number, y: number) => hits.find((h) => pointInPolygon(x, y, h.points))?.lineId ?? null;
    for (let x = -20; x <= 120; x += 7) {
      for (let y = -20; y <= 130; y += 7) {
        expect(findHitAtImageCoord(x, y, hits)?.lineId ?? null).toBe(brute(x, y));
      }
    }
  });
});
