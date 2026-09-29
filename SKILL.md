---
name: tuitui-bot
description: 通过360推推机器人向指定人员或群聊发送文本、图片、文件和交互式卡片消息，拉取历史聊天记录，并可撤回已发送消息。当用户要求给推推里的某人/某群发消息、发图、发文件、发交互卡片、撤回消息、查看/拉取聊天记录，或管理推推机器人凭据(新增/查看机器人配置)时使用。
---

# 推推机器人消息发送

Python 实现的推推机器人客户端，等价于官方 `@qihoo/tuitui-bot-sdk`。
本 skill 不绑定任何特定平台：任何能执行 shell 命令的 AI Agent
（Qoder、Claude Code、Cursor 等）均可加载使用，也可作为 CLI 工具直接人工操作。
凭据保存在 [config.yaml](config.yaml)，脚本位于 [scripts/tuitui_bot.py](scripts/tuitui_bot.py)。

## 快速开始

在 skill 目录内直接执行：`python scripts/tuitui_bot.py <命令>`。
若安装为 Qoder skill，约定路径为 `.qoder/skills/tuitui-bot/scripts/tuitui_bot.py`；
其他 Agent 平台按各自约定放置，或直接以本目录为工具目录调用。
依赖 `requests` 和 `PyYAML`（缺失时执行 `pip install requests pyyaml`）。

```bash
# 验证凭据 / 查看机器人身份
python scripts/tuitui_bot.py info
# 返回示例: {"name": "运维机器人", "uid": "3000000000000000000", "account": "ops_bot"}

# 获取群 ID：列出机器人所在的所有群（先要把机器人拉进目标群）
python scripts/tuitui_bot.py groups
# 返回示例: [{"group_id": "123456789", "name": "项目群"}]
```

所有命令成功时输出 JSON 到 stdout；失败时以非零码退出并打印 `[错误] ...` 到 stderr。

## 命令一览

| 命令 | 用途 | 备注 |
| --- | --- | --- |
| `info` | 查询机器人信息（名称/UID/账号），验证凭据 | |
| `groups` | 列出机器人所在的所有群 | |
| `send-text` | 发送文本（支持 Markdown） | |
| `send-image` | 发送图片（JPG/PNG/GIF） | 需上传文件 |
| `send-file` | 发送文件/附件（任意类型，≤100MB） | 需上传文件 |
| `send-interactive` | 发送交互式卡片 | 仅支持恰好一个接收目标 |
| `pull` | 拉取历史消息(群聊或单聊) | 支持相对时间/分页 |
| `recall` | 撤回已发送的消息 | 仅支持恰好一个接收目标 |

## 收件人指定

`--to-account <推推账号>` / `--to-uid <UID>`（均可重复，最多 100 个）/ `--to-group <群ID>`。
群聊与个人互斥；发送/撤回类命令必须指定至少一个目标。

## 发送命令

```bash
# 文本（支持 Markdown）
python scripts/tuitui_bot.py send-text --to-account zhangsan --text "部署完成"

# 按 UID 发送
python scripts/tuitui_bot.py send-text --to-uid 7652669648945546 --text "你好"

# 图片（仅 JPG/PNG/GIF；支持本地路径或 http(s) URL，可用 --filename 自定义上传名）
python scripts/tuitui_bot.py send-image --to-account zhangsan --file ./chart.png
python scripts/tuitui_bot.py send-image --to-account zhangsan --file ./data.jpg --filename report.jpg

# 文件/附件（任意类型，≤100MB；支持本地路径或 URL）
python scripts/tuitui_bot.py send-file --to-group 123456 --file ./报告.pdf

# 交互式卡片：简写方式（仅允许恰好一个接收目标）
python scripts/tuitui_bot.py send-interactive --to-account zhangsan \
  --head "审批请求" --content "是否同意发布上线？" \
  --action "同意=approve" --action "拒绝=reject"

# 交互式卡片：完整结构（复杂卡片用 JSON 文件）
python scripts/tuitui_bot.py send-interactive --to-account zhangsan --card card.json

# 撤回已发送的消息（--msgid 为消息 ID，可从发送接口响应中取）
python scripts/tuitui_bot.py recall --to-account zhangsan --msgid "1024_abc123"
python scripts/tuitui_bot.py recall --to-group 123456 --msgid "1024_abc123"
```

