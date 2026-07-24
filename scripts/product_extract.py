#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
product_extract.py —— Workflow C（AI real-person talking heade-commerce product demo）C1 stage：产品资产extract

用途：从userupload的"产品多角度video"中，自动挑出若干张【clear + 正光 + 角度多样】的
关键frame，构建"产品参考图集"，供后续：
  1) 真产品贴图composite（关键展示镜头用real产品图，保证 logo/文字 100% 不变形）；
  2) 多参考条件generate（把产品图作为 reference 喂给 Seedance/Kling 多图参考）。

纯 opencv + numpy 本地run，零额外积分消耗。

score/rating维度：
  - clear度：Laplacian 方差（越大越锐利，剔除blurry/运动虚焦frame）
  - 曝光：平均brightness落在合理区间（剔除过曝/欠曝）
  - 角度多样性：对候选frame做直方图去重，保证抽出的是"不同角度"而非"同一角度连拍"

output：
  - 若干 product_ref_XX.jpg（ASCII 命名，可直接喂model）
  - product_manifest.json（每张图的score/rating/来源frame号/time戳）

用法：
  python product_extract.py \
    --video product_raw.mp4 \
    --out-dir product_refs \
    --top 6 \
    --min-sharp 60 \
    --bright-lo 40 --bright-hi 220

⚠️ 坑点：cv2.imread/VideoCapture 读不了中文path，请先把videocopy成 ASCII file名。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np


def compute_sharpness(gray):
    """Laplacian 方差衡量clear度，越大越锐利。"""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness(gray):
    """平均brightness（0-255）。"""
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
    ap = argparse.ArgumentParser(description="从产品多角度videoextractclear/多样的参考图集")
    ap.add_argument("--video", required=True, help="产品多角度video（ASCII path）")
    ap.add_argument("--out-dir", required=True, help="outputdirectory（存参考图 + manifest）")
    ap.add_argument("--top", type=int, default=6, help="最终保留的参考图数量")
    ap.add_argument("--sample-step", type=int, default=3, help="每隔 N frame采样一次")
    ap.add_argument("--min-sharp", type=float, default=60.0, help="clear度下限（Laplacian 方差）")
    ap.add_argument("--bright-lo", type=float, default=40.0, help="brightness下限（剔除欠曝）")
    ap.add_argument("--bright-hi", type=float, default=220.0, help="brightness上限（剔除过曝）")
    ap.add_argument("--dup-thresh", type=float, default=0.85,
                    help="角度去重阈值：直方图相似度>此值视为同角度，只保留更clear的")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        print(f"[ERR] videodoes not exist: {args.video}", file=sys.stderr)
        sys.exit(2)
    # ASCII pathcheck（cv2 读中文path会failed）
    try:
        args.video.encode("ascii")
    except UnicodeEncodeError:
        print(f"[ERR] videopath含非 ASCII 字符，cv2 read会failed，请先copy成纯英文名: {args.video}",
              file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"[ERR] 无法openvideo: {args.video}", file=sys.stderr)
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
        # 曝光/clear度硬过滤
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
        print("[ERR] 无合格候选frame（可能video过暗/过曝/全程blurry）。"
              "可降低 --min-sharp 或放宽 --bright 区间retry。", file=sys.stderr)
        sys.exit(1)

    # 按clear度降序，贪心选取"角度多样"的 top-N
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

    # 若去重后不足 top（角度单一），用剩余最clearframe补齐
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

    print(f"[OK] 候选frame {len(candidates)} → 抽取参考图 {len(picked)} 张")
    for r in manifest["refs"]:
        print(f"  {r['file']}  frame#{r['src_frame']}  t={r['timestamp']}s  "
              f"锐利={r['sharpness']}  brightness={r['brightness']}")
    print(f"[OK] manifest: {mpath}")
    print("[TIP] 请从中人工挑选【正面label/logo 最clear】的 1-2 张作为贴图composite主图；"
          "其余作多参考条件辅助图。")


if __name__ == "__main__":
    main()
