export interface paths {
    "/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/adults": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Adults */
        get: operations["list_adults_v1_adults_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/adults/{adult_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_v1_adults__adult_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Rename */
        patch: operations["rename_v1_adults__adult_id__patch"];
        trace?: never;
    };
    "/v1/adults/{adult_id}/level-up": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Level Up */
        post: operations["level_up_v1_adults__adult_id__level_up_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/auth/guest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Guest */
        post: operations["create_guest_v1_auth_guest_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/clock": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Clock */
        get: operations["read_clock_v1_clock_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/daily-circuit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Today */
        get: operations["today_v1_daily_circuit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/daily-circuit/ranking": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ranking */
        get: operations["ranking_v1_daily_circuit_ranking_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/daily-circuit/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start */
        post: operations["start_v1_daily_circuit_start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/daily-circuit/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit */
        post: operations["submit_v1_daily_circuit_submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/dev/time": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Time */
        get: operations["read_time_v1_dev_time_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/dev/time/advance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Advance Time */
        post: operations["advance_time_v1_dev_time_advance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/dev/time/reset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Time */
        post: operations["reset_time_v1_dev_time_reset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/flies/{fly_id}/behavior": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Behavior */
        get: operations["behavior_v1_flies__fly_id__behavior_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/flies/{fly_id}/brain/activity": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Activity
         * @description Observe a copy of an owned adult or active week's larva, in 20 equal windows.
         */
        get: operations["activity_v1_flies__fly_id__brain_activity_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/flies/{fly_id}/experiments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Experiment */
        post: operations["experiment_v1_flies__fly_id__experiments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/friends": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Friends */
        get: operations["list_friends_v1_friends_get"];
        put?: never;
        /** Add Friend */
        post: operations["add_friend_v1_friends_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/friends/{friend_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove Friend */
        delete: operations["remove_friend_v1_friends__friend_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/friends/{friend_id}/gift": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Gift */
        post: operations["gift_v1_friends__friend_id__gift_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/friends/{friend_id}/lab": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Lab */
        get: operations["lab_v1_friends__friend_id__lab_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/friends/{friend_id}/like": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Like */
        post: operations["like_v1_friends__friend_id__like_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/home": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Home */
        get: operations["home_v1_home_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/inventory": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Inventory */
        get: operations["inventory_v1_inventory_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Job */
        get: operations["read_job_v1_jobs__job_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_v1_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Me */
        patch: operations["patch_me_v1_me_patch"];
        trace?: never;
    };
    "/v1/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Notifications */
        get: operations["notifications_v1_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/odds": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Odds */
        get: operations["odds_v1_odds_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/puzzles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Issue */
        post: operations["issue_v1_puzzles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/puzzles/{puzzle_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit */
        post: operations["submit_v1_puzzles__puzzle_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/shiori/ask": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Ask */
        post: operations["ask_v1_shiori_ask_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/shiori/memo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Memo */
        get: operations["read_memo_v1_shiori_memo_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sleep/end": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** End */
        post: operations["end_v1_sleep_end_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/sleep/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start */
        post: operations["start_v1_sleep_start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/team": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Team */
        get: operations["get_team_v1_team_get"];
        /** Set Team */
        put: operations["set_team_v1_team_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/team/collect": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Collect */
        post: operations["collect_v1_team_collect_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/weeks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Past Weeks */
        get: operations["past_weeks_v1_weeks_get"];
        put?: never;
        /** Start Week */
        post: operations["start_week_v1_weeks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/weeks/current": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Current */
        get: operations["read_current_v1_weeks_current_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/weeks/current/eclose": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Eclose */
        post: operations["eclose_v1_weeks_current_eclose_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/weeks/current/presentation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Presentation */
        get: operations["read_presentation_v1_weeks_current_presentation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/zukan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Zukan */
        get: operations["zukan_v1_zukan_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** ActivityEdge */
        ActivityEdge: {
            /** Post Group */
            post_group: string;
            /** Pre Group */
            pre_group: string;
            /**
             * Sign
             * @enum {string}
             */
            sign: "excitatory" | "inhibitory";
            /**
             * Weight Sum
             * @description Signed learned wiring sum before individual gains
             */
            weight_sum: number;
        };
        /** ActivityGroup */
        ActivityGroup: {
            /** Circuit */
            circuit: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "sensory" | "inter" | "output" | "modulatory";
            /** Name */
            name: string;
            /**
             * Rates
             * @description Mean firing rate per neuron in Hz, one per window
             */
            rates: number[];
        };
        /** AddFriend */
        AddFriend: {
            /** Friend Code */
            friend_code: string;
        };
        /** AdvanceRequest */
        AdvanceRequest: {
            /** Hours */
            hours?: number | null;
            /** To */
            to?: ("next_slot" | "next_day" | "eclosion") | null;
        };
        /** AskRequest */
        AskRequest: {
            /** Question */
            question: string;
        };
        /** BrainActivity */
        BrainActivity: {
            /** Duration Ms */
            duration_ms: number;
            /** Edges */
            edges: components["schemas"]["ActivityEdge"][];
            /** Groups */
            groups: components["schemas"]["ActivityGroup"][];
            /**
             * Scenario
             * @enum {string}
             */
            scenario: "rest" | "sugar" | "bitter" | "sugar+bitter" | "looming" | "light_left" | "light_right" | "antenna_touch" | "liked_odor" | "disliked_odor";
        };
        /** DailyAttempt */
        DailyAttempt: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Started At
             * Format: date-time
             */
            started_at: string;
        };
        /** DailyAvatar */
        DailyAvatar: {
            /**
             * Sex
             * @enum {string}
             */
            sex: "m" | "f";
            /**
             * Strain
             * @enum {string}
             */
            strain: "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
        };
        /** DailyCheckpoint */
        DailyCheckpoint: {
            /** Cell */
            cell: number;
            /** K */
            k: number;
        };
        /** DailyCircuitParams */
        DailyCircuitParams: {
            /** Checkpoints */
            checkpoints: components["schemas"]["DailyCheckpoint"][];
            /**
             * Cue
             * @constant
             */
            cue: "banana";
            /**
             * N
             * @constant
             */
            n: 7;
            /**
             * Valence
             * @constant
             */
            valence: "reward";
        };
        /** DailyCircuitResponse */
        DailyCircuitResponse: {
            attempt: components["schemas"]["DailyAttempt"] | null;
            /**
             * Day
             * Format: date
             */
            day: string;
            my_result: components["schemas"]["DailyResult"] | null;
            params: components["schemas"]["DailyCircuitParams"];
            /**
             * Resets At
             * Format: date-time
             */
            resets_at: string;
            /**
             * Server Now
             * Format: date-time
             */
            server_now: string;
        };
        /** DailyRanking */
        DailyRanking: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Entries */
            entries: components["schemas"]["DailyRankingEntry"][];
        };
        /** DailyRankingEntry */
        DailyRankingEntry: {
            avatar: components["schemas"]["DailyAvatar"];
            /** Display Name */
            display_name: string;
            /** Elapsed Ms */
            elapsed_ms: number;
            /** Is Me */
            is_me: boolean;
            /** Rank */
            rank: number;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /** User Id */
            user_id: string;
        };
        /** DailyResult */
        DailyResult: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Elapsed Ms */
            elapsed_ms: number;
            /** Shizuku */
            shizuku: number;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
        };
        /** DailyStartRequest */
        DailyStartRequest: {
            /**
             * Day
             * Format: date
             */
            day: string;
        };
        /** DailySubmitRequest */
        DailySubmitRequest: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Elapsed Ms */
            elapsed_ms: number;
            /** Path */
            path: number[];
        };
        /** ExperimentRequest */
        ExperimentRequest: {
            /**
             * Cue
             * @default banana
             * @enum {string}
             */
            cue: "banana" | "apple_vinegar" | "yeast" | "grape" | "blue_light";
            /**
             * Kind
             * @default odor_choice
             * @constant
             */
            kind: "odor_choice";
            /**
             * Trials
             * @default 100
             */
            trials: number;
        };
        /** GuestRequest */
        GuestRequest: {
            /** Display Name */
            display_name: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** IssueRequest */
        IssueRequest: {
            /** Cue */
            cue?: ("banana" | "apple_vinegar" | "yeast" | "grape" | "blue_light") | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "meal" | "training" | "cleaning" | "temperature" | "pupation_site";
            /** Valence */
            valence?: ("reward" | "punish") | null;
        };
        /** ProfilePatch */
        ProfilePatch: {
            /** Display Name */
            display_name?: string | null;
            /** Favorite Adult Id */
            favorite_adult_id?: string | null;
            /** Title */
            title?: string | null;
        };
        /** RenameAdult */
        RenameAdult: {
            /** Name */
            name: string;
        };
        /** SendGift */
        SendGift: {
            /** Amount */
            amount: number;
            /** Material */
            material: string;
        };
        /** TeamRequest */
        TeamRequest: {
            /** Adult Ids */
            adult_ids: string[];
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** @enum {string} */
        Slot: "morning" | "noon" | "night";
        /** @enum {string} */
        Stage: "egg" | "larva1" | "larva2" | "larva3" | "wandering" | "pupa" | "adult";
        /** @enum {string} */
        ActionKind: "meal" | "training" | "cleaning" | "temperature" | "pupation_site" | "sleep" | "wake";
        /** @enum {string} */
        TodoStatus: "done" | "available" | "locked";
        /** @enum {string} */
        WeekRank: "normal" | "silver" | "gold" | "rainbow";
        TodoItem: {
            action: components["schemas"]["ActionKind"];
            status: components["schemas"]["TodoStatus"];
            slot?: components["schemas"]["Slot"] | null;
            remaining?: number | null;
            available_at?: string | null;
        };
        Balances: {
            shizuku: number;
            research_points: number;
            kohaku: number;
        };
        Fly: {
            stage: components["schemas"]["Stage"];
            hunger: number;
            cleanliness: number;
            mood: number;
            mood_label: string;
            growth: number;
        };
        WeekSummary: {
            id: string;
            research_day: number;
            stage: components["schemas"]["Stage"];
            ready_to_eclose: boolean;
            care_miss: number;
            points_so_far: number;
        };
        Week: components["schemas"]["WeekSummary"] & {
            started_at: string;
            status: string;
            fly: components["schemas"]["Fly"];
            days: {
                research_day: number;
                events: {
                    [key: string]: unknown;
                }[];
            }[];
        };
        PastWeek: {
            id: string;
            rank: components["schemas"]["WeekRank"] | null;
            points: number;
            adult_id: string | null;
            started_at: string;
            eclosed_at: string | null;
        };
        Adult: {
            id: string;
            name: string;
            /** @enum {string} */
            sex: "m" | "f";
            /** @enum {string} */
            strain: "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
            stars: number;
            traits: string[];
            skills: {
                [key: string]: boolean;
            };
            level: number;
            preferences: {
                [key: string]: number;
            };
            week_id: string;
            subskills: string[];
            level_cap: number;
            exp: number;
            energy: number;
            created_at: string;
        };
        TeamMemberSummary: components["schemas"]["Adult"] & {
            slot: number;
            bag: {
                [key: string]: number;
            };
            shizuku: number;
            pending_exp: number;
        };
        Team: {
            members: components["schemas"]["TeamMemberSummary"][];
            bag_total: number;
            collectable: boolean;
        };
        Memo: {
            id?: string;
            text: string;
            evidence: string[];
        };
        HomeData: {
            clock: {
                game_now: string;
                slot: components["schemas"]["Slot"];
                research_day: number | null;
                weekday_label: string | null;
            };
            week: components["schemas"]["WeekSummary"] | null;
            fly: components["schemas"]["Fly"] | null;
            todo: components["schemas"]["TodoItem"][];
            balances: components["schemas"]["Balances"];
            team: components["schemas"]["Team"];
            shiori: {
                memo: components["schemas"]["Memo"] | null;
            };
        };
        Profile: {
            id: string;
            display_name: string;
            friend_code: string;
            title: string | null;
            favorite_adult_id: string | null;
            balances: components["schemas"]["Balances"];
            research_rank: number | null;
        };
        Guest: {
            user: components["schemas"]["Profile"];
            token: string;
        };
        Puzzle: {
            puzzle_id: string;
            /** @enum {string} */
            kind: "meal" | "training" | "cleaning" | "temperature" | "pupation_site";
            params: {
                [key: string]: unknown;
            };
            issued_at: string;
            expires_at: string;
        };
        PuzzleResult: {
            valid?: boolean;
            score?: number;
            lines?: number;
            max_combo?: number;
            theme_cells?: number;
            great_success?: boolean;
            stars?: number;
            hirameki?: boolean;
            hit?: boolean;
            grades?: ("perfect" | "good" | "miss")[];
            /** @enum {string} */
            grade?: "perfect" | "good" | "miss";
            effects?: {
                [key: string]: number | boolean;
            };
            seq: number;
            event_id: string;
        };
        Presentation: {
            meal_points: number;
            training_points: number;
            care_points: number;
            care_miss: number;
            penalty: number;
            points: number;
            rank: components["schemas"]["WeekRank"];
            shizuku: number;
            research_points: number;
        };
        Eclosion: {
            omen_sequence: number[];
            tier: number;
            adult: {
                id: string;
                name: string;
                /** @enum {string} */
                sex: "m" | "f";
                /** @enum {string} */
                strain: "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
                stars: number;
                traits: string[];
                skills: {
                    [key: string]: boolean;
                };
                level: number;
                preferences: {
                    [key: string]: number;
                };
            };
        };
        SleepStart: {
            id: string;
            started_at: string;
        };
        SleepEnd: {
            id: string;
            hours: number;
            bonus: number;
            energy_recovered: {
                [key: string]: number;
            };
        };
        Collection: {
            materials: {
                [key: string]: number;
            };
            shizuku: number;
            exp: {
                [key: string]: number;
            };
            team: components["schemas"]["Team"];
        };
        Friend: {
            id: string;
            display_name: string;
            friend_code: string;
            title: string | null;
        };
        Lab: {
            user: {
                id: string;
                display_name: string;
            };
            adults: components["schemas"]["Adult"][];
            team: components["schemas"]["Team"];
            week: {
                stage: components["schemas"]["Stage"];
                research_day: number;
                fly: components["schemas"]["Fly"];
            } | null;
        };
        Notification: {
            id: string;
            kind: string;
            payload: {
                [key: string]: unknown;
            };
            created_at: string;
            read_at: string | null;
        };
        Zukan: {
            behaviors: {
                id: string;
                observed: boolean;
            }[];
            strains: {
                /** @enum {string} */
                id: "wild" | "white" | "yellow" | "ebony" | "curly" | "vestigial";
                name: string;
                observed: boolean;
            }[];
            completion: {
                behaviors: number;
                strains: number;
            };
        };
        Job: {
            id: string;
            kind: string;
            /** @enum {string} */
            status: "pending" | "running" | "succeeded" | "failed";
            result: {
                [key: string]: unknown;
            } | null;
            error: {
                [key: string]: unknown;
            } | null;
            created_at: string;
            finished_at: string | null;
        };
        ApiErrorBody: {
            error: {
                code: string;
                message: string;
                details?: {
                    [key: string]: unknown;
                };
            };
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_healthz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_adults_v1_adults_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Adult"][];
                };
            };
        };
    };
    detail_v1_adults__adult_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                adult_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Adult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rename_v1_adults__adult_id__patch: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                adult_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RenameAdult"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Adult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    level_up_v1_adults__adult_id__level_up_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                adult_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Adult"] & {
                        cost: number;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_guest_v1_auth_guest_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuestRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Guest"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_clock_v1_clock_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string | number;
                    };
                };
            };
        };
    };
    today_v1_daily_circuit_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DailyCircuitResponse"];
                };
            };
        };
    };
    ranking_v1_daily_circuit_ranking_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DailyRanking"];
                };
            };
        };
    };
    start_v1_daily_circuit_start_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DailyStartRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DailyCircuitResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_v1_daily_circuit_submit_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DailySubmitRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DailyResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_time_v1_dev_time_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string | number;
                    };
                };
            };
        };
    };
    advance_time_v1_dev_time_advance_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdvanceRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string | number;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reset_time_v1_dev_time_reset_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string | number;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    behavior_v1_flies__fly_id__behavior_get: {
        parameters: {
            query?: {
                scenario?: string;
            };
            header?: never;
            path: {
                fly_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: number;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activity_v1_flies__fly_id__brain_activity_get: {
        parameters: {
            query?: {
                scenario?: "rest" | "sugar" | "bitter" | "sugar+bitter" | "looming" | "light_left" | "light_right" | "antenna_touch" | "liked_odor" | "disliked_odor";
            };
            header?: never;
            path: {
                fly_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BrainActivity"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    experiment_v1_flies__fly_id__experiments_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                fly_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExperimentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_friends_v1_friends_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Friend"][];
                };
            };
        };
    };
    add_friend_v1_friends_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AddFriend"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_friend_v1_friends__friend_id__delete: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                friend_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: boolean;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    gift_v1_friends__friend_id__gift_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                friend_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SendGift"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    lab_v1_friends__friend_id__lab_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                friend_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Lab"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    like_v1_friends__friend_id__like_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                friend_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: boolean;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    home_v1_home_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeData"];
                };
            };
        };
    };
    inventory_v1_inventory_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: number;
                    };
                };
            };
        };
    };
    read_job_v1_jobs__job_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Job"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_v1_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Profile"];
                };
            };
        };
    };
    patch_me_v1_me_patch: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfilePatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Profile"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    notifications_v1_notifications_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Notification"][];
                };
            };
        };
    };
    odds_v1_odds_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    issue_v1_puzzles_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IssueRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Puzzle"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_v1_puzzles__puzzle_id__submit_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path: {
                puzzle_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PuzzleResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ask_v1_shiori_ask_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AskRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_memo_v1_shiori_memo_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Memo"] | null;
                };
            };
        };
    };
    end_v1_sleep_end_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SleepEnd"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_v1_sleep_start_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SleepStart"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_team_v1_team_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Team"];
                };
            };
        };
    };
    set_team_v1_team_put: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TeamRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Team"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    collect_v1_team_collect_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Collection"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    past_weeks_v1_weeks_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PastWeek"][];
                };
            };
        };
    };
    start_week_v1_weeks_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Week"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_current_v1_weeks_current_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Week"];
                };
            };
        };
    };
    eclose_v1_weeks_current_eclose_post: {
        parameters: {
            query?: never;
            header: {
                "Idempotency-Key": string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Eclosion"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_presentation_v1_weeks_current_presentation_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Presentation"];
                };
            };
        };
    };
    zukan_v1_zukan_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Zukan"];
                };
            };
        };
    };
}
