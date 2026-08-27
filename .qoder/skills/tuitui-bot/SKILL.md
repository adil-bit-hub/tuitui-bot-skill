---
name: tuitui-bot
description: 通过360推推机器人向指定人员或群聊发送文本、图片、文件和交互式卡片消息。当用户要求给推推里的某人/某群发消息、发图、发文件、发交互卡片，或管理推推机器人凭据(新增/查看机器人配置)时使用。
---

# 推推机器人消息发送

Python 实现的推推机器人客户端，等价于官方 `@qihoo/tuitui-bot-sdk`。
凭据保存在 [config.yaml](config.yaml)，脚本位于 [scripts/tuitui_bot.py](scripts/tuitui_bot.py)。

## 快速开始

脚本路径固定为 `.qoder/skills/tuitui-bot/scripts/tuitui_bot.py`（相对工作区）。
依赖 `requests` 和 `PyYAML`（本机已安装；缺失时执行 `pip install requests pyyaml`）。

```bash
# 验证凭据 / 查看机器人身份
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py info
```

## 发送命令

收件人三种写法（群聊与个人互斥）：
`--to-account <推推账号>` / `--to-uid <UID>`（均可重复，最多 100 个）/ `--to-group <群ID>`。

```bash
# 文本（支持 Markdown）
python .../tuitui_bot.py send-text --to-account zhangsan --text "部署完成"

# 图片（仅 JPG/PNG/GIF；支持本地路径或 http(s) URL）
python .../tuitui_bot.py send-image --to-account zhangsan --file ./chart.png

# 文件/附件（任意类型，≤100MB；支持本地路径或 URL）
python .../tuitui_bot.py send-file --to-group 123456 --file ./报告.pdf

# 交互式卡片：简写方式（仅允许恰好一个接收目标）
python .../tuitui_bot.py send-interactive --to-account zhangsan \
  --head "审批请求" --content "是否同意发布上线？" \
  --action "同意=approve" --action "拒绝=reject"

# 交互式卡片：完整结构（复杂卡片用 JSON 文件）
python .../tuitui_bot.py send-interactive --to-account zhangsan --card card.json
```

`--action` 简写格式：`按钮文本`、`文本=name` 或 `文本=name:value`；
也可直接传 JSON 串（须含 `text` 和 `name` 字段）。

多机器人时加 `--bot <名称>` 选择；`--config <路径>` 可换配置文件。

## 凭据管理

`config.yaml` 结构：

```yaml
default: ceshi        # 默认机器人
bots:
  ceshi:
    appid: "3199004586"
    secret: "<secret>"
    # api_base: 可选，默认官方生产环境
```

用户提供新机器人的 appid/secret 时，在 `bots` 下追加一个条目即可，
不要把 secret 输出到对话或日志中。

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
- API 失败时脚本以非零码退出并打印 `errcode` 与响应详情；
  响应中的 `trans_id` 可提供给推推技术支持排查。
- 官方 SDK 文档: <https://www.npmjs.com/package/@qihoo/tuitui-bot-sdk>