## 拉取历史消息（pull）

```bash
# 拉群聊今天的消息（默认 --time today，最多 100 条）
python scripts/tuitui_bot.py pull --to-group 123456

# 拉单聊最近 7 天的消息
python scripts/tuitui_bot.py pull --to-account zhangsan --time last_7_days

# 分页翻页：用上一页响应里的 cursor
python scripts/tuitui_bot.py pull --to-group 123456 --time last_30_minutes --limit 50 --cursor "76599..."
```

- `--to-group` 与 `--to-account` 互斥，必须指定其一；群 ID 可用 `groups` 命令获取。
- `--time` 相对时间：`today` / `yesterday` / `day_before_yesterday` / `this_week` /
  `last_week` / `this_month` / `last_month` / `this_year`，或 `last_{N}_{unit}`
  （unit ∈ `minutes`/`hours`/`days`/`months`）；也可用 `--start-time`/`--end-time` 指定绝对范围。
- 输出 `{messages, has_more, cursor}`；`has_more=true` 时用返回的 `cursor` 继续翻页。
- 每条消息含 `message_id`、`from_account`、`from_name`、`msg_type`、`text`、
  `at_me`、`reply_to`（引用块，仅引用消息时有）及原始数据 `raw`；
  `message_id`/`group_id` 为大数，一律当字符串处理。
- `--raw` 直接输出服务端原始响应；`--asc` 按时间升序返回。

`--action` 简写格式：`按钮文本`、`文本=name` 或 `文本=name:value`；
也可直接传 JSON 串（须含 `text` 和 `name` 字段）。

交互式卡片参数：`--head`（头部文案，配合 `--head-bgcolor` 设置底色如 `#3873FA`）、
`--title`、`--content`、`--url`（卡片整体跳转链接）、`--action`（可多次）。

多机器人时加 `--bot <名称>` 选择；`--config <路径>` 可换配置文件。

## 凭据管理

`config.yaml` 结构：

```yaml
default: ceshi        # 默认机器人
bots:
  ceshi:
    appid: "3199004586"
    secret: "<secret>"
    # api_base: 可选，默认官方生产环境 https://im.live.360.cn:8282/robot
```

用户提供新机器人的 appid/secret 时，在 `bots` 下追加一个条目即可，
不要把 secret 输出到对话或日志中。
appid/secret 缺失或未找到指定机器人时，脚本会打印配置格式提示并以非零码退出。

## 交互式卡片结构（--card JSON）

```json
{
  "head": { "text": "头部文案", "bgcolor": "#3873FA", "tcolor": "FFFFFF" },
  "body": { "title": "标题", "content": "正文" },
  "url": "https://example.com",
  "action": [
    { "text": "同意", "name": "approve", "value": "approve",
      "color": "FFFFFF", "bgcolor": "#3873FA",
      "confirm": { "title": "确认", "content": "确定同意吗？", "ok": "确定", "cancel": "取消" } }
  ]
}
```

可选字段：`fields`（表单输入项）、`footer`、`summary`、`id`、`value`、
`action[].business`（跳转 web/umapp/native/conference）。

## 注意事项

- 交互卡片发送后如需处理按钮点击，需在推推后台配置交互回调（Webhook），
  本 skill 只负责发送，不接收回调。
- 消息内容支持 Markdown，交互式卡片除外。
- 图片仅支持 JPG/PNG/GIF 后缀，其余扩展名上传时打印警告（仍会尝试发送）。
- API 失败时脚本以非零码退出并打印 `errcode` 与响应详情；
  响应中的 `trans_id` 可提供给推推技术支持排查。
- 官方 SDK 文档: <https://www.npmjs.com/package/@qihoo/tuitui-bot-sdk>
