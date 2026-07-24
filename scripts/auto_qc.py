#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""

auto_qc.py - Workflow B generatevideo



:"check""check",retry.

(file//frame/encode/),user.

dependency:opencv-python, numpy( imageio-ffmpeg  ffmpeg, opencv frame)



exit:0=pass/succeed,1=pass/succeed(retry)

"""



import sys

import json

import argparse



import numpy as np

import cv2





def qc(video_path, expect_duration=None, black_thresh=12.0,

       still_diff_thresh=0.5, sample_step=3):

    """, dict(exception,write issues)."""

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

        rep["issues"].append("openvideo(encode/file/pathASCII)")

        return rep

    rep["opened"] = True



    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    rep["fps"] = round(fps, 2)

    rep["frame_count"] = total

    if total <= 0:

        rep["issues"].append("frame0(video/generatefailed)")

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



    # 

    if rep["black_frame_ratio"] > 0.3:

        rep["issues"].append("aspect ratio %.2f(>0.3,generate)" % rep["black_frame_ratio"])

    if rep["still_frame_ratio"] > 0.8:

        rep["issues"].append("frameaspect ratio %.2f(>0.8,generate/)" % rep["still_frame_ratio"])

    if expect_duration is not None and rep["duration_sec"] > 0:

        deviation = abs(rep["duration_sec"] - expect_duration) / expect_duration

        if deviation > 0.3:

            rep["issues"].append(

                " %.2fs/%.2fs(>30%%)" % (rep["duration_sec"], expect_duration))



    rep["ok"] = len(rep["issues"]) == 0

    return rep





def main():

    ap = argparse.ArgumentParser(description="Workflow B generatevideo")

    ap.add_argument("--video", required=True, help="videopath")

    ap.add_argument("--expect-duration", type=float, default=None,

                    help="(),()")

    ap.add_argument("--black-thresh", type=float, default=12.0,

                    help="(0-255 brightness,,12)")

    ap.add_argument("--still-diff-thresh", type=float, default=0.5,

                    help="frame(frame,frame,0.5,)")

    ap.add_argument("--sample-step", type=int, default=3,

                    help="frame,3frame1frame")

    ap.add_argument("--out", default=None, help="JSONoutputpath()")

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

