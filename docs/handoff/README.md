# ChatGPT / Codex Handoff README

## 这套目录是干什么的

这里放的是 ChatGPT 和 Codex 之间的文件流转目录。

目标是：

- ChatGPT 产出 Markdown
- Codex 把 Markdown 转成 JSON envelope
- Codex 根据 task 文件执行处理
- Codex 生成结果
- Codex 再生成一个可直接拖回 ChatGPT 的 `.md` 文件

## 目录结构

```text
docs/handoff/projects/<project_slug>/threads/<thread_slug>/
  00-source/
  10-validated/
  20-codex-in/
  30-codex-out/
  40-archive/
```

## 你平时怎么把材料交给我

优先顺序如下：

1. ChatGPT Canvas 导出的 `.md`
2. 你直接粘贴给我的 JSON
3. `.docx`
4. `.pdf`

建议默认用 `.md`。

## 什么时候直接粘贴 JSON

如果 ChatGPT 已经给了你完整的 JSON envelope，那最省事的方式就是直接粘贴给我。

我会把它落成：

```text
00-source/<doc_slug>.envelope.json
```

你不需要自己额外另存成文件。

## 什么时候给我 `.md`

如果你从 ChatGPT Canvas 下载的是 `.md`，直接把文件给我就可以。

我会：

1. 放到 `00-source/`
2. 生成 `.envelope.json`
3. 复制到 `10-validated/`
4. 建好 `.task.json`

## `.docx` 和 `.pdf` 能不能用

能用，但只是 fallback。

原因是：

- `.docx` 和 `.pdf` 不适合直接做结构化交接
- 代码块、Mermaid、标题层级更容易丢

所以如果你给我 `.docx` 或 `.pdf`，我会先尽量转成 Markdown，再进入 handoff 流程。

## Codex 跑完后你会拿到什么

你至少会拿到三个东西：

- `.result.md`
- `.result.json`
- `.chatgpt-return.md`

其中最适合你拖回 ChatGPT 的，就是：

```text
30-codex-out/<doc_slug>.chatgpt-return.md
```

## 当前 TVT 样板

当前已经建好的样板线程在：

```text
docs/handoff/projects/tvt/threads/openclaw-agent-dualtrack/
```

当前可以直接打开并拖回 ChatGPT 的文件是：

```text
docs/handoff/projects/tvt/threads/openclaw-agent-dualtrack/30-codex-out/tvt-openclaw-agent-dualtrack-v1.chatgpt-return.md
```

## 对话完整备份也可以走同一套体系

现在这套 handoff 也可以直接备份 Codex 当前线程。

流程是：

1. 从本地 `~/.codex/sessions/*.jsonl` 导出当前线程
2. 生成按时间顺序排列的完整 Markdown 备份
3. 生成 `.envelope.json`
4. 再复制出一个可直接拖回 ChatGPT 的 `.chatgpt-return.md`

当前已经生成的一份样板在这里：

```text
docs/handoff/projects/ainur/threads/codex-other-app-integration/30-codex-out/codex-other-app-integration-backup-20260308-195610.chatgpt-return.md
```

如果你要我以后继续这样备份，只要直接说：

- `用 $chatgpt-codex-handoff 完整备份当前对话`
- `用 $chatgpt-codex-handoff 把当前线程导出到 handoff 目录`
- `用 $chatgpt-codex-handoff 备份当前对话并给我一个可拖回 ChatGPT 的 md`

默认语义是：

- 如果你是在某个 thread 里发这句命令，我应该备份那个 thread
- 不是备份我当前正在解释问题的另一个 thread

如果你要显式指定，也可以直接说 thread 名，例如：

- `用 $chatgpt-codex-handoff 完整备份“设计 multi-agents 工作流”这个 thread`

## 增量备份也已经支持

如果你已经做过一次完整备份，后面又继续推进了项目，现在可以只备份“新增的对话部分”。

增量备份会自动：

1. 找到这个线程最近一次备份
2. 读取那份备份里最后一条事件的时间戳
3. 只导出这之后新增的用户消息、助手消息、工具调用和工具输出
4. 生成新的时间戳文件

你可以这样叫我：

- `用 $chatgpt-codex-handoff 增量备份当前对话`
- `用 $chatgpt-codex-handoff 只备份上次完整备份之后新增的内容`
- `用 $chatgpt-codex-handoff 为这个线程生成增量备份并给我可拖回 ChatGPT 的 md`

如果你要指定 thread，也可以说：

- `用 $chatgpt-codex-handoff 为“设计 multi-agents 工作流”做增量备份`
