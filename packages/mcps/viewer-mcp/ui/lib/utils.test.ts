import { describe, it, expect } from "vitest";
import { parsePageResult, parseThumbnailResult } from "./utils";

// Minimal CallToolResult-shaped fixture — the real type is erased at build time, so we
// avoid importing the SDK here and just build the shape the parsers read.
function result(structuredContent?: unknown, text?: string): any {
  const r: any = { content: text !== undefined ? [{ type: "text", text }] : [] };
  if (structuredContent !== undefined) r.structuredContent = structuredContent;
  return r;
}

describe("parsePageResult", () => {
  const page = { index: 0, imageDataUrl: "u", textLayer: { textLines: [], pageWidth: 100, pageHeight: 200 } };

  it("reads page from structuredContent", () => {
    expect(parsePageResult(result({ page }))).toEqual(page);
  });

  it("falls back to parsing the first text block as JSON", () => {
    expect(parsePageResult(result(undefined, JSON.stringify({ page })))).toEqual(page);
  });

  it("returns null when there is no page / no content / bad json", () => {
    expect(parsePageResult(result({ notpage: 1 }))).toBeNull();
    expect(parsePageResult(result(undefined, "not json"))).toBeNull();
    expect(parsePageResult(result())).toBeNull();
  });
});

describe("parseThumbnailResult", () => {
  it("reads the thumbnails array from structuredContent", () => {
    const thumbnails = [{ index: 0, dataUrl: "a" }, { index: 1, dataUrl: "b" }];
    expect(parseThumbnailResult(result({ thumbnails }))).toEqual(thumbnails);
  });

  it("falls back to the text block, and returns [] when absent", () => {
    const thumbnails = [{ index: 0, dataUrl: "x" }];
    expect(parseThumbnailResult(result(undefined, JSON.stringify({ thumbnails })))).toEqual(thumbnails);
    expect(parseThumbnailResult(result({}))).toEqual([]);
    expect(parseThumbnailResult(result(undefined, "nope"))).toEqual([]);
  });
});
