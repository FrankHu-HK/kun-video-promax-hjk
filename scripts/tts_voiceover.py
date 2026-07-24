# -*- coding: utf-8 -*-
"""
tts_voiceover.py (v2.9.0) - AI 口播真人配音引擎（本地优先 · 零云端零国外零付费）
===================================================================================
把"口播话术/脚本文本"变成真人配音音频。

设计原则（诚实版）：
  - 默认后端 pyttsx3：调用系统自带语音（Windows=SAPI5，含中文嗓音），
    **完全离线、零云端、零国外、零付费**，绝对诚实，永不破"两条底线"。
  - 可选后端 edge_tts：音质更自然，但走微软国外免费云（无 Key、免费），
    属于"可选升级"，启用时明确告知用户这是国外云服务（不默认、不隐瞒）。
  - 两个后端都真实可用，不返回假音频。

用法：
  # 默认本地离线配音（推荐，零云端）
  python scripts/tts_voiceover.py --text "这款产品三大卖点……" --out voice.wav

  # 读文件里的多行话术
  python scripts/tts_voiceover.py --text-file script.txt --out voice.wav

  # 换中文嗓音 + 语速（pyttsx3 用 rate，edge_tts 用 rate）
  python scripts/tts_voiceover.py --text "..." --out voice.wav --voice zh-CN-XiaoxiaoNeural --rate +5%

  # 可选：用 edge_tts（国外免费云，音质更好）
  python scripts/tts_voiceover.py --text "..." --out voice.mp3 --backend edge_tts

  # 列出可用嗓音
  python scripts/tts_voiceover.py --list-voices --backend pyttsx3
  python scripts/tts_voiceover.py --list-voices --backend edge_tts
"""
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# 常见中文嗓音（仅作提示，实际以本机/edge_tts 可用列表为准）
DEFAULT_VOICES = {
    "pyttsx3": "",  # 留空=系统默认中文嗓音
    "edge_tts": "zh-CN-XiaoxiaoNeural",  # 微软小晓（女声，自然）
}

EDGE_CN_VOICES = [
    "zh-CN-XiaoxiaoNeural",   # 女声（推荐，自然）
    "zh-CN-YunxiNeural",      # 男声（年轻）
    "zh-CN-YunyangNeural",    # 男声（新闻播报感）
    "zh-CN-XiaoyiNeural",     # 女声（温柔）
    "zh-CN-YunjianNeural",    # 男声（沉稳）
]


