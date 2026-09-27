import { describe, expect, it } from "vitest";
import { genotypeNotation, LOCI, phenotypes, predictOffspring, punnettSquare, wildType } from "./genetics";

describe("Mendelian inheritance", () => {
  it.each(["w", "y"] as const)("passes maternal %s to all sons and makes carrier daughters", locus => {
    const mother = { ...wildType("f"), [locus]: [locus, locus] };
    const result = predictOffspring(mother, wildType("m"));
    expect(result.lethalProbability).toBe(0);
    expect(result.outcomes).toEqual([
      { sex: "f", phenotypes: ["wild"], probability: 0.5 },
      { sex: "m", phenotypes: [locus === "w" ? "white" : "yellow"], probability: 0.5 },
    ]);
  });
  it("never passes paternal white to sons", () => {
    const result = predictOffspring(wildType("f"), { ...wildType("m"), w: ["w"] });
    expect(result.outcomes.every(row => row.phenotypes[0] === "wild")).toBe(true);
  });
  it.each(["e", "vg"] as const)("predicts 1:3 recessive %s expression", locus => {
    const result = predictOffspring({ ...wildType("f"), [locus]: [locus, "+"] }, { ...wildType("m"), [locus]: [locus, "+"] });
    expect(result.outcomes.filter(row => !row.phenotypes.includes("wild")).reduce((sum, row) => sum + row.probability, 0)).toBe(0.25);
  });
  it("normalizes Curly survivors to 2:1 and reports 25% lethal embryos", () => {
    const result = predictOffspring({ ...wildType("f"), Cy: ["Cy", "+"] }, { ...wildType("m"), Cy: ["Cy", "+"] });
    expect(result.lethalProbability).toBe(0.25);
    expect(result.outcomes.filter(row => row.phenotypes.includes("curly")).reduce((sum, row) => sum + row.probability, 0)).toBeCloseTo(2 / 3);
    expect(result.outcomes.reduce((sum, row) => sum + row.probability, 0)).toBeCloseTo(1);
  });
  it("preserves combined traits and handles hidden carriers", () => {
    expect(phenotypes({ ...wildType("m"), w: ["w"], e: ["e", "e"], Cy: ["Cy", "+"] })).toEqual(["white", "ebony", "curly"]);
    expect(phenotypes({ ...wildType("f"), w: ["w", "+"], e: ["e", "+"] })).toEqual(["wild"]);
    const result = predictOffspring({ ...wildType("f"), w: ["w", "+"], y: ["y", "+"], e: ["e", "+"], vg: ["vg", "+"], Cy: ["Cy", "+"] }, { ...wildType("m"), w: ["w"], y: ["y"], e: ["e", "+"], vg: ["vg", "+"], Cy: ["Cy", "+"] });
    expect(result.outcomes.reduce((sum, row) => sum + row.probability, 0)).toBeCloseTo(1);
    expect(result.outcomes.some(row => row.phenotypes.length === 5)).toBe(true);
  });
  it("shows hemizygous notation and maternal/paternal Punnett axes", () => {
    const mother = { ...wildType("f"), w: ["w", "+"] };
    const father = { ...wildType("m"), w: ["w"] };
    expect(genotypeNotation(mother)[0]).toEqual({ locus: "w", notation: "w/+", carrier: true });
    expect(genotypeNotation(father)[0].notation).toBe("w/Y");
    expect(punnettSquare(mother, father, "w")).toEqual({ maternal: ["w", "+"], paternal: ["w", "Y"] });
  });
  it("rejects invalid sex, copy count, alleles and lethal parents", () => {
    expect(() => predictOffspring(wildType("m"), wildType("f"))).toThrow();
    expect(() => phenotypes({ ...wildType("f"), w: ["w"] })).toThrow();
    for (const locus of LOCI) expect(() => phenotypes({ ...wildType("f"), [locus]: ["bad", "+"] })).toThrow();
    expect(() => phenotypes({ ...wildType("f"), Cy: ["Cy", "Cy"] })).toThrow();
  });
});
