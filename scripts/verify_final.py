# -*- coding: utf-8 -*-
"""stage4 verify： OCR  + face swap。
: verify_final.py --video video --bbox stage1face_bboxes.json --models-dir ... --insight-root ...
"""
import os, json, argparse
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

KEYWORDS = ("", "CallmeSJ", "SJ", "Call me", "AI", "generate", "A1", "A I", "A.I", "A｜", "AIgenerate")


def hit(text):
    t = text.upper()
    return any(k.upper() in t for k in KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--bbox", default=None, help="stage1 face_bboxes.json")
    ap.add_argument("--models-dir", required=True)
    ap.add_argument("--insight-root", required=True)
    ap.add_argument("--step", type=int, default=3, help="OCR(=1)")
    args = ap.parse_args()

    ocr = RapidOCR()
    cap = cv2.VideoCapture(args.video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # face swap（stage1 bbox record）
    if args.bbox and os.path.exists(args.bbox):
        bb = json.load(open(args.bbox, encoding="utf-8"))
        bbs = bb["bboxes"]
        n = len(bbs)
        swapped = sum(1 for b in bbs if b is not None)
        right_swapped = sum(1 for b in bbs if b is not None and (b[0] + b[2]) / 2 > W * 0.5)
        print(f"[face swap] frame={n} face swap={swapped} face swap={right_swapped} skip()={n - swapped}",
              flush=True)

    #  OCR
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
    print(f"[video] {W}x{H} {fps:.2f}fps frame{total}", flush=True)
    print(f"[] {sampled}frame, {len(residue)}frame, {rate:.1%}", flush=True)
    print(f"[frame(30)] {residue[:30]}", flush=True)
    if rate > 0.02:
        print("⚠️ (>2%), suggestionremove watermark", flush=True)
    else:
        print("✅ ", flush=True)


if __name__ == "__main__":
    main()
