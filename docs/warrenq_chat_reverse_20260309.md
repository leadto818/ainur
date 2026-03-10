# WarrenQ Chat Reverse Notes

Date: 2026-03-09
Site: `https://pure.warrenq.com/#/home`

## Current conclusion

WarrenQ chat is a same-origin SPA chat panel embedded in `#/home`.

The current best-supported model is:

1. Session management uses ordinary HTTP endpoints.
2. User ask and regenerate both route through one shared sender.
3. The shared sender uses `POST` plus streaming `data:` chunks in `onDownloadProgress`.
4. The most likely submit endpoint for both first ask and regenerate is:
   - `/cloudtest/chat/v2/agent/chat/askRegenerateAnswer`
5. The behavior is distinguished by payload field:
   - `askType: "ask"`
   - `askType: "RegenerateAnswer"`

This is not yet proven by direct runtime interception, but it is the strongest conclusion supported by the loaded bundles.

## Real browser flow

### UI facts

- Chat input is a Quill editor: `.ql-editor`
- Direct `innerHTML` mutation is not enough
- Valid input path must go through editor-native input flow
- Send is successful once the send button leaves disabled state

### Browser automation flow

1. Open existing logged-in Chrome tab at `pure.warrenq.com/#/home`
2. If needed, click `新建会话`
3. Wait for init requests
4. Insert prompt into `.ql-editor`
5. Click `发送`
6. Wait until answering finishes
7. Extract the last `.message-container`
8. If present, separately extract smart stock cards / tables

## Confirmed session-layer endpoints

These were extracted from loaded JS bundles and observed page behavior.

### Session and history

- `/chat/v2/chat/addChatSession`
- `/chat/v2/chat/session/getSessionListByWq`
- `/chat/v2/agent/newchat/page/findWqSessionPage`
- `/chat/v2/chat/queryChatRecordNew`
- `/chat/v2/agent/record/query`
- `/chat/v2/agent/debug/recordlist/query`
- `/chat/v2/chat/getLastChatRecord`
- `/chat/v2/agent/record/getLastChatRecord`
- `/chat/v2/chat/cleaningRecord`
- `/chat/v2/agent/record/cleaningRecord`
- `/chat/v2/chat/removeChatRecord`
- `/chat/v2/agent/record/remove`
- `/chat/v2/chat/removeMoreChatSession`
- `/chat/v2/chat/modifyChatSession`
- `/chat/v2/chat/pinnedSession`

### Agent config and guide

- `/chat/v2/agent/getWqDefaultAgent`
- `/chat/v2/agent/getAskDto`
- `/chat/v2/agent/getPrologue`
- `/chat/v2/userAdvice/chatUserAdviceOption`
- `/nlpagent/v2/recommend_question`

### Attached file helpers

- `/chat/v2/agent/base/file/moreFilesave`
- `/chat/v2/agent/base/file/getAnalysisStatus`
- `/chat/v2/agent/newchat/findFileBySessionId`
- `/chat/v2/chatFile/getFileDirectory`

## Shared sender

The sender implementation comes from the chat bundle and has this shape:

```js
window.__do__.post(this.option.sendUrl, JSON.stringify(e), {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "*"
  },
  data: JSON.stringify(e),
  signal: this.ac.signal,
  onDownloadProgress: async (evt) => {
    const rows = evt.target.responseText
      .split("\\n")
      .filter(x => x.startsWith("data:"))
      .filter(x => {
        try {
          return JSON.parse(x.substring(5))
        } catch {
          return false
        }
      })
  }
})
```

### Implication

The answer stream is not a normal one-shot JSON response.

It is a streamed response parsed from newline-delimited `data:` chunks.

## Normal ask payload

The `sendMessage(...)` implementation constructs a payload with these fields:

```json
{
  "sessionId": "...",
  "askType": "ask",
  "query": "user prompt",
  "formatQuery": "...",
  "raw": "...",
  "chat_history": [],
  "debug_mode": true,
  "generator_model_name": "...",
  "planner_model_name": "...",
  "agentId": "...",
  "agentBatchId": "...",
  "chatType": "new_chat | new_chat_agent | ...",
  "selected_text": "...",
  "title": "...",
  "flag_kb_only": false,
  "urlVersion": "...",
  "recomQuestionFlag": 1,
  "recordDocs": [
    {
      "docName": "...",
      "docId": "...",
      "fileSize": "...",
      "extension": "...",
      "filePath": "...",
      "md5": "...",
      "sourceFileId": "...",
      "sourceType": 1,
      "mappingFileId": "...",
      "mappingFileType": "...",
      "at_index": 0
    }
  ]
}
```

