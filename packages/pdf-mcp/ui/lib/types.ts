/**
 * Type definitions for the PDF Viewer MCP App.
 */

// ---------------------------------------------------------------------------
// Annotation Types (matches the reference pdf-annotations.ts)
// ---------------------------------------------------------------------------

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface AnnotationBase {
  id: string;
  page: number;
}

export interface HighlightAnnotation extends AnnotationBase {
  type: "highlight";
  rects: Rect[];
  color?: string;
  content?: string;
}

export interface UnderlineAnnotation extends AnnotationBase {
  type: "underline";
  rects: Rect[];
  color?: string;
}

export interface StrikethroughAnnotation extends AnnotationBase {
  type: "strikethrough";
  rects: Rect[];
  color?: string;
}

export interface NoteAnnotation extends AnnotationBase {
  type: "note";
  x: number;
  y: number;
  content: string;
  color?: string;
}

export interface RectangleAnnotation extends AnnotationBase {
  type: "rectangle";
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  fillColor?: string;
  rotation?: number;
}

export interface CircleAnnotation extends AnnotationBase {
  type: "circle";
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  fillColor?: string;
}

export interface LineAnnotation extends AnnotationBase {
  type: "line";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
}

export interface FreetextAnnotation extends AnnotationBase {
  type: "freetext";
  x: number;
  y: number;
  content: string;
  fontSize?: number;
  color?: string;
}

export interface StampAnnotation extends AnnotationBase {
  type: "stamp";
  x: number;
  y: number;
  label: string;
  color?: string;
  rotation?: number;
}

export interface ImageAnnotation extends AnnotationBase {
  type: "image";
  x: number;
  y: number;
  width: number;
  height: number;
  imageData?: string;
  imageUrl?: string;
  mimeType?: string;
  rotation?: number;
}

export type PdfAnnotationDef =
  | HighlightAnnotation
  | UnderlineAnnotation
  | StrikethroughAnnotation
  | NoteAnnotation
  | RectangleAnnotation
  | CircleAnnotation
  | LineAnnotation
  | FreetextAnnotation
  | StampAnnotation
  | ImageAnnotation;

// ---------------------------------------------------------------------------
// Viewer State
// ---------------------------------------------------------------------------

export interface PdfViewerData {
  viewId: string;
  url: string;
  title: string;
  sourceUrl: string;
  currentPage: number;
  totalPages: number;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SearchMatch {
  pageIndex: number;
  matchIndex: number;
}

// ---------------------------------------------------------------------------
// Tracked Annotation (annotation + its DOM elements)
// ---------------------------------------------------------------------------

export interface TrackedAnnotation {
  def: PdfAnnotationDef;
  elements: HTMLElement[];
}

// ---------------------------------------------------------------------------
// Gallery
// ---------------------------------------------------------------------------

export interface GalleryItem {
  url: string;
  title: string;
  description: string;
  thumbnail_url?: string;
  category?: string;
}
