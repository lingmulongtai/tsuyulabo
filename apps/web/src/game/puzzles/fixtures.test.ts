import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { verifyCleaning, verifyMeal, verifyTemperature, verifyTraining } from "./index";
import type { PuzzleContracts } from "./types";

// Anchor to this file, not process.cwd(): npm workspaces run from apps/web.
const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../..");
const fixtureRoot = join(repoRoot, "packages", "fixtures", "puzzles");
const kinds = ["meal", "training", "cleaning", "temperature"] as const;
type Kind = (typeof kinds)[number];
type Fixture = {
  [K in Kind]: {
    kind: K;
    description: string;
    params: PuzzleContracts[K]["params"];
    submission: PuzzleContracts[K]["submission"];
    expected: PuzzleContracts[K]["result"];
  }
}[Kind];

function jsonFiles(directory: string): string[] {
  if (!existsSync(directory)) return [];
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? jsonFiles(path) : entry.isFile() && entry.name.endsWith(".json")
      ? [path] : [];
  }).sort();
}

function verify(fixture: Fixture) {
  switch (fixture.kind) {
    case "meal": return verifyMeal(fixture.params, fixture.submission);
    case "training": return verifyTraining(fixture.params, fixture.submission);
    case "cleaning": return verifyCleaning(fixture.params, fixture.submission);
    case "temperature": return verifyTemperature(fixture.params, fixture.submission);
  }
}

describe("shared puzzle fixtures", () => {
  for (const kind of kinds) {
    describe(kind, () => {
      const files = jsonFiles(join(fixtureRoot, kind));
      if (files.length === 0) {
        it.skip("awaits shared JSON fixtures from the server implementation", () => {});
      }
      for (const file of files) {
        it(relative(repoRoot, file), () => {
          // Fixture JSON is the shared typed contract; malformed or mismatched files must fail.
          const fixture = JSON.parse(readFileSync(file, "utf8")) as Fixture;
          expect(fixture.kind).toBe(kind);
          expect(verify(fixture)).toEqual(fixture.expected);
        });
      }
    });
  }
});
