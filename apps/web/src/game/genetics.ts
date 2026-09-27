/** Independent-locus mirror of the server rules in docs/specs/genetics.md. */
export const LOCI = ["w", "y", "e", "Cy", "vg"] as const;
export type Locus = typeof LOCI[number];
export type Sex = "f" | "m";
export type Phenotype = "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
export type Genotype = { sex: Sex } & Record<Locus, readonly string[]>;
const TRAITS: Record<Locus, Phenotype> = { w: "white", y: "yellow", e: "ebony", Cy: "curly", vg: "vestigial" };
const xLinked = (locus: Locus) => locus === "w" || locus === "y";

export function wildType(sex: Sex): Genotype {
  return { sex, w: sex === "f" ? ["+", "+"] : ["+"], y: sex === "f" ? ["+", "+"] : ["+"], e: ["+", "+"], Cy: ["+", "+"], vg: ["+", "+"] };
}

function validate(genotype: Genotype) {
  if (genotype.sex !== "f" && genotype.sex !== "m") throw new Error("Invalid sex");
  for (const locus of LOCI) {
    const copies = xLinked(locus) && genotype.sex === "m" ? 1 : 2;
    if (genotype[locus].length !== copies || genotype[locus].some(a => a !== "+" && a !== locus)) throw new Error(`Invalid ${locus} alleles`);
  }
}

export function phenotypes(genotype: Genotype): Phenotype[] {
  validate(genotype);
  if (genotype.Cy.every(a => a === "Cy")) throw new Error("Lethal Cy/Cy genotype");
  const expressed = LOCI.filter(locus => locus === "Cy" ? genotype.Cy.includes("Cy") : genotype[locus].every(a => a === locus)).map(locus => TRAITS[locus]);
  return expressed.length ? expressed : ["wild"];
}

export function genotypeNotation(genotype: Genotype): { locus: Locus; notation: string; carrier: boolean }[] {
  validate(genotype);
  return LOCI.map(locus => ({ locus,
    notation: [...genotype[locus], ...(xLinked(locus) && genotype.sex === "m" ? ["Y"] : [])].join("/"),
    carrier: locus !== "Cy" && genotype[locus].includes(locus) && genotype[locus].includes("+"),
  }));
}

export interface Prediction { sex: Sex; phenotypes: Phenotype[]; probability: number }

export function predictOffspring(mother: Genotype, father: Genotype): { outcomes: Prediction[]; lethalProbability: number } {
  phenotypes(mother); phenotypes(father);
  if (mother.sex !== "f" || father.sex !== "m") throw new Error("Select a mother and father");
  const grouped = new Map<string, Prediction>();
  let lethalProbability = 0;
  for (const sex of ["f", "m"] as const) {
    let states = [{ genotype: wildType(sex), probability: 0.5 }];
    for (const locus of LOCI) {
      const paternal = xLinked(locus) && sex === "m" ? [null] : father[locus];
      states = states.flatMap(state => mother[locus].flatMap(maternal => paternal.map(allele => ({
        genotype: { ...state.genotype, [locus]: allele === null ? [maternal] : [maternal, allele] },
        probability: state.probability / mother[locus].length / paternal.length,
      }))));
    }
    for (const state of states) {
      if (state.genotype.Cy.every(a => a === "Cy")) { lethalProbability += state.probability; continue; }
      const traits = phenotypes(state.genotype);
      const key = `${sex}:${traits.join(",")}`;
      const previous = grouped.get(key);
      if (previous) previous.probability += state.probability;
      else grouped.set(key, { sex, phenotypes: traits, probability: state.probability });
    }
  }
  return { lethalProbability, outcomes: [...grouped.values()].map(outcome => ({ ...outcome, probability: outcome.probability / (1 - lethalProbability) })) };
}

/** Each equally likely cell is a maternal allele crossed with a paternal allele. */
export function punnettSquare(mother: Genotype, father: Genotype, locus: Locus) {
  return { maternal: mother[locus], paternal: xLinked(locus) ? [father[locus][0], "Y"] : father[locus] };
}
