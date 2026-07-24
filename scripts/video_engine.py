# -*- coding: utf-8 -*-
"""
video_engine.py (v2.8.0) - Workflow B/C videogenerate（、、）
===================================================================================
（）：
  -  --engine local：100% 、、、。
  - Workflow B（motion transfer·）=「 + face swapmotion transfer」：
       pose_extract.py videoclear，target/goalvideoface swap，
      "target/goalvideo"video（**/background/**）。real。
  - Workflow C（AI ·）= →(tts_voiceover.py： pyttsx3 
      ， edge_tts )→video/composite mp4（background）。
      **real**，；"driver"model( Wav2Lip)，
      ，，。
  - mode（--mode director）：""（AI //hint/tip），
      user""。
  - （agnes/nvidia/seedance/kling）：**real**，select
    E200「 --engine local」，fakevideo。""。

：
  # motion transfer（，recommended）
  python scripts/video_engine.py --workflow B \\
    --video ref.mp4 --photo target.jpg --engine local

  # AI （extract + ）
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

# ============ error ============
ERROR_CODES = {
    "E200": "real， --engine local（）",
    "E201": "failed / ",
    "E205": "dependency",
}

# ============ （status） ============
ENGINE_ROUTES = {
    "local": {
        "display_name": "（ · real）",
        "type": "local",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": True,
        "supports": ["B", "C"],
        "description": "、、。B=face swapmotion transfer()；C=extract+。",
    },
    "agnes": {
        "display_name": "AGNES videogenerate（real）",
        "type": "cloud_free",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "：real API ，select local。",
    },
    "nvidia": {
        "display_name": "NVIDIA videogenerate（real）",
        "type": "cloud_free",
        "is_free": True,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "：real API ，select local。",
    },
    "seedance": {
        "display_name": "Seedance 2.0（real）",
        "type": "cloud_trial",
        "is_free": False,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "：real API ，select local。",
    },
    "kling": {
        "display_name": "Kling 3.0（real）",
        "type": "cloud_paid",
        "is_free": False,
        "is_foreign": False,
        "is_implemented": False,
        "supports": ["B", "C"],
        "description": "：real API ，select local。",
    },
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def _script(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def run_motion_qc(ref_path, out_json, pose_model=""):
    """Workflow B ：video。

     (score, verdict)  (None, msg)。
    """
    pose = _script("pose_extract.py")
    if not os.path.exists(pose):
        return None, "，skip"
    cmd = ["python", pose, "--video", ref_path, "--out", out_json]
    if pose_model and os.path.exists(pose_model):
        cmd += ["--model", pose_model]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return None, "exception: %s" % e
    if r.returncode != 0:
        return None, "failed: %s" % r.stderr.strip()[:200]
    try:
        with open(out_json, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("motion_score"), d.get("verdict", "")
    except Exception:
        return None, "resultfailed"


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _audio_duration(audio_path):
    """ ffprobe audio（），failed None。"""
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
    """compositevideo / ， mp4（ffmpeg）。

    - video：（background）。
    - ：image(ken-burns)++background → 。
     (ok, cmd_str)。print_cmd=True （ ffmpeg verify）。
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
        target = "video"
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
        target = "++()"
    else:
        return False, "video，compositevideo（audio）"

    if print_cmd:
        logging.info("  [print-cmd] : %s", " ".join('"%s"' % c if " " in c else c for c in cmd))
        return True, " ".join(cmd)
    logging.info("  compositevideo（%s）…", target)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except Exception as e:
        logging.error("  ffmpeg exception: %s", e)
        return False, str(e)
    if r.returncode != 0:
        logging.error(r.stderr.strip()[:400])
        return False, r.stderr.strip()[:200]
    return True, " ".join(cmd)


