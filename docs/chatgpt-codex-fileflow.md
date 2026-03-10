# ChatGPT 与 Codex 文件流转方案

## 目标

把 ChatGPT 生成的结构化文档稳定地交给 Codex 或 OpenClaw 处理，并支持 Codex 结果再回传给 ChatGPT 或上层 Orchestrator，尽量做到：

- 不丢失标题层级
- 不破坏 Markdown 结构
- 不破坏代码块
- 不破坏 Mermaid 图
- 可以追踪来源项目、线程、文档版本
- 可以让 Codex 直接消费

结论上，`JSON envelope + Markdown body + task/result 双向接口` 是最稳妥的交接方式。

## 设计原则

这套流转按 Codex 的对象模型来设计：

- `project`：当前工作区或项目
- `thread`：一次主题会话
- `document`：线程中产出的某一份可交接内容
- `artifact`：Codex 处理后的输出

所以目录和元数据都围绕这四层展开，而不是做一个松散的 `docs/` 大杂烩。

## 推荐目录

建议在项目里固定一套目录：

```text
docs/
  handoff/
    projects/
      <project_slug>/
        manifest.json
        threads/
          <thread_slug>/
            00-source/
              <doc_slug>.md
              <doc_slug>.envelope.json
            10-validated/
              <doc_slug>.envelope.json
            20-codex-in/
              <doc_slug>.task.json
            30-codex-out/
              <doc_slug>.result.md
              <doc_slug>.result.json
            40-archive/
              <doc_slug>.snapshot.md
              <doc_slug>.snapshot.json
```

## 目录含义

### `docs/handoff/projects/<project_slug>/manifest.json`

项目级索引。

记录：

- 项目名
- 项目路径
- 最近处理线程
- 已登记文档
- 当前 schema 版本

### `threads/<thread_slug>/00-source/`

ChatGPT 原始交付区。

这里放两份文件：

- 原始 Markdown
- 对应的 JSON envelope

这样做的原因是：

- Markdown 便于人阅读和审校
- JSON envelope 便于 Codex 稳定解析

### `threads/<thread_slug>/10-validated/`

校验后的规范输入。

只有通过校验的 envelope 才进入这里。

校验内容至少包括：

- 必填字段完整
- `project`、`thread`、`doc_name` 存在
- block 类型合法
- 代码块和 Mermaid 块完整闭合

### `threads/<thread_slug>/20-codex-in/`

Codex 的任务入口。

这里的 `.task.json` 用于告诉 Codex：

- 要读取哪个 envelope
- 目标动作是什么
- 输出位置在哪里

### `threads/<thread_slug>/30-codex-out/`

Codex 的输出区。

通常会放：

- 人类可读结果：`.result.md`
- 机器可读结果：`.result.json`

其中 `.result.json` 是 Codex 返回给 ChatGPT 或 Orchestrator 的标准回传接口。

### `threads/<thread_slug>/40-archive/`

归档快照区。

保留每次处理后的稳定版本，避免后续覆盖。
建议至少归档：

- 输入 Markdown 快照
- 输入 envelope 快照
- task 快照
- result.md 快照
- result.json 快照

## 文件命名规则

建议统一用 slug，不要直接把中文标题当文件名。

例如：

- `project_slug`: `tvt`
- `thread_slug`: `openclaw-agent-baseline`
- `doc_slug`: `tvt-openclaw-agent-baseline-v1`

那么文件就是：

```text
docs/handoff/projects/tvt/threads/openclaw-agent-baseline/00-source/tvt-openclaw-agent-baseline-v1.md
docs/handoff/projects/tvt/threads/openclaw-agent-baseline/00-source/tvt-openclaw-agent-baseline-v1.envelope.json
```

## 推荐的 JSON envelope 结构

