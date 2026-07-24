# -*- coding: utf-8 -*-
"""
stage2.5 兜底：固定区域 inpaint 去除平台级固定 logo（如右下角"抖音"角标）。
技能 SKILL.md 原引用了本file但实际缺失，此处按相同语义实现并install到技能directory。
用法:
  python fix_logo.py --input swapped_clean.mp4 --output swapped_clean_v2.mp4 \
      --region 1100 1190 595 715 --radius 10
  region parameter顺序: y0 y1 x0 x1 (含余量)
dependency: opencv-python, numpy
"""
import cv2, numpy as np, argparse, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--region", nargs=4, type=int, required=True,
                    metavar=("y0", "y1", "x0", "x1"))
    ap.add_argument("--radius", type=int, default=10)
    args = ap.parse_args()

    y0, y1, x0, x1 = args.region
    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # 钳制到画面范围
    y0, y1 = max(0, y0), min(H, y1)
    x0, x1 = max(0, x0), min(W, x1)
    vw = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    t0 = time.time()
    for i in range(total):
        ok, frame = cap.read()
        if not ok:
            break
        mask = np.zeros((H, W), np.uint8)
        mask[y0:y1, x0:x1] = 255
        frame = cv2.inpaint(frame, mask, args.radius, cv2.INPAINT_TELEA)
        vw.write(frame)
        if (i + 1) % 100 == 0:
            print(f"[{i+1}/{total}] {time.time()-t0:.0f}s", flush=True)
    cap.release(); vw.release()
    print(f"DONE {args.output} 区域 y[{y0},{y1}] x[{x0},{x1}] 用时{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