def run_local_fallback(workflow, ref_path, photo_path, output_path, pose_model="", no_motion_qc=False,
                       script="", anchor="", bgm="", voice="", rate=None, tts_backend="pyttsx3",
                       print_cmd=False):
    """（real）。

    B: (pose_extract) → face swapmotion transfer(faceswap_pro)，/background/。
    C: extract(product_extract) → available（real-person talking head）。
    """
    if workflow == "B":
        # step 1：
        if not no_motion_qc:
            qc_json = output_path + ".motion_qc.json"
            score, verdict = run_motion_qc(ref_path, qc_json, pose_model)
            if score is not None:
                logging.info("  score/rating=%s/100 | %s", score, verdict)
                if score < 35:
                    logging.warning("  ⚠️ video/clear，；suggestion。")
            else:
                logging.warning("  ⚠️ %s（skip，face swap）", verdict)
        else:
            logging.info("  skip（--no-motion-qc）")

        # step 2：face swapmotion transfer（）
        fs = _script("faceswap_pro.py")
        if not os.path.exists(fs):
            raise SystemExit("E205:  faceswap_pro.py，motion transfer")
        logging.info("  face swapmotion transfer： %s  %s（/background/）",
                     os.path.basename(photo_path), os.path.basename(ref_path))
        r = subprocess.run(
            ["python", fs, "--video", ref_path, "--photo", photo_path, "--out", output_path],
            capture_output=True, timeout=3600,
        )
        if r.returncode != 0:
            logging.error(r.stderr.decode("utf-8", "replace")[:400])
        return r.returncode == 0

    elif workflow == "C":
        # step 1： → （ pyttsx3 ； edge_tts ）
        if not script:
            raise SystemExit("Workflow C  --script（）； --product/--anchor compositevideo")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import tts_voiceover as tts
        except Exception as e:
            raise SystemExit("E205: load tts_voiceover.py（）: %s" % e)
        voice_out = output_path + ".voice.wav" if output_path.endswith(".mp4") else output_path + ".voice.wav"
        if tts_backend == "edge_tts":
            tts.generate_edge_tts(script, voice_out, voice=voice or tts.DEFAULT_VOICES["edge_tts"], rate=rate)
        else:
            tts.generate_pyttsx3(script, voice_out, voice=voice, rate=rate)
        logging.info("  ✅ generate: %s", voice_out)

        # step 2：——extract（，/）
        pe = _script("product_extract.py")
        if os.path.exists(pe) and ref_path and os.path.exists(ref_path) and ref_path.endswith((".mp4", ".mov", ".avi", ".mkv")):
            out_dir = output_path + "_product_refs"
            try:
                subprocess.run(["python", pe, "--video", ref_path, "--out-dir", out_dir],
                               capture_output=True, timeout=300)
                logging.info("  extract: %s", out_dir)
            except Exception as e:
                logging.warning("  ⚠️ extractskip（）: %s", e)

        # step 3：compositevideo（video→；→；→audio）
        if output_path.endswith((".mp4", ".mov", ".avi", ".mkv")):
            ok, cmd = compose_koubo(ref_path if (ref_path and ref_path.endswith((".mp4", ".mov", ".avi", ".mkv"))) else "",
                                    anchor, voice_out, bgm, output_path, print_cmd=print_cmd)
            if not ok:
                logging.warning("  ⚠️ videocompositedone（%s）；audio: %s", cmd, voice_out)
                return True  # success，videocomposite
            logging.info("  videogenerate: %s", output_path)
        else:
            logging.info("  outputvideopath，audio: %s", voice_out)
        return True
    return False


