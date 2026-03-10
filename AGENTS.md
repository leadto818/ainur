# Browser Session Rules

## Default rule

- For browser tasks, always prefer the user's already-open browser window and existing logged-in session.
- Do not default to launching a fresh Chrome instance, fresh Playwright profile, or isolated browser context if the task depends on login state, extensions, local storage, cookies, or browser permissions.

## When working with authenticated sites

- Assume a newly launched browser instance will lose:
  - login state
  - cookies/local storage/session storage
  - extension state
  - browser-level permissions
  - AppleScript JavaScript permission state
- Because of that, do not open a new browser instance for authenticated workflows unless the user explicitly asks for it or the existing browser session is unusable.

## AppleScript / Chrome automation rule

- Before using AppleScript `execute javascript` against Google Chrome, first prefer the user's existing Chrome window.
- If JavaScript from Apple Events is required, check whether `View > Developer > Allow JavaScript from Apple Events` is enabled in that exact Chrome instance.
- Do not create a new Chrome instance if the task depends on that setting; a new instance may not inherit the same permission state.

## WarrenQ-specific rule

- For WarrenQ and similar chat tools, first reuse the currently open WarrenQ tab.
- Prefer DOM inspection, in-page instrumentation, and network observation inside the user's existing session.
- Do not switch to a fresh Playwright/Chrome instance unless the user explicitly accepts the cost of re-login and re-enabling permissions.

## Escalation rule

- If a fresh instance seems necessary, warn the user first with the concrete tradeoff:
  - re-login required
  - Apple event JavaScript may need to be re-enabled
  - automation may stop working until permissions are restored
