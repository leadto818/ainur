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

## TVT Multi-Agent Design Principles

### Purpose

Use Codex to design and refine the TVT multi-agent collaboration system. The focus is on editing agent definitions, collaboration logic, task flow, and feedback loops, not on prematurely collapsing the system into a single executable program.

### Design premises

1. Goal: an agent collaboration system

- `Master`、`Quarter`、各 `staff`（`iwencai`、`warrenq`、`hibor`、`shiguang`）应组成协作网络。
- 优先设计信息流、任务拆解、调度机制和反馈闭环，而不是单点功能执行。

2. Fully use agent capability

- 每个 agent 都应使用自己的模型能力完成任务理解、query 生成、判断、整理或冲突识别。
- 避免过度模板化、纯硬编码分支或把 agent 降级成“只会调用脚本的壳”。

3. Task decomposition before execution

- 在系统设计里，意图识别、任务拆解、query 生成、staff 路由与调度优先于 execution。
- 查询、抓取、脚本调用只是协作链中的一个环节，不应成为系统主体。

4. Closed-loop feedback is core

- 所有信息最终必须回流到 `Master`，用于综合判断、下一轮任务生成和策略修正。
- 保留原始数据、结构化摘要、冲突标注、证据缺口和未验证项。

### Codex editing principles

1. Do not default to writing executable programs

- 优先产出 agent 本体设定、职责边界、任务规则、交互协议、query 模板、回传格式和质量门控规则。
- 代码只作为验证 agent 逻辑或支撑协作流程的辅助工具。

2. Agents are autonomous but constrained

- `Master` 负责总体目标、约束、验收标准和闭环判断。
- `Quarter` 负责拆解任务、生成 staff query、派发与汇总。
- `Staff` 负责执行查询、返回结构化情报与原始证据。
- 各 agent 可以自主生成内容，但必须服从统一协作协议和质量门控。

3. Prefer templates and contracts over hardcoding

- query、任务单、回传结构优先使用 JSON、Markdown、envelope 等稳定格式。
- 先定义接口契约，再落地脚本或执行器，保证 agent 可替换、可验证、可扩展。

4. Optimize for extensibility

- 设计时预留 staff 扩展、模板升级、任务类型新增和路由策略调整的空间。
- 新增 skill 或新 staff 时，应尽量无痛接入现有闭环，而不是重写总流程。

5. Shift quality gates left

- 在任务派发前先自检拆解逻辑、query 质量、证据路径和输入边界。
- 不要把明显跑偏、含混或不可执行的任务直接下发给下层 agent。

6. Iterate and learn

- 允许 agent 通过多轮尝试优化 query、调度策略和输出结构。
- 日志、失败原因、冲突来源和反馈记录必须可追踪、可复盘。

### Codex operating guidance

When editing this project, prefer the following sequence:

1. 先输出 `Master` 本体设定、任务规则和委派提示词模板。
2. 再输出 `Quarter` 的任务拆解规则、staff 调度策略和 query 模板。
3. 再定义 `iwencai`、`warrenq`、`hibor`、`shiguang` 等 staff skill 规范。
4. 使用 JSON / Markdown / envelope 验证信息流闭环。
5. 检查闭环是否保持 `Master -> Quarter -> Staff -> Quarter -> Aggregate -> Master`。
6. 优先修改协作逻辑、协议和模板，不要先去改浏览器脚本或执行脚本。

### Summary rule

For TVT work in this project, Codex should treat agent collaboration as the primary design object. Favor smart agents with clear contracts, stable feedback loops, and explicit quality gates over single-program shortcuts.
