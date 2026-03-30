/**
 * Annotation persistence — diff-based model for localStorage.
 * Stores only changes relative to the PDF's native annotations.
 */

import type { PdfAnnotationDef, Rect } from "./types";

// ---------------------------------------------------------------------------
// Diff Model
// ---------------------------------------------------------------------------

export interface AnnotationDiff {
  added: PdfAnnotationDef[];
  removed: string[];
  formFields: Record<string, string | boolean>;
}

export function emptyDiff(): AnnotationDiff {
  return { added: [], removed: [], formFields: {} };
}

export function isDiffEmpty(diff: AnnotationDiff): boolean {
  return (
    diff.added.length === 0 &&
    diff.removed.length === 0 &&
    Object.keys(diff.formFields).length === 0
  );
}

export function serializeDiff(diff: AnnotationDiff): string {
  return JSON.stringify(diff);
}

export function deserializeDiff(json: string): AnnotationDiff {
  try {
    const parsed = JSON.parse(json);
    return {
      added: Array.isArray(parsed.added) ? parsed.added : [],
      removed: Array.isArray(parsed.removed) ? parsed.removed : [],
      formFields:
        parsed.formFields && typeof parsed.formFields === "object"
          ? parsed.formFields
          : {},
    };
  } catch {
    return emptyDiff();
  }
}

export function mergeAnnotations(
  pdfAnnotations: PdfAnnotationDef[],
  diff: AnnotationDiff,
): PdfAnnotationDef[] {
  const removedSet = new Set(diff.removed);
  const merged = pdfAnnotations.filter((a) => !removedSet.has(a.id));
  const addedIds = new Set(diff.added.map((a) => a.id));
  const result = merged.filter((a) => !addedIds.has(a.id));
  result.push(...diff.added);
  return result;
}

export function computeDiff(
  pdfAnnotations: PdfAnnotationDef[],
  currentAnnotations: PdfAnnotationDef[],
  formFields: Map<string, string | boolean>,
  baselineFormFields?: Map<string, string | boolean>,
): AnnotationDiff {
  const pdfIds = new Set(pdfAnnotations.map((a) => a.id));
  const currentIds = new Set(currentAnnotations.map((a) => a.id));

  const added = currentAnnotations.filter((a) => !pdfIds.has(a.id));
  const removed = pdfAnnotations
    .filter((a) => !currentIds.has(a.id))
    .map((a) => a.id);

  const formFieldsObj: Record<string, string | boolean> = {};
  for (const [k, v] of formFields) {
    if (baselineFormFields?.get(k) === v) continue;
    formFieldsObj[k] = v;
  }
  if (baselineFormFields) {
    for (const [k, v] of baselineFormFields) {
      if (!formFields.has(k) && v !== "" && v !== false) {
        formFieldsObj[k] = formFields.get(k) ?? "";
      }
    }
  }

  return { added, removed, formFields: formFieldsObj };
}

// ---------------------------------------------------------------------------
// Color Helpers
// ---------------------------------------------------------------------------

