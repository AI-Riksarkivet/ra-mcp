/**
 * Type definitions for the Document Viewer
 */

export interface TextLine {
  id: string;
  polygon: string;
  transcription: string;
  hpos: number;
  vpos: number;
  width: number;
  height: number;
  confidence?: number;
}

export interface PageTextLayer {
  textLines: TextLine[];
  pageWidth: number;
  pageHeight: number;
}

export interface PageData {
  index: number;
  imageDataUrl: string;
  textLayer: PageTextLayer;
}

export interface PageUrl {
  image: string;
  textLayer: string;
}

export interface ThumbnailData {
  index: number;
  dataUrl: string;
}

/** Initial payload — built from tool arguments */
export interface ViewerData {
  pageUrls: PageUrl[];
  pageMetadata: string[];
  highlightTerm: string;
  highlightTermColor: string;
}

export interface TooltipState {
  text: string;
  x: number;
  y: number;
}
