/**
 * PDF.js wrapper — initialization, page rendering, text layer.
 */

import * as pdfjsLib from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";
import { TextLayer } from "pdfjs-dist";

// Configure worker — use inline fallback for CSP-restricted environments
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export { type PDFDocumentProxy, type PDFPageProxy };

const CMAP_URL = "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.0.0/cmaps/";

/**
 * Load a PDF from a Uint8Array.
 */
export async function loadPdfFromBytes(data: Uint8Array): Promise<PDFDocumentProxy> {
  const loadingTask = pdfjsLib.getDocument({
    data,
    cMapUrl: CMAP_URL,
    cMapPacked: true,
    enableXfa: true,
  });
  return loadingTask.promise;
}



/**
 * Render a PDF page to a canvas.
 */
export async function renderPage(
  page: PDFPageProxy,
  canvas: HTMLCanvasElement,
  scale: number,
  devicePixelRatio: number = window.devicePixelRatio || 1,
): Promise<{ width: number; height: number }> {
  const viewport = page.getViewport({ scale: scale * devicePixelRatio });
  const displayViewport = page.getViewport({ scale });

  canvas.width = viewport.width;
  canvas.height = viewport.height;
  canvas.style.width = `${displayViewport.width}px`;
  canvas.style.height = `${displayViewport.height}px`;

  const ctx = canvas.getContext("2d")!;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Cancel any previous render on this canvas
  if ((canvas as any).__renderTask) {
    (canvas as any).__renderTask.cancel();
  }

  const renderTask = page.render({
    canvasContext: ctx,
    viewport,
    canvas,
  });
  (canvas as any).__renderTask = renderTask;

  try {
    await renderTask.promise;
  } catch (e: any) {
    if (e?.name === "RenderingCancelledException") return { width: 0, height: 0 };
    throw e;
  } finally {
    if ((canvas as any).__renderTask === renderTask) {
      (canvas as any).__renderTask = null;
    }
  }

  return { width: displayViewport.width, height: displayViewport.height };
}

/**
 * Build a text layer on top of the canvas for text selection.
 */
export async function buildTextLayer(
  page: PDFPageProxy,
  container: HTMLDivElement,
  scale: number,
): Promise<void> {
  container.innerHTML = "";

  const textContent = await page.getTextContent();
  const viewport = page.getViewport({ scale });

  container.style.width = `${viewport.width}px`;
  container.style.height = `${viewport.height}px`;

  const textLayer = new TextLayer({
    textContentSource: textContent,
    container,
    viewport,
  });

  await textLayer.render();
}


// ---------------------------------------------------------------------------
// Outline (Table of Contents)
// ---------------------------------------------------------------------------

export interface OutlineItem {
  title: string;
  pageNum: number | null;
  items: OutlineItem[];
}

/**
 * Extract the PDF outline (bookmarks/TOC) as a tree of items with page numbers.
 * Returns null if the PDF has no outline.
 */
export async function getOutline(doc: PDFDocumentProxy): Promise<OutlineItem[] | null> {
  const outline = await doc.getOutline();
  if (!outline || outline.length === 0) return null;

  async function resolveItem(item: any): Promise<OutlineItem> {
    let pageNum: number | null = null;
    try {
      let dest = item.dest;
      if (typeof dest === "string") {
        dest = await doc.getDestination(dest);
      }
      if (Array.isArray(dest) && dest.length > 0) {
        const pageIndex = await doc.getPageIndex(dest[0]);
        pageNum = pageIndex + 1;
      }
    } catch { /* dest resolution can fail for malformed PDFs */ }

    const children: OutlineItem[] = [];
    if (item.items?.length > 0) {
      for (const child of item.items) {
        children.push(await resolveItem(child));
      }
    }

    return { title: item.title || "Untitled", pageNum, items: children };
  }

  const result: OutlineItem[] = [];
  for (const item of outline) {
    result.push(await resolveItem(item));
  }
  return result;
}

// ---------------------------------------------------------------------------
// Thumbnails
// ---------------------------------------------------------------------------

/**
 * Render a page thumbnail as a data URL.
 * Reuses a single offscreen canvas with a mutex to serialize concurrent
 * renders (PDF.js can't render to the same canvas simultaneously).
 */
let _thumbCanvas: HTMLCanvasElement | null = null;
let _thumbQueue: Promise<void> = Promise.resolve();

export async function renderThumbnail(
  doc: PDFDocumentProxy,
  pageNum: number,
  maxWidth: number = 120,
): Promise<string> {
  // Queue this render after any in-flight one finishes
  let dataUrl: string;
  const work = _thumbQueue.then(async () => {
    const page = await doc.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1 });
    const thumbScale = maxWidth / viewport.width;
    const thumbViewport = page.getViewport({ scale: thumbScale });

    if (!_thumbCanvas) _thumbCanvas = document.createElement("canvas");
    _thumbCanvas.width = thumbViewport.width;
    _thumbCanvas.height = thumbViewport.height;
    const ctx = _thumbCanvas.getContext("2d")!;

    await page.render({
      canvasContext: ctx,
      viewport: thumbViewport,
      canvas: _thumbCanvas,
    }).promise;

    dataUrl = _thumbCanvas.toDataURL("image/jpeg", 0.6);
  });
  _thumbQueue = work.catch(() => {}); // don't block queue on errors
  await work;
  return dataUrl!;
}
