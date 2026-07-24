# -*- coding: utf-8 -*-
"""
batch_faceswap.py (v2.4.2) - Workflow E：batchface swap（）
==========================================================
target/goal × N video → face swap，output：
  output_dir/
    video1_faceswapped.mp4
    video2_faceswapped.mp4
    ...
    batch_state.json     # status（videostatus）
    batch_report.json    # 

capability（v2.4.2 ）：
  --workers N           process N video（ 1 ，stable； 2-4 ）
  --preset xxx          parameter()， Pro ：auto/speed/quality/sideface/occlusion
  --resume              ：read batch_state.json，donetask（success）
  --continue-on-error   failedinterrupt，continue
  --retry N             videofailedretry( 1)
  progress + ETA show/display（/）

：
  python scripts/batch_faceswap.py --photo target/goal.jpg --videos "v1.mp4;v2.mp4" --out-dir batchoutput
  python scripts/batch_faceswap.py --photo target/goal.jpg --videos-dir videofile --out-dir batchoutput --workers 4 --preset quality
  python scripts/batch_faceswap.py ... --resume          # interrupt
"""
import os
import sys
import json
import argparse
import subprocess
import logging
import time
from pathlib import Path

ERROR_CODES = {
    "E400": "video（ --videos  --videos-dir）",
    "E401": "videofiledoes not exist",
    "E402": "batchface swapfailed（generatefile）",
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def get_videos_from_dir(dir_path):
    """directoryvideofile（mp4/mov/mkv）"""
    exts = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    p = Path(dir_path)
    if not p.exists():
        raise SystemExit(f"E401: videodirectorydoes not exist: {dir_path}")
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts])


def parse_videos_arg(v):
    """ --videos parameter（）"""
    if not v:
        return []
    #  ; , ， 
    parts = v.replace(",", ";").replace("，", ";").split(";")
    return [p.strip() for p in parts if p.strip()]


