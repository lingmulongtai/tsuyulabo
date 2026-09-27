// The API currently exports dict responses. These refinements mirror its serializers;
// keep them here until the API exports response models. Never modify openapi.json.
const str = { type: "string" }, num = { type: "number" }, bool = { type: "boolean" };
const obj = (properties, optional = []) => ({ type: "object", properties, required: Object.keys(properties).filter(k => !optional.includes(k)) });
const ref = name => ({ $ref: `#/components/schemas/${name}` });
const arr = items => ({ type: "array", items });
const nullable = schema => ({ anyOf: [schema, { type: "null" }] });
const en = (...values) => ({ type: "string", enum: values });
const dict = (value = {}) => ({ type: "object", additionalProperties: value });
const adultBase = { id: str, name: str, sex: en("m", "f"), strain: en("wild", "white", "yellow", "ebony", "curly", "vestigial"), stars: num, traits: arr(str), skills: dict(bool), level: num, preferences: dict(num), genotype: ref("Genotype"), phenotypes: arr(en("wild", "white", "yellow", "ebony", "curly", "vestigial")), mutation: nullable(obj({ locus: en("w", "y", "e", "Cy", "vg"), copy: num })) };
export const schemas = {
  Genotype: obj({ sex: en("m", "f"), w: arr(en("+", "w")), y: arr(en("+", "y")), e: arr(en("+", "e")), Cy: arr(en("+", "Cy")), vg: arr(en("+", "vg")) }),
  Slot: en("morning", "noon", "night"),
  Stage: en("egg", "larva1", "larva2", "larva3", "wandering", "pupa", "adult"),
  ActionKind: en("meal", "training", "cleaning", "temperature", "pupation_site", "sleep", "wake"),
  TodoStatus: en("done", "available", "locked"),
  WeekRank: en("normal", "silver", "gold", "rainbow"),
  TodoItem: obj({ action: ref("ActionKind"), status: ref("TodoStatus"), slot: nullable(ref("Slot")), remaining: nullable(num), available_at: nullable(str) }, ["slot", "remaining", "available_at"]),
  Balances: obj({ shizuku: num, research_points: num, kohaku: num }),
  Fly: obj({ stage: ref("Stage"), hunger: num, cleanliness: num, mood: num, mood_label: str, growth: num }),
  WeekSummary: obj({ id: str, research_day: num, stage: ref("Stage"), ready_to_eclose: bool, care_miss: num, points_so_far: num }),
  Week: { allOf: [ref("WeekSummary"), obj({ started_at: str, status: str, fly: ref("Fly"), days: arr(obj({ research_day: num, events: arr(dict()) })) })] },
  PastWeek: obj({ id: str, rank: nullable(ref("WeekRank")), points: num, adult_id: nullable(str), started_at: str, eclosed_at: nullable(str) }),
  Adult: obj({ ...adultBase, week_id: str, subskills: arr(str), level_cap: num, exp: num, energy: num, created_at: str }),
  TeamMemberSummary: { allOf: [ref("Adult"), obj({ slot: num, bag: dict(num), shizuku: num, pending_exp: num })] },
  Team: obj({ members: arr(ref("TeamMemberSummary")), bag_total: num, collectable: bool }),
  Memo: obj({ id: str, text: str, evidence: arr(str) }, ["id"]),
  HomeData: obj({ clock: obj({ game_now: str, slot: ref("Slot"), research_day: nullable(num), weekday_label: nullable(str) }), week: nullable(ref("WeekSummary")), fly: nullable(ref("Fly")), todo: arr(ref("TodoItem")), balances: ref("Balances"), team: ref("Team"), shiori: obj({ memo: nullable(ref("Memo")) }) }),
  Profile: obj({ id: str, display_name: str, friend_code: str, title: nullable(str), favorite_adult_id: nullable(str), balances: ref("Balances"), research_rank: nullable(num) }),
  Guest: obj({ user: ref("Profile"), token: str }),
  Puzzle: obj({ puzzle_id: str, kind: en("meal", "training", "cleaning", "temperature", "pupation_site"), params: dict(), issued_at: str, expires_at: str }),
  PuzzleResult: obj({ valid: bool, score: num, lines: num, max_combo: num, theme_cells: num, great_success: bool, stars: num, hirameki: bool, hit: bool, grades: arr(en("perfect", "good", "miss")), grade: en("perfect", "good", "miss"), effects: dict({ anyOf: [num, bool] }), seq: num, event_id: str }, ["valid", "score", "lines", "max_combo", "theme_cells", "great_success", "stars", "hirameki", "hit", "grades", "grade", "effects"]),
  Presentation: obj({ meal_points: num, training_points: num, care_points: num, care_miss: num, penalty: num, points: num, rank: ref("WeekRank"), shizuku: num, research_points: num }),
  Eclosion: obj({ omen_sequence: arr(num), tier: num, lethal_redraws: num, adult: obj(adultBase) }),
  SleepStart: obj({ id: str, started_at: str }),
  SleepEnd: obj({ id: str, hours: num, bonus: num, energy_recovered: dict(num) }),
  Collection: obj({ materials: dict(num), shizuku: num, exp: dict(num), team: ref("Team") }),
  Friend: obj({ id: str, display_name: str, friend_code: str, title: nullable(str) }),
  Lab: obj({ user: obj({ id: str, display_name: str }), adults: arr(ref("Adult")), team: ref("Team"), week: nullable(obj({ stage: ref("Stage"), research_day: num, fly: ref("Fly") })) }),
  Notification: obj({ id: str, kind: str, payload: dict(), created_at: str, read_at: nullable(str) }),
  Zukan: obj({ behaviors: arr(obj({ id: str, observed: bool })), strains: arr(obj({ id: adultBase.strain, name: str, observed: bool })), completion: obj({ behaviors: num, strains: num }) }),
  Job: obj({ id: str, kind: str, status: en("pending", "running", "succeeded", "failed"), result: nullable(dict()), error: nullable(dict()), created_at: str, finished_at: nullable(str) }),
  ApiErrorBody: obj({ error: obj({ code: str, message: str, details: dict() }, ["details"]) }),
};
export const responses = {
  "PATCH /v1/adults/{adult_id}": ref("Adult"),
  "POST /v1/auth/guest": ref("Guest"), "GET /v1/me": ref("Profile"), "PATCH /v1/me": ref("Profile"),
  "GET /v1/home": ref("HomeData"), "GET /v1/weeks": arr(ref("PastWeek")), "POST /v1/weeks": ref("Week"), "GET /v1/weeks/current": ref("Week"), "GET /v1/weeks/current/presentation": ref("Presentation"), "POST /v1/weeks/current/eclose": ref("Eclosion"),
  "POST /v1/puzzles": ref("Puzzle"), "POST /v1/puzzles/{puzzle_id}/submit": ref("PuzzleResult"),
  "POST /v1/sleep/start": ref("SleepStart"), "POST /v1/sleep/end": ref("SleepEnd"),
  "GET /v1/adults": arr(ref("Adult")), "GET /v1/adults/{adult_id}": ref("Adult"), "POST /v1/adults/{adult_id}/level-up": { allOf: [ref("Adult"), obj({ cost: num })] },
  "GET /v1/team": ref("Team"), "PUT /v1/team": ref("Team"), "POST /v1/team/collect": ref("Collection"),
  "GET /v1/friends": arr(ref("Friend")), "GET /v1/friends/{friend_id}/lab": ref("Lab"), "GET /v1/notifications": arr(ref("Notification")),
  "GET /v1/zukan": ref("Zukan"), "GET /v1/jobs/{job_id}": ref("Job"), "GET /v1/shiori/memo": nullable(ref("Memo")),
};
