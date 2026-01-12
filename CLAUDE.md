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
 XCUITest    Espresso      Playwright
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

### Phase 4: Android（Espresso）ドライバー実装
- [ ] Espresso環境セットアップ
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
    "spec": "specs/Login.md"
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
    { "layout": "Layouts/Login.json", "spec": "specs/Login.md" },
    { "layout": "Layouts/Home.json", "spec": "specs/Home.md" }
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

| アクション | 説明 | 必須パラメータ | オプション |
|-----------|------|---------------|-----------|
| `tap` | 要素をタップ | `id` | - |
| `doubleTap` | ダブルタップ | `id` | - |
| `longPress` | 長押し | `id` | `duration` (ms) |
| `input` | テキスト入力 | `id`, `value` | - |
| `clear` | 入力クリア | `id` | - |
| `scroll` | スクロール | `id`, `direction` | `amount` |
| `swipe` | スワイプ | `id`, `direction` | - |
| `waitFor` | 要素出現待機 | `id` | `timeout` (ms, default: 5000) |
| `wait` | 固定時間待機 | `ms` | - |
| `back` | 戻る操作 | - | - |
| `screenshot` | スクショ保存 | `name` | - |

### アサーション一覧

| アサーション | 説明 | 必須パラメータ | オプション |
|-------------|------|---------------|-----------|
| `visible` | 表示確認 | `id` | - |
| `notVisible` | 非表示確認 | `id` | - |
| `enabled` | 有効確認 | `id` | - |
| `disabled` | 無効確認 | `id` | - |
| `text` | テキスト検証 | `id` | `equals`, `contains` |
| `count` | 要素数検証 | `id`, `equals` | - |
| `state` | VM状態検証 | `path`, `equals` | - |

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
- **Android Driver**: Kotlin + Espresso
- **Web Driver**: TypeScript + Playwright
- **CLI**: Commander.js or oclif
- **CI/CD**: GitHub Actions

## 関連リポジトリ

- SwiftJsonUI: `~/resource/SwiftJsonUI`
- KotlinJsonUI: `~/resource/KotlinJsonUI`
- ReactJsonUI: `~/resource/ReactJsonUI`
- JsonUI Wiki (Swift): `~/resource/SwiftyJsonUI_wiki/`
- JsonUI Wiki (Kotlin): `~/resource/KotlinJsonUI_wiki/`
