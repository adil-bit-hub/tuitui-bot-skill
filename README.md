# tuitui-bot — 360 推推机器人 Qoder Skill

一个用 **Python** 实现的 [Qoder Skill](https://qoder.com)，等价于官方
[`@qihoo/tuitui-bot-sdk`](https://www.npmjs.com/package/@qihoo/tuitui-bot-sdk)（Node.js），
通过推推机器人开放 API 向指定人员或群聊发送：

- 文本消息（支持 Markdown）
- 图片（JPG / PNG / GIF）
- 文件 / 附件（任意类型，≤100MB）
- 交互式卡片（按钮、表单、跳转）

## 安装

将本仓库克隆到你的工作区，使 skill 位于 `.qoder/skills/tuitui-bot/`：

```bash
git clone <本仓库> .qoder/skills/tuitui-bot-tmp
# 或直接复制 tuitui-bot 目录到 .qoder/skills/ 下
```

依赖：

```bash
pip install requests pyyaml
```

## 配置凭据

复制示例配置并填入你的机器人 appid / secret：

```bash
cp .qoder/skills/tuitui-bot/config.example.yaml .qoder/skills/tuitui-bot/config.yaml
```

```yaml
default: mybot
bots:
  mybot:
    appid: "你的appid"
    secret: "你的secret"
```

> ⚠️ `config.yaml` 含敏感凭据，已在 `.gitignore` 中排除，切勿提交到仓库。

## 使用

```bash
# 校验凭据
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py info

# 文本
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py send-text \
  --to-account zhangsan --text "部署完成"

# 图片
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py send-image \
  --to-account zhangsan --file ./chart.png

# 文件
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py send-file \
  --to-group 123456 --file ./报告.pdf

# 交互式卡片
python .qoder/skills/tuitui-bot/scripts/tuitui_bot.py send-interactive \
  --to-account zhangsan --head "审批请求" --content "是否同意发布？" \
  --action "同意=approve" --action "拒绝=reject"
```

收件人：`--to-account`（推推账号）/ `--to-uid` / `--to-group`（群聊，与个人互斥）。

在 Qoder 中可直接对话触发，例如：“给 fengzhao 发一张图”“发个审批卡片给某群”。

## API 说明

底层为推推机器人开放 API（逆向自官方 SDK v1.0.19）：

- Base: `https://im.live.360.cn:8282/robot`，所有请求以 `appid` + `secret` 查询参数鉴权
- `POST /message/custom/send` — 发送 text / image / attachment / interactive 消息
- `POST /media/upload?type=image|file` — 上传媒体，返回 `media_id`
- `GET  /prop/get` — 查询机器人属性

响应 `errcode=0` 为成功；失败时打印 `errcode`、`errmsg` 与 `trans_id`（可用于向推推技术支持排查）。

## 许可

仅供内部学习使用。
