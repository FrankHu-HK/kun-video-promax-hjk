# -*- coding: utf-8 -*-
"""
batch_faceswap.py (v2.4.2) - Workflow E：batchface swap（高级版）
==========================================================
一个target/goal照片 × N 个video → 一次性跑完所有face swap，output：
  output_dir/
    video1_faceswapped.mp4
    video2_faceswapped.mp4
    ...
    batch_state.json     # 精准断点续跑status（每video一行status）
    batch_report.json    # 汇总报告

高级capability（v2.4.2 从底层重做）：
  --workers N           并行process N 个video（默认 1 串行，stable省资源；多核机器设 2-4 提速）
  --preset xxx          parameter预设(便捷调参)，透传给 Pro 版：auto/speed/quality/sideface/occlusion
  --resume              精准断点续跑：read batch_state.json，只跑未done的task（不重跑已success的）
  --continue-on-error   某个failed不interrupt，continue其余
  --retry N             单videofailedretry次数(默认 1)
  实时progress + ETA show/display（已用/预计剩余秒数）

用法：
  python scripts/batch_faceswap.py --photo target/goal.jpg --videos "v1.mp4;v2.mp4" --out-dir batchoutput
  python scripts/batch_faceswap.py --photo target/goal.jpg --videos-dir videofile夹 --out-dir batchoutput --workers 4 --preset quality
  python scripts/batch_faceswap.py ... --resume          # interrupt后接着跑
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
    "E400": "未指定video（用 --videos 或 --videos-dir）",
    "E401": "videofiledoes not exist",
    "E402": "batchface swap中途failed（已generate部分file）",
}


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def get_videos_from_dir(dir_path):
    """从directory中获取所有videofile（mp4/mov/mkv）"""
    exts = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    p = Path(dir_path)
    if not p.exists():
        raise SystemExit(f"E401: videodirectorydoes not exist: {dir_path}")
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts])


def parse_videos_arg(v):
    """解析 --videos parameter（分号或逗号分隔）"""
    if not v:
        return []
    # 支持 ; , ， 三种分隔符
    parts = v.replace(",", ";").replace("，", ";").split(";")
    return [p.strip() for p in parts if p.strip()]


def run_faceswap_for_one(photo, video, output, use_pro=True, resume=False, preset="auto"):
    """调用 faceswap.py 或 faceswap_pro.py process单个video。

    use_pro=True 时透传 --preset（便捷调参），并在 resume 时透传 --resume 让
    Pro 版从自身分段status续跑，实现「batchinterrupt → 单video内部也从断点continue」的双层续跑。
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script = "faceswap_pro.py" if use_pro else "faceswap.py"
    script_path = os.path.join(script_dir, script)
    if not os.path.exists(script_path):
        raise SystemExit(f"未找到脚本: {script_path}")
    cmd = ["python", script_path, "--video", video, "--photo", photo, "--out", output]
    if use_pro and preset and preset != "auto":
        cmd += ["--preset", preset]
    if resume:
        cmd.append("--resume")
    r = subprocess.run(cmd, capture_output=True, timeout=1800)
    return r.returncode == 0, r.stderr.decode("utf-8", errors="ignore")


def main():
    ap = argparse.ArgumentParser(description="batchface swap（一个照片 × N 个video）· 高级版 v2.4.2")
    ap.add_argument("--photo", required=True, help="target/goal人脸照")
    ap.add_argument("--videos", help="video列表（分号/逗号分隔）")
    ap.add_argument("--videos-dir", help="videofile夹")
    ap.add_argument("--out-dir", default="batch_output", help="outputdirectory")
    ap.add_argument("--basic", action="store_true", help="使用基础版（默认 Pro 版）")
    ap.add_argument("--continue-on-error", action="store_true", help="failed时continueprocess其他video")
    ap.add_argument("--resume", action="store_true",
                    help="断点续跑：read batch_state.json，skip已donevideo，只跑未done的")
    ap.add_argument("--retry", type=int, default=1, help="单videofailedretry次数(默认1)")
    ap.add_argument("--workers", type=int, default=1,
                    help="并行process的video数(高级版，默认1串行；CPU多核可设2-4提速)")
    ap.add_argument("--preset", default="auto",
                    choices=["auto", "speed", "quality", "sideface", "occlusion"],
                    help="parameter预设(便捷调参)，透传给 Pro 版")
    ap.add_argument("--debug", action="store_true", help="Debug log")
    args = ap.parse_args()
    setup_logging(args.debug)

    if not os.path.exists(args.photo):
        raise SystemExit(f"E100: target/goal照片does not exist: {args.photo}")

    # 收集video列表
    videos = parse_videos_arg(args.videos)
    if args.videos_dir:
        videos.extend(get_videos_from_dir(args.videos_dir))
    if not videos:
        raise SystemExit("E400: 未指定video（用 --videos 或 --videos-dir）")

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

    # 精准断点续跑status（每videostatus落盘，支持interrupt后接着跑）
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
            logging.warning("  [%s] 第 %d 次failed: %s", os.path.basename(v), attempt + 1, err[:160])
        return False, last_err

    # 组织task（断点续跑：已success且产物存在则skip）
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
            logging.info("[%d/%d] ✅ already exists，skip(断点续跑): %s", i, len(videos), output)
            continue
        tasks.append((i, v, output))

    total_tasks = len(tasks)
    done_cnt = 0
    t0_all = time.time()
    logging.info("=" * 60)
    logging.info("🔁 batchface swap高级版（%s）待process %d 个，并行度=%d，预设=%s",
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
            logging.info("  progress %d/%d (%.0f%%) · 已用%.0fs · 预计剩余%.0fs",
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
    logging.info("汇总: %s", report_path)


if __name__ == "__main__":
    main()
