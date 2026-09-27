# Task W5-breeding — strains, mating and the next generation (Phase 2, real genetics)

Branch: `feat/breeding`. Work in `docs/specs/` (a new spec section first), `services/api/`, `apps/web/`.

企画書 §5 「交配と次の世代」: pick two adults → next week's egg. Strains follow **real inheritance**:
`white` (w) and `yellow` (y) are **X-linked recessive**, `ebony` (e) and `vestigial` (vg) are autosomal recessive,
`Curly` (Cy) is autosomal **dominant** (and homozygous lethal). Sex is XX female / XY male (real flies). Phenotype
colours already exist in the web art (`src/components/art/palette.ts`).

1. **Spec first**: add `docs/specs/genetics.md` — genotype representation per individual (two alleles per
   autosomal locus, X alleles for females ×2 / males ×1), Mendelian draw with the server RNG, phenotype from
   genotype, Cy/Cy lethality handling (re-draw, and record it), mutation chance at eclosion (the existing rainbow
   tier now introduces one new mutant allele instead of picking a phenotype directly), how wild adults from normal
   weeks get genotypes (wild-type homozygous, plus hidden heterozygous carriers at a small documented rate so
   surprises happen). Commit it as its own `docs(spec)` commit.
2. **Domain** (pure): `genetics.py` with full unit tests including textbook crosses (e.g. white-eyed female ×
   wild male → all sons white-eyed, all daughters red-eyed carriers; Cy/+ × Cy/+ → 2:1 Curly:wild among survivors,
   within statistical tolerance).
3. **API**: store genotype on adults (migration, backfill wild-type for existing rows); `POST /v1/weeks` accepts
   `parents: [mother_id, father_id]` (must be one female + one male owned by the player, adults not used as parents
   this week); the egg's genotype is drawn at week start (hidden until eclosion); eclosion reveals phenotype +
   genotype; `GET /v1/zukan` strain section driven by phenotypes seen. Friend mating (お見合い) can be a stub
   endpoint returning 501 with a TODO. Re-export OpenAPI and regenerate web types.
4. **Web**: on home when no week is running, offer 「卵を受け取る」 or 「交配する」 → a parent picker (two cards:
   mother / father from `/v1/adults`, showing phenotype art and a Punnett-style prediction of offspring phenotypes
   with probabilities from a TS mirror of the domain rules — keep it small and tested with vitest). Adult detail
   shows genotype notation (e.g. `w/w`, `Cy/+`) with a 本物 badge. Match the existing design system.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
