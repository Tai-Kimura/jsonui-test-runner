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
- `state`: reads the screen's Data through the default provider (the state
  bridge, §6) or a provider the harness passes. Instant like the others: a
  bridge that is absent, or a path that does not resolve, is not met; a
  truncated bridge (iOS, over 32 KB) is an **error** (fails the step / loop),
  not a silent skip.

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

Application per platform (applied **before** the app under test starts; the
order, and what else the same launch carries, is §10.2):

- **iOS**: the runner owns four `launchEnvironment` keys —
  `JSONUI_TEST_CLEAR_STATE`, `JSONUI_TEST_ARGS`, `JSONUI_TEST_PERMISSIONS` and
  `JSONUI_TEST_INITIAL_STATE` — and removes all four before every launch, then
  sets the ones this launch needs. A key set for one file therefore never
  reaches the next file's launch. `JSONUI_TEST_CLEAR_STATE = "1"` when
  `clearState` is true; `JSONUI_TEST_ARGS` is the JSON-encoded `arguments`
  map; `JSONUI_TEST_PERMISSIONS` the JSON-encoded `permissions` map.
- **Android**: `clearState` → an in-process wipe of the app's persisted state
  (files, shared_prefs, databases, cache, code_cache). Not `pm clear`: the
  instrumentation runs in the app's process, and `pm clear` kills it.
  Permissions → `pm grant` for `allow`; `deny` is asserted (a granted
  permission declared `deny` fails the file — an in-run revoke kills the
  process); `unset` leaves the inherited state. `arguments` → the
  `JSONUI_TEST_ARGS` string extra (JSON) on the relaunch intent.
