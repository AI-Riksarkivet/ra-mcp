import { writeHostFiles } from "./hosts";

// Runs once before any worker starts — writes the mock-host files a single time
// so parallel workers never race on creating/deleting them (see hosts.ts).
export default function globalSetup(): void {
  writeHostFiles();
}
