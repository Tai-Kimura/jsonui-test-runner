# jsonui-test-runner

JsonUIライブラリ（SwiftJsonUI / KotlinJsonUI / ReactJsonUI）向けのクロスプラットフォームUIテスト自動化ツール。

## 概要

JSONで定義されたテストケースを、iOS・Android・Webで統一的に実行できるテストランナーです。

### 特徴

- **宣言的テスト定義**: テストケースをJSONで記述
- **クロスプラットフォーム**: iOS (XCUITest) / Android (Espresso) / Web (Playwright) 対応
- **AIエージェント連携**: レイアウトJSONと仕様書からテストケースを自動生成
- **柔軟なテスト構成**: 画面単体テストとフローテストの両方に対応

## インストール

```bash
# TODO: 実装後に追記
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
│   ├── android/                # Espresso実装
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

| アクション | 説明 | パラメータ |
|-----------|------|-----------|
| `tap` | 要素をタップ | `id` |
| `doubleTap` | ダブルタップ | `id` |
| `longPress` | 長押し | `id`, `duration?` |
| `input` | テキスト入力 | `id`, `value` |
| `clear` | 入力クリア | `id` |
| `scroll` | スクロール | `id`, `direction` |
| `swipe` | スワイプ | `id`, `direction` |
| `waitFor` | 要素出現を待機 | `id`, `timeout?` |
| `wait` | 指定時間待機 | `ms` |
| `back` | 戻る | - |
| `screenshot` | スクリーンショット | `name` |

### アサーション

| アサーション | 説明 | パラメータ |
|-------------|------|-----------|
| `visible` | 要素が表示されている | `id` |
| `notVisible` | 要素が非表示 | `id` |
| `enabled` | 要素が有効 | `id` |
| `disabled` | 要素が無効 | `id` |
| `text` | テキスト検証 | `id`, `equals?`, `contains?` |
| `count` | 要素数検証 | `id`, `equals` |
| `state` | ViewModel状態検証 | `path`, `equals` |

## 対応JsonUIライブラリ

- [SwiftJsonUI](https://github.com/anthropics/SwiftJsonUI) - iOS
- [KotlinJsonUI](https://github.com/anthropics/KotlinJsonUI) - Android
- [ReactJsonUI](https://github.com/anthropics/ReactJsonUI) - Web

## ライセンス

MIT License
