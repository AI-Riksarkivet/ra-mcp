/** Design constants for the PDF viewer. */

export const ANNOTATION_COLORS = {
  highlight: "rgba(255, 255, 0, 0.35)",
  underline: "#ff0000",
  strikethrough: "#ff0000",
  note: "#f5a623",
  rectangle: "#0066cc",
  circle: "#0066cc",
  line: "#333333",
  freetext: "#333333",
  stamp: "#cc0000",
  image: "#999999",
} as const;

export const SEARCH_HIGHLIGHT = {
  color: "rgba(255, 255, 0, 0.4)",
  activeColor: "rgba(255, 165, 0, 0.6)",
} as const;

export const ZOOM = {
  min: 0.25,
  max: 5.0,
  step: 0.25,
  default: 1.0,
  fitWidth: -1,
} as const;

export const DEFAULT_PDF_URL =
  "https://filer.riksarkivet.se/nedladdningsbara-filer/Hur%20riket%20styrdes_63MB.pdf";
