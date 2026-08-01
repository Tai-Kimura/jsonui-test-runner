# jsonui-test-runner 開発ガイド

## プロジェクト概要

JsonUIライブラリ（SwiftJsonUI / KotlinJsonUI / ReactJsonUI）向けのクロスプラットフォームUIテスト自動化ツール。

### 目的

- JsonUIで作成されたUIを、iOS・Android・Webで統一的にテスト
- AIエージェントによるテストケース自動生成
- CI/CD、エミュレータ、実機での実行をサポート

## アーキテクチャ

```
┌─────────────────────────────────────┐
│     Test Definition (JSON)          │
│  - Screen Tests (1:1 with layout)   │
│  - Flow Tests (N:1 cross-screen)    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         Core Runner (TypeScript)     │
│  - JSON Parser                       │
│  - Test Orchestrator                 │
│  - Reporter                          │
└─────────────────┬───────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐   ┌─────────┐   ┌─────────┐
│  iOS  │   │ Android │   │   Web   │
│Driver │   │ Driver  │   │ Driver  │
└───┬───┘   └────┬────┘   └────┬────┘
    │            │              │
    ▼            ▼              ▼
 XCUITest   UIAutomator    Playwright
```

## 実装フェーズ

### Phase 1: テストJSON仕様・スキーマ作成
- [ ] screen-test.schema.json の作成
- [ ] flow-test.schema.json の作成
- [ ] actions.schema.json の作成（アクション・アサーション定義）
- [ ] サンプルテストケースの作成

### Phase 2: Web（Playwright）ドライバー実装
- [ ] Playwright環境セットアップ
- [ ] アクション実装（tap, input, scroll等）
- [ ] アサーション実装（visible, text, state等）
- [ ] ReactJsonUIとの連携テスト

### Phase 3: iOS（XCUITest）ドライバー実装
- [ ] XCUITest環境セットアップ
- [ ] アクション実装
- [ ] アサーション実装
- [ ] SwiftJsonUIとの連携テスト
- [ ] id属性 → accessibilityIdentifier のマッピング確認

### Phase 4: Android（UIAutomator）ドライバー実装
- [ ] UIAutomator環境セットアップ
- [ ] アクション実装
- [ ] アサーション実装
- [ ] KotlinJsonUIとの連携テスト

### Phase 5: CI/CD統合
- [ ] GitHub Actions ワークフロー作成
- [ ] iOS Simulator での自動テスト
- [ ] Android Emulator での自動テスト
- [ ] Playwright での自動テスト
- [ ] テストレポート生成・アップロード

### Phase 6: AIエージェント連携
- [ ] テスト生成エージェントのプロンプト設計
- [ ] レイアウトJSON解析ロジック
- [ ] 仕様書（Markdown）解析ロジック
- [ ] テストケース生成・出力

## テストJSON仕様

### ファイル構成

```
tests/
├── screens/              # 画面単体テスト（レイアウトJSONと1:1対応）
│   ├── Login.test.json   # ← Layouts/Login.json に対応
│   └── Home.test.json    # ← Layouts/Home.json に対応
└── flows/                # フローテスト（複数画面をまたぐ）
    ├── login-flow.test.json
    └── purchase-flow.test.json
```

### 画面単体テスト形式

```json
{
  "$schema": "../schemas/screen-test.schema.json",
  "type": "screen",
  "source": {
    "layout": "Layouts/Login.json",
    "document": "specs/Login.md"
  },
  "metadata": {
    "name": "ログイン画面テスト",
    "generatedAt": "2026-01-12T10:00:00Z",
    "generatedBy": "test-agent-v1"
  },
  "initialState": {
    "viewModel": {
      "email": "",
      "password": "",
      "isLoading": false
    }
  },
  "cases": [
    {
      "name": "初期表示確認",
      "steps": [
        { "assert": "visible", "id": "email_input" },
        { "assert": "visible", "id": "password_input" },
        { "assert": "disabled", "id": "login_button" }
      ]
    },
    {
      "name": "ログイン成功",
      "steps": [
        { "action": "input", "id": "email_input", "value": "test@example.com" },
        { "action": "input", "id": "password_input", "value": "password123" },
        { "action": "tap", "id": "login_button" },
        { "assert": "state", "path": "isLoading", "equals": true },
        { "action": "waitFor", "id": "home_screen", "timeout": 5000 }
      ]
    }
  ]
}
```

### フローテスト形式

