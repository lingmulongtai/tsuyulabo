# Genetics and breeding (Phase 2)

This section supersedes the strain/sex draw in game-rules §7. Tier odds, stars,
traits and omens stay unchanged. Inheritance and phenotype are server-authoritative.

## Individual genotype

JSON: `{ "sex": "f", "w": ["+", "+"], "y": ["+", "+"],
"e": ["+", "+"], "vg": ["+", "+"], "Cy": ["+", "+"] }`.
`+` is wild type; the other allowed allele at each locus is its locus name.
Autosomal loci always have two alleles. Females are XX (`f`) and have two alleles
at w and y; males are XY (`m`) and have one (Y carries neither locus).
Allele order records maternal then paternal inheritance, not dominance.

w (white eyes) and y (yellow body) are X-linked recessive. e (ebony body) and vg
(vestigial wings) are autosomal recessive. Cy (Curly wings) is autosomal dominant;
Cy/Cy is lethal. Recessive traits require every copy at that locus to be mutant.
`phenotypes` contains every expressed trait in order white, yellow, ebony, curly,
vestigial, or just wild when none are expressed. `strain` is the first phenotype,
for compatibility with single-strain art. Combination art and epistasis are not
modeled. The 本物 badge refers to these real inheritance modes, not a complete
fly genome simulation. This small Mendelian model samples loci independently;
chromosomal linkage/recombination maps are outside this phase. Predictions must
say that linkage and new eclosion mutations are not included.

## Egg creation and mutation

The server RNG supplies all draws. Sex is an equal paternal X/Y draw. Each
autosomal allele is sampled uniformly from the corresponding parent. Sons get
only maternal X alleles; daughters also get the father's sole X allele.
Reject a Cy/Cy embryo and repeat the entire draw until viable; persist the number
of rejected embryos as `lethal_redraws` on the week. Parents must themselves be
viable. Cy/+ × Cy/+ therefore yields 2:1 Curly:wild among survivors (25% lethal
before redrawing). The UI reports survivor probabilities and the excluded lethal
probability separately. No client-supplied seed or genotype is accepted.

Normal eggs have wild-type alleles, except for an independent 5% chance of one
hidden heterozygous mutant allele at each recessive locus eligible for carriage:
e and vg in both sexes, w and y only in females. The allele copy is uniformly
chosen. No spontaneous Cy is added at egg creation. Sex and genotype are stored
at week start and remain hidden in all week/home/event responses until eclosion.
Legacy adults are backfilled with sex-appropriate wild-type genotypes; their
historical strain remains a display/discovery record, not an inheritable allele.
Legacy active weeks receive a wild-type genotype once, at their next eclosion.

Tier 3 introduces exactly one new mutant allele at eclosion, instead of choosing
a phenotype. Choose uniformly among loci with an eligible `+` copy, then uniformly
among those copies. Exclude Cy if a Cy allele already exists, preventing a lethal
mutation. A fully mutant viable individual has no eligible copy: record no
mutation. Other tiers never mutate. Thus mutation probability is the existing
tier-3 probability (0.5%, 1%, 4%, 10% by rank); a new recessive allele can be a
hidden carrier. Record `{locus, copy}` or null as `mutation` on the adult.

## API and parental use

`POST /v1/weeks` accepts no body, `{}`, or `{parents: [mother_id, father_id]}`.
Reject wrong length/unknown fields (422), missing or unowned adults (404), wrong
sex/order or duplicate adults (422), an active week (409), or parents already
used in the current game calendar week (409 `parent_already_used`). The calendar
week begins Monday 04:00 Asia/Tokyo, using the existing game clock. Starting a
normal egg does not consume parental use. Each adult records its last breeding
week boundary; use cannot move backwards after a dev clock reset. User mutation
locking and the transaction cover checks, draws, parental use and week creation.
An idempotent replay must not redraw or consume another use.

Store mother/father IDs, hidden egg genotype and lethal redraw count on Week;
store genotype, mutation and last parental-use boundary on Adult. Eclosion returns
the adult genotype, phenotypes and mutation, plus `lethal_redraws`. Adult list and
detail include genotype and phenotypes. `GET /v1/zukan` discovers expressed traits
only (including historical legacy strains), never hidden carrier alleles.
## Friend mating (お見合い)

`POST /v1/weeks/friend-mating` accepts `{friend_id, adult_id, friend_adult_id}`.
The proposer owns the first adult, the friend owns the second, and their sexes
must differ. Only registered friends can propose or accept. A proposal expires
exactly 48 hours after creation (at the boundary it cannot be accepted/declined).
The shared clock is the later of the two players' game clocks, including dev
offsets. Dev time cannot be reset after either player participates in a proposal.
One proposal per adult pair per shared calendar week (Monday 04:00 JST), including
declined/expired proposals and proposals in the opposite direction. Proposing
checks parental availability but does not reserve or consume it.

`GET /v1/weeks/friend-mating` returns `{incoming, outgoing}` with IDs, participant
names, parent names/IDs, status and expiry. Only the recipient can call
`POST /v1/weeks/friend-mating/{id}/accept` or `/decline`. Accept rechecks friendship,
ownership and both parents' availability in the shared week at acceptance. It
marks both parents used for that week, sharing the limit with ordinary breeding;
last-use boundaries never move backwards. Two sequential independent draws from
the server RNG use `domain/genetics.py` with the same mother and father, including
lethal redraws. Each owner gets one pending egg. Acceptance is allowed during an
active week. Decline/expiry consumes no parents. Stale competing proposals fail
acceptance if either parent has since been used. Both users receive notifications
on proposal, acceptance and decline; expired status is evaluated when read.

`GET /v1/weeks/pending-eggs` returns only the owner's unused eggs (ID, proposal ID,
parent IDs/names, received time). `POST /v1/weeks` additionally accepts
`{pending_egg_id}` mutually exclusive with `parents`. Starting consumes the egg
once and copies its stored genotype, parents and lethal redraw count to the week;
an active week returns 409 without consuming it. Pending eggs do not expire and
remain usable after unfriending. Egg sex/genotype/redraws stay hidden until
eclosion. All writes and notifications are transactional and idempotent. Pair
actions lock both users in ID order to serialize with other social/breeding work.
No purchase, currency, item or paid benefit changes eligibility or inheritance.

`GET /v1/weeks/friend-mating/options/{friend_id}` provides the friend's adult
IDs/names, sex, genotype and availability solely for the mating picker. This is
an explicit, friendship-gated genetics disclosure for predicting offspring; the
ordinary public lab allowlist and owner-only adult endpoints remain unchanged.
The client uses the existing Punnett helper and displays model limitations.

## Web

When no week is active, home offers 卵を受け取る and 交配する. The picker has mother
and father cards populated from `/v1/adults`, with phenotype art and sex filtering.
A small pure TS mirror enumerates Punnett outcomes, combines equal phenotypes,
and normalizes probabilities after excluding Cy/Cy. It labels the model's limits
and shows both sexes and all phenotypes, including carrier explanations. Adult
detail shows every locus (`w/w`, `w/Y`, `Cy/+`, etc.) and a 本物 badge.
Friend lab adult cards offer お見合いを申し込む, an opposite-sex own-adult picker
and offspring prediction. Friends shows incoming accept/decline cards and outgoing
status. Home without a running week offers pending eggs beside the normal and
breeding choices; starting another egg leaves pending eggs available.
