/**
 * Utility functions for the Document Viewer
 */

import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { PageData, ThumbnailData } from "./types";

/**
 * Extract structuredContent from a CallToolResult.
 * callServerTool responses should include it, but guard with a fallback
 * that tries to parse the first text content block as JSON.
 */
function getStructured(result: CallToolResult): Record<string, unknown> | null {
  const sc = (result as any).structuredContent;
  if (sc && typeof sc === "object") return sc;

  // Fallback: try parsing first text block as JSON
  const text = result.content?.find((c) => c.type === "text");
  if (text && "text" in text) {
    try {
      const parsed = JSON.parse(text.text);
      if (parsed && typeof parsed === "object") return parsed;
    } catch {
      // not JSON — ignore
    }
  }
  return null;
}

/**
 * Parse load_page tool result into a single PageData.
 */
export function parsePageResult(result: CallToolResult): PageData | null {
  const sc = getStructured(result);
  if (sc && "page" in sc) {
    return sc.page as PageData;
  }
  return null;
}

/**
 * Parse load_thumbnails tool result into ThumbnailData array.
 */
export function parseThumbnailResult(result: CallToolResult): ThumbnailData[] {
  const sc = getStructured(result);
  if (sc && "thumbnails" in sc) {
    return sc.thumbnails as ThumbnailData[];
  }
  return [];
}
