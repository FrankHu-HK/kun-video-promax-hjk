# -*- coding: utf-8 -*-
"""
videoremove watermark（）：frame OCR ， inpaint 。
 clean_ai_label.py ：//AI，"AI/generate"。
dependency: opencv-python, numpy, rapidocr-onnxruntime
"""
import cv2, numpy as np, argparse, time
from rapidocr_onnxruntime import RapidOCR

# （OCR  @ detect Q，）
KEYWORDS = ("", "CallmeSJ", "SJ", "Call me", "AI", "generate", "A1", "A I", "A.I", "A｜", "AIgenerate")


def hit(text):
    t = text.upper()
    return any(k.upper() in t for k in KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="swapped_clean.mp4")
    ap.add_argument("--radius", type=int, default=8)
    ap.add_argument("--scale", type=int, default=2, help="OCR ()")
    args = ap.parse_args()

    ocr = RapidOCR()
    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vw = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    t0 = time.time()
    repaired = 0
    for i in range(total):
        ok, frame = cap.read()
        if not ok:
            break
        rh, rw = frame.shape[:2]
        small = cv2.resize(frame, (rw * args.scale, rh * args.scale))
        res, _ = ocr(small)
        mask = np.zeros((rh, rw), np.uint8)
        if res:
            for box, text, _score in res:
                if hit(text):
                    xs = [p[0] / args.scale for p in box]
                    ys = [p[1] / args.scale for p in box]
                    x0 = max(0, int(min(xs)) - 10)
                    y0 = max(0, int(min(ys)) - 10)
                    x1 = min(rw, int(max(xs)) + 10)
                    y1 = min(rh, int(max(ys)) + 10)
                    mask[y0:y1, x0:x1] = 255
        if mask.sum() > 0:
            inp = cv2.inpaint(frame, mask, args.radius, cv2.INPAINT_TELEA)
            frame = inp
            repaired += 1
        vw.write(frame)
        if (i + 1) % 50 == 0:
            print(f"[{i+1}/{total}] {time.time()-t0:.0f}s {repaired}", flush=True)
    cap.release(); vw.release()
    print(f"DONE {args.output} frame={repaired} {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
