/**
 * Decoded-image LRU cache + prefetch.
 *
 * Page images are ~1500px IIIF JPEGs. Decoding one on the main thread (which the
 * first canvas drawImage forces) is the dominant page-navigation jank. Awaiting
 * `img.decode()` moves the decode off the paint path, and caching the decoded
 * HTMLImageElement means revisited / prefetched neighbour pages skip fetch+decode
 * entirely.
 */

const cache = new Map<string, HTMLImageElement>();
const inflight = new Map<string, Promise<HTMLImageElement>>();
const MAX_ENTRIES = 8;

/** Fetch + decode an image (or return the cached decoded one), LRU-bounded. */
export async function loadDecodedImage(url: string): Promise<HTMLImageElement> {
  const hit = cache.get(url);
  if (hit) {
    cache.delete(url);
    cache.set(url, hit); // refresh LRU recency
    return hit;
  }

  // Dedup concurrent loads of the same URL — the cache only holds COMPLETED decodes, so a
  // prefetch racing a navigation would otherwise decode the same multi-MB JPEG twice on the
  // main thread (the exact jank this module exists to avoid).
  const pending = inflight.get(url);
  if (pending) return pending;

  const load = (async () => {
    const img = new Image();
    img.src = url;
    await img.decode();
    cache.set(url, img);
    if (cache.size > MAX_ENTRIES) {
      const oldest = cache.keys().next().value;
      if (oldest !== undefined) cache.delete(oldest);
    }
    return img;
  })();
  inflight.set(url, load);
  try {
    return await load;
  } finally {
    inflight.delete(url);
  }
}

/** Warm the cache for a URL in the background; failures are ignored. */
export function prefetchImage(url: string): void {
  if (!url || cache.has(url)) return;
  void loadDecodedImage(url).catch(() => {});
}
