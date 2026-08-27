#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""360 推推机器人 Python 客户端。

@qihoo/tuitui-bot-sdk 的等价 Python 实现，通过推推机器人开放 API
发送文本、图片、文件（附件）和交互式卡片消息。

凭据保存在 skill 目录下的 config.yaml，支持多个机器人配置。
"""

import argparse
import json
import mimetypes
import sys
from pathlib import Path

import requests
import yaml

API_BASE = "https://im.live.360.cn:8282/robot"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100MB
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}


class TuituiApiError(RuntimeError):
    """推推 API 调用失败，message 中包含 errcode 与响应详情。"""


# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------

class TuituiBot:
    def __init__(self, appid, app_secret, api_base=API_BASE, timeout=60):
        self.appid = str(appid).strip()
        self.app_secret = str(app_secret).strip()
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    # -- 底层请求 -----------------------------------------------------------

    def _request(self, method, endpoint, payload=None, files=None,
                 extra_params=None):
        params = {"appid": self.appid, "secret": self.app_secret}
        if extra_params:
            params.update(extra_params)
        url = f"{self.api_base}{endpoint}"
        if method == "GET":
            resp = self.session.get(url, params=params, timeout=self.timeout)
        elif files is not None:
            resp = self.session.post(url, params=params, files=files,
                                     timeout=self.timeout)
        else:
            resp = self.session.post(url, params=params, json=payload or {},
                                     timeout=self.timeout)
        try:
            data = json.loads(resp.content.decode("utf-8")) if resp.content else {}
        except (ValueError, UnicodeDecodeError):
            raise TuituiApiError(
                f"{endpoint} 返回非 JSON 响应 (HTTP {resp.status_code}): "
                f"{resp.text[:500]}")
        if resp.status_code // 100 != 2:
            raise TuituiApiError(
                f"{endpoint} 请求失败 HTTP {resp.status_code}: {data}")
        errcode = data.get("errcode", 0)
        try:
            errcode = int(errcode)
        except (TypeError, ValueError):
            errcode = -1
        if errcode != 0:
            raise TuituiApiError(f"{endpoint} 失败 errcode={errcode}: {data}")
        return data

    # -- 机器人属性 ---------------------------------------------------------

    def info(self):
        data = self._request("GET", "/prop/get")
        return {
            "name": str(data.get("robot_name", "")).strip(),
            "uid": str(data.get("robot_uid", "")),
            "account": str(data.get("robot_account", "")).strip(),
        }

    # -- 文件上传 -----------------------------------------------------------

    def upload(self, content: bytes, filename: str, media_type: str) -> str:
        """上传媒体，返回 media_id。media_type: image | file"""
        if len(content) > MAX_UPLOAD_BYTES:
            raise TuituiApiError(
                f"文件过大: {len(content) / 1048576:.2f}MB，超过 100MB 限制")
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        files = {"media": (filename, content, mime)}
        data = self._request("POST", "/media/upload", files=files,
                             extra_params={"type": media_type})
        return data["media_id"]

    # -- 发送消息 -----------------------------------------------------------

    def send_raw(self, payload: dict) -> dict:
        return self._request("POST", "/message/custom/send", payload)

    def send_text(self, target, text, at=None):
        payload = {**target, "msgtype": "text",
                   "text": {"content": text}, "at": at or []}
        return self.send_raw(payload)

    def send_image(self, target, media_id):
        payload = {**target, "msgtype": "image",
                   "image": {"media_id": media_id}, "at": []}
        return self.send_raw(payload)

    def send_attachment(self, target, media_id):
        payload = {**target, "msgtype": "attachment",
                   "attachment": {"media_id": media_id}, "at": []}
        return self.send_raw(payload)

    def send_interactive(self, target, interactive: dict):
        payload = {**target, "msgtype": "interactive",
                   "interactive": interactive}
        return self.send_raw(payload)

    def modify_text(self, account_or_group, message_id, text, is_group=False):
        if is_group:
            target = {"togroups": [{"group": account_or_group,
                                    "msgid": message_id}]}
        else:
            target = {"tousers": [{"user": account_or_group,
                                   "msgid": message_id}]}
        payload = {**target, "msgtype": "text", "text": {"content": text}}
        return self._request("POST", "/message/custom/modify", payload)

    def modify_interactive(self, account_or_group, message_id, interactive,
                           is_group=False):
        if is_group:
            target = {"togroups": [{"group": account_or_group,
                                    "msgid": message_id}]}
        else:
            target = {"tousers": [{"user": account_or_group,
                                   "msgid": message_id}]}
        payload = {**target, "msgtype": "interactive",
                   "interactive": interactive}
        return self._request("POST", "/message/custom/modify", payload)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def build_target(accounts=None, uids=None, group=None) -> dict:
    """构造消息目标。群聊与个人不可混用；个人最多 100 个。"""
    accounts = [a.strip() for a in (accounts or []) if a and a.strip()]
    uids = [u.strip() for u in (uids or []) if u and u.strip()]
    group = group.strip() if group else ""
    if group:
        if accounts or uids:
            raise ValueError("--to-group 不能与 --to-account/--to-uid 同时使用")
        return {"togroups": [group]}
    payload = {}
    if accounts:
        if len(accounts) > 100:
            raise ValueError("账号数超过 100 上限")
        payload["tousers"] = accounts
    if uids:
        if len(uids) > 100:
            raise ValueError("UID 数超过 100 上限")
        payload["touids"] = uids
    if not payload:
        raise ValueError("必须指定 --to-account、--to-uid 或 --to-group")
    return payload


def load_content(source: str) -> tuple:
    """读取本地文件或下载 http(s) URL，返回 (bytes, filename)。"""
    if source.lower().startswith(("http://", "https://")):
        resp = requests.get(source, timeout=120)
        resp.raise_for_status()
        filename = Path(source.split("?")[0].split("#")[0]).name or "media"
        return resp.content, filename
    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"本地文件不存在: {source}")
    return path.read_bytes(), path.name


def parse_action(spec: str) -> dict:
    """解析按钮参数：JSON 串，或 `文本[=name[:value]]` 简写。"""
    spec = spec.strip()
    if spec.startswith("{"):
        action = json.loads(spec)
        if "text" not in action or "name" not in action:
            raise ValueError("JSON 按钮必须包含 text 和 name")
        return action
    parts = spec.split(":", 2) if "=" not in spec else spec.split("=", 1)
    if len(parts) == 1:
        return {"text": parts[0], "name": parts[0], "value": parts[0]}
    text, rest = parts[0], parts[1]
    if ":" in rest:
        name, value = rest.split(":", 1)
    else:
        name = value = rest
    return {"text": text, "name": name, "value": value}


def build_interactive(args) -> dict:
    """根据命令行参数构造交互式卡片结构。"""
    if args.card:
        card_text = Path(args.card).read_text(encoding="utf-8")
        return json.loads(card_text)
    interactive = {}
    if args.head or args.head_bgcolor:
        head = {"text": args.head or "通知"}
        if args.head_bgcolor:
            head["bgcolor"] = args.head_bgcolor
        interactive["head"] = head
    body = {}
    if args.title:
        body["title"] = args.title
    if args.content:
        body["content"] = args.content
    if body:
        interactive["body"] = body
    if args.url:
        interactive["url"] = args.url
    if args.action:
        interactive["action"] = [parse_action(a) for a in args.action]
    if not interactive:
        raise ValueError("卡片内容为空：请提供 --card 或 --head/--title/--content/--action")
    return interactive


def load_bot(config_path: str, bot_name=None) -> TuituiBot:
    path = Path(config_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"配置文件不存在: {path}\n"
            "请创建 config.yaml，格式:\n"
            "default: ceshi\n"
            "bots:\n"
            "  ceshi:\n"
            "    appid: '3199004586'\n"
            "    secret: 'xxxx'")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    bots = cfg.get("bots") or {}
    name = bot_name or cfg.get("default") or next(iter(bots), None)
    if not name or name not in bots:
        raise ValueError(
            f"未找到机器人配置 '{name}'，可用: {list(bots)}")
    bot_cfg = bots[name]
    if not bot_cfg.get("appid") or not bot_cfg.get("secret"):
        raise ValueError(f"机器人 '{name}' 缺少 appid 或 secret")
    return TuituiBot(bot_cfg["appid"], bot_cfg["secret"],
                     api_base=bot_cfg.get("api_base", API_BASE))


def emit(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _force_utf8_stdio():
    # Windows 控制台默认 GBK，强制 UTF-8 避免中文乱码（保留 --ascii 回退）
    if "--ascii" in sys.argv:
        sys.argv.remove("--ascii")
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def add_target_args(parser):
    parser.add_argument("--to-account", action="append", default=[],
                        metavar="ACCOUNT", help="收件人推推账号，可多次指定")
    parser.add_argument("--to-uid", action="append", default=[],
                        metavar="UID", help="收件人 UID，可多次指定")
    parser.add_argument("--to-group", metavar="GROUP", help="目标群聊 ID")


# ---------------------------------------------------------------------------
# 命令行
# ---------------------------------------------------------------------------

def main(argv=None):
    if argv is None:
        _force_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="tuitui_bot", description="360 推推机器人消息发送工具")
    default_config = Path(__file__).resolve().parent.parent / "config.yaml"
    parser.add_argument("--config", default=str(default_config),
                        help=f"凭据 YAML 路径 (默认: {default_config})")
    parser.add_argument("--bot", help="使用的机器人配置名 (默认: config 中的 default)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("info", help="查询机器人信息，验证凭据是否有效")

    p = sub.add_parser("send-text", help="发送文本消息")
    add_target_args(p)
    p.add_argument("--text", required=True, help="消息内容，支持 Markdown")

    p = sub.add_parser("send-image", help="发送图片消息 (JPG/PNG/GIF)")
    add_target_args(p)
    p.add_argument("--file", required=True, help="本地图片路径或 http(s) URL")
    p.add_argument("--filename", help="上传时显示的文件名 (默认取源文件名)")

    p = sub.add_parser("send-file", help="发送文件(附件)消息")
    add_target_args(p)
    p.add_argument("--file", required=True, help="本地文件路径或 http(s) URL")
    p.add_argument("--filename", help="上传时显示的文件名 (默认取源文件名)")

    p = sub.add_parser("send-interactive", help="发送交互式卡片(仅限单一目标)")
    add_target_args(p)
    p.add_argument("--card", help="完整卡片结构 JSON 文件路径")
    p.add_argument("--head", help="卡片头部文案")
    p.add_argument("--head-bgcolor", help="头部背景色，如 #3873FA")
    p.add_argument("--title", help="卡片标题")
    p.add_argument("--content", help="卡片正文")
    p.add_argument("--url", help="卡片整体跳转链接")
    p.add_argument("--action", action="append", default=[], metavar="SPEC",
                   help="按钮: `文本[=name[:value]]` 简写或 JSON 串，可多次指定")

    args = parser.parse_args(argv)

    try:
        bot = load_bot(args.config, args.bot)

        if args.command == "info":
            emit(bot.info())
            return 0

        target = build_target(args.to_account, args.to_uid, args.to_group)

        if args.command == "send-text":
            emit(bot.send_text(target, args.text))
        elif args.command == "send-image":
            content, filename = load_content(args.file)
            filename = args.filename or filename
            if Path(filename).suffix.lower() not in IMAGE_EXTS:
                print(f"警告: 推推仅支持 JPG/PNG/GIF 作为图片，"
                      f"{filename} 可能被服务端拒绝", file=sys.stderr)
            media_id = bot.upload(content, filename, "image")
            emit(bot.send_image(target, media_id))
        elif args.command == "send-file":
            content, filename = load_content(args.file)
            filename = args.filename or filename
            media_id = bot.upload(content, filename, "file")
            emit(bot.send_attachment(target, media_id))
        elif args.command == "send-interactive":
            count = (len(target.get("tousers", []))
                     + len(target.get("touids", []))
                     + len(target.get("togroups", [])))
            if count != 1:
                raise ValueError("交互式卡片仅支持恰好一个接收目标")
            interactive = build_interactive(args)
            emit(bot.send_interactive(target, interactive))
        return 0
    except (TuituiApiError, ValueError, FileNotFoundError,
            requests.RequestException) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
