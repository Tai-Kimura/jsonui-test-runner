# jsonui-test-runner

JsonUIライブラリ（SwiftJsonUI / KotlinJsonUI / ReactJsonUI）向けのクロスプラットフォームUIテスト自動化ツール。

## 概要

JSONで定義されたテストケースを、iOS・Android・Webで統一的に実行できるテストランナーです。

### 特徴

- **宣言的テスト定義**: テストケースをJSONで記述
- **クロスプラットフォーム**: iOS (XCUITest) / Android (UIAutomator) / Web (Playwright) 対応
- **AIエージェント連携**: レイアウトJSONと仕様書からテストケースを自動生成
- **柔軟なテスト構成**: 画面単体テストとフローテストの両方に対応

## インストール

`jsonui-test` CLI は [jsonui-cli](https://github.com/Tai-Kimura/jsonui-cli) へ移設されました
（`test_tools/` に self-contained で同梱）。このリポジトリはテストスキーマ（`schemas/`）・
ドライバ（`drivers/`）・examples の正本です。

```bash
# jsonui-test CLI 単体
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/test_tools/installer/bootstrap.sh | bash

# もしくは jsonui-cli 一式（jui / jsonui-doc も入る）
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/installer/bootstrap.sh | bash
```

## 使い方

### 1. テストケースの作成

画面単体テスト (`tests/screens/Login.test.json`):

```json
{
  "type": "screen",
  "source": {
    "layout": "Layouts/Login.json"
  },
  "cases": [
    {
      "name": "初期表示確認",
      "steps": [
        { "assert": "visible", "id": "email_input" },
        { "assert": "visible", "id": "password_input" },
        { "assert": "disabled", "id": "login_button" }
      ]
    }
  ]
}
```

### 2. テストの実行

テストの実行方法はプラットフォームごとに異なります。各ドライバーのREADMEを参照してください：

- **iOS**: [drivers/ios/README.md](drivers/ios/README.md) - XCUITestフレームワークで実行
- **Android**: [drivers/android/README.md](drivers/android/README.md) - UIAutomatorで実行
- **Web**: [drivers/web/README.md](drivers/web/README.md) - Playwrightで実行

### 3. テストファイルのバリデーション

```bash
# jsonui-test CLIでテストファイルを検証
jsonui-test validate tests/screens/Login.test.json
```

## プロジェクト構成

```
jsonui-test-runner/
├── schemas/                    # JSON Schema定義
│   ├── screen-test.schema.json
│   ├── flow-test.schema.json
│   └── actions.schema.json
├── drivers/                    # プラットフォーム別ドライバー
│   ├── ios/                    # XCUITest実装
│   ├── android/                # UIAutomator実装
│   └── web/                    # Playwright実装
├── core/                       # 共通ロジック
│   ├── runner.ts
│   ├── parser.ts
│   └── reporter.ts
├── cli/                        # CLIツール
│   └── jsonui-test
└── tests/                      # テストケース格納場所
    ├── screens/                # 画面単体テスト
    └── flows/                  # フローテスト
```

## テストJSON仕様

### アクション

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

### アサーション

すべてのアサーションは**自動待機（auto-wait）**します: 条件が成立するまで100ms間隔でポーリングし、成立した時点で即座に成功、タイムアウト（デフォルト5000ms、`timeout`で上書き）で失敗します。`waitFor`を前置する必要はありません。

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

### 共通ステップ属性

すべてのアクション・アサーションに付与できます:

| 属性 | 説明 |
|------|------|
| `label` | ログ・レポートに表示するステップ名（※`selectOption`では従来通り選択肢ラベルの意味） |
| `optional` | `true`なら失敗を警告に降格して続行 |
| `when` | 事前条件。不成立ならステップをスキップ。`visible` / `notVisible` / `platform` / `state` をAND評価 |

```json
{ "action": "tap", "id": "tutorial_close", "when": { "visible": "tutorial_overlay" }, "optional": true }
```

### 起動設定（launch）

テストルートに `launch` を書くと、アプリ起動前に状態クリア・権限・起動引数を適用します:

```json
"launch": {
  "clearState": true,
  "permissions": { "camera": "allow", "location": "deny" },
  "arguments": { "mockApi": true }
}
```

プラットフォーム別の適用方法（iOS: `launchEnvironment`、Android: `pm clear`/`pm grant`、Web: `grantPermissions`/`sessionStorage`）はドライバーごとの実装に従います。

### 実行時変数

`readText` で読んだ値は `@{変数名}` で後続ステップから参照できます（ロード時の `args` 置換の後、実行時に解決）:

```json
{ "action": "readText", "id": "order_number_label", "variable": "orderNo" },
{ "action": "tap", "id": "detail_link" },
{ "assert": "text", "id": "detail_order_number", "equals": "@{orderNo}" }
```

### テスト結果レポート

各ドライバーは共通形式の結果JSON（`schemas/results.schema.json`）を出力でき、CLIでJUnit XML / HTMLに変換できます:

```bash
jsonui-test report results-web.json results-ios.json --format junit -o report.xml
jsonui-test report results-web.json --format html -o report.html
```

## 対応JsonUIライブラリ

- [SwiftJsonUI](https://github.com/Tai-Kimura/SwiftJsonUI) - iOS
- [KotlinJsonUI](https://github.com/Tai-Kimura/KotlinJsonUI) - Android
- [ReactJsonUI](https://github.com/Tai-Kimura/ReactJsonUI) - Web

## ライセンス

MIT License
