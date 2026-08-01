# Advanced test feature set (P0–P3)

Semantics specification for features added 2026-07-08. This document is the
single source of truth for driver behavior — all three drivers (iOS/XCUITest,
Android/UIAutomator, Web/Playwright) MUST implement the semantics described
here identically unless a platform limitation is explicitly noted.

Element identification remains **JsonUI layout `id` only**. No text/regex/
relational selectors are added — that is a deliberate design decision.

---

## 1. Common step attributes

Every step (action or assertion, in screen tests, flow inline steps, and block
steps) accepts these optional attributes:

| Attribute | Type | Default | Semantics |
|---|---|---|---|
| `label` | string | – | Human-readable step name. Used in logs and reports instead of the auto-generated description. **Exception**: on `selectOption`, `label` keeps its original meaning (option text to select) and there is no step-name attribute. |
| `optional` | boolean | `false` | When `true`, a failure of this step is recorded as a **warning** on the current test case result and execution continues with the next step. Skipped-by-`when` is NOT a warning. |
| `when` | condition object | – | Pre-condition. If not satisfied, the step is **skipped** (logged, not a warning, not a failure). |

### 1.1 Condition object (used by `when` and `repeat.while`)

```json
{
  "visible": "element_id",
  "notVisible": "element_id",
  "platform": "ios" | ["ios", "android"],
  "state": { "path": "user.isPremium", "equals": true }
}
```

- Multiple keys = **AND**.
- `visible` / `notVisible`: **instant** check of current UI (no polling, no
  implicit wait). Element existing but off-screen/hidden counts as not visible.
- `platform`: same matching rules as the existing `platform` field.
- `state`: requires a state provider (see §6). If no provider is configured,
  evaluating a `state` condition is an **error** (fails the step / loop), not a
  silent skip.

## 2. Assertion auto-wait (fluent assertions)

All element assertions poll the condition every **100ms** until it holds or the
timeout elapses. Timeout = step `timeout` (ms) if present, else the runner's
`defaultTimeout` (5000ms).

- `visible`, `enabled`, `disabled`, `text`, `count`, `state`: pass as soon as
  the condition holds; fail with the current actual value in the error message
  when the timeout elapses.
- `notVisible`: passes as soon as the element is gone or invisible; fails if it
  is still visible at timeout. (No fixed pre-wait; poll from t=0.)
- `count` with `equals: 0` must not fail early just because the element is
  absent — absence IS the passing condition.

All assertion definitions gain an optional `timeout` parameter in the schema.

## 3. New / extended actions

### 3.1 `scrollUntilVisible`

```json
{ "action": "scrollUntilVisible", "id": "submit_button",
  "container": "form_scroll", "direction": "down", "timeout": 20000 }
```

- `id` (required): target element to bring into view.
- `container` (optional): id of the scrollable element to scroll. When omitted:
  Web scrolls the window; iOS/Android scroll the first scrollable view found
  (`XCUIElementTypeScrollView`/`ScrollView`/scrollable=true), falling back to a
  screen-center swipe.
- `direction` (default `"down"`): direction the content moves toward (i.e.
  `down` reveals content below).
- `timeout` (default **20000ms**).
- Loop: if target visible → done. Else scroll one step (~70% of the container
  viewport) and re-check. Two consecutive scrolls with no scroll-position /
  content change before the target is found = "end reached" → fail immediately
  with a distinct message. Otherwise fail at timeout.

### 3.2 `readText`

```json
{ "action": "readText", "id": "order_number_label", "variable": "orderNo" }
```

- Reads the element's user-visible text (for input fields: current value) and
  stores it in the **runtime variable store** under `variable`.
- Runtime variables are referenced with the existing `@{name}` placeholder
  syntax. Resolution order: load-time args substitution first (existing
  behavior), then runtime variables at **step-execution time** for any
  remaining `@{name}` placeholders. Unknown names stay as literal text
  (consistent with args behavior).
- Scope: the variable store lives for the duration of one runner invocation
  (a whole flow, or a whole screen-test run) and is shared across cases/steps.

### 3.3 `repeat` (control step)

```json
{ "action": "repeat", "times": 3, "steps": [ ... ] }
{ "action": "repeat", "while": { "visible": "next_button" }, "steps": [ ... ] }
{ "action": "repeat", "times": 10, "while": { "notVisible": "end_marker" }, "steps": [ ... ] }
```

- `times` only: run the block exactly `times` times.
- `while` only: evaluate condition before each iteration; loop while it holds.
  Safety cap **100 iterations**; hitting the cap while the condition still
  holds is a step **failure** (guards infinite loops).
- Both: loop while condition holds, at most `times` iterations. Reaching
  `times` is NOT a failure (`times` acts as the cap).
