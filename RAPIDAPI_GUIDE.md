# RapidAPI登録ガイド — Japan Used Car Price Stats API

goo-net-car-scraperの`statsMode`を、RapidAPIで販売するための手順書。

## APIの仕様

| 項目 | 内容 |
|---|---|
| 名称 | Japan Used Car Price Stats API |
| 機能 | 日本の現在の中古車相場（モデル別の価格統計）を返す |
| バックエンド | Apify同期API（既に実証済み・12〜17秒応答） |
| 対象顧客 | 中古車輸出業者・市場調査・ディーラー価格ベンチマーク |

## バックエンド（実証済みエンドポイント）

```bash
curl -X POST "https://api.apify.com/v2/acts/bgm5Gxn4BeBmoO7xD/run-sync-get-dataset-items?token=APIFY_TOKEN&timeout=120" \
  -H "Content-Type: application/json" \
  -d '{"statsMode": true, "statsKeyword": "N-BOX", "maxItems": 30, "maxPages": 1}'
```

レスポンス例:
```json
{
  "statsType": "goo-net-car-price",
  "keyword": "N-BOX",
  "count": 5,
  "priceMin": 230000,
  "priceMax": 1907000,
  "priceAvg": 974400,
  "priceMedian": 596000,
  "sampleItems": [{"title": "...", "price": 230000, "detailUrl": "...", "shop": "..."}]
}
```

## 登録手順（30分）

### 1. アカウント作成
1. https://rapidapi.com/ にアクセス → Sign Up（GitHub/Google連携が簡単）
2. プロフィールを完成（ニックネーム・国）

### 2. API登録
1. ダッシュボード → **My APIs** → **Add New API**
2. API名: `Japan Used Car Price Stats API`
3. カテゴリ: Automotive または Data
4. 説明文（英語・SEO用）:
   "Real-time price statistics for used cars in Japan. Get min/median/average prices per model from goo-net.com, Japan's largest used car portal. Ideal for exporters, market researchers, and dealer pricing benchmarks."

### 3. エンドポイント定義（2つ）
| メソッド | パス | パラメータ |
|---|---|---|
| POST | `/car-price-stats` | `statsKeyword` (required, 例: N-BOX), `bodyType` (任意), `maxItems` (default 30) |
| GET | `/health` | なし（"OK"を返すだけ） |

バックエンドURLに、Apify同期APIのURLを設定する。
（Apify同期APIをそのままプロキシする形。`token`はRapidAPI側のヘッダー設定で注入）

### 4. 価格設定
- 推奨: **$0.02/リクエスト**（Apify実行コスト約$0.01 + マージン）
- プラン構成例: Free（10件/月）/ Basic $9.99（500件）/ Pro $49.99（3,000件）

### 5. 公開とテスト
1. テストコンソールで `statsKeyword=N-BOX` を実行 → 200 OK確認
2. Publish API → レビュー後公開

## 注意点

- **RapidAPI手数料は20%**（$0.02のうち$0.004）— 価格設定に織り込み済み
- **Apify実行コスト**: 1リクエスト=アクター起動$0.00005 + データ件数分。statsKeyword指定時は1〜3ページ分（約$0.01）
- 負荷分散: キャッシュを入れたい場合は、同一キーワードの結果を1日キャッシュ（毎日クロールのため）
- 言語: 英語のみでOK（中南米向けに西語説明も加えると良い）

## 期待収益

- 中位: 月$50〜300（ニッチAPIとして）
- 上位: 月$1,000+（輸出業者が定期的に利用する場合）
- 競合: RapidAPIに「Japan used car price」系APIはほぼ存在しない（2026-08調査）