def run_faceswap_for_one(photo, video, output, use_pro=True, resume=False, preset="auto"):
    """ faceswap.py  faceswap_pro.py processvideo。

    use_pro=True  --preset（）， resume  --resume 
    Pro status，「batchinterrupt → videocontinue」。
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script = "faceswap_pro.py" if use_pro else "faceswap.py"
    script_path = os.path.join(script_dir, script)
    if not os.path.exists(script_path):
        raise SystemExit(f": {script_path}")
    cmd = ["python", script_path, "--video", video, "--photo", photo, "--out", output]
    if use_pro and preset and preset != "auto":
        cmd += ["--preset", preset]
    if resume:
        cmd.append("--resume")
    r = subprocess.run(cmd, capture_output=True, timeout=1800)
    return r.returncode == 0, r.stderr.decode("utf-8", errors="ignore")


def main():
    ap = argparse.ArgumentParser(description="batchface swap（ × N video）·  v2.4.2")
    ap.add_argument("--photo", required=True, help="target/goal")
    ap.add_argument("--videos", help="video（/）")
    ap.add_argument("--videos-dir", help="videofile")
    ap.add_argument("--out-dir", default="batch_output", help="outputdirectory")
    ap.add_argument("--basic", action="store_true", help="（ Pro ）")
    ap.add_argument("--continue-on-error", action="store_true", help="failedcontinueprocessvideo")
    ap.add_argument("--resume", action="store_true",
                    help="：read batch_state.json，skipdonevideo，done")
    ap.add_argument("--retry", type=int, default=1, help="videofailedretry(1)")
    ap.add_argument("--workers", type=int, default=1,
                    help="processvideo(，1；CPU2-4)")
    ap.add_argument("--preset", default="auto",
                    choices=["auto", "speed", "quality", "sideface", "occlusion"],
                    help="parameter()， Pro ")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    if not os.path.exists(args.photo):
        raise SystemExit(f"E100: target/goaldoes not exist: {args.photo}")

    # video
    videos = parse_videos_arg(args.videos)
    if args.videos_dir:
        videos.extend(get_videos_from_dir(args.videos_dir))
    if not videos:
        raise SystemExit("E400: video（ --videos  --videos-dir）")

    # checkvideo
    for v in videos:
        if not os.path.exists(v):
            logging.warning("videodoes not exist，skip: %s", v)

    # createoutputdirectory
    os.makedirs(args.out_dir, exist_ok=True)

    use_pro = not args.basic
    report = {
        "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "totalVideos": len(videos),
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "usePro": use_pro,
        "preset": args.preset,
        "workers": max(1, args.workers),
        "results": [],
    }

    # status（videostatus，interrupt）
    state_path = os.path.join(args.out_dir, "batch_state.json")
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

    def process_one(v, output):
        last_err = ""
        for attempt in range(max(1, args.retry + 1)):
            try:
                ok, err = run_faceswap_for_one(args.photo, v, output, use_pro, args.resume, args.preset)
            except Exception as e:
                err = str(e)
                ok = False
            if ok:
                return True, ""
            last_err = err
            logging.warning("  [%s]  %d failed: %s", os.path.basename(v), attempt + 1, err[:160])
        return False, last_err

    # task（：successskip）
    tasks = []
    for i, v in enumerate(videos, 1):
        v = v.strip()
        if not v or not os.path.exists(v):
            report["skipped"] += 1
            report["results"].append({"video": v, "status": "skipped", "reason": "file not found"})
            continue
        base = os.path.splitext(os.path.basename(v))[0]
        output = os.path.join(args.out_dir, f"{base}_faceswapped.mp4")
        if args.resume and state.get(v) == "success" and os.path.exists(output) and os.path.getsize(output) > 0:
            report["skipped"] += 1
            report["results"].append({"video": v, "output": output, "status": "skipped", "reason": "resume: already done"})
            logging.info("[%d/%d] ✅ already exists，skip(): %s", i, len(videos), output)
            continue
        tasks.append((i, v, output))

    total_tasks = len(tasks)
    done_cnt = 0
    t0_all = time.time()
    logging.info("=" * 60)
    logging.info("🔁 batchface swap（%s）process %d ，=%d，=%s",
                 "Pro" if use_pro else "Basic", total_tasks, max(1, args.workers), args.preset)
    logging.info("=" * 60)

    def _worker(task):
        i, v, output = task
        logging.info("[%d/%d] start: %s", i, len(videos), v)
        ok, err = process_one(v, output)
        return i, v, output, ok, err

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(_worker, t) for t in tasks]
        for fut in as_completed(futures):
            i, v, output, ok, err = fut.result()
            done_cnt += 1
            if ok:
                report["succeeded"] += 1
                report["results"].append({"video": v, "output": output, "status": "success"})
                state[v] = "success"
                logging.info("  ✅ done[%d/%d]: %s", done_cnt, total_tasks, output)
            else:
                report["failed"] += 1
                report["results"].append({"video": v, "output": output, "status": "fail", "error": err[:200]})
                state[v] = "fail"
                logging.error("  ❌ failed[%d/%d]: %s", done_cnt, total_tasks, err[:200])
                if not args.continue_on_error:
                    for f in futures:
                        f.cancel()
                    break
            el = time.time() - t0_all
            rate = done_cnt / el if el > 0 else 0
            eta = (total_tasks - done_cnt) / rate if rate > 0 else 0
            logging.info("  progress %d/%d (%.0f%%) · %.0fs · %.0fs",
                         done_cnt, total_tasks, done_cnt * 100.0 / total_tasks, el, eta)
            try:
                with open(state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False)
            except Exception:
                pass

    report["endedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report_path = os.path.join(args.out_dir, "batch_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logging.info("=" * 60)
    logging.info("DONE: success=%d failed=%d skip=%d", report["succeeded"], report["failed"], report["skipped"])
    logging.info(": %s", report_path)


if __name__ == "__main__":
    main()
