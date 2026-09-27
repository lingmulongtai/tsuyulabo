# スクリーンショット


[再撮影の手順](../infra.md#readme-screenshots-and-play-video) ／ [プロジェクトに戻る](../../README.md)

実際のローカル API で1週間をプレイし、同じ場面をライト／ダークで撮影。
画面は 390 × 844、画像は2倍の 780 × 1688 ピクセルです。
日付の進行には開発用の時計を使っています。

プレイ動画（75 秒のハイライト版）は、フル機能の FFmpeg があるときだけ作られます（Playwright 同梱の FFmpeg では変換できない）。
`winget install ffmpeg` などで入れてから `FFMPEG_PATH=<ffmpeg.exe> node apps/web/e2e/helpers/encode-media.mjs` を実行すると、
撮影済みの `eval-results/media/playthrough-raw.webm` から `docs/media/playthrough.webm` を作れます。
ランク・羽化・行動はゲームの実際の結果、脳の表示は合成配線 `toy-v0` のモデルです。
シオリはローカルスタックに設定されたプロバイダーで回答します（標準設定は Mock）。

| 場面 | ライト | ダーク |
| --- | :---: | :---: |
| 研究3日目・2齢幼虫のホーム | <img src="screens/home-light.webp" alt="幼虫のホーム、ライト" width="195"> | <img src="screens/home-dark.webp" alt="幼虫のホーム、ダーク" width="195"> |
| ごはん・ライン消去 | <img src="screens/meal-light.webp" alt="ごはんのライン消去、ライト" width="195"> | <img src="screens/meal-dark.webp" alt="ごはんのライン消去、ダーク" width="195"> |
| しつけ・回路をつなぐ途中 | <img src="screens/training-light.webp" alt="回路パズルの途中、ライト" width="195"> | <img src="screens/training-dark.webp" alt="回路パズルの途中、ダーク" width="195"> |
| しつけ・★★★達成 | <img src="screens/training-result-light.webp" alt="しつけの三つ星結果、ライト" width="195"> | <img src="screens/training-result-dark.webp" alt="しつけの三つ星結果、ダーク" width="195"> |
| そうじ・緑のゾーンをねらう | <img src="screens/cleaning-light.webp" alt="そうじのタイミング、ライト" width="195"> | <img src="screens/cleaning-dark.webp" alt="そうじのタイミング、ダーク" width="195"> |
| 温度あわせ・25℃でストップ | <img src="screens/temperature-light.webp" alt="25℃の温度ゲージ、ライト" width="195"> | <img src="screens/temperature-dark.webp" alt="25℃の温度ゲージ、ダーク" width="195"> |
| 研究発表会・ランク発表 | <img src="screens/presentation-light.webp" alt="研究発表会、ライト" width="195"> | <img src="screens/presentation-dark.webp" alt="研究発表会、ダーク" width="195"> |
| 羽化・成虫との出会い | <img src="screens/eclosion-light.webp" alt="羽化の結果、ライト" width="195"> | <img src="screens/eclosion-dark.webp" alt="羽化の結果、ダーク" width="195"> |
| 成虫・行動のアニメーション | <img src="screens/adult-light.webp" alt="成虫の観察ノート、ライト" width="195"> | <img src="screens/adult-dark.webp" alt="成虫の観察ノート、ダーク" width="195"> |
| 脳の観察・糖のシナリオを再生 | <img src="screens/brain-light.webp" alt="糖への神経反応、ライト" width="195"> | <img src="screens/brain-dark.webp" alt="糖への神経反応、ダーク" width="195"> |
| 研究チーム・集まった材料袋 | <img src="screens/team-light.webp" alt="開けられる材料袋、ライト" width="195"> | <img src="screens/team-dark.webp" alt="開けられる材料袋、ダーク" width="195"> |
| 図鑑・行動と系統の発見 | <img src="screens/zukan-light.webp" alt="ツユの図鑑、ライト" width="195"> | <img src="screens/zukan-dark.webp" alt="ツユの図鑑、ダーク" width="195"> |
| 今日の回路・全員同じ問題 | <img src="screens/daily-light.webp" alt="今日の回路、ライト" width="195"> | <img src="screens/daily-dark.webp" alt="今日の回路、ダーク" width="195"> |
| 迷路レース・脳が決める走り | <img src="screens/race-light.webp" alt="迷路レースのリプレイ、ライト" width="195"> | <img src="screens/race-dark.webp" alt="迷路レースのリプレイ、ダーク" width="195"> |
| シオリ・研究記録に基づく回答 | <img src="screens/shiori-light.webp" alt="シオリの回答、ライト" width="195"> | <img src="screens/shiori-dark.webp" alt="シオリの回答、ダーク" width="195"> |
