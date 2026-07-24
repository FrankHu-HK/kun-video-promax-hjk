# -*- coding: utf-8 -*-
"""
enhance_4k.py (v2.8.0) - Workflow D：videoclear度增强（4K 升频）
=============================================================
对低resolution/低码率video做超resolution放大并real增强clear度：
  - 主path（零dependency、CPU 友好）：ffmpeg lanczos 升频 + unsharp sharpen（real可见的clear提升）
  - 可选增强：若 models/ 下放置了 cv2.dnn_superres model（如 ESPCN_x4.pb），自动enable AI 超分

与旧版区别（诚实化 + real生效）：
  - 旧版声称"real-ESRGAN / CV2 DNN / ffmpeg 三引擎自动选"，实际开箱只有 ffmpeg 能跑；
    新版明确：默认走 ffmpeg+sharpen（开箱即用），AI 超分需你自行放置model才enable。
  - 新增「clear度量化对比」：升频前后用 Laplacian 方差实测clear度，报告提升百分比，
    让"变clear"可被verify，而非空口。

用法：
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

# ============ error码 ============
ERROR_CODES = {
    "E300": "ffmpeg 未找到（请先install ffmpeg 并加入 PATH）",
    "E301": "不支持的target/goalresolution（仅 720p/1080p/1440p/4k）",
    "E302": "无法确定源resolution，请显式指定 --target",
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def has_dnn_model(model_dir):
    """检测 models/ 下是否有 cv2.dnn_superres model（.pb）。"""
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
    raise SystemExit("E301: 不支持的target/goalresolution: %s" % target)


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
    """采样若干frame，返回平均 Laplacian 方差（clear度代理指标）。"""
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
    """ffmpeg lanczos 升频 + unsharp sharpen（real可见clear提升，零额外dependency）。"""
    if not has_ffmpeg():
        raise SystemExit("E300: ffmpeg 未找到，请先install ffmpeg")
    logging.info("  使用 ffmpeg lanczos 升频 + unsharp sharpen → %dx%d", target_w, target_h)
    # unsharp: brightness 5x5 强度1.2（sharpen），色度轻微 0.5（去彩边）
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
    """cv2.dnn_superres AI 超分（需 .pb model），output后再用 ffmpeg 规整resolution/encode。"""
    logging.info("  使用 cv2.dnn_superres AI 超分（model=%s）", os.path.basename(model_path))
    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        # 从file名推断算法与倍数
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
        logging.warning("  dnn modelloadfailed，回退 ffmpeg: %s", e)
        return enhance_ffmpeg(input_path, output_path, target_w, target_h)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise SystemExit("E300: 无法openinputvideo")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tmp = output_path + ".dnn_tmp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp, fourcc, fps, (target_w, target_h))
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        up = sr.upsample(frame)
        # 规整到target/goalresolution（少数情况 dnn output与 target 不一致）
        if up.shape[1] != target_w or up.shape[0] != target_h:
            up = cv2.resize(up, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        out.write(up)
    cap.release()
    out.release()
    # 用 ffmpeg 重新encode为 H.264（cv2 默认 mp4v 兼容性差）
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
    ap = argparse.ArgumentParser(description="videoclear度增强（4K 升频 · realsharpen+量化）")
    ap.add_argument("--input", required=True, help="inputvideopath")
    ap.add_argument("--output", required=True, help="outputvideopath")
    ap.add_argument("--target", default="1080p", help="target/goalresolution：720p/1080p/1440p/4k 或 WxH")
    ap.add_argument("--engine", default="auto", choices=["auto", "ffmpeg", "dnn"],
                    help="超分引擎（auto=有model用dnn否则ffmpeg）")
    ap.add_argument("--model-dir", default="models", help="cv2.dnn_superres modeldirectory")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    if not os.path.exists(args.input):
        raise SystemExit("E100: videofiledoes not exist: %s" % args.input)

    target_w, target_h = parse_target(args.target)
    curr_w, curr_h = get_current_resolution(args.input)
    if curr_w and curr_h:
        logging.info("源resolution: %dx%d → target/goal: %dx%d", curr_w, curr_h, target_w, target_h)
        if curr_w >= target_w and curr_h >= target_h:
            logging.warning("源已是 %dx%d，无需升频（将仅做sharpen）", curr_w, curr_h)

    # clear度量化：升频前
    sharp_before = measure_sharpness(args.input)
    if sharp_before is not None:
        logging.info("升频前平均clear度(Laplacian方差)=%.1f", sharp_before)

    # select引擎
    engine = args.engine
    dnn_model = has_dnn_model(args.model_dir) if engine in ("auto", "dnn") else None
    if engine == "auto":
        engine = "dnn" if dnn_model else "ffmpeg"
    logging.info("使用引擎: %s", engine)

    scale = 4 if target_w >= 2160 else 2
    if engine == "dnn" and dnn_model:
        enhance_dnn(args.input, args.output, dnn_model, scale, target_w, target_h)
    else:
        enhance_ffmpeg(args.input, args.output, target_w, target_h)

    # clear度量化：升频后
    sharp_after = measure_sharpness(args.output)
    if sharp_after is not None and sharp_before:
        delta = (sharp_after - sharp_before) / sharp_before * 100.0
        logging.info("升频后平均clear度=%.1f（变化 %+.1f%%）", sharp_after, delta)
        if delta < 0:
            logging.warning("⚠️ clear度未提升（源已较clear或插值smooth），属正常；可换更锐素材或加 dnn model。")
    logging.info("DONE -> %s", args.output)


if __name__ == "__main__":
    main()