```json
{
  "schema_version": "1.0",
  "meta": {
    "source_system": "chatgpt",
    "target_system": "codex",
    "project": {
      "slug": "tvt",
      "name": "TVT"
    },
    "thread": {
      "slug": "openclaw-agent-baseline",
      "name": "TVT-OpenClaw-Agent 基础执行文档"
    },
    "document": {
      "slug": "tvt-openclaw-agent-baseline-v1",
      "name": "TVT-OpenClaw-Agent 基础执行文档",
      "version": "1.0",
      "created_at": "2026-03-08T10:00:00+08:00",
      "content_format": "markdown-blocks"
    }
  },
  "payload": {
    "blocks": [
      {
        "type": "heading",
        "level": 1,
        "text": "TVT-OpenClaw-Agent 基础执行文档"
      },
      {
        "type": "paragraph",
        "text": "总体架构说明..."
      },
      {
        "type": "mermaid",
        "language": "mermaid",
        "code": "flowchart TB\nMaster[master]\nQuarter[quarter]"
      },
      {
        "type": "code",
        "language": "bash",
        "code": "openclaw agents refresh"
      }
    ]
  }
}
```

注意：`thread.slug`、`document.slug`、目录路径里的 `<thread_slug>`、`<doc_slug>` 必须一致。
不要出现 metadata 写 `openclaw-agent-dualtrack`，但目录却仍用 `openclaw-agent-baseline` 的情况，否则后续索引、校验和回传会混乱。

## 为什么不要只存 Markdown

只存 Markdown 的问题是：

- 人能看，但机器难稳定抽取结构
- Mermaid 和代码块容易在二次转存时被误处理
- 不方便挂项目、线程、版本等强元数据

所以最稳妥的做法不是“只用 JSON 取代 Markdown”，而是：

- `Markdown` 作为人类审阅稿
- `JSON envelope` 作为系统交接稿

## 推荐流转步骤

### 1. ChatGPT 产出正文

ChatGPT 先输出标准 Markdown 文档。

输出到：

```text
threads/<thread_slug>/00-source/<doc_slug>.md
```

### 2. 生成 JSON envelope

把 Markdown 结构转成 block 列表，保留：

- heading
- paragraph
- list
- blockquote
- code
- mermaid
- table

输出到：

```text
threads/<thread_slug>/00-source/<doc_slug>.envelope.json
```

### 3. 校验

校验通过后，复制到：

```text
threads/<thread_slug>/10-validated/<doc_slug>.envelope.json
```

这一步的目的不是形式主义，而是挡住这些错误：

- 缺失 `schema_version`
- `meta` 字段不完整
- Markdown 转 JSON 时 block 顺序错乱
- Mermaid 被截断
- 代码块语言丢失

### 4. 生成 Codex 任务文件

建立一个最小任务描述：

```json
{
  "task_type": "ingest_document",
  "input_envelope": "../10-validated/tvt-openclaw-agent-baseline-v1.envelope.json",
  "expected_outputs": [
    "../30-codex-out/tvt-openclaw-agent-baseline-v1.result.md",
    "../30-codex-out/tvt-openclaw-agent-baseline-v1.result.json"
  ]
}
```

放到：

```text
threads/<thread_slug>/20-codex-in/<doc_slug>.task.json
```

### 5. Codex / OpenClaw 消费

Codex 读取 `.task.json`，再读取 envelope。

消费时应遵守：

- 优先使用 envelope 的 block 顺序重建文档语义
- 不要把 Mermaid 当普通代码块丢掉
- 不要把 heading 降级成普通段落
- 必要时再回看原始 Markdown 做对照

### 6. 产出结果

Codex 输出两份结果：

- `.result.md`：人类可读
- `.result.json`：机器可追踪

写到：

```text
threads/<thread_slug>/30-codex-out/
```

建议 `.result.json` 至少包含这些字段：