def _read_text(text, text_file):
    if text_file:
        if not os.path.exists(text_file):
            raise SystemExit("E100: 话术文件不存在: %s" % text_file)
        with open(text_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not text:
        raise SystemExit("E100: 必须提供 --text 或 --text-file")
    return text.strip()


def _normalize_rate(rate):
    """pyttsx3 用 100~300 的整数 words-per-minute（默认 200）；
    edge_tts 用 SSML 的 +N% / -N%。统一入口：接受 '+5%'/'-10%' 或纯整数。"""
    if rate is None:
        return None
    rate = str(rate).strip()
    if rate.endswith("%"):
        return rate  # edge_tts 直接用
    try:
        return int(rate)  # pyttsx3 用整数 wpm
    except ValueError:
        return 200


def generate_pyttsx3(text, out_path, voice="", rate=None):
    """默认后端：系统离线语音（Windows SAPI5 含中文）。零云端零国外零付费。"""
    try:
        import pyttsx3
    except Exception:
        raise SystemExit(
            "E205: 未安装 pyttsx3（本地离线配音引擎）。\n"
            "请先运行: pip install pyttsx3\n"
            "（Windows 自带 SAPI 中文嗓音，装完即可离线配音；"
            "或用 --backend edge_tts 走免费云，但那是国外服务）"
        )
    # pyttsx3 只稳妥支持 wav；若用户要 mp3 则提醒
    if out_path.lower().endswith(".mp3"):
        logging.warning("  pyttsx3 后端只稳定输出 wav，已自动改为 .wav")
        out_path = out_path[:-4] + ".wav"
    engine = pyttsx3.init()
    try:
        voices = engine.getProperty("voices")
        if voice and voices:
            match = None
            for v in voices:
                if voice.lower() in v.id.lower():
                    match = v.id
                    break
            if match:
                engine.setProperty("voice", match)
            else:
                logging.warning("  未找到指定嗓音 %s，用系统默认中文嗓音", voice)
        if rate is not None:
            try:
                engine.setProperty("rate", int(rate))
            except Exception:
                pass
        engine.setProperty("volume", 1.0)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
    finally:
        try:
            engine.stop()
        except Exception:
            pass
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
        raise SystemExit("E201: pyttsx3 生成音频失败（可能无可用中文嗓音或权限问题）")
    return out_path


def generate_edge_tts(text, out_path, voice=DEFAULT_VOICES["edge_tts"], rate=None):
    """可选升级后端：edge_tts（微软国外免费云，无 Key）。音质更自然。"""
    logging.warning(
        "  ⚠️ 你正在使用 edge_tts：它走微软国外免费云服务（无 Key、免费），"
        "会突破本技能默认『零国外』底线；如不接受请改用默认 pyttsx3 离线后端。"
    )
    try:
        import edge_tts
    except Exception:
        raise SystemExit(
            "E205: 未安装 edge_tts（可选升级后端）。\n"
            "请先运行: pip install edge_tts\n"
            "（或用默认 --backend pyttsx3 完全离线配音，零国外零付费）"
        )
    # 用 SSML 控制语速
    if rate and str(rate).endswith("%"):
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xml:lang="zh-CN"><prosody rate="%s">%s</prosody></speak>'
            % (rate, _esc(text))
        )
        comm = edge_tts.Communicate(ssml, voice)
    else:
        comm = edge_tts.Communicate(text, voice)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    import asyncio
    try:
        asyncio.run(comm.save(out_path))
    except Exception as e:
        raise SystemExit("E201: edge_tts 生成失败: %s（检查网络/嗓音名）" % e)
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
        raise SystemExit("E201: edge_tts 未产出有效音频")
    return out_path


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def list_voices(backend):
    if backend == "edge_tts":
        try:
            import edge_tts
        except Exception:
            raise SystemExit("E205: 未安装 edge_tts，无法列嗓音；先 pip install edge_tts")
        import asyncio
        voices = asyncio.run(edge_tts.list_voices())
        cn = [v for v in voices if v["Locale"].startswith("zh-CN")]
        print("可用中文嗓音（edge_tts，微软国外免费云）：")
        for v in cn:
            print("  %s  |  %s" % (v["ShortName"], v.get("FriendlyName", "")))
        return
    # pyttsx3
    try:
        import pyttsx3
    except Exception:
        raise SystemExit("E205: 未安装 pyttsx3；先 pip install pyttsx3")
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    print("本机可用嗓音（pyttsx3，离线系统语音）：")
    for v in voices:
        tag = "  ←含中文" if any(k in v.id.lower() for k in ("zh", "chinese", "china")) else ""
        print("  %s  |  %s%s" % (v.id, v.name, tag))


def main():
    ap = argparse.ArgumentParser(
        description="AI 口播真人配音（默认本地离线零云端 · 可选 edge_tts 免费云）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--text", help="口播话术/脚本文本")
    ap.add_argument("--text-file", help="话术文本文件（多行）")
    ap.add_argument("--out", default="voice.wav", help="输出音频路径（pyttsx3→wav，edge_tts→mp3/wav）")
    ap.add_argument("--backend", default="pyttsx3", choices=["pyttsx3", "edge_tts"],
                    help="配音后端：pyttsx3=本地离线零国外(默认) / edge_tts=微软国外免费云(音质更好)")
    ap.add_argument("--voice", default="", help="嗓音名（pyttsx3 用系统 id 模糊匹配；edge_tts 用如 zh-CN-XiaoxiaoNeural）")
    ap.add_argument("--rate", default=None, help="语速：pyttsx3 用整数 wpm(默认200)；edge_tts 用 +5pct/-10pct 写法")
    ap.add_argument("--list-voices", action="store_true", help="列出可用嗓音后退出")
    args = ap.parse_args()

    if args.list_voices:
        list_voices(args.backend)
        return

    text = _read_text(args.text, args.text_file)
    rate = _normalize_rate(args.rate)
    voice = args.voice or DEFAULT_VOICES.get(args.backend, "")

    logging.info("🎙️ AI 口播配音  backend=%s  voice=%s", args.backend, voice or "系统默认")
    if args.backend == "pyttsx3":
        out = generate_pyttsx3(text, args.out, voice=voice, rate=rate)
    else:
        out = generate_edge_tts(text, args.out, voice=voice, rate=rate)
    logging.info("DONE -> 配音已生成: %s (零云端零付费)", out)


if __name__ == "__main__":
    main()
