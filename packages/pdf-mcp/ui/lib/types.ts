/**
 * Type definitions for the PDF Viewer MCP App.
 */

export interface PdfViewerData {
  viewId: string;
  url: string;
  title: string;
  sourceUrl: string;
  currentPage: number;
  totalPages: number;
}

export interface GalleryItem {
  url: string;
  title: string;
  description: string;
  thumbnail_url?: string;
  category?: string;
}
