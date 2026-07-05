import { defineConfig } from "vitest/config";

// Standalone test config so vitest doesn't load the build's vite.config.ts (which requires
// the INPUT env var). The UI's pure logic (geometry, parsers, reducers) is tested here in
// a plain node environment — no browser needed.
export default defineConfig({
  test: {
    include: ["ui/**/*.test.ts"],
    environment: "node",
  },
});