## Regenerate payload

The `regenerateMessage(...)` implementation constructs:

```json
{
  "sessionId": "...",
  "askType": "RegenerateAnswer",
  "questionId": "...",
  "formatQuery": "...",
  "raw": "...",
  "debug_mode": true,
  "agentId": "...",
  "agentBatchId": "...",
  "generator_model_name": "...",
  "planner_model_name": "...",
  "selected_text": "...",
  "title": "...",
  "chatType": "...",
  "urlVersion": "...",
  "flag_kb_only": false,
  "recordDocs": []
}
```

## Strongest current endpoint hypothesis

### Hypothesis

Both first ask and regenerate are sent to:

`/cloudtest/chat/v2/agent/chat/askRegenerateAnswer`

### Why this is currently the best hypothesis

1. `sendMessage(...)` and `regenerateMessage(...)` both call the same `core.send(...)`
2. The only loaded sender implementation with a concrete `sendUrl` literal points to:
   - `chat/v2/agent/chat/askRegenerateAnswer`
3. Loaded WARRENQ chunks do not expose another `/chat/v2/agent/chat/*` submit endpoint
4. The sender path is generic and clearly designed to accept both payload shapes

### What is still missing

Direct runtime interception of the request URL at send time.

AppleScript JS execution on the existing Chrome tab can read DOM and storage, but does not expose page runtime globals on this site, so `window.__do__` interception is not currently available from that path.

## Dynamic evidence already observed

From the active WarrenQ tab resource timeline, the latest visible chat-layer requests included:

- `https://pure.warrenq.com/cloudtest/chat/v2/chat/session/getSessionListByWq`
- `https://pure.warrenq.com/cloudtest/chat/v2/agent/record/query`

This matches the session-sync side of the model.

The actual answer body is still most consistent with the sender's streaming `POST` handler.

## Smart stock card side path

The answer body may append stock selection cards. These are rendered separately from the plain text answer.

Observed related endpoints:

- `/smartfansChatAIservice/agent/multipleFactor/filter/stockMultipleFactorFilter`
- `/smartfansChatAIservice/agent/multipleFactor/filter/fundMultipleFactorFilter`
- `/smartfansChatAIservice/agent/multipleFactor/filter/bondMultipleFactorFilter`

These are downstream card/data endpoints, not the main chat submit endpoint.

## Minimal API trial plan

### Step 1

Create a session:

`POST /cloudtest/chat/v2/chat/addChatSession`

Minimal body:

```json
{
  "sessionName": "新对话",
  "sessionType": "agent",
  "chatType": "new_chat",
  "agentId": "...",
  "agentBatchId": "..."
}
```

### Step 2

Send normal ask to the current best candidate endpoint:

`POST /cloudtest/chat/v2/agent/chat/askRegenerateAnswer`

Minimal body:

```json
{
  "sessionId": "...",
  "askType": "ask",
  "query": "公告了openclaw业务的上市公司有哪些",
  "formatQuery": "公告了openclaw业务的上市公司有哪些",
  "raw": "{\"type\":\"TextMessage\",\"content\":\"公告了openclaw业务的上市公司有哪些\"}",
  "chat_history": [],
  "agentId": "...",
  "agentBatchId": "...",
  "chatType": "new_chat"
}
```

### Step 3

Read the response as a streaming body and parse lines prefixed with `data:`.

### Step 4

After stream end, optionally pull:

- `/cloudtest/chat/v2/agent/record/query`
- `/cloudtest/chat/v2/chat/session/getSessionListByWq`

## Validation targets for the next round

1. Confirm whether `askRegenerateAnswer` accepts `askType: "ask"`
2. Confirm the exact required headers beyond default auth/signature headers already injected by the site
3. Capture a real streamed response sample
4. Confirm whether any hidden runtime-composed URL overrides `sendUrl`

## Practical status

Enough is known now to attempt a direct API reproduction.

The next practical move is not more UI exploration. It is a controlled request replay using the current logged-in browser state as reference.
