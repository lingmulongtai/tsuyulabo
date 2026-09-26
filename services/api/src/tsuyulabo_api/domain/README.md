# Pure game domain

These modules use only the standard library. All game timestamps must be aware;
all randomness is supplied as `random.Random`. Pass game time after applying the
user's dev offset in the API layer. Domain functions perform no I/O and return
fresh values. RNG objects intentionally advance; persist the seed/state with the
corresponding result in the API transaction.

## API integration

- `clock`: `game_day` returns the JST date of the 04:00 day boundary;
  `research_day` is one-based and is not capped at seven. `iter_slots` returns
  full slot boundaries intersecting `[start, end)`; `completed_slots` returns
  deadlines in `(start, end]`. Naive and reversed timestamps are rejected.
- `lifecycle.action_availability(week_start, now, usage)` accepts successful
  `CareEvent` records for the week. Each `TodoItem` carries an action, current
  `status`, current quota (`used`, `limit`), and the earliest next `available_at`.
  A usable action has `available_at=now`; one without a future window has `None`.
  `ready_to_eclose` is separate from `stage_at`: pupa remains the computed stage
  until the API records the completed eclosion. New-week eligibility is API state.
- `stats`: initialize `Stats(week_start)`, call `decay` before applying a meal or
  cleaning at its timestamp, and persist the whole returned state. Floats and
  zero-hunger timestamps are internal; `display()` rounds the public stats.
  Late-night egg receipt hatches immediately at receipt. Decay initializes at
  hatch, integrates only until pupa, and preserves the first starvation deadline.
- `care_miss.evaluate`: pass the **full** week's successful event log, even when
  evaluating a short period. Union returned `(kind, research_day, slot_or_none)`
  keys with previously stored keys. Scope the unique storage key by week ID.
  Starvation is charged once per research week. An omitted pupation action
  returns a miss; `default_pupation_choice` gives the middle option for the API
  to apply separately. Do not insert that fallback as a user care action.
- Puzzle `generate(rng, context)` returns `(public_params, private_secret)`.
  Context keys are `research_day`, `theme`, `cue`, `valence` where relevant.
  Never send private training paths or site winners to the client. `verify`
  returns `VerifyResult`; `.to_dict()` is the shared fixture/API representation.
  Invalid submissions do not consume the puzzle. Run `verify_wall_clock` using
  server-issued/submitted times as well; enforce ownership and single successful
  submission atomically in the API. Params are trusted issuance data; malformed
  request envelopes belong to the API schema validation layer.
- `meal.roll` and `training.roll` return luck and effect fields separately from
  deterministic verification. Training association values come from the brain;
  call `skill_unlocked` with that resulting value, not the puzzle strength.
  Pupation's winning option is rolled at issuance; `roll` reveals that fixed result.
- `presentation.summarize` accepts one week's care log plus unique miss keys.
  `rewards` follows the spec literally: negative points produce negative floor
  rewards. The economy owner should decide any future nonnegative-reward policy
  by changing the spec, not by silently changing the domain formula.
- `eclosion.roll` takes rank, temperature average and site hit; store its result
  once, including the presentation-only omen sequence. Odds are exposed by `odds`.
- `adults.add_exp` handles multiple level thresholds and returns stored subskills.
  `level_up` returns `(new_state, cost)`; it does not debit currency. Pass available
  balance and debit atomically in the API. Excess exp at the cap is discarded;
  paid level-ups preserve current exp below the cap. Subskill rolls are independent
  and uniform (duplicates are allowed since only traits specify exclusivity).
- `team.gather`: persist `GatherState` including fractional item progress, shizuku,
  pending exp and RNG state. On collection, transfer the bag/currency and clear
  those fields in the caller; preserve fractional progress. Award and clear
  pending exp through `adults.add_exp`; settle before changing level, subskills,
  preferences, team membership or energy. Positive `apple_vinegar` preference maps
  to apple; negative preferences do not reduce base material weights.
- `sleep.wake` takes energy already settled to wake time. It returns sleep rewards
  and capped final energy; availability/quota is supplied by `lifecycle`.
- `friends.generate_code` is seeded and pure; enforce uniqueness and retry any
  collision in storage. Validation is strict uppercase with no whitespace folding.

## Choices where the specs leave details open

- Only `banana_search` is named in the skill list; the remaining reward/avoid IDs
  and Japanese labels are defined in `constants.SKILL_UNLOCKS` for integration.
  Pupation text variants extend the three described settings.
- The optional fake-out is emitted for gold only. Rainbow has no higher specified
  color, so its sequence ends at rainbow without inventing a fifth tier.
- Gathering integrates energy continuously across 60/20 thresholds. A full bag
  stops both item and shizuku gathering; energy keeps decaying. Royal jelly takes
  one bag slot instead of a material and grants one exp, so the capacity always holds.
- Puzzle elapsed timestamps must encompass their operations. Temperature and
  training use the common issuance lifetime, with no invented five-second cutoff.
  Temperature rounds positive half ties up for JavaScript parity. Cleaning uses
  a `1e-12` tolerance solely to preserve inclusive mathematical zone boundaries.
  See `packages/fixtures/README.md` for verifier precedence and fixture conventions.

These interpretations should be kept consistent when wiring the API and TS side;
no game tuning numbers or specified scoring formulas were changed.