- `steps` may contain any actions/assertions including nested `repeat`/`retry`.

### 3.4 `retry` (control step)

```json
{ "action": "retry", "maxRetries": 2, "steps": [ ... ] }
```

- Runs the block; when any step inside fails, re-runs the **whole block** from
  the start. `maxRetries` = number of retries after the first attempt, range
  0–3, default **1**. Fails with the last error when exhausted.
- Note: wrapping a whole test in `retry` is an anti-pattern; the cap of 3
  exists deliberately.

### 3.5 `tap` — `retryTapIfNoChange`

```json
{ "action": "tap", "id": "submit", "retryTapIfNoChange": true }
```

- After tapping, wait ~500ms for the UI to change. If the UI is unchanged,
  tap once more ("ghost tap" mitigation). Detection:
  - iOS: hash of the app hierarchy snapshot (`app.debugDescription`) before/after.
  - Android: `UiDevice.waitForWindowUpdate(pkg, 500)` result.
  - Web: accepted and **ignored** (Playwright actionability already covers this).

### 3.6 `setLocation`

```json
{ "action": "setLocation", "latitude": 35.6812, "longitude": 139.7671 }
```

- Web: Playwright `context.setGeolocation(...)` (grants `geolocation`
  permission if needed).
- iOS: `XCUIDevice.shared.location = XCUILocation(...)` where the SDK provides
  it; otherwise throw `unsupported` with a clear message.
- Android: best effort — enable mock location for the instrumentation package
  via `appops` shell + register a test `LocationManager` provider. If the
  device rejects it, fail with a clear message.

### 3.7 `addMedia`

```json
{ "action": "addMedia", "paths": ["fixtures/photo1.png"] }
```

- Seeds media fixtures into the device/library so the app can pick them.
  Supported types: png/jpg/jpeg/gif (photo) and mp4 (video).