- **Web**: the runner applies it — there is no helper for the harness to call.
  `clearState` clears cookies and the origin's local and session storage
  (IndexedDB is not touched); permissions: when any value is `deny` or
  `unset`, `context.clearPermissions()` first, then the `allow`s are granted
  again (clearing only for `unset` left an earlier file's `allow` in place);
  `arguments` → `sessionStorage["JSONUI_TEST_ARGS"]` (JSON). Then the runner
  calls the harness's `afterLaunch(page)` hook (runner config; awaited) — the
  place to seed what `clearState` removed, such as an auth cookie — and only
  then writes the initialState, switches the mocks and reloads the page once
  (`goto` on a reopen). A throw from `afterLaunch` fails the launch like any
  other launch step. At the end of the file the runner removes
  `JSONUI_TEST_ARGS` and `JSONUI_TEST_INITIAL_STATE` from sessionStorage.

The app-side reading of `JSONUI_TEST_ARGS` / `JSONUI_TEST_CLEAR_STATE` is a
convention for JsonUI apps and is not provided by the libraries; the drivers
deliver them and stop there. `JSONUI_TEST_INITIAL_STATE` is different: the
libraries read it (§10).

## 6. `state` (the bridge is the default provider)

- `state` (assertion) and `when.state` read the ViewModel data of a screen.
  With JsonUI libraries that have the state bridge (SwiftJsonUI ≥ 10.30.0,
  KotlinJsonUI ≥ 2.44.0, generated with the jsonui-cli of the same train) the
  harness passes nothing: the driver's default provider resolves `path` in the
  bridge's `data` (§10.4, §10.5).
- Which screen: in a screen test, the screen under test; in a flow, the
  step's `screen`, else the last `screen` an earlier step named; a case a flow
  references reads its own file's screen.
- A provider the harness passes still wins (iOS `ViewModelStateProvider`,
  Android `ViewModelStateProvider`, web `stateProvider` in the runner config).
- `state` takes part in auto-wait (§2): an absent bridge or an unresolved path
  is "not yet" and is polled; a truncated bridge fails at once.

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
| `state` assertion / condition | ✅ bridge leaf `__state_<id>` (≥1.15.0) | ✅ marker semantics `JsonUIState` (≥1.17.0) | ✅ `__JSONUI_STATE__[id]` (≥1.15.0) |
| `initialState` (file / case / flow) | ✅ env, receipt checked (≥1.15.0) | ✅ intent extra, receipt checked (≥1.17.0) | ✅ sessionStorage, receipt checked (≥1.15.0) |
| launch: clearState | env contract | in-process wipe | runner: cookies + storage (≥1.15.0) |
| launch: permissions | env `JSONUI_TEST_PERMISSIONS` | `pm grant`, deny asserted | runner: clear on deny/unset, then grant (≥1.15.0) |
| launch: arguments | launchEnvironment (owned keys reset per launch, ≥1.15.0) | intent extras | runner: sessionStorage (≥1.15.0) |
| `setLocation` | SDK-dependent | best effort | ✅ |
| `addMedia` | ✅ simulator only (≥1.7.0) | ✅ | ✅ file input |
| results JSON | ✅ | ✅ | ✅ |
| JUnit/HTML report | via CLI | via CLI | via CLI |

## 10. initialState, the state bridge and the launch sequence

Contract for every repository that takes part: the three drivers, the two
libraries (SwiftJsonUI, KotlinJsonUI), the three generators (sjui / kjui /
rjui) and `jsonui-test validate`. The shared vectors in `specs/vectors/`
(§10.7) fix the parts that are data; an implementation passes them as
written.

Versions that implement it: drivers ios 1.15.0, android 1.17.0, web 1.15.0;
SwiftJsonUI 10.30.0; KotlinJsonUI 2.44.0; the jsonui-cli released with them.
There is no transition period: a driver of this version fails a file whose
initialState the app did not confirm (§10.5).

### 10.1 Screen id

As `jsonui-cli/shared/core/screen_identity.json`: the layout file's basename
without `.json`, verbatim, with a size-class variant (`@compact` / `@medium`
/ `@regular`) removed. The screen under test is the screen id of
`source.layout` (required by the schema) — the child screen, also when
`embeddedIn` is set.

### 10.2 The launch sequence and delivery

The same order on every platform:

1. **clearState** — iOS env `JSONUI_TEST_CLEAR_STATE=1`; Android in-process
   wipe; web cookies + the origin's local / session storage.
2. **permissions** — iOS env `JSONUI_TEST_PERMISSIONS`; Android grant, deny
   asserted; web clear-then-grant (§5).
3. **arguments** — key `JSONUI_TEST_ARGS`: iOS env, Android intent extra,
   web sessionStorage. Web then calls the harness hook `afterLaunch(page)`
   when one is configured (§5), on every launch — per case on a reopen.
4. **initialState** — key `JSONUI_TEST_INITIAL_STATE`, carried the same way
   as the arguments.
5. **mocks** — `scenarioSet`.
6. **launch** — iOS `app.launch()`, Android relaunch, web `reload` (`goto` on
   a reopen). Exactly once.
7. **receipt** — for each screen the payload names that is checked at this
   point (§10.5).
8. **setup**.

- A launch happens only when there is a `launch`, `mocks` or a non-empty
  initialState. With none of them the driver does not launch, as before.
- An empty initialState (`viewModel: {}`, `viewModels: {}`) is the same as
  none: no payload, and not a reason to launch.
- With `caseIsolation: "reopen"`, steps 1–8 run again before each case; the
  case's payload is the file's initialState merged with the case's, key by
  key (shallow: a case's value replaces the file's value for that key
  whole, objects included; a case's `null` is a value and replaces it too).
  A case gated out (skip / platform / responsive) opens nothing.
- With `shared` (the default), a case-level initialState cannot be
  delivered — the screen is opened once, before the first case. Validate
  error; the driver fails that case only (`failureReason: "setup"`, code
  `case-initial-state-needs-reopen`) and still delivers the file's payload.
- Cleanup: iOS — the next launch removes the four owned keys first (§5);
  Android — extras belong to one intent; web — the runner removes
  `JSONUI_TEST_ARGS` and `JSONUI_TEST_INITIAL_STATE` from sessionStorage at
  the end of the file.

The payload (`JSONUI_TEST_INITIAL_STATE`, a JSON string):

```json
{
  "version": 1,
  "launchId": "6F1C2A9E-3B7D-4C1E-9A55-0D2F8E7B4C11",
  "screens": { "login": { "email": "test@example.com", "password": "" } }
}
```

- `launchId`: a UUID the driver makes for each launch.
- `writtenAt` (web only): the page's `Date.now()` when the runner wrote the
  payload (ms since the epoch, the browser's clock). The app consumes the
  payload only in a document whose `performance.timeOrigin` is later than
  `writtenAt` — the document the launch's reload / `goto` opens. A document
  that already existed when the payload was written (one still hydrating
  from before the launch) leaves it untouched: it does not apply it, does not
  remove its screen from the stored payload, and shows no receipt (its bridge
  carries `launchId: null`). Without this, such a document took the payload
  first and the reloaded one had nothing to apply. A payload without
  `writtenAt` is not consumed on web.
- `screens`: in a screen test, the screen under test only, with the file's
  `initialState.viewModel` (merged with the case's on a reopen); in a flow,
  `initialState.viewModels` as written. Keys of `viewModels` are screen ids,
  the same values the flow's steps write in `screen`.
- The driver does not judge the values: an unknown key, a `null` or a value
  of the wrong type travels in the payload and the app rejects it (§10.3).
  The validator judges them before the run.
- Flows: a file or case a flow references runs inside the flow without its
  own initialState — the flow's launch has already happened. It is not
  applied; validate and the driver warn (`referenced-initial-state-ignored`).
  `initialState.screen` is no longer part of the flow schema.

### 10.3 Applying it in the app

- **Reading**: iOS — `ProcessInfo.processInfo.environment`, once. Android —
  the intent extra of the Activity the screen is in; never kept in process
  memory across launches. Web — sessionStorage, in a document opened after
  the payload's `writtenAt` (§10.2).
- **Gate**: the same as the screen marker. iOS — DEBUG, or the Info.plist key
  `com.swiftjsonui.SCREEN_MARKER`; Android — `FLAG_DEBUGGABLE`, or the
  meta-data `com.kotlinjsonui.SCREEN_MARKER`; web — `NODE_ENV !==
  'production'`. A closed gate means no receiving and no bridge.
- **Once**: consumption is recorded per `launchId × screenId`. A screen built
  again in the same launch (navigated away and back, recreated) is not
  applied again. Web also removes the consumed screen from the stored
  payload.
- **When**: after launch, the first time that screen appears. A ViewModel
  `init` or `onAppear` may already have run with default values by then;
  values an API provides are made with `mocks`, not initialState.
- **Keys**: Data names of that screen (the layout's `data` section), top
  level only. No dot notation (`user.name` is one key, and it is not a Data
  name). Keys are case-sensitive. Properties of the ViewModel that are not
  in `data` cannot be set.

**Types.** A key is checked in this order: not a data field → unsupported
type → null → type. Every key is judged on its own: the accepted ones are
applied even when others are rejected.

- Class spelling: the class as the layout writes it, read with the
  generators' vocabulary (`type_mapping.json`): `Integer` is `Int`, `Number`
  is `Double`, `Boolean` / `bool` are `Bool`, and lower-case spellings are
  their capitalised class. Optional is a trailing `?` and nothing else.

| data class | accepts | notes |
|---|---|---|
| String | string | |
| Int | number with no fractional part, from −2147483648 to 2147483647 | `2.0` is accepted (JavaScript cannot tell it from `2`, so it is the only rule all three faces can apply alike); `1.5`, `true`, `"1"`, `2147483648` are rejected |
| Double / Float / CGFloat / Number | any number, integers included | |
| Bool | boolean | `0` / `1` / `"true"` are rejected |
| Color | string (a colour token or hex) | resolved as the existing data update resolves it |
| `Array(X)` / `[X]` / `List<X>`, X one of the classes above | array whose every element is X | elements are not optional: `["a", null]` is rejected for `Array(String)` |
| `Array` | array of strings / numbers / booleans | a nested array or object is rejected |
| `Object` / `Hash` | object whose values are strings / numbers / booleans | a nested array or object is rejected |
| any of the above with a trailing `?` | the same, plus `null` | |
| closures / event handlers, `CollectionDataSource`, `Void`, `Visibility`, `Image`, `EdgeInsets`, `Dp`, `Alignment`, an array of a custom type (`[OrderItem]`), any other class | nothing | `unsupported type <class>`, also for `null` on an optional one |

`Visibility` is unsupported because its value differs per face (an enum on
SwiftUI, a Boolean on Compose); accepting it would first need a vocabulary
of values.

**Rejection reasons** (fixed strings; `<class>` is the class as the layout
spells it, `?` included):

- `not a data field`
- `type mismatch: expected <class>`
- `null for non-optional <class>`
- `unsupported type <class>`
- Android only: `viewModel has no updateData` (the generated ViewModel lacks
  the update block; the build warns about it)

The libraries do not apply through the existing data update
(`update(dictionary:)`, `fromMap`), which drops a value that does not fit
without saying so; the generators emit a checking apply function.

### 10.4 The state bridge (app → driver)

For each screen showing, while the gate is open:

```json
{
  "launchId": "6F1C2A9E-3B7D-4C1E-9A55-0D2F8E7B4C11",
  "initialState": { "applied": ["email"], "rejected": [{ "key": "nickname", "reason": "not a data field" }] },
  "data": { "email": "test@example.com", "password": "" }
}
```

- `launchId`: the launch the app is in, or `null` when it was not given one.
- `initialState`: present only when this screen applied a payload in this
  launch; `null` otherwise.
- `data`: the screen's Data, the fields whose class the table in §10.3
  accepts.
- Published again every time the data changes. Test builds only, so it is not
  throttled.
- Where:
  - iOS: the `accessibilityValue` of a dedicated leaf with the identifier
    `__state_<screenId>` — a transparent leaf like the screen marker, separate
    from it so the marker stays one per screen. Over 32 KB the value is
    `{"truncated": <bytes>}` instead.
  - Android: the semantics key `JsonUIState` (a JSON string) on the screen
    marker node itself; no extra node (a zero-size node drops out of the
    tree).
  - Web: `window.__JSONUI_STATE__[screenId]`.
- Two instances of one screen showing at once: which one's bridge is read is
  not specified.

### 10.5 What the driver checks

- **Receipt**: after a launch that carried a payload, the driver waits for the
  screen under test's bridge to show `initialState` with the same `launchId`,
  up to `screenReadyTimeout` (web: the existing setting; iOS and Android: a
  new setting of the same name; 15000 ms by default).
  - None by then → the cases fail with `failureReason: "setup"` (shared: all
    the cases of the file; reopen: that case). The message lists the likely
    causes: a library older than the versions above (rebuild with this
    jsonui-cli); a build with the gate closed; on web, a page that does not
    go through the generated hook; a screen id that does not match.
  - Any `rejected` entry → the same failure, listing each key and reason.
- **Flows**: each screen in `viewModels` is checked the first time the flow
  reaches it — when a step's `screen` changes and the implicit screen check
  passes. Same judgement. With `verifyScreenTransitions` off there is no
  implicit screen check, and the receipt is still checked the first time a
  step's `screen` changes to that screen. A screen leaves the pending set only
  once its receipt passed, so a retried flow body checks it again. A screen in
  `viewModels` the flow never reaches is a warning: a screen still pending
  when the flow ends, so a screen an earlier attempt reached but did not
  confirm is a warning too when the attempt that passed never went there.
- **Default state provider**: when the harness passes none, `state` resolves
  its `path` in the bridge `data` of the screen §6 names. The path rule and
  the bridge outcomes are `state-path.json`:
  - absent bridge, or a bridge without `data` → pending (auto-wait keeps
    polling; the timeout says the bridge is absent);
  - `truncated` → fails at once ("the iOS bridge holds up to 32 KB");
  - otherwise the path resolves or it does not; not resolving is pending.

### 10.6 What launch covers

- Web `clearState` covers cookies and local / session storage, not IndexedDB.
- iOS `clearState` and `arguments` on every face are delivered (env / extra /
  storage) and no further: the app-side reader is the app's (§5).

### 10.7 Shared vectors

| file | input → expected | run by |
|---|---|---|
| `specs/vectors/initial-state-payload.json` | test file (+ referenced files) → launches with their `screens`, case failures, warnings, validate errors | 3 drivers, `jsonui-test validate` |
| `specs/vectors/initial-state-coercion.json` | declared data (name, class) + input → applied keys, rejected keys with reasons | 3 generators, 2 libraries |
| `specs/vectors/state-path.json` | bridge `data` + path → value or not resolved; bridge → pending / truncated / value / unresolved | 3 drivers |

Expected results are codes, not messages; each implementation writes its own
message from the code. `launchId` is random and is not compared; order inside
objects and of applied / rejected is not compared.

| code | where | meaning |
|---|---|---|
| `case-initial-state-needs-reopen` | driver (case `setup` failure), validate | a case-level initialState in a `shared` file |
| `referenced-initial-state-ignored` | driver warning, validate warning | a flow references a file / case that has an initialState |
| `flow-initial-state-screen-removed` | validate | a flow writes `initialState.screen` |

jsonui-cli keeps one more vector in `shared/core/`: layout → Data names and
classes, so that validate (Python) and the three generators (Ruby) collect the
same names.

### 10.8 Not covered

- An action that sets state mid-run.
- State that is not the ViewModel's `data`.
- A flow's starting screen (`initialState.screen` is removed).
- Reading `JSONUI_TEST_ARGS` / `JSONUI_TEST_CLEAR_STATE` in the app.
