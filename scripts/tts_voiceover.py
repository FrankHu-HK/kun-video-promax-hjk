# -*- coding: utf-8 -*-
"""
tts_voiceover.py (v2.9.0) - AI （ · ）
===================================================================================
"/"audio。

（）：
  -  pyttsx3：（Windows=SAPI5，），
    **、、、**，，""。
  -  edge_tts：natural，（ Key、），
    ""，enableuser（、）。
  - realavailable，fakeaudio。

：
  # （recommended，）
  python scripts/tts_voiceover.py --text "……" --out voice.wav

  # file
  python scripts/tts_voiceover.py --text-file script.txt --out voice.wav

  #  + （pyttsx3  rate，edge_tts  rate）
  python scripts/tts_voiceover.py --text "..." --out voice.wav --voice zh-CN-XiaoxiaoNeural --rate +5%

  # ： edge_tts（，）
  python scripts/tts_voiceover.py --text "..." --out voice.mp3 --backend edge_tts

  # available
  python scripts/tts_voiceover.py --list-voices --backend pyttsx3
  python scripts/tts_voiceover.py --list-voices --backend edge_tts
"""
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# （hint/tip，/edge_tts available）
DEFAULT_VOICES = {
    "pyttsx3": "",  # =
    "edge_tts": "zh-CN-XiaoxiaoNeural",  # （，natural）
}

EDGE_CN_VOICES = [
    "zh-CN-XiaoxiaoNeural",   # （recommended，natural）
    "zh-CN-YunxiNeural",      # （）
    "zh-CN-YunyangNeural",    # （）
    "zh-CN-XiaoyiNeural",     # （）
    "zh-CN-YunjianNeural",    # （）
]


def _read_text(text, text_file):
    if text_file:
        if not os.path.exists(text_file):
            raise SystemExit("E100: filedoes not exist: %s" % text_file)
        with open(text_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not text:
        raise SystemExit("E100:  --text  --text-file")
    return text.strip()


def _normalize_rate(rate):
    """pyttsx3  100~300  words-per-minute（ 200）；
    edge_tts  SSML  +N% / -N%。： '+5%'/'-10%' 。"""
    if rate is None:
        return None
    rate = str(rate).strip()
    if rate.endswith("%"):
        return rate  # edge_tts 
    try:
        return int(rate)  # pyttsx3  wpm
    except ValueError:
        return 200


def generate_pyttsx3(text, out_path, voice="", rate=None):
    """：（Windows SAPI5 ）。。"""
    try:
        import pyttsx3
    except Exception:
        raise SystemExit(
            "E205: install pyttsx3（）。\n"
            "run: pip install pyttsx3\n"
            "（Windows  SAPI ，；"
            " --backend edge_tts ，）"
        )
    # pyttsx3  wav；user mp3 
    if out_path.lower().endswith(".mp3"):
        logging.warning("  pyttsx3 stableoutput wav， .wav")
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
                logging.warning("   %s，", voice)
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
        raise SystemExit("E201: pyttsx3 generateaudiofailed（availableauthorization）")
    return out_path


def generate_edge_tts(text, out_path, voice=DEFAULT_VOICES["edge_tts"], rate=None):
    """：edge_tts（， Key）。natural。"""
    logging.warning(
        "  ⚠️  edge_tts：（ Key、），"
        "『』； pyttsx3 。"
    )
    try:
        import edge_tts
    except Exception:
        raise SystemExit(
            "E205: install edge_tts（）。\n"
            "run: pip install edge_tts\n"
            "（ --backend pyttsx3 ，）"
        )
    #  SSML 
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
        raise SystemExit("E201: edge_tts generatefailed: %s（check/）" % e)
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
        raise SystemExit("E201: edge_tts audio")
    return out_path


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def list_voices(backend):
    if backend == "edge_tts":
        try:
            import edge_tts
        except Exception:
            raise SystemExit("E205: install edge_tts，； pip install edge_tts")
        import asyncio
        voices = asyncio.run(edge_tts.list_voices())
        cn = [v for v in voices if v["Locale"].startswith("zh-CN")]
        print("available（edge_tts，）：")
        for v in cn:
            print("  %s  |  %s" % (v["ShortName"], v.get("FriendlyName", "")))
        return
    # pyttsx3
    try:
        import pyttsx3
    except Exception:
        raise SystemExit("E205: install pyttsx3； pip install pyttsx3")
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    print("available（pyttsx3，）：")
    for v in voices:
        tag = "  ←" if any(k in v.id.lower() for k in ("zh", "chinese", "china")) else ""
        print("  %s  |  %s%s" % (v.id, v.name, tag))


def main():
    ap = argparse.ArgumentParser(
        description="AI （ ·  edge_tts ）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--text", help="/")
    ap.add_argument("--text-file", help="file（）")
    ap.add_argument("--out", default="voice.wav", help="outputaudiopath（pyttsx3→wav，edge_tts→mp3/wav）")
    ap.add_argument("--backend", default="pyttsx3", choices=["pyttsx3", "edge_tts"],
                    help="：pyttsx3=() / edge_tts=()")
    ap.add_argument("--voice", default="", help="（pyttsx3  id blurry；edge_tts  zh-CN-XiaoxiaoNeural）")
    ap.add_argument("--rate", default=None, help="：pyttsx3  wpm(200)；edge_tts  +5pct/-10pct ")
    ap.add_argument("--list-voices", action="store_true", help="availableexit")
    args = ap.parse_args()

    if args.list_voices:
        list_voices(args.backend)
        return

    text = _read_text(args.text, args.text_file)
    rate = _normalize_rate(args.rate)
    voice = args.voice or DEFAULT_VOICES.get(args.backend, "")

    logging.info("🎙️ AI   backend=%s  voice=%s", args.backend, voice or "")
    if args.backend == "pyttsx3":
        out = generate_pyttsx3(text, args.out, voice=voice, rate=rate)
    else:
        out = generate_edge_tts(text, args.out, voice=voice, rate=rate)
    logging.info("DONE -> generate: %s ()", out)


if __name__ == "__main__":
    main()
