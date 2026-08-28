# tuitui-bot — 360 推推机器人 Python 客户端 / Agent Skill

一个用 **Python** 实现的推推机器人客户端，等价于官方
[`@qihoo/tuitui-bot-sdk`](https://www.npmjs.com/package/@qihoo/tuitui-bot-sdk)（Node.js），
通过推推机器人开放 API 完成：

- 发送**文本**消息（支持 Markdown）
- 发送**图片**（JPG / PNG / GIF）
- 发送**文件 / 附件**（任意类型，≤100MB）
- 发送**交互式卡片**（按钮、表单、跳转链接）
- **撤回**已发送的消息
- 列出机器人所在的**群**（获取群 ID）
- 多机器人凭据管理（YAML 配置）

它首先是一个**命令行工具**，人工可直接使用；同时附带 `SKILL.md` 指令文档，
可被任何能执行 shell 命令的 AI Agent 加载为 skill
（[Qoder](https://qoder.com)、Claude Code、Cursor 等），不绑定任何特定平台。

## 目录结构

```
tuitui-bot-skill/
├── SKILL.md              # Agent 指令文档（供各类 AI Agent 读取）
├── README.md
├── config.example.yaml   # 凭据配置示例（入库）
├── config.yaml           # 你的真实凭据（不入库，需自行创建）
└── scripts/
    └── tuitui_bot.py     # Python 客户端 / 命令行工具
```

## 安装

```bash
git clone https://github.com/adil-bit-hub/tuitui-bot-skill.git
cd tuitui-bot-skill
pip install requests pyyaml
```

### 配置凭据

```bash
cp config.example.yaml config.yaml
```

```yaml
default: mybot          # 默认使用的机器人
bots:
  mybot:
    appid: "你的appid"
    secret: "你的secret"
    # api_base: 可选，默认 https://im.live.360.cn:8282/robot
```

> ⚠️ `config.yaml` 含敏感凭据，已被 `.gitignore` 排除，**切勿提交到仓库**。

### 作为 Agent Skill 安装（可选）

- **Qoder**：克隆到工作区的 `.qoder/skills/tuitui-bot` 目录即可被自动发现。
- **其他 Agent**：按各自平台的 skill/工具约定放置本目录，或让 Agent 读取 `SKILL.md` 后通过 CLI 操作。

## 使用

### 命令行

```bash
# 校验凭据 / 查看机器人身份
python scripts/tuitui_bot.py info

# 列出机器人所在的所有群（获取群 ID；需先把机器人拉进目标群）
python scripts/tuitui_bot.py groups

# 发送文本（支持 Markdown）
python scripts/tuitui_bot.py send-text --to-account zhangsan --text "部署完成"

# 发送图片（仅 JPG/PNG/GIF；支持本地路径或 http(s) URL，--filename 可自定义上传名）
python scripts/tuitui_bot.py send-image --to-account zhangsan --file ./chart.png

# 发送文件/附件（任意类型，≤100MB）
python scripts/tuitui_bot.py send-file --to-group 123456 --file ./报告.pdf

# 发送交互式卡片（仅限恰好一个接收目标）
python scripts/tuitui_bot.py send-interactive --to-account zhangsan \
  --head "审批请求" --content "是否同意发布上线？" \
  --action "同意=approve" --action "拒绝=reject"

# 复杂卡片：从 JSON 文件读取完整结构
python scripts/tuitui_bot.py send-interactive --to-account zhangsan --card card.json

# 撤回消息（--msgid 取自发送响应中的 msgid）
python scripts/tuitui_bot.py recall --to-account zhangsan --msgid "7678769490990369626"
```

收件人三种写法（群聊与个人互斥，个人最多 100 个）：

| 参数 | 含义 |
| --- | --- |
| `--to-account <账号>` | 推推账号，可重复 |
| `--to-uid <UID>` | 用户 UID，可重复 |
| `--to-group <群ID>` | 群聊 ID |

其他选项：`--bot <名称>` 切换机器人；`--config <路径>` 指定配置文件。

### 在 AI Agent 中对话触发

加载本 skill 后直接对 Agent 说自然语言即可，例如：

- “给 fengzhao 发消息：记得打卡”
- “把这张图发给 fengzhao”
- “给某群发一个审批卡片”
- “撤回刚才发的消息”

## API 说明

底层为推推机器人开放 API（逆向自官方 SDK v1.0.19）：

- Base：`https://im.live.360.cn:8282/robot`，所有请求以 `appid` + `secret` 查询参数鉴权
- `POST /message/custom/send` — 发送 text / image / attachment / interactive 消息
- `POST /message/custom/modify` — 撤回消息等
- `POST /media/upload?type=image|file` — 上传媒体，返回 `media_id`
- `GET /prop/get` — 查询机器人属性
- `GET /group/robot/in` — 列出机器人所在群

响应 `errcode=0` 为成功；失败时脚本以非零码退出并打印 `errcode`、`errmsg`
与 `trans_id`（可提供给推推技术支持排查）。

## 注意事项

- 交互卡片如需处理按钮点击回调，需在推推后台配置 Webhook；本工具只负责发送与撤回。
- 消息内容支持 Markdown，交互式卡片除外。
- 推推为 360 内部产品，机器人能力开通与使用请遵循公司内部规范。
- 官方 SDK 文档：<https://www.npmjs.com/package/@qihoo/tuitui-bot-sdk>