```json
{
  "schema_version": "1.0",
  "meta": {
    "source_system": "codex",
    "target_system": "chatgpt",
    "project": {
      "slug": "tvt",
      "name": "TVT"
    },
    "thread": {
      "slug": "openclaw-agent-dualtrack",
      "name": "TVT-OpenClaw-Agent 双轨文件流"
    },
    "document": {
      "slug": "tvt-openclaw-agent-dualtrack-v1",
      "name": "TVT-OpenClaw-Agent 双轨文件流 + ChatGPT/Codex 闭环流程",
      "version": "1.0"
    },
    "execution": {
      "task_type": "ingest_document",
      "task_id": "codex-task-001",
      "executed_at": "2026-03-08T16:40:00+08:00",
      "status": "success",
      "orchestrator": "openclaw"
    },
    "input_refs": {
      "task": "../20-codex-in/tvt-openclaw-agent-dualtrack-v1.task.json",
      "envelope": "../10-validated/tvt-openclaw-agent-dualtrack-v1.envelope.json"
    }
  },
  "payload": {
    "summary": "文档已完成 ingest，并生成结构化输出。",
    "artifacts": [
      {
        "type": "markdown",
        "path": "./tvt-openclaw-agent-dualtrack-v1.result.md"
      }
    ]
  }
}
```

这样 ChatGPT 或上层编排器就能稳定知道：

- 这是哪个项目、哪个线程、哪份文档的结果
- 这次任务是否成功
- 输入来自哪里
- 输出产物在哪里

### 7. ChatGPT / Orchestrator 回收结果

ChatGPT 或上层编排器读取 `30-codex-out/*.result.json`。

可做的动作包括：

- 渲染结果给用户
- 判断是否继续下一轮任务
- 根据 `status` 决定重试、补料或结束
- 把本次结果登记进更高层的任务板或 Notion

这一步让系统从单向交接变成闭环。

### 8. 归档快照

当这次处理确认稳定后，把输入和关键输出做快照归档到：

```text
threads/<thread_slug>/40-archive/
```

## 推荐的 block 类型

建议第一版只支持这些，够用了：

- `heading`
- `paragraph`
- `list`
- `blockquote`
- `code`
- `mermaid`
- `table`
- `thematic_break`

不要一开始就做太多花哨类型，否则校验和兼容都会变脆。

## 版本控制建议

### 文档版本

文档级版本写在：

- `meta.document.version`

例如：

- `1.0`
- `1.1`
- `2.0`

### schema 版本

envelope 结构版本写在：

- `schema_version`

例如：

- `1.0`

这两个版本不要混在一起。

## 对你这个 TVT 场景的直接建议

如果你现在要交接的是：

- `TVT-OpenClaw-Agent 基础执行文档`

那我建议先这样落地：

```text
docs/
  handoff/
    projects/
      tvt/
        manifest.json
        threads/
          openclaw-agent-dualtrack/
            00-source/
              tvt-openclaw-agent-dualtrack-v1.md
              tvt-openclaw-agent-dualtrack-v1.envelope.json
            10-validated/
              tvt-openclaw-agent-dualtrack-v1.envelope.json
            20-codex-in/
              tvt-openclaw-agent-dualtrack-v1.task.json
            30-codex-out/
              tvt-openclaw-agent-dualtrack-v1.result.md
              tvt-openclaw-agent-dualtrack-v1.result.json
            40-archive/
              tvt-openclaw-agent-dualtrack-v1.snapshot.md
              tvt-openclaw-agent-dualtrack-v1.snapshot.json
```

## 最终建议

如果只是团队阅读，Markdown 就够。

如果要做 ChatGPT -> Codex -> OpenClaw 的稳定文件流转，推荐固定采用：

1. `Markdown` 原文
2. `JSON envelope` 交接
3. `task.json` 驱动 Codex 消费
4. `result.md + result.json` 作为输出
5. `result.json` 反向回传给 ChatGPT / Orchestrator

这样设计的好处是：

- 人和机器都能读
- 结构不会丢
- 项目、线程、文档来源可追踪
- 后面加自动化也容易