- Android: insert files into the media store (gallery).
- iOS (driver ≥ 1.7.0): seed into the photo library via PhotoKit —
  **simulator only** (on a real device seeded assets would remain in the
  user's photo library). The UITest runner needs a `photos-add` pre-grant
  (`xcrun simctl privacy <udid> grant photos-add <uitest-bundle-id>.xctrunner`);
  the jsonui-test CLI applies it automatically.
- Web: set the files on a file input.
- Seeding accumulates across runs on the same simulator/emulator — assert on
  existence or app state after picking, never on counts.

> **2026-08-01 amendment**: the original text declared addMedia Android-only
> on the grounds that an in-process XCUITest driver cannot seed media.
> Superseded — the iOS driver seeds via PhotoKit since 1.7.0 and the web
> driver sets file inputs; the paragraph above is the current contract.

## 4. `screenshot` assertion (visual regression)

```json
{ "assert": "screenshot", "name": "login_initial",
  "cropId": "login_card", "threshold": 98.0 }
```

- Captures the screen (or, with `cropId`, the bounding box of that element)
  and compares against the baseline PNG.
- Baseline path: `<baselineDir>/<platform>/<name>.png`. `baselineDir` is a
  runner config value (web default `./baselines`; iOS/Android default to the
  runner's artifact/files directory).
- `threshold`: required **similarity** percentage, 0–100, default **98.0**.
  Similarity = 100 × (matching pixels / total pixels); a pixel matches when
  each RGBA channel differs by ≤ 16/255.
- Baseline missing → save the current capture as the new baseline and **pass
  with a warning** ("baseline created").
- Runner config `updateBaselines: true` → always overwrite baseline and pass.
- Dimension mismatch → immediate fail with both sizes in the message.

## 5. Launch configuration

Screen tests and flow tests accept a root-level `launch` object:

```json
"launch": {
  "clearState": true,
  "permissions": { "camera": "allow", "location": "deny", "notifications": "unset" },
  "arguments": { "mockApi": true, "apiBase": "http://localhost:8080" }
}
```

Permission names (cross-platform set): `camera`, `microphone`, `location`,
`notifications`, `photos`, `contacts`, `calendar`, `bluetooth`. Values:
`allow` / `deny` / `unset`.

Application per platform (applied **before** the app under test starts):

- **iOS**: the driver sets `launchEnvironment["JSONUI_TEST_ARGS"]` to the
  JSON-encoded `arguments` map and `launchEnvironment["JSONUI_TEST_CLEAR_STATE"] = "1"`
  when `clearState` is true (the JsonUI app framework honors these — app-side
  contract). Permissions: `unset` uses `resetAuthorizationStatus(for:)`;
  `allow`/`deny` installs a UI interruption monitor that answers system
  permission alerts accordingly for the run.
- **Android**: `clearState` → `pm clear <pkg>` via `UiAutomation` shell before
  launch; permissions → `pm grant` / `pm revoke` (runtime permissions);
  `arguments` → intent extras (`JSONUI_TEST_ARGS` as JSON string extra) on the
  launch intent.
- **Web**: exposed as a `applyLaunchConfig(context, launch)` helper —
  `clearState` clears cookies + local/session storage for the origin;
  `permissions` maps to `context.grantPermissions()` (deny = omit, unset =
  `clearPermissions()`); `arguments` are written to
  `sessionStorage["JSONUI_TEST_ARGS"]` (JSON) before navigation.

The app-side contract (`JSONUI_TEST_ARGS` / `JSONUI_TEST_CLEAR_STATE`) is a
convention for JsonUI apps; library support is tracked separately.

## 6. `state` parity (StateProvider on all platforms)

- iOS already has `ViewModelStateProvider` (protocol, `getValue(at:)`).
- Android: add the equivalent `ViewModelStateProvider` interface
  (`fun getValue(path: String): Any?`), injectable into the runner; the
  `state` assertion and `state` conditions use it.
- Web: add a `StateProvider` interface. Default implementation reads
  `window.__JSONUI_STATE__` (object; `path` is dot-notation into it) via
  `page.evaluate`. Custom providers injectable through runner config.
- `state` assertion participates in auto-wait polling (§2).

## 7. Teardown guarantee

- Screen tests: `teardown` runs even when `setup` threw or any case failed.
  If `setup` throws, all cases are recorded as failed ("setup failed") and
  teardown still runs.
- Flow tests: `teardown` runs even when `steps` threw.
- A teardown failure marks the run failed (recorded as an extra failed result
  entry named `"teardown"`), guaranteeing teardown runs like an after-hook.

## 8. Results & reports

### 8.1 Standardized results JSON (all drivers)

Every driver can serialize its run result to a common JSON shape
(`schemas/results.schema.json`):

```json
{
  "format": "jsonui-test-results",
  "version": 1,
  "platform": "web",
  "suites": [{
    "suiteName": "ログイン画面テスト",
    "totalDurationMs": 1234,
    "results": [{
      "testName": "ログイン画面テスト",
      "caseName": "初期表示確認",
      "status": "passed" | "failed" | "skipped",
      "error": "…",
      "warnings": ["optional step failed: …", "baseline created: …"],
      "durationMs": 320
    }]
  }]
}
```

Existing in-memory result models keep their current fields (`passed` stays for
API compatibility); they gain `skipped` and `warnings`. `status` in the JSON is
derived: skipped → `"skipped"`, else passed/failed.

- Web: `ResultsWriter.write(results, path)` (default `./jsonui-results.json`).
- iOS: results JSON attached as an `XCTAttachment` and written to the runner's
  temp/documents dir when a `resultsPath` config is set.
- Android: written to the instrumented app's external files dir when
  `resultsPath` config is set.

### 8.2 CLI report conversion

`jsonui-test report <results.json>... --format junit|html [-o <path>]`

- `junit`: standard JUnit XML (`<testsuites>/<testsuite>/<testcase>` with
  `<failure>`, `<skipped/>`, and warnings as `<system-out>`).
- `html`: standalone single-file HTML summary (suite table, per-case status,
  errors/warnings expandable).
- Multiple input files (e.g. one per platform) merge into one report;
  `platform` becomes part of the suite name.

## 9. Support matrix

| Feature | iOS | Android | Web |
|---|---|---|---|
| auto-wait assertions | ✅ | ✅ | ✅ |
| `optional` / `label` / `when` | ✅ | ✅ | ✅ |
| `scrollUntilVisible` | ✅ | ✅ | ✅ |
| `readText` + runtime vars | ✅ | ✅ | ✅ |
| `repeat` / `retry` | ✅ | ✅ | ✅ |
| `retryTapIfNoChange` | ✅ | ✅ | accepted, no-op |
| `screenshot` assertion | ✅ | ✅ | ✅ |
| `state` assertion / condition | ✅ (existing) | ✅ (new) | ✅ (new, `__JSONUI_STATE__`) |
| launch: clearState | env contract | `pm clear` | storage clear |
| launch: permissions | reset + interruption monitor | `pm grant/revoke` | `grantPermissions` |
| launch: arguments | launchEnvironment | intent extras | sessionStorage |
| `setLocation` | SDK-dependent | best effort | ✅ |
| `addMedia` | ✅ simulator only (≥1.7.0) | ✅ | ✅ file input |
| results JSON | ✅ | ✅ | ✅ |
| JUnit/HTML report | via CLI | via CLI | via CLI |
