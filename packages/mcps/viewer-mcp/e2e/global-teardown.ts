import { removeHostFiles } from "./hosts";

// Runs once after all workers finish — safe to remove the mock-host files here
// because no test is still running (unlike a per-worker afterAll).
export default function globalTeardown(): void {
  removeHostFiles();
}
