# -*- coding: utf-8 -*-
"""
对成品video做 OCR 全片复核，confirm无 AI/generate 字样残留。用法见 SKILL.md stage 4。
返回 0 残留则合格。dependency: opencv-python, numpy, rapidocr-onnxruntime
"""
import cv2, argparse
from rapidocr_onnxruntime import RapidOCR

KEYWORDS = ("AI", "generate", "A1", "A I", "A.I")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--step", type=int, default=10, help="抽样步长(越小越严)")
    args = ap.parse_args()

    ocr = RapidOCR()
    cap = cv2.VideoCapture(args.video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("成品总frame数", total)
    hits, fi = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if fi % args.step == 0:
            h0, w0 = frame.shape[:2]
            small = cv2.resize(frame, (int(w0 * 0.5), int(h0 * 0.5)))
            res, _ = ocr(small)
            if res:
                for box, text, _s in res:
                    t = text.upper()
                    if any(k.upper() in t for k in KEYWORDS):
                        hits.append((fi, text))
                        print(f"残留 frame{fi:4d} \"{text}\"")
        fi += 1
    cap.release()
    print("=== 成品残留命中:", len(hits))
    if not hits:
        print("✅ 成品已无 AI/generate 字样残留")
    else:
        print("❌ 仍有残留，需回到stage 2 调整区域/关键字")


if __name__ == "__main__":
    main()
