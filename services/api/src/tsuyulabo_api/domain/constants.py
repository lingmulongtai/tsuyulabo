"""Alpha tuning and Japanese display text from game-rules.md and puzzles.md."""

from __future__ import annotations

TIMEZONE = "Asia/Tokyo"
DAY_BOUNDARY_HOUR = 4
SLOT_HOURS = {"morning": 4, "noon": 12, "night": 18}
SLOT_NAMES = {"morning": "朝", "noon": "昼", "night": "夜"}
WEEKDAY_LABELS = ("月", "火", "水", "木", "金", "土", "日")
WEEK_DAYS = 7
HATCH_DAY = 1
MOLT_DAY = 3
LARVA3_DAY = 4
WANDERING_DAY = 5
PUPA_DAY = 6
ECLOSION_DAY = 7
MEAL_DAYS = tuple(range(1, 8))
TRAINING_DAYS = tuple(range(2, 8))
CLEANING_DAYS = (2, 3, 4, 5)
TEMPERATURE_DAYS = (1, 6)
TRAINING_DAILY_LIMIT = 3
ONCE = 1
STAT_MAX = 100
HATCH_HUNGER = 60.0
HATCH_CLEANLINESS = 100.0
HUNGER_DECAY = 12.5
CLEANLINESS_DECAY = 4.0
MEAL_HUNGER = 40
GREAT_MEAL_HUNGER = 60
MOOD_HUNGER_WEIGHT = 0.6
MOOD_CLEANLINESS_WEIGHT = 0.4
MOOD_LABELS = ((70, "ごきげん"), (40, "ふつう"), (0, "しょんぼり"))
HUNGER_ZERO_HOURS = 3
CARE_MISS_PENALTY = 500
GREAT_POINTS = 1000
TRAINING_STAR_POINTS = 400
HIRAMEKI_POINTS = 300
CARE_SCORE_POINTS = 5
SITE_HIT_POINTS = 1000
RANK_THRESHOLDS = {"normal": 0, "silver": 6000, "gold": 11000, "rainbow": 16000}
RANK_NAMES = {"normal": "ノーマル", "silver": "シルバー", "gold": "ゴールド", "rainbow": "にじ"}
TIER_COLORS = ("白", "青", "金", "虹")
ODDS = {
    "normal": (72.0, 22.0, 5.5, 0.5),
    "silver": (60.0, 30.0, 9.0, 1.0),
    "gold": (40.0, 38.0, 18.0, 4.0),
    "rainbow": (20.0, 40.0, 30.0, 10.0),
}
TEMPERATURE_BONUS_THRESHOLD = 80
TEMPERATURE_ODDS_SHIFT = 3
SITE_ODDS_SHIFT = 2
FAKE_OUT_CHANCE = 0.30
SEXES = ("m", "f")
WILD_STRAIN = "wild"
STRAINS = {
    "wild": "野生型",
    "white": "白眼",
    "yellow": "黄体",
    "ebony": "黒体",
    "curly": "巻き翅",
    "vestigial": "痕跡翅",
}
MUTATIONS = tuple(key for key in STRAINS if key != WILD_STRAIN)
TRAITS = {
    "right_turner": ("右曲がりぐせ", 0.15),
    "left_turner": ("左曲がりぐせ", -0.15),
    "light_lover": ("光が大好き", 0.30),
    "keen_nose": ("匂いにするどい", 0.25),
    "brave": ("度胸がある", 0.20),
    "wanderer": ("よく歩く", 0.30),
    "easygoing": ("のんびりや", -0.30),
    "glutton": ("食いしんぼう", 0.25),
}
TRAIT_COUNT = 2
EXCLUSIVE_TRAITS = (
    frozenset(("right_turner", "left_turner")),
    frozenset(("wanderer", "easygoing")),
)
ADULT_CAPACITY = 30
LEVEL_CAPS = {1: 20, 2: 30, 3: 40, 4: 50, 5: 60}
LEVEL_COST_FACTOR = 20
EXP_FACTOR = 10
ITEM_EXP = 1
SUBSKILL_LEVELS = (10, 25, 50)
SUBSKILLS = {
    "gather_s": ("採集量アップS", 0.08),
    "gather_m": ("採集量アップM", 0.16),
    "great_up": ("大成功率アップ", 0.02),
    "drop_bonus": ("しずくボーナス", 0.20),
    "bag_up": ("材料袋アップ", 10),
    "energy_up": ("げんき回復アップ", 0.20),
    "rp_up": ("研究ポイントアップ", 0.05),
}
TEAM_CAPACITY = 5
TEAM_GREAT_BONUS_CAP = 0.10
GATHER_BASE = 1.5
GATHER_PER_LEVEL = 0.1
ENERGY_DECAY = 5.0
ENERGY_FACTORS = ((60, 1.0), (20, 0.6), (0, 0.2))
BAG_CAPACITY = 30
MATERIALS = ("banana", "apple", "grape", "yeast", "agar")
MATERIAL_NAMES = dict(zip(MATERIALS, ("バナナ", "りんご", "ぶどう", "酵母", "寒天"), strict=True))
PREFERENCE_WEIGHT = 2.0
CUE_MATERIALS = {"banana": "banana", "apple_vinegar": "apple", "grape": "grape", "yeast": "yeast"}
SHIZUKU_BASE = 2
SHIZUKU_PER_LEVEL = 0.2
RARE_DROP_CHANCE = 0.01
RARE_DROP = "royal_jelly"
ROYAL_JELLY_ENERGY = 30
SLEEP_MAX_HOURS = 10
SLEEP_BONUS_MAX_HOURS = 8
SLEEP_SHIZUKU_PER_HOUR = 25
SLEEP_ENERGY_PER_HOUR = 15
PRESENTATION_SHIZUKU_DIVISOR = 6
PRESENTATION_RP_DIVISOR = 40
CURRENCIES = {"shizuku": "しずく", "research_points": "研究ポイント", "kohaku": "こはく"}
INITIAL_SHIZUKU = 300
FRIEND_CODE_LENGTH = 8
FRIEND_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
FRIEND_CAPACITY = 50
FRIEND_LIKES_PER_DAY = 1
FRIEND_GIFTS_PER_DAY = 1
FRIEND_GIFT_MAX = 5
FRIEND_GIFT_RP = 10
PUZZLE_EXPIRY_MS = 600_000
WALL_CLOCK_GRACE_MS = 2000
MEAL_ROWS = MEAL_COLS = 8
MEAL_TIME_LIMIT_MS = 30_000
MEAL_TIME_GRACE_MS = 1500
MEAL_HAND_SIZE = 3
MEAL_PIECE_COUNT = 90
SHAPES = {
    "m1": ((0, 0),),
    "d2h": ((0, 0), (0, 1)),
    "d2v": ((0, 0), (1, 0)),
    "i3h": ((0, 0), (0, 1), (0, 2)),
    "i3v": ((0, 0), (1, 0), (2, 0)),
    "l3a": ((0, 0), (1, 0), (1, 1)),
    "l3b": ((0, 0), (0, 1), (1, 0)),
    "l3c": ((0, 0), (0, 1), (1, 1)),
    "l3d": ((0, 1), (1, 0), (1, 1)),
    "o4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "i4h": tuple((0, c) for c in range(4)),
    "i4v": tuple((r, 0) for r in range(4)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "s4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "i5h": tuple((0, c) for c in range(5)),
    "i5v": tuple((r, 0) for r in range(5)),
    "o9": tuple((r, c) for r in range(3) for c in range(3)),
}
SHAPE_WEIGHTS = dict(
    zip(SHAPES, (4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1), strict=True)
)
THEME_WEIGHT = 0.30
OTHER_INGREDIENT_WEIGHT = 0.175
LINE_SCORE = 100
COMBO_STEP = 0.5
THEME_CELL_SCORE = 15
GREAT_BASE_CHANCE = 0.04
GREAT_SCORE_DIVISOR = 12000
GREAT_BASE_CAP = 0.35
GREAT_FINAL_CAP = 0.6
FINAL_DAY_MULTIPLIER = 2
GROWTH_SCORE_DIVISOR = 100
LARVA3_GROWTH_MULTIPLIER = 1.5
GREAT_GROWTH_MULTIPLIER = 2
CUES = {
    "banana": "バナナの匂い",
    "apple_vinegar": "りんご酢の匂い",
    "yeast": "酵母の匂い",
    "grape": "ぶどうの匂い",
    "blue_light": "青い光の合図",
}
VALENCES = {"reward": "あまいごほうび", "punish": "にがいごはん"}
TRAINING_SIZES = {2: 5, 3: 5, 4: 6, 5: 6, 6: 6, 7: 6}
CHECKPOINT_COUNTS = {5: 5, 6: 7}
TRAINING_SCALE_CELLS = 25
TRAINING_THREE_STAR_MS = 12000
TRAINING_TWO_STAR_MS = 25000
HIRAMEKI_CHANCE = 0.10
HIRAMEKI_THREE_STAR_CHANCE = 0.15
LEARNING_PER_STAR = 0.12
HIRAMEKI_MULTIPLIER = 2
SKILL_THRESHOLD = 0.6
# Only banana_search is named in the spec; other stable IDs complete that table.
SKILL_UNLOCKS = {
    "banana": {
        "reward": ("banana_search", "バナナさがし"),
        "punish": ("banana_avoid", "バナナよけ"),
    },
    "apple_vinegar": {
        "reward": ("apple_search", "りんごさがし"),
        "punish": ("apple_avoid", "りんごよけ"),
    },
    "yeast": {"reward": ("yeast_search", "酵母さがし"), "punish": ("yeast_avoid", "酵母よけ")},
    "grape": {"reward": ("grape_search", "ぶどうさがし"), "punish": ("grape_avoid", "ぶどうよけ")},
    "blue_light": {"reward": ("light_search", "光さがし"), "punish": ("light_avoid", "光よけ")},
}
CLEANING_PERIODS = {2: 1400, 3: 1300, 4: 1200, 5: 1100}
CLEANING_TAPS = 3
CLEANING_TIME_LIMIT_MS = 10000
CLEANING_ZONE = {"center": 0.5, "perfect": 0.06, "good": 0.15}
CLEANING_POINTS = {"perfect": 34, "good": 22, "miss": 5}
TEMPERATURE_PERIOD_MS = 1600
TEMPERATURE_CENTER_C = 25.0
TEMPERATURE_AMP_C = 7.0
TEMPERATURE_PENALTY = 20
TEMPERATURE_GRADES = ((90, "perfect"), (60, "good"), (0, "miss"))
SITE_HINT_ACCURACY = 0.70
SITE_TEXT_POOLS = (
    (
        ("びんの壁の上のほう", "乾いていて、えさから遠い"),
        ("壁の乾いたところ", "えさから離れている"),
    ),
    (("えさの表面", "しめっていて、やわらかい"), ("えさのそば", "しっとりしている")),
    (("ふたのすぐ下", "明るくて、風が通る"), ("びんの口の近く", "光が入って風が通る")),
)
SITE_HINTS = (
    "えさから離れた乾いた場所を探してみよう。",
    "しめったやわらかい場所に注目してみよう。",
    "明るくて風の通る場所を探してみよう。",
)
SITE_IDS = ("a", "b", "c")
REASON_CODES = frozenset(
    (
        "not_in_hand",
        "already_placed",
        "out_of_bounds",
        "cell_occupied",
        "time_exceeded",
        "non_monotonic_time",
        "wrong_length",
        "not_adjacent",
        "revisit",
        "bad_start",
        "bad_end",
        "checkpoint_order",
        "wrong_tap_count",
    )
)