def require_local_or_error(engine_name):
    """real → ，fakevideo。"""
    route = ENGINE_ROUTES.get(engine_name)
    if route and route.get("is_implemented"):
        return
    raise SystemExit(
        "E200:  '%s' real（）。\n"
        ": --engine local （、、real）。\n"
        "fakevideo，disable。" % engine_name
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
    """【】——user""。

    annotation： AI  SKILL.md done（、dependency、）。
    ，；
    "XXvideo" workflow。
    """
    logging.info("=" * 60)
    logging.info("🎬 mode（Director Mode） ·  · ")
    logging.info("=" * 60)
    logging.info(" 4 ，《video》：")
    logging.info("  ① video/（：）")
    logging.info("  ② （/video//，）")
    logging.info("  ③ target/goal（ 15s / 30s / 60s）")
    logging.info("  ④ （  /  / ）")
    logging.info("-" * 60)
    logging.info("《video》output（9 ）：")
    for i, el in enumerate([
        "video（///）",
        "",
        "（···）",
        "",
        "/suggestion",
        "",
        "production（face swap/motion transfer//4K）",
        "",
        "（，confirm）",
    ], 1):
        logging.info("  %d. %s", i, el)
    logging.info("=" * 60)


def main():
    ap = argparse.ArgumentParser(
        description="videogenerate（， · ）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--mode", default="video", choices=["video", "director"],
                    help="video=generatevideo( --workflow)；director=()")
    ap.add_argument("--workflow", choices=["B", "C"], help="B=motion transfer, C=e-commerce product demo（--mode video ）")
    ap.add_argument("--engine", default="local", choices=list(ENGINE_ROUTES.keys()),
                    help="（ local=；， local）")
    ap.add_argument("--video", help="video（Workflow B ）")
    ap.add_argument("--photo", help="target/goal（Workflow B ）")
    ap.add_argument("--product", help="video（Workflow C ，）")
    ap.add_argument("--anchor", help="/（Workflow C ，）")
    ap.add_argument("--script", help="（Workflow C ；video）")
    ap.add_argument("--bgm", help="background（Workflow C ）")
    ap.add_argument("--voice", default="", help="（pyttsx3  id；edge_tts  zh-CN-XiaoxiaoNeural）")
    ap.add_argument("--rate", default=None, help="：pyttsx3  wpm(200)；edge_tts  +5%/-10%")
    ap.add_argument("--tts-backend", default="pyttsx3", choices=["pyttsx3", "edge_tts"],
                    help="：pyttsx3=() / edge_tts=")
    ap.add_argument("--pose-model", default="", help="pose_landmarker_full.task（enablepose）")
    ap.add_argument("--no-motion-qc", action="store_true", help="skip（Workflow B）")
    ap.add_argument("--print-cmd", action="store_true", help=" ffmpeg composite（ ffmpeg verify）")
    ap.add_argument("--out", default="video_engine_output.mp4", help="outputpath")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    # mode：，
    if args.mode == "director":
        run_director()
        return

    if not args.workflow:
        raise SystemExit("--mode video  --workflow (B/C)")
    logging.info("=" * 60)
    route = ENGINE_ROUTES[args.engine]
    logging.info("🎬 videogenerate v2.9.0  workflow=%s engine=%s (%s)",
                 args.workflow, args.engine, route["display_name"])
    logging.info("=" * 60)

    # parameter
    if args.workflow == "B":
        if not args.video or not args.photo:
            raise SystemExit("Workflow B  --video  --photo")
        ref_path, photo_path = args.video, args.photo
    else:
        if not args.script:
            raise SystemExit("Workflow C  --script（）； --product/--anchor compositevideo")
        ref_path, photo_path = args.product or "", args.anchor or ""

    for p in ([ref_path] + ([photo_path] if photo_path else [])):
        if p and not os.path.exists(p):
            raise SystemExit("E100: filedoes not exist: %s" % p)

    if args.workflow not in route["supports"]:
        raise SystemExit("%s  Workflow %s" % (args.engine, args.workflow))

    # ：real → 
    if route["type"] != "local":
        require_local_or_error(args.engine)
        return

    # path（real）
    ok = run_local_fallback(
        args.workflow, ref_path, photo_path, args.out,
        pose_model=args.pose_model, no_motion_qc=args.no_motion_qc,
        script=args.script or "", anchor=args.anchor or "", bgm=args.bgm or "",
        voice=args.voice or "", rate=args.rate, tts_backend=args.tts_backend,
        print_cmd=args.print_cmd)
    if not ok:
        raise SystemExit("E201: failed，checklog")

    if args.workflow == "B":
        extra = {"method": "face swapmotion transfer（/background/）"}
        write_report(args.out, args.workflow, "local", extra)
        logging.info("DONE -> %s (motion transfer，)", args.out)
    else:
        write_report(args.out, args.workflow, "local",
                     extra={"method": "AI：+composite()"})
        logging.info("DONE -> %s ( AI ，)", args.out)


if __name__ == "__main__":
    main()
