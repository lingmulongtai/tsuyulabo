# ツユラボ Tsuyu Labo

> 本物のハエの脳で育つ。毎週1匹、卵から育てる育成研究ゲーム。

朝・昼・夜にごはんを作り、パズルでしつけ、1週間で卵を成虫まで育てる。日曜の夜は羽化と研究発表会。
育てた子は研究チームに加わり、フレンドと競い、次の世代へつながっていく。

名前の由来：ショウジョウバエの学名 *Drosophila* は、ギリシャ語で「露を好むもの」。

## しくみ

- **Web アプリ**（`apps/web`）: Next.js + TypeScript。演出は PixiJS、音は Web Audio。
- **ゲーム API**（`services/api`）: FastAPI。時刻・採点・報酬・通貨はすべてサーバーで決める。
- **脳エンジン**（`services/brain`）: PyTorch で一から書いたスパイキング・ニューラルネット。しつけでキノコ体のつながりが変わり、個体差が行動に出る。
- **研究員シオリ**（`services/shiori`）: 自作の LLM エージェント。すべての説明に記録や実験の ID をつけ、実在しない根拠は表示しない。
- **ワーカー**（`services/worker`）: Redis キューで脳とシオリの重い処理を回す。

詳しくは [開発計画](docs/DEVELOPMENT_PLAN.md) と [仕様](docs/specs/) を参照。

## 開発

```bash
docker compose up
```

## データの出典

- 成虫オスの配線: MaleCNS v1.0（FlyEM / HHMI Janelia ほか、CC-BY、Berg et al., 2026, Cell）
- 幼虫の配線: Winding et al., 2023, Science

アルファ版は、上記の回路の形に合わせて細胞数を小さくした合成配線（`toy-v0`）を使っています。
