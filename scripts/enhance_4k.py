# -*- coding: utf-8 -*-
"""
enhance_4k.py (v2.8.0) - Workflow D：videoclear（4K ）
=============================================================
resolution/videoresolutionrealclear：
  - path（dependency、CPU ）：ffmpeg lanczos  + unsharp sharpen（realclear）
  - ： models/  cv2.dnn_superres model（ ESPCN_x4.pb），enable AI 

（ + real）：
  - "real-ESRGAN / CV2 DNN / ffmpeg "， ffmpeg ；
    ： ffmpeg+sharpen（），AI modelenable。
  - 「clear」： Laplacian clear，，
    "clear"verify，。

：
  python scripts/enhance_4k.py --input video.mp4 --output 4kvideo.mp4 --target 4k
  python scripts/enhance_4k.py --input video.mp4 --output 1080p.mp4 --target 1080p
"""
import os
import sys
import argparse
import subprocess
import logging
import shutil

import cv2
import numpy as np

# ============ error ============
ERROR_CODES = {
    "E300": "ffmpeg （install ffmpeg  PATH）",
    "E301": "target/goalresolution（ 720p/1080p/1440p/4k）",
    "E302": "resolution， --target",
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def has_dnn_model(model_dir):
    """ models/  cv2.dnn_superres model（.pb）。"""
    if not os.path.isdir(model_dir):
        return None
    for f in os.listdir(model_dir):
        if f.lower().endswith(".pb") and ("espcn" in f.lower() or "fsrcnn" in f.lower()
                                          or "fsrcnn" in f.lower() or "espcn" in f.lower()
                                          or "lapsrn" in f.lower() or "superres" in f.lower()):
            return os.path.join(model_dir, f)
    return None


def parse_target(target):
    t = target.lower().replace("p", "")
    mapping = {
        "720": (1280, 720), "1080": (1920, 1080), "1440": (2560, 1440),
        "2160": (3840, 2160), "4k": (3840, 2160), "2k": (2560, 1440),
    }
    if t in mapping:
        return mapping[t]
    if "x" in t:
        try:
            w, h = t.split("x")
            return int(w), int(h)
        except Exception:
            pass
    raise SystemExit("E301: target/goalresolution: %s" % target)


def get_current_resolution(input_path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", input_path],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            w, h = r.stdout.strip().split("x")
            return int(w), int(h)
    except Exception:
        pass
    return None, None


def measure_sharpness(video_path, sample_n=12):
    """frame， Laplacian （clear）。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) or sample_n
    step = max(1, total // sample_n)
    vals = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vals.append(cv2.Laplacian(gray, cv2.CV_64F).var())
        idx += 1
    cap.release()
    return float(np.mean(vals)) if vals else None


def enhance_ffmpeg(input_path, output_path, target_w, target_h):
    """ffmpeg lanczos  + unsharp sharpen（realclear，dependency）。"""
    if not has_ffmpeg():
        raise SystemExit("E300: ffmpeg ，install ffmpeg")
    logging.info("   ffmpeg lanczos  + unsharp sharpen → %dx%d", target_w, target_h)
    # unsharp: brightness 5x5 1.2（sharpen）， 0.5（）
    vf = ("scale=%d:%d:flags=lanczos,"
          "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=1.2:"
          "chroma_msize_x=5:chroma_msize_y=5:chroma_amount=0.5"
          % (target_w, target_h))
    cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", vf,
           "-c:v", "libx264", "-crf", "18", "-preset", "medium",
           "-c:a", "copy", output_path]
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    if r.returncode != 0:
        raise SystemExit("ffmpeg failed: %s" % r.stderr.decode("utf-8", "ignore")[:200])
    return True


def enhance_dnn(input_path, output_path, model_path, scale, target_w, target_h):
    """cv2.dnn_superres AI （ .pb model），output ffmpeg resolution/encode。"""
    logging.info("   cv2.dnn_superres AI （model=%s）", os.path.basename(model_path))
    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        # file
        name = os.path.basename(model_path).lower()
        if "espcn" in name:
            algo = "espcn"
        elif "fsrcnn" in name:
            algo = "fsrcnn"
        elif "lapsrn" in name:
            algo = "lapsrn"
        else:
            algo = "espcn"
        sr.setModel(algo, scale)
    except Exception as e:
        logging.warning("  dnn modelloadfailed， ffmpeg: %s", e)
        return enhance_ffmpeg(input_path, output_path, target_w, target_h)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise SystemExit("E300: openinputvideo")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tmp = output_path + ".dnn_tmp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp, fourcc, fps, (target_w, target_h))
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        up = sr.upsample(frame)
        # target/goalresolution（ dnn output target ）
        if up.shape[1] != target_w or up.shape[0] != target_h:
            up = cv2.resize(up, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        out.write(up)
    cap.release()
    out.release()
    #  ffmpeg encode H.264（cv2  mp4v ）
    if has_ffmpeg():
        cmd = ["ffmpeg", "-y", "-i", tmp, "-c:v", "libx264", "-crf", "18",
               "-c:a", "copy", output_path]
        subprocess.run(cmd, capture_output=True, timeout=600)
        if os.path.exists(tmp):
            os.remove(tmp)
    else:
        shutil.move(tmp, output_path)
    return True


def main():
    ap = argparse.ArgumentParser(description="videoclear（4K  · realsharpen+）")
    ap.add_argument("--input", required=True, help="inputvideopath")
    ap.add_argument("--output", required=True, help="outputvideopath")
    ap.add_argument("--target", default="1080p", help="target/goalresolution：720p/1080p/1440p/4k  WxH")
    ap.add_argument("--engine", default="auto", choices=["auto", "ffmpeg", "dnn"],
                    help="（auto=modeldnnffmpeg）")
    ap.add_argument("--model-dir", default="models", help="cv2.dnn_superres modeldirectory")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    if not os.path.exists(args.input):
        raise SystemExit("E100: videofiledoes not exist: %s" % args.input)

    target_w, target_h = parse_target(args.target)
    curr_w, curr_h = get_current_resolution(args.input)
    if curr_w and curr_h:
        logging.info("resolution: %dx%d → target/goal: %dx%d", curr_w, curr_h, target_w, target_h)
        if curr_w >= target_w and curr_h >= target_h:
            logging.warning(" %dx%d，（sharpen）", curr_w, curr_h)

    # clear：
    sharp_before = measure_sharpness(args.input)
    if sharp_before is not None:
        logging.info("clear(Laplacian)=%.1f", sharp_before)

    # select
    engine = args.engine
    dnn_model = has_dnn_model(args.model_dir) if engine in ("auto", "dnn") else None
    if engine == "auto":
        engine = "dnn" if dnn_model else "ffmpeg"
    logging.info(": %s", engine)

    scale = 4 if target_w >= 2160 else 2
    if engine == "dnn" and dnn_model:
        enhance_dnn(args.input, args.output, dnn_model, scale, target_w, target_h)
    else:
        enhance_ffmpeg(args.input, args.output, target_w, target_h)

    # clear：
    sharp_after = measure_sharpness(args.output)
    if sharp_after is not None and sharp_before:
        delta = (sharp_after - sharp_before) / sharp_before * 100.0
        logging.info("clear=%.1f（ %+.1f%%）", sharp_after, delta)
        if delta < 0:
            logging.warning("⚠️ clear（clearsmooth），； dnn model。")
    logging.info("DONE -> %s", args.output)


if __name__ == "__main__":
    main()