```json
{
  "$schema": "../schemas/flow-test.schema.json",
  "type": "flow",
  "sources": [
    { "layout": "Layouts/Login.json", "document": "specs/Login.md" },
    { "layout": "Layouts/Home.json", "document": "specs/Home.md" }
  ],
  "metadata": {
    "name": "ログイン〜ホーム遷移フロー"
  },
  "steps": [
    { "screen": "Login", "action": "input", "id": "email_input", "value": "test@example.com" },
    { "screen": "Login", "action": "input", "id": "password_input", "value": "pass123" },
    { "screen": "Login", "action": "tap", "id": "login_button" },
    { "screen": "Home", "assert": "visible", "id": "welcome_label" }
  ]
}
```

### アクション一覧

`?` 付きパラメータはオプション、`=` は既定値。表は `schemas/actions.schema.json`（SSoT）の `x-doc` から `npm run docs` で生成される — 手編集禁止。

<!-- generated:actions -->
| アクション | 説明 | パラメータ | プラットフォーム |
|---|---|---|---|
| `tap` | 要素をタップ | `id`, `text?`, `retryTapIfNoChange?=false` | `retryTapIfNoChange`（ゴーストタップ緩和）は Web では受理のみ・no-op |
| `doubleTap` | 要素をダブルタップ | `id` | - |
| `longPress` | 要素を長押し | `id`, `duration?=500` | - |
| `input` | 指定要素にテキスト入力 | `id`, `value` | - |
| `typeText` | フォーカス中の欄へキーボード入力（要素 id 不要。不可視のコード入力欄など向け） | `value`, `timeout?` | - |
| `clear` | 入力内容をクリア | `id` | - |
| `scroll` | 指定方向へスクロール | `id`, `direction`, `amount?` | - |
| `scrollUntilVisible` | 要素が見えるまでスクロール（終端到達で即失敗） | `id`, `container?`, `direction?=down`, `timeout?=20000` | - |
| `swipe` | 要素をスワイプ | `id`, `direction` | - |
| `waitFor` | 要素の出現を待機 | `id`, `timeout?=5000` | - |
| `waitForAny` | いずれかの要素の出現を待機 | `ids`, `timeout?=5000` | - |
| `wait` | 指定時間待機 | `ms` | - |
| `back` | 戻る操作 | - | - |
| `hideKeyboard` | ソフトキーボードを閉じる（未表示なら no-op） | - | - |
| `screenshot` | スクリーンショットを保存 | `name` | - |
| `alertTap` | アラート／ダイアログのボタンをタップ | `button`, `timeout?=5000` | - |
| `selectOption` | ドロップダウン／ピッカーから選択 | `id`, `value?`, `index?`, `timeout?=5000` | - |
| `tapItem` | コレクション内のアイテムをタップ | `id`, `index`, `timeout?=5000` | - |
| `selectTab` | タブを選択 | `id`, `index`, `timeout?=5000` | - |
| `readText` | 要素のテキストを実行時変数に読む（`@{変数名}` で後続参照） | `id`, `variable`, `timeout?=5000` | - |
| `repeat` | ステップ群を繰り返す（`times`／`while` 併用可、安全上限 100 回） | `times?`, `while?`, `steps` | - |
| `retry` | 失敗時にブロック全体を再実行 | `maxRetries?=1`, `steps` | - |
| `setLocation` | モック位置情報を設定 | `latitude`, `longitude` | iOS: SDK 依存 ／ Android: best effort ／ Web: setGeolocation |
| `addMedia` | メディアフィクスチャを端末に追加（png/jpg/jpeg/gif/mp4。蓄積するため件数でなく存在を検証） | `paths`, `id?`, `timeout?` | Android: ギャラリー（MediaStore）／ iOS: PhotoKit〈シミュレータ限定・photos-add 許可は CLI が自動付与〉／ Web: file input |
| `setMocks` | エンドポイント（operationId）ごとのモックシナリオを切り替え | `mocks` | - |
| `setViewport` | ビューポートをリサイズ（レスポンシブ検証） | `width`, `height` | Web のみ。iOS/Android は警告付き no-op（`when.responsive` でゲート） |
| `setOrientation` | 画面の向きを変更 | `orientation` | iOS: XCUIDevice ／ Android: UiDevice ／ Web: モバイルエミュレーション時のみ（他は警告付き no-op） |
| `emitHook` | アプリが登録したテストフックを呼び出す（`window.__jsonuiTestHooks`） | `name`, `hookArgs?` | Web のみ。iOS/Android は警告付き no-op（`when.platform` でゲート） |
<!-- /generated:actions -->

### アサーション一覧

全アサーションはauto-wait（100msポーリング、成立で即成功、デフォルト5000ms / `timeout`で上書き）。