export function cssColorToRgb(
  color: string,
): { r: number; g: number; b: number } | null {
  const hex = color.match(/^#([0-9a-f]{3,8})$/i);
  if (hex) {
    let h = hex[1];
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return {
      r: parseInt(h.slice(0, 2), 16) / 255,
      g: parseInt(h.slice(2, 4), 16) / 255,
      b: parseInt(h.slice(4, 6), 16) / 255,
    };
  }
  const rgbMatch = color.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  if (rgbMatch) {
    return {
      r: parseInt(rgbMatch[1]) / 255,
      g: parseInt(rgbMatch[2]) / 255,
      b: parseInt(rgbMatch[3]) / 255,
    };
  }
  return null;
}

export function defaultColor(type: PdfAnnotationDef["type"]): string {
  switch (type) {
    case "highlight": return "#ffff00";
    case "underline":
    case "strikethrough": return "#ff0000";
    case "note": return "#f5a623";
    case "rectangle":
    case "circle": return "#0066cc";
    case "line":
    case "freetext": return "#333333";
    case "stamp": return "#cc0000";
    case "image": return "#00000000";
  }
}

// ---------------------------------------------------------------------------
// PDF.js Annotation Import
// ---------------------------------------------------------------------------

const PDFJS_TYPE_MAP: Record<number, PdfAnnotationDef["type"]> = {
  1: "note",
  3: "freetext",
  4: "line",
  5: "rectangle",
  6: "circle",
  9: "highlight",
  10: "underline",
  12: "strikethrough",
  13: "stamp",
};

function pdfjsColorToHex(
  color: Uint8ClampedArray | number[] | null | undefined,
): string | undefined {
  if (!color || color.length < 3) return undefined;
  const r = Math.round(color[0]);
  const g = Math.round(color[1]);
  const b = Math.round(color[2]);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

function pdfjsRectToRect(rect: number[]): Rect {
  return {
    x: Math.min(rect[0], rect[2]),
    y: Math.min(rect[1], rect[3]),
    width: Math.abs(rect[2] - rect[0]),
    height: Math.abs(rect[3] - rect[1]),
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function importPdfjsAnnotation(
  ann: any,
  pageNum: number,
  index: number,
): PdfAnnotationDef | null {
  const ourType = PDFJS_TYPE_MAP[ann.annotationType];
  if (!ourType) return null;
  if (ann.annotationType === 20) return null; // form widget

  const id = ann.ref
    ? `pdf-${ann.ref.num}-${ann.ref.gen}`
    : ann.id
      ? `pdf-${ann.id}`
      : `pdf-${pageNum}-${index}`;
  const color = pdfjsColorToHex(ann.color);

  switch (ourType) {
    case "highlight":
    case "underline":
    case "strikethrough": {
      let rects: Rect[];
      if (ann.quadPoints?.length > 0) {
        rects = [];
        for (const qp of ann.quadPoints) {
          if (qp.length >= 8) {
            const xs = [qp[0], qp[2], qp[4], qp[6]];
            const ys = [qp[1], qp[3], qp[5], qp[7]];
            rects.push({
              x: Math.min(...xs),
              y: Math.min(...ys),
              width: Math.max(...xs) - Math.min(...xs),
              height: Math.max(...ys) - Math.min(...ys),
            });
          }
        }
      } else if (ann.rect) {
        rects = [pdfjsRectToRect(ann.rect)];
      } else {
        return null;
      }
      if (rects.length === 0) return null;
      const base = { id, page: pageNum, rects, color };
      if (ourType === "highlight") {
        return { ...base, type: "highlight", content: ann.contentsObj?.str || undefined };
      }
      return { ...base, type: ourType } as PdfAnnotationDef;
    }
    case "note": {
      if (!ann.rect) return null;
      const rect = pdfjsRectToRect(ann.rect);
      return { type: "note", id, page: pageNum, x: rect.x, y: rect.y + rect.height, content: ann.contentsObj?.str || "", color };
    }
    case "rectangle":
    case "circle": {
      if (!ann.rect) return null;
      const rect = pdfjsRectToRect(ann.rect);
      return { type: ourType, id, page: pageNum, x: rect.x, y: rect.y, width: rect.width, height: rect.height, color } as PdfAnnotationDef;
    }
    case "line": {
      if (ann.lineCoordinates?.length >= 4) {
        return { type: "line", id, page: pageNum, x1: ann.lineCoordinates[0], y1: ann.lineCoordinates[1], x2: ann.lineCoordinates[2], y2: ann.lineCoordinates[3], color };
      }
      if (!ann.rect) return null;
      const r = pdfjsRectToRect(ann.rect);
      return { type: "line", id, page: pageNum, x1: r.x, y1: r.y, x2: r.x + r.width, y2: r.y + r.height, color };
    }
    case "freetext": {
      if (!ann.rect) return null;
      const rect = pdfjsRectToRect(ann.rect);
      return { type: "freetext", id, page: pageNum, x: rect.x, y: rect.y + rect.height, content: ann.contentsObj?.str || "", fontSize: ann.fontSize || 12, color };
    }
    case "stamp": {
      if (!ann.rect) return null;
      const rect = pdfjsRectToRect(ann.rect);
      return { type: "stamp", id, page: pageNum, x: rect.x, y: rect.y + rect.height, label: ann.name || ann.contentsObj?.str || "STAMP", color };
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Base64 Helpers
// ---------------------------------------------------------------------------

export function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export function uint8ArrayToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
