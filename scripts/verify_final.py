# -*- coding: utf-8 -*-
"""阶段4 综合验证：抖音水印残留 OCR 复核 + 换脸覆盖统计。
用法: verify_final.py --video 最终视频 --bbox 阶段1的face_bboxes.json --models-dir ... --insight-root ...
"""
import os, json, argparse
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

KEYWORDS = ("抖音", "CallmeSJ", "SJ思杰", "Call me", "AI", "生成", "A1", "A I", "A.I", "A｜", "AI生成")


def hit(text):
    t = text.upper()
    return any(k.upper() in t for k in KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--bbox", default=None, help="阶段1的 face_bboxes.json")
    ap.add_argument("--models-dir", required=True)
    ap.add_argument("--insight-root", required=True)
    ap.add_argument("--step", type=int, default=3, help="OCR抽样步长(全片=1)")
    args = ap.parse_args()

    ocr = RapidOCR()
    cap = cv2.VideoCapture(args.video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 换脸覆盖统计（来自阶段1 bbox 记录）
    if args.bbox and os.path.exists(args.bbox):
        bb = json.load(open(args.bbox, encoding="utf-8"))
        bbs = bb["bboxes"]
        n = len(bbs)
        swapped = sum(1 for b in bbs if b is not None)
        right_swapped = sum(1 for b in bbs if b is not None and (b[0] + b[2]) / 2 > W * 0.5)
        print(f"[换脸统计] 总帧={n} 已换脸={swapped} 其中右侧换脸={right_swapped} 跳过(无右侧脸)={n - swapped}",
              flush=True)

    # 水印残留抽样 OCR
    residue = []
    i = 0
    sampled = 0
    while i < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2))
        res, _ = ocr(small)
        if res:
            for box, text, _score in res:
                if hit(text):
                    residue.append(i)
                    break
        sampled += 1
        i += args.step
    cap.release()
    rate = len(residue) / sampled if sampled else 0
    print(f"[视频] {W}x{H} {fps:.2f}fps 总帧{total}", flush=True)
    print(f"[水印残留] 抽{sampled}帧, 含抖音残留{len(residue)}帧, 残留率{rate:.1%}", flush=True)
    print(f"[残留帧号(前30)] {residue[:30]}", flush=True)
    if rate > 0.02:
        print("⚠️ 残留率偏高(>2%), 建议增强去水印或全片复查", flush=True)
    else:
        print("✅ 抖音水印残留可控", flush=True)


if __name__ == "__main__":
    main()
