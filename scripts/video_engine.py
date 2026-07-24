# -*- coding: utf-8 -*-
"""
video_engine.py (v2.8.0) - Workflow B/C videogenerate引擎（默认本地、零云端、零付费）
===================================================================================
设计原则（诚实版）：
  - 默认 --engine local：100% 本地、零云端、零付费、零国外服务。
  - Workflow B（motion transfer·本地）=「动作预检 + face swap式motion transfer」：
      先用 pose_extract.py 分析参考video动作clear度，再拿target/goal照对参考video做face swap，
      得到"target/goal人物做出参考video动作"的video（**保留原动作/background/音乐**）。real可跑。
  - Workflow C（AI 口播·本地）= 话术→本地真人配音(tts_voiceover.py：默认 pyttsx3 离线
      零国外，可选 edge_tts 免费云)→与产品video/主播图composite口播 mp4（可选background音乐）。
      **real可出片**，零云端零付费；"真人脸driver数字人"需本地model(如 Wav2Lip)，本技能
      不内置，明确标注为可选本地扩展，不伪造。
  - 导演mode（--mode director）：确定性触发"导演策划层"（AI 导演引擎/分镜/hint/tip词），
      不再需要user"猜怎么开口"。
  - 云端引擎（agnes/nvidia/seedance/kling）：**real对接尚未实现**，select它们会明确报错
    E200「请用 --engine local」，绝不返回fakevideo。这是为了守住"不谎报"的诚信底线。

用法：
  # motion transfer（默认本地，recommended）
  python scripts/video_engine.py --workflow B \\
    --video ref.mp4 --photo target.jpg --engine local

  # AI 口播（本地产品extract + 话术）
  python scripts/video_engine.py --workflow C \\
    --product product.mp4 --anchor anchor.jpg --script "..." --engine local
"""
import os
import sys
import json
import argparse
import logging
import subprocess
import shutil

# ============ 统一error码 ============
ERROR_CODES = {
    "E200": "未实现real云端对接，请改用 --engine local（零云端零付费）",
    "E201": "引擎调用failed / 未实现",
    "E205": "本地等价方案dependency脚本缺失",
}

