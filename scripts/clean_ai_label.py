# -*- coding: utf-8 -*-
"""
frame OCR  AI/generate  ->  inpaint （background）。
 SKILL.md stage 2。dependency: opencv-python, numpy, rapidocr-onnxruntime
"""
import cv2, numpy as np, argparse, time
from rapidocr_onnxruntime import RapidOCR

# （ AI ）
KEYWORDS = ("AI", "generate", "A1", "A I", "A.I", "A｜", "AIgenerate")


def hit(text):
    t = text.upper()
    return any(k.upper() in t for k in KEYWORDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="swapped_clean.mp4")
    # : --region y0 y1 x0 x1 (frame)
    ap.add_argument("--region", nargs=4, type=int, default=None,
                    metavar=("Y0", "Y1", "X0", "X1"))
    ap.add_argument("--radius", type=int, default=6)
    args = ap.parse_args()

    ocr = RapidOCR()
    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vw = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    # (frame)；frame
    if args.region:
        sy0, sy1, sx0, sx1 = args.region
    else:
        sy0, sy1, sx0, sx1 = 0, H, 0, W

    t0 = time.time()
    repaired = 0
    for i in range(total):
        ok, frame = cap.read()
        if not ok:
            break
        roi = frame[sy0:sy1, sx0:sx1].copy()
        rh, rw = roi.shape[:2]
        # resize 2x  OCR 
        small = cv2.resize(roi, (rw * 2, rh * 2))
        res, _ = ocr(small)
        mask = np.zeros((rh, rw), np.uint8)
        if res:
            for box, text, _score in res:
                if hit(text):
                    xs = [p[0] / 2 for p in box]   # small->roi
                    ys = [p[1] / 2 for p in box]
                    x0 = max(0, int(min(xs)) - 8)
                    y0 = max(0, int(min(ys)) - 8)
                    x1 = min(rw, int(max(xs)) + 8)
                    y1 = min(rh, int(max(ys)) + 8)
                    mask[y0:y1, x0:x1] = 255
        if mask.sum() > 0:
            inp = cv2.inpaint(roi, mask, args.radius, cv2.INPAINT_TELEA)
            frame[sy0:sy1, sx0:sx1] = inp
            repaired += 1
        vw.write(frame)
        if (i + 1) % 300 == 0:
            print(f"[{i+1}/{total}] {time.time()-t0:.0f}s {repaired}", flush=True)
    cap.release(); vw.release()
    print(f"DONE {args.output} frame={repaired} {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