<!-- generated:assertions -->
| アサーション | 説明 | パラメータ | プラットフォーム |
|---|---|---|---|
| `visible` | 要素が表示されている | `id`, `timeout?` | - |
| `notVisible` | 要素が非表示または不存在 | `id`, `timeout?` | - |
| `enabled` | 要素が有効 | `id`, `timeout?` | - |
| `disabled` | 要素が無効 | `id`, `timeout?` | - |
| `text` | テキストを検証（`equals`／`contains`） | `id`, `equals?`, `contains?`, `timeout?` | - |
| `count` | 要素数を検証（`equals: 0` は不存在で成立） | `id`, `equals`, `timeout?` | - |
| `state` | ViewModel 状態を検証（`path` はドット記法、StateProvider 必須） | `path`, `equals`, `timeout?` | - |
| `screenshot` | ベースライン画像とのビジュアル比較（ベースライン無しは新規作成＋警告） | `name`, `cropId?`, `threshold?=98` | - |
| `openedUrl` | 直近の `window.open` 呼び出しの URL を検証 | `equals?`, `contains?`, `timeout?` | Web のみ（`when.platform: web` でゲート） |
| `screen` | 指定画面の表示を検証（排他は主張しない — 埋め込み／タブ等で複数同時あり得る） | `name`, `timeout?` | - |
<!-- /generated:assertions -->

### 表の再生成（スキーマ変更時必須）

`schemas/actions.schema.json` にステップを追加・変更したら:

1. 当該定義に `x-doc` を書く（`ja` = 表の説明。`platforms` = プラットフォーム注記、差異がある場合のみ）
2. `npm run docs` — README.md / CLAUDE.md のマーカー間を再生成（`x-doc` 欠落はエラーで停止）
3. コミット前に `npm run docs:check` — 表が stale なら exit 1

`node scripts/gen-action-tables.mjs --json` で機械可読ダンプ（スキル等の下流ツール向け）。
パラメータ表記は required 素／optional `?`／スキーマ `default` は `=値` で自動描画される。

### 共通ステップ属性 / launch / 実行時変数 / レポート

- 全ステップ共通: `label`（表示名。`selectOption`のみ従来の選択肢ラベルの意味）、`optional`（失敗を警告に降格）、`when`（事前条件: `visible`/`notVisible`/`platform`/`state`のAND。不成立でスキップ）
- テストルートの `launch`: `clearState` / `permissions` / `arguments`（起動前適用）
- `readText`で読んだ値は `@{変数名}` で実行時参照（ロード時args置換→実行時変数の順で解決）
- 結果JSON（`schemas/results.schema.json`）→ `jsonui-test report --format junit|html` で変換
- セマンティクスのSSoT: `specs/2026-07-08-advanced-test-features.md`（ドライバー実装は必ずここに従う）

## 要素の特定方法

JsonUIの `id` 属性を使用して要素を特定する。

### プラットフォーム別マッピング

| Platform | id属性のマッピング先 |
|----------|---------------------|
| iOS | `accessibilityIdentifier` |
| Android | `contentDescription` or `resource-id` |
| Web | `data-testid` attribute |

### JsonUI側での設定例

```json
{
  "class": "TextField",
  "id": "email_input",
  "properties": {
    "placeholder": "メールアドレス"
  }
}
```

## AIエージェント連携

### エージェントへの入力形式

```json
{
  "task": "generate_screen_test",
  "inputs": {
    "layout": {
      "path": "Layouts/Login.json",
      "content": { /* JSONの内容 */ }
    },
    "spec": {
      "path": "specs/Login.md",
      "content": "## ログイン画面\n\n### 機能\n- メールアドレスとパスワードでログイン\n..."
    },
    "testSchema": { /* テストJSONスキーマ */ }
  },
  "output": {
    "path": "tests/screens/Login.test.json"
  }
}
```

### 仕様書（spec）フォーマット

```markdown
## 画面名

### 概要
画面の目的・役割を記述

### 機能
- 機能1の説明
- 機能2の説明

### 期待動作
1. 初期状態の説明
2. ユーザー操作と結果の説明
3. エラー時の動作

### テスト観点
- 検証すべきポイント
- エッジケース
```

## 技術スタック

- **Core**: TypeScript / Node.js
- **iOS Driver**: Swift + XCUITest
- **Android Driver**: Kotlin + UIAutomator
- **Web Driver**: TypeScript + Playwright
- **CLI**: Commander.js or oclif
- **CI/CD**: GitHub Actions

## 関連リポジトリ

- SwiftJsonUI: `~/resource/SwiftJsonUI`
- KotlinJsonUI: `~/resource/KotlinJsonUI`
- ReactJsonUI: `~/resource/ReactJsonUI`
- JsonUI Wiki (Swift): `~/resource/SwiftyJsonUI_wiki/`
- JsonUI Wiki (Kotlin): `~/resource/KotlinJsonUI_wiki/`
