/**
 * PDF.js wrapper — initialization, page rendering, text layer.
 */

import * as pdfjsLib from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";
import { TextLayer } from "pdfjs-dist";

// Configure worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export { type PDFDocumentProxy, type PDFPageProxy };

/**
 * Load a PDF from a Uint8Array.
 */
export async function loadPdfFromBytes(data: Uint8Array): Promise<PDFDocumentProxy> {
  const loadingTask = pdfjsLib.getDocument({
    data,
    cMapUrl: "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.0.0/cmaps/",
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

  await page.render({
    canvasContext: ctx,
    viewport,
    canvas,
  }).promise;

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

/**
 * Extract plain text from a page.
 */
export async function extractPageText(page: PDFPageProxy): Promise<string> {
  const textContent = await page.getTextContent();
  return textContent.items
    .map((item: any) => ("str" in item ? item.str : ""))
    .join(" ");
}

/**
 * Search for text matches on a page. Returns array of match rects
 * in PDF coordinate space (for highlight overlay).
 */
export async function searchPageText(
  page: PDFPageProxy,
  query: string,
  scale: number,
): Promise<{ rects: DOMRect[]; count: number }> {
  if (!query) return { rects: [], count: 0 };

  const textContent = await page.getTextContent();
  const viewport = page.getViewport({ scale });
  const queryLower = query.toLowerCase();

  const rects: DOMRect[] = [];
  let count = 0;

  for (const item of textContent.items) {
    if (!("str" in item)) continue;
    const text = (item as any).str as string;
    const textLower = text.toLowerCase();
    let idx = 0;

    while ((idx = textLower.indexOf(queryLower, idx)) !== -1) {
      count++;
      // Approximate rect from transform
      const tx = (item as any).transform;
      if (tx) {
        const [a, b, c, d, e, f] = tx;
        const fontSize = Math.sqrt(a * a + b * b);
        const charWidth = fontSize * 0.6;
        const x = e + idx * charWidth;
        const y = f;
        const w = queryLower.length * charWidth;
        const h = fontSize;

        // Transform to viewport coordinates
        const [vx, vy] = viewport.convertToViewportPoint(x, y);
        const [vx2, vy2] = viewport.convertToViewportPoint(x + w, y + h);

        rects.push(new DOMRect(
          Math.min(vx, vx2),
          Math.min(vy, vy2),
          Math.abs(vx2 - vx),
          Math.abs(vy2 - vy),
        ));
      }
      idx += queryLower.length;
    }
  }

  return { rects, count };
}