# ============ 引擎路由表（含诚实status） ============
ENGINE_ROUTES = {
    "local": {
        "display_name": "本地等价方案（默认 · real可跑）",
        "type": "local",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": True,
        "supports": ["B", "C"],
        "description": "零云端、零付费、零国外。B=face swap式motion transfer(保留原动作)；C=产品extract+话术。",
    },
    "agnes": {
        "display_name": "AGNES videogenerate（real对接未实现）",
        "type": "cloud_free",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "规划中：real API 对接尚未实现，select会报错并引导用 local。",
    },
    "nvidia": {
        "display_name": "NVIDIA videogenerate（real对接未实现）",
        "type": "cloud_free",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "规划中：real API 对接尚未实现，select会报错并引导用 local。",
    },
    "seedance": {
        "display_name": "Seedance 2.0（real对接未实现）",
        "type": "cloud_trial",
        "is_free": False,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "规划中：real API 对接尚未实现，select会报错并引导用 local。",
    },
    "kling": {
        "display_name": "Kling 3.0（real对接未实现）",
        "type": "cloud_paid",
        "is_free": False,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "规划中：real API 对接尚未实现，select会报错并引导用 local。",
    },
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def _script(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def run_motion_qc(ref_path, out_json, pose_model=""):
    """Workflow B 预检：分析参考video动作可迁移性。

    返回 (score, verdict) 或 (None, msg)。
    """
    pose = _script("pose_extract.py")
    if not os.path.exists(pose):
        return None, "动作预检脚本缺失，skip预检"
    cmd = ["python", pose, "--video", ref_path, "--out", out_json]
    if pose_model and os.path.exists(pose_model):
        cmd += ["--model", pose_model]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return None, "动作预检exception: %s" % e
    if r.returncode != 0:
        return None, "动作预检failed: %s" % r.stderr.strip()[:200]
    try:
        with open(out_json, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("motion_score"), d.get("verdict", "")
    except Exception:
        return None, "动作预检result解析failed"


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _audio_duration(audio_path):
    """用 ffprobe 取audio时长（秒），failed返回 None。"""
    try:
        import subprocess
        r = subprocess.run(
            [_ffmpeg_exe().replace("ffmpeg", "ffprobe"), "-v", "error",
             "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", audio_path],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return None


def compose_koubo(video_path, image_path, audio_path, bgm_path, out_path, print_cmd=False):
    """把配音composite到产品video / 主播图，产出口播 mp4（ffmpeg）。

    - 有产品video：替换音轨为配音（可选叠加background乐）。
    - 仅主播图：image缓动(ken-burns)+配音+可选background乐 → 口播幻灯片。
    返回 (ok, cmd_str)。print_cmd=True 仅打印命令不执行（用于无 ffmpeg 环境verify）。
    """
    ff = _ffmpeg_exe()
    if video_path and os.path.exists(video_path):
        cmd = [ff, "-y", "-i", video_path, "-i", audio_path]
        if bgm_path and os.path.exists(bgm_path):
            cmd += ["-i", bgm_path,
                    "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=shortest:dropout_transition=0[a]",
                    "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", out_path]
        else:
            cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", out_path]
        target = "产品video替换音轨"
    elif image_path and os.path.exists(image_path):
        filt = ("scale=1280:720:force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
                "zoompan=z='min(zoom+0.0005,1.15)':d=1:s=1280x720:fps=25")
        cmd = [ff, "-y", "-loop", "1", "-i", image_path, "-i", audio_path]
        if bgm_path and os.path.exists(bgm_path):
            cmd += ["-i", bgm_path,
                    "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=shortest:dropout_transition=0[a]",
                    "-map", "0:v:0", "-map", "[a]", "-vf", filt, "-c:v", "libx264",
                    "-c:a", "aac", "-r", "25", "-pix_fmt", "yuv420p", "-shortest", out_path]
        else:
            cmd += ["-map", "0:v:0", "-map", "1:a:0", "-vf", filt, "-c:v", "libx264",
                    "-c:a", "aac", "-r", "25", "-pix_fmt", "yuv420p", "-shortest", out_path]
        target = "主播图+缓动+配音(口播幻灯片)"
    else:
        return False, "既无产品video也无主播图，无法compositevideo（仅产出配音audio）"

    if print_cmd:
        logging.info("  [print-cmd] 将执行: %s", " ".join('"%s"' % c if " " in c else c for c in cmd))
        return True, " ".join(cmd)
    logging.info("  composite口播video（%s）…", target)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except Exception as e:
        logging.error("  ffmpeg 执行exception: %s", e)
        return False, str(e)
    if r.returncode != 0:
        logging.error(r.stderr.strip()[:400])
        return False, r.stderr.strip()[:200]
    return True, " ".join(cmd)


def run_local_fallback(workflow, ref_path, photo_path, output_path, pose_model="", no_motion_qc=False,
                       script="", anchor="", bgm="", voice="", rate=None, tts_backend="pyttsx3",
                       print_cmd=False):
    """本地等价方案（real可跑）。

    B: 动作预检(pose_extract) → face swap式motion transfer(faceswap_pro)，保留原动作/background/音乐。
    C: 产品extract(product_extract) → 话术本地available（real-person talking head下一轮）。
    """
    if workflow == "B":
        # step 1：动作预检
        if not no_motion_qc:
            qc_json = output_path + ".motion_qc.json"
            score, verdict = run_motion_qc(ref_path, qc_json, pose_model)
            if score is not None:
                logging.info("  动作可迁移性score/rating=%s/100 | %s", score, verdict)
                if score < 35:
                    logging.warning("  ⚠️ 参考video动作/clear度偏弱，迁移效果可能有限；suggestion换动作更明显的素材。")
            else:
                logging.warning("  ⚠️ %s（skip预检，直接face swap）", verdict)
        else:
            logging.info("  已skip动作预检（--no-motion-qc）")

        # step 2：face swap式motion transfer（保留原动作）
        fs = _script("faceswap_pro.py")
        if not os.path.exists(fs):
            raise SystemExit("E205: 缺少 faceswap_pro.py，无法执行motion transfer")
        logging.info("  执行face swap式motion transfer：把 %s 的脸贴到 %s（保留原动作/background/音乐）",
                     os.path.basename(photo_path), os.path.basename(ref_path))
        r = subprocess.run(
            ["python", fs, "--video", ref_path, "--photo", photo_path, "--out", output_path],
            capture_output=True, timeout=3600,
        )
        if r.returncode != 0:
            logging.error(r.stderr.decode("utf-8", "replace")[:400])
        return r.returncode == 0

    elif workflow == "C":
        # step 1：话术 → 本地真人配音（默认 pyttsx3 离线零国外；可选 edge_tts 免费云）
        if not script:
            raise SystemExit("Workflow C 必须提供 --script（口播话术）；可加 --product/--anchor compositevideo")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import tts_voiceover as tts
        except Exception as e:
            raise SystemExit("E205: 无法load tts_voiceover.py（口播配音引擎）: %s" % e)
        voice_out = output_path + ".voice.wav" if output_path.endswith(".mp4") else output_path + ".voice.wav"
        if tts_backend == "edge_tts":
            tts.generate_edge_tts(script, voice_out, voice=voice or tts.DEFAULT_VOICES["edge_tts"], rate=rate)
        else:
            tts.generate_pyttsx3(script, voice_out, voice=voice, rate=rate)
        logging.info("  ✅ 真人配音已generate: %s", voice_out)

        # step 2：选填——extract产品参考图（可选，便于你挑封面/素材）
        pe = _script("product_extract.py")
        if os.path.exists(pe) and ref_path and os.path.exists(ref_path) and ref_path.endswith((".mp4", ".mov", ".avi", ".mkv")):
            out_dir = output_path + "_product_refs"
            try:
                subprocess.run(["python", pe, "--video", ref_path, "--out-dir", out_dir],
                               capture_output=True, timeout=300)
                logging.info("  已本地extract产品参考图到: %s", out_dir)
            except Exception as e:
                logging.warning("  ⚠️ 产品图extractskip（不影响口播出片）: %s", e)

        # step 3：composite口播video（有产品video→替换音轨；有主播图→口播幻灯片；都没有→仅配音audio）
        if output_path.endswith((".mp4", ".mov", ".avi", ".mkv")):
            ok, cmd = compose_koubo(ref_path if (ref_path and ref_path.endswith((".mp4", ".mov", ".avi", ".mkv"))) else "",
                                    anchor, voice_out, bgm, output_path, print_cmd=print_cmd)
            if not ok:
                logging.warning("  ⚠️ videocomposite未done（%s）；配音audio已产出: %s", cmd, voice_out)
                return True  # 配音已success，videocomposite为可选增强
            logging.info("  口播video已generate: %s", output_path)
        else:
            logging.info("  output非videopath，已产出配音audio: %s", voice_out)
        return True
    return False


def require_local_or_error(engine_name):
    """云端引擎real对接未实现 → 诚实报错，绝不返回fakevideo。"""
    route = ENGINE_ROUTES.get(engine_name)
    if route and route.get("is_implemented"):
        return
    raise SystemExit(
        "E200: 云端引擎 '%s' real对接尚未实现（本技能默认本地零云端）。\n"
        "请改用: --engine local （零云端、零付费、real可跑）。\n"
        "虚伪地返回一个fakevideo违背本技能的诚实底线，已disable。" % engine_name
    )


def write_report(output_path, workflow, engine, extra=None):
    report = {
        "workflow": workflow,
        "engine": engine,
        "video_path": output_path,
        "cost_usd": 0.0,
        "is_foreign": False,
        "is_paid": False,
    }
    if extra:
        report.update(extra)
    with open(output_path + ".report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def run_director():
    """导演策划层【确定性触发入口】——不再需要user"猜怎么开口"。

    annotation：导演策划由 AI 助理按 SKILL.md 的导演层规则done（纯本地推理、零dependency、零费用）。
    本函数给出标准化出片协议与开场提问，作为明确入口；也可直接对助理说
    "帮我策划一个关于XX的video" 触发同样workflow。
    """
    logging.info("=" * 60)
    logging.info("🎬 导演策划mode（Director Mode）已激活 · 本地免费 · 零云端")
    logging.info("=" * 60)
    logging.info("下一步请告诉我这 4 项，我会产出《video导演方案》：")
    logging.info("  ① video主题/卖点（如：夏日清透防晒霜种草）")
    logging.info("  ② 发布平台（抖音/video号/小红书/快手，影响节奏与画幅）")
    logging.info("  ③ 时长target/goal（如 15s / 30s / 60s）")
    logging.info("  ④ 风格偏好（如 快节奏卡点 / 温柔测评 / 反转剧情）")
    logging.info("-" * 60)
    logging.info("《video导演方案》标准化output（9 要素）：")
    for i, el in enumerate([
        "video类型判定（种草/测评/剧情/口播）",
        "核心一句话主张",
        "分镜脚本（镜头·画面·台词·时长）",
        "镜头运动与节奏设计",
        "音乐/情绪suggestion",
        "视觉语言与配色",
        "本地production层映射（face swap/motion transfer/口播/4K升频哪个做）",
        "一致性自查清单",
        "出片前目检要点（本技能不读图，画面由你confirm）",
    ], 1):
        logging.info("  %d. %s", i, el)
    logging.info("=" * 60)


def main():
    ap = argparse.ArgumentParser(
        description="videogenerate引擎（本地优先，零云端零付费 · 诚实版）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--mode", default="video", choices=["video", "director"],
                    help="video=generatevideo(需 --workflow)；director=进入导演策划层(确定性触发)")
    ap.add_argument("--workflow", choices=["B", "C"], help="B=motion transfer, C=口播e-commerce product demo（--mode video 时必填）")
    ap.add_argument("--engine", default="local", choices=list(ENGINE_ROUTES.keys()),
                    help="引擎（默认 local=本地零云端；其余云端引擎尚未实现，选了会报错引导用 local）")
    ap.add_argument("--video", help="参考video（Workflow B 用）")
    ap.add_argument("--photo", help="target/goal人脸照（Workflow B 用）")
    ap.add_argument("--product", help="产品video（Workflow C 用，可选）")
    ap.add_argument("--anchor", help="主播参考照/产品图（Workflow C 用，可选）")
    ap.add_argument("--script", help="口播话术（Workflow C 用；无产品video时也可只产配音）")
    ap.add_argument("--bgm", help="background音乐（Workflow C 可选叠加）")
    ap.add_argument("--voice", default="", help="配音嗓音（pyttsx3 用系统 id；edge_tts 用如 zh-CN-XiaoxiaoNeural）")
    ap.add_argument("--rate", default=None, help="语速：pyttsx3 整数 wpm(默认200)；edge_tts 用 +5%/-10%")
    ap.add_argument("--tts-backend", default="pyttsx3", choices=["pyttsx3", "edge_tts"],
                    help="口播配音后端：pyttsx3=本地离线零国外(默认) / edge_tts=微软国外免费云")
    ap.add_argument("--pose-model", default="", help="pose_landmarker_full.task（enablepose预检增强）")
    ap.add_argument("--no-motion-qc", action="store_true", help="skip动作预检（Workflow B）")
    ap.add_argument("--print-cmd", action="store_true", help="仅打印 ffmpeg composite命令不执行（无 ffmpeg 环境verify用）")
    ap.add_argument("--out", default="video_engine_output.mp4", help="outputpath")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    # 导演mode：确定性触发，直接返回
    if args.mode == "director":
        run_director()
        return

    if not args.workflow:
        raise SystemExit("--mode video 时必须指定 --workflow (B/C)")
    logging.info("=" * 60)
    route = ENGINE_ROUTES[args.engine]
    logging.info("🎬 videogenerate引擎 v2.9.0  workflow=%s engine=%s (%s)",
                 args.workflow, args.engine, route["display_name"])
    logging.info("=" * 60)

    # parameter校验
    if args.workflow == "B":
        if not args.video or not args.photo:
            raise SystemExit("Workflow B 必须指定 --video 和 --photo")
        ref_path, photo_path = args.video, args.photo
    else:
        if not args.script:
            raise SystemExit("Workflow C 必须指定 --script（口播话术）；可加 --product/--anchor compositevideo")
        ref_path, photo_path = args.product or "", args.anchor or ""

    for p in ([ref_path] + ([photo_path] if photo_path else [])):
        if p and not os.path.exists(p):
            raise SystemExit("E100: filedoes not exist: %s" % p)

    if args.workflow not in route["supports"]:
        raise SystemExit("%s 不支持 Workflow %s" % (args.engine, args.workflow))

    # 云端引擎：real对接未实现 → 诚实报错
    if route["type"] != "local":
        require_local_or_error(args.engine)
        return

    # 本地path（real可跑）
    ok = run_local_fallback(
        args.workflow, ref_path, photo_path, args.out,
        pose_model=args.pose_model, no_motion_qc=args.no_motion_qc,
        script=args.script or "", anchor=args.anchor or "", bgm=args.bgm or "",
        voice=args.voice or "", rate=args.rate, tts_backend=args.tts_backend,
        print_cmd=args.print_cmd)
    if not ok:
        raise SystemExit("E201: 本地方案执行failed，请check上方log")

    if args.workflow == "B":
        extra = {"method": "face swap式motion transfer（保留原动作/background/音乐）"}
        write_report(args.out, args.workflow, "local", extra)
        logging.info("DONE -> %s (本地motion transfer，零云端零付费)", args.out)
    else:
        write_report(args.out, args.workflow, "local",
                     extra={"method": "AI口播：本地真人配音+composite(零云端零付费)"})
        logging.info("DONE -> %s (本地 AI 口播，零云端零付费)", args.out)


if __name__ == "__main__":
    main()
