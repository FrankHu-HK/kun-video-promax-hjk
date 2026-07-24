#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
product_extract.py —— Workflow C（AI 真人口播带货）C1 阶段：产品资产提取

用途：从用户上传的"产品多角度视频"中，自动挑出若干张【清晰 + 正光 + 角度多样】的
关键帧，构建"产品参考图集"，供后续：
  1) 真产品贴图合成（关键展示镜头用真实产品图，保证 logo/文字 100% 不变形）；
  2) 多参考条件生成（把产品图作为 reference 喂给 Seedance/Kling 多图参考）。

纯 opencv + numpy 本地运行，零额外积分消耗。

评分维度：
  - 清晰度：Laplacian 方差（越大越锐利，剔除模糊/运动虚焦帧）
  - 曝光：平均亮度落在合理区间（剔除过曝/欠曝）
  - 角度多样性：对候选帧做直方图去重，保证抽出的是"不同角度"而非"同一角度连拍"

输出：
  - 若干 product_ref_XX.jpg（ASCII 命名，可直接喂模型）
  - product_manifest.json（每张图的评分/来源帧号/时间戳）

用法：
  python product_extract.py \
    --video product_raw.mp4 \
    --out-dir product_refs \
    --top 6 \
    --min-sharp 60 \
    --bright-lo 40 --bright-hi 220

⚠️ 坑点：cv2.imread/VideoCapture 读不了中文路径，请先把视频复制成 ASCII 文件名。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np


def compute_sharpness(gray):
    """Laplacian 方差衡量清晰度，越大越锐利。"""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness(gray):
    """平均亮度（0-255）。"""
    return float(gray.mean())


def hist_signature(frame, bins=32):
    """计算 HSV 直方图签名，用于角度去重（同角度直方图相近）。"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [bins, bins], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist.flatten()


def hist_similarity(a, b):
    """相关系数，1=完全相同。"""
    return float(cv2.compareHist(
        a.reshape(-1, 1).astype("float32"),
        b.reshape(-1, 1).astype("float32"),
        cv2.HISTCMP_CORREL,
    ))


def main():
    ap = argparse.ArgumentParser(description="从产品多角度视频提取清晰/多样的参考图集")
    ap.add_argument("--video", required=True, help="产品多角度视频（ASCII 路径）")
    ap.add_argument("--out-dir", required=True, help="输出目录（存参考图 + manifest）")
    ap.add_argument("--top", type=int, default=6, help="最终保留的参考图数量")
    ap.add_argument("--sample-step", type=int, default=3, help="每隔 N 帧采样一次")
    ap.add_argument("--min-sharp", type=float, default=60.0, help="清晰度下限（Laplacian 方差）")
    ap.add_argument("--bright-lo", type=float, default=40.0, help="亮度下限（剔除欠曝）")
    ap.add_argument("--bright-hi", type=float, default=220.0, help="亮度上限（剔除过曝）")
    ap.add_argument("--dup-thresh", type=float, default=0.85,
                    help="角度去重阈值：直方图相似度>此值视为同角度，只保留更清晰的")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        print(f"[ERR] 视频不存在: {args.video}", file=sys.stderr)
        sys.exit(2)
    # ASCII 路径检查（cv2 读中文路径会失败）
    try:
        args.video.encode("ascii")
    except UnicodeEncodeError:
        print(f"[ERR] 视频路径含非 ASCII 字符，cv2 读取会失败，请先复制成纯英文名: {args.video}",
              file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"[ERR] 无法打开视频: {args.video}", file=sys.stderr)
        sys.exit(2)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    candidates = []  # {idx, ts, sharp, bright, sig, frame}
    idx = -1
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        idx += 1
        if idx % args.sample_step != 0:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharp = compute_sharpness(gray)
        bright = compute_brightness(gray)
        # 曝光/清晰度硬过滤
        if sharp < args.min_sharp:
            continue
        if bright < args.bright_lo or bright > args.bright_hi:
            continue
        candidates.append({
            "idx": idx,
            "ts": round(idx / fps, 3),
            "sharp": round(sharp, 2),
            "bright": round(bright, 2),
            "sig": hist_signature(frame),
            "frame": frame,
        })
    cap.release()

    if not candidates:
        print("[ERR] 无合格候选帧（可能视频过暗/过曝/全程模糊）。"
              "可降低 --min-sharp 或放宽 --bright 区间重试。", file=sys.stderr)
        sys.exit(1)

    # 按清晰度降序，贪心选取"角度多样"的 top-N
    candidates.sort(key=lambda c: c["sharp"], reverse=True)
    picked = []
    for c in candidates:
        is_dup = False
        for p in picked:
            if hist_similarity(c["sig"], p["sig"]) > args.dup_thresh:
                is_dup = True
                break
        if not is_dup:
            picked.append(c)
        if len(picked) >= args.top:
            break

    # 若去重后不足 top（角度单一），用剩余最清晰帧补齐
    if len(picked) < args.top:
        picked_idx = {p["idx"] for p in picked}
        for c in candidates:
            if c["idx"] not in picked_idx:
                picked.append(c)
            if len(picked) >= args.top:
                break

    manifest = {
        "source_video": args.video,
        "fps": round(fps, 3),
        "total_frames": total,
        "candidate_count": len(candidates),
        "picked_count": len(picked),
        "refs": [],
    }
    for i, p in enumerate(picked):
        name = f"product_ref_{i:02d}.jpg"
        path = os.path.join(args.out_dir, name)
        cv2.imwrite(path, p["frame"], [cv2.IMWRITE_JPEG_QUALITY, 95])
        manifest["refs"].append({
            "file": name,
            "src_frame": p["idx"],
            "timestamp": p["ts"],
            "sharpness": p["sharp"],
            "brightness": p["bright"],
        })

    mpath = os.path.join(args.out_dir, "product_manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[OK] 候选帧 {len(candidates)} → 抽取参考图 {len(picked)} 张")
    for r in manifest["refs"]:
        print(f"  {r['file']}  帧#{r['src_frame']}  t={r['timestamp']}s  "
              f"锐利={r['sharpness']}  亮度={r['brightness']}")
    print(f"[OK] manifest: {mpath}")
    print("[TIP] 请从中人工挑选【正面标签/logo 最清晰】的 1-2 张作为贴图合成主图；"
          "其余作多参考条件辅助图。")


if __name__ == "__main__":
    main()
