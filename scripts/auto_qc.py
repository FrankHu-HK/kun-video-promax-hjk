#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
auto_qc.py — Workflow B 生成视频技术层自动质检

作用：把"人反复手动检查"变成"机器自动检查"，不达标触发重试。
仅做技术层质检（文件完整/黑屏/静帧/编码/时长），画面像不像需用户目检。
依赖：opencv-python, numpy（可选 imageio-ffmpeg 取 ffmpeg，本脚本仅用 opencv 读帧）

退出码：0=通过，1=不通过（调用方据此触发自动重试）
"""

import sys
import json
import argparse

import numpy as np
import cv2


def qc(video_path, expect_duration=None, black_thresh=12.0,
       still_diff_thresh=0.5, sample_step=3):
    """技术层质检，返回报告 dict（不抛异常，遇错写入 issues）。"""
    rep = {
        "video": video_path,
        "ok": False,
        "opened": False,
        "frame_count": 0,
        "fps": 0.0,
        "duration_sec": 0.0,
        "black_frame_ratio": 0.0,
        "still_frame_ratio": 0.0,
        "issues": [],
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        rep["issues"].append("无法打开视频（编码不兼容/文件损坏/路径含中文未ASCII化）")
        return rep
    rep["opened"] = True

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    rep["fps"] = round(fps, 2)
    rep["frame_count"] = total
    if total <= 0:
        rep["issues"].append("帧数为0（空视频/生成失败）")
        cap.release()
        return rep

    prev_gray = None
    black_cnt = 0
    still_cnt = 0
    sampled = 0
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % sample_step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_b = float(gray.mean())
            if mean_b < black_thresh:
                black_cnt += 1
            if prev_gray is not None:
                diff = float(np.abs(gray.astype(np.int16) - prev_gray.astype(np.int16)).mean())
                if diff < still_diff_thresh:
                    still_cnt += 1
            prev_gray = gray
            sampled += 1
        idx += 1
    cap.release()

    rep["duration_sec"] = round(total / fps, 2) if fps > 0 else 0.0
    if sampled > 0:
        rep["black_frame_ratio"] = round(black_cnt / sampled, 3)
        rep["still_frame_ratio"] = round(still_cnt / max(sampled - 1, 1), 3)

    # 判定
    if rep["black_frame_ratio"] > 0.3:
        rep["issues"].append("黑屏比例过高 %.2f（>0.3，疑似生成全黑）" % rep["black_frame_ratio"])
    if rep["still_frame_ratio"] > 0.8:
        rep["issues"].append("静帧比例过高 %.2f（>0.8，疑似未生成/静止图）" % rep["still_frame_ratio"])
    if expect_duration is not None and rep["duration_sec"] > 0:
        deviation = abs(rep["duration_sec"] - expect_duration) / expect_duration
        if deviation > 0.3:
            rep["issues"].append(
                "时长偏差过大 实际%.2fs/预期%.2fs（>30%%）" % (rep["duration_sec"], expect_duration))

    rep["ok"] = len(rep["issues"]) == 0
    return rep


def main():
    ap = argparse.ArgumentParser(description="Workflow B 生成视频技术层自动质检")
    ap.add_argument("--video", required=True, help="待质检视频路径")
    ap.add_argument("--expect-duration", type=float, default=None,
                    help="预期时长(秒)，用于偏差判定（可选）")
    ap.add_argument("--black-thresh", type=float, default=12.0,
                    help="黑屏判定阈值（0-255 平均亮度，低于即黑屏，默认12）")
    ap.add_argument("--still-diff-thresh", type=float, default=0.5,
                    help="静帧判定阈值（相邻帧平均差异，低于即静帧，默认0.5，保守可调高）")
    ap.add_argument("--sample-step", type=int, default=3,
                    help="抽帧步长，默认每3帧取1帧")
    ap.add_argument("--out", default=None, help="JSON报告输出路径(可选)")
    args = ap.parse_args()

    rep = qc(args.video,
             expect_duration=args.expect_duration,
             black_thresh=args.black_thresh,
             still_diff_thresh=args.still_diff_thresh,
             sample_step=args.sample_step)

    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
