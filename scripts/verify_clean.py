# -*- coding: utf-8 -*-

"""

video OCR ,confirm AI/generate . SKILL.md stage 4.

 0 .dependency: opencv-python, numpy, rapidocr-onnxruntime

"""

import cv2, argparse

from rapidocr_onnxruntime import RapidOCR



KEYWORDS = ("AI", "generate", "A1", "A I", "A.I")





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--video", required=True)

    ap.add_argument("--step", type=int, default=10, help="()")

    args = ap.parse_args()



    ocr = RapidOCR()

    cap = cv2.VideoCapture(args.video)

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("frame", total)

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

                        print(f" frame{fi:4d} \"{text}\"")

        fi += 1

    cap.release()

    print("=== :", len(hits))

    if not hits:

        print("✅  AI/generate ")

    else:

        print("❌ ,stage 2 /")





if __name__ == "__main__":

    main()

