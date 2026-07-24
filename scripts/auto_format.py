# -*- coding: utf-8 -*-
"""
auto_format.py (v2.2.0) - videoformatprocess
===========================================
"formatprocess"：
  - inputvideoformat
  -  ffmpeg  mp4(H.264)
  - retry（）
  - （encode）

inputformat（mov/mkv/avi/webm/flv/mp4/HEVC...） →  mp4(H.264) output
"""
import os
import sys
import subprocess
import argparse
import logging
import shutil
import json

# ============ error ============
ERROR_CODES = {
    "E300": "ffmpeg （install ffmpeg  PATH）",
    "E301": "inputfileread（/format）",
    "E302": "failed（encode/）",
    "E303": "failed（retry 3 ）",
}

# outputparameter
STANDARD_PARAMS = {
    "vcodec": "libx264",  # encode
    "acodec": "aac",  # audio
    "pix_fmt": "yuv420p",  # format
    "preset": "medium",
    "crf": "18",  # 
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def probe_video(input_path):
    """ ffprobe videoinformation"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=format_name:stream=codec_name,codec_type,width,height", "-of", "json", input_path],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception:
        pass
    return None


def is_standard_mp4(input_path, info=None):
    """check mp4(H.264)"""
    if info is None:
        info = probe_video(input_path)
    if not info:
        return False
    fmt = (info.get("format", {}).get("format_name") or "").lower()
    has_h264 = False
    has_aac = False
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and s.get("codec_name") == "h264":
            has_h264 = True
        if s.get("codec_type") == "audio" and s.get("codec_name") == "aac":
            has_aac = True
    if "mp4" in fmt and has_h264:
        return True
    return False


def convert_to_mp4(input_path, output_path=None, max_retry=3):
    """ mp4(H.264)，retry"""
    if not has_ffmpeg():
        raise SystemExit("E300: ffmpeg ，install ffmpeg  PATH")
    if not os.path.exists(input_path):
        raise SystemExit(f"E301: inputfiledoes not exist: {input_path}")
    if output_path is None:
        # outputfile
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path) or ".", f"{base}_std.mp4")
    # check
    if is_standard_mp4(input_path):
        logging.info("  input mp4(H.264)，")
        if input_path != output_path:
            shutil.copy2(input_path, output_path)
        return output_path
    # 
    logging.info("   %s → %s", input_path, output_path)
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", STANDARD_PARAMS["vcodec"],
        "-preset", STANDARD_PARAMS["preset"],
        "-crf", STANDARD_PARAMS["crf"],
        "-pix_fmt", STANDARD_PARAMS["pix_fmt"],
        "-c:a", STANDARD_PARAMS["acodec"],
        "-movflags", "+faststart",  # 
        output_path,
    ]
    last_err = None
    for attempt in range(max_retry):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=1800)
            if r.returncode == 0 and os.path.exists(output_path):
                return output_path
            last_err = (r.stderr or b"").decode("utf-8", errors="ignore")[:200]
            logging.warning("   %d failed: %s", attempt + 1, last_err)
        except Exception as e:
            last_err = str(e)
            logging.warning("   %d exception: %s", attempt + 1, e)
        if attempt < max_retry - 1:
            wait = 5 * (2 ** attempt)
            logging.info("   %ds retry...", wait)
            import time as _t
            _t.sleep(wait)
    raise SystemExit(f"E302: failed（retry {max_retry} ）: {last_err}")


def download_with_retry(url, output_path, max_retry=3):
    """file（retry）"""
    import time as _t
    last_err = None
    for attempt in range(max_retry):
        try:
            r = subprocess.run(
                ["curl", "-fL", "--retry", "2", "--connect-timeout", "30", url, "-o", output_path],
                capture_output=True, timeout=600,
            )
            if r.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            last_err = (r.stderr or b"").decode("utf-8", errors="ignore")[:200]
        except Exception as e:
            last_err = str(e)
        logging.warning("   %d failed: %s", attempt + 1, last_err)
        if attempt < max_retry - 1:
            wait = 10 * (2 ** attempt)
            logging.info("   %ds retry...", wait)
            _t.sleep(wait)
    raise SystemExit(f"E303: failed（retry {max_retry} ）: {last_err}")


def safe_input(input_path, output_dir=None):
    """inputvideo mp4（H.264/AAC）—— work/tasksafe。
    input mp4，path； output_dir/<filename>_std.mp4
    """
    if not os.path.exists(input_path):
        raise SystemExit(f"E301: inputfiledoes not exist: {input_path}")
    if is_standard_mp4(input_path):
        logging.info("  ✅ input %s  mp4(H.264)，", os.path.basename(input_path))
        return input_path
    if output_dir is None:
        output_dir = os.path.dirname(input_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    out = os.path.join(output_dir, f"{base}_std.mp4")
    return convert_to_mp4(input_path, out)


def main():
    ap = argparse.ArgumentParser(description="videoformatprocess（ + retry）")
    ap.add_argument("--input", required=True, help="inputvideopath（format）")
    ap.add_argument("--output", help="outputpath（ ./<name>_std.mp4）")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)
    out = convert_to_mp4(args.input, args.output)
    logging.info("DONE -> %s", out)


if __name__ == "__main__":
    main()
