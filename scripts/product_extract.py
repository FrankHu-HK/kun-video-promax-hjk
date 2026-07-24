#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""

product_extract.py - Workflow C (AI real-person talking-head / e-commerce product demo), C1 stage: extract frames.



The user uploads a video; this script clears and selects the best frames:

  1) composite (real, logo / 100% overlay);

  2) generate a reference (Seedance / Kling style).



Runs on opencv + numpy.



score / rating:

  - clarity: Laplacian variance (low = blurry frame)

  - brightness: mean pixel value (0-255)



output:

  - product_ref_XX.jpg (ASCII filename, model input)

  - product_manifest.json (score / rating / frame / time)



usage:

  python product_extract.py \

    --video product_raw.mp4 \

    --out-dir product_refs \

    --top 6 \

    --min-sharp 60 \

    --bright-lo 40 --bright-hi 220



warning: cv2.imread / VideoCapture require ASCII paths; keep the source video filename ASCII.

"""

import argparse

import json

import os

import sys



import cv2

import numpy as np





def compute_sharpness(gray):

    """Laplacian clear,."""

    return float(cv2.Laplacian(gray, cv2.CV_64F).var())





def compute_brightness(gray):

    """brightness(0-255)."""

    return float(gray.mean())





def hist_signature(frame, bins=32):

    """ HSV ,()."""

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    hist = cv2.calcHist([hsv], [0, 1], None, [bins, bins], [0, 180, 0, 256])

    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

    return hist.flatten()





def hist_similarity(a, b):

    """,1=."""

    return float(cv2.compareHist(

        a.reshape(-1, 1).astype("float32"),

        b.reshape(-1, 1).astype("float32"),

        cv2.HISTCMP_CORREL,

    ))





def main():

    ap = argparse.ArgumentParser(description="videoextractclear/")

    ap.add_argument("--video", required=True, help="video(ASCII path)")

    ap.add_argument("--out-dir", required=True, help="outputdirectory( + manifest)")

    ap.add_argument("--top", type=int, default=6, help="")

    ap.add_argument("--sample-step", type=int, default=3, help=" N frame")

    ap.add_argument("--min-sharp", type=float, default=60.0, help="clear(Laplacian )")

    ap.add_argument("--bright-lo", type=float, default=40.0, help="brightness()")

    ap.add_argument("--bright-hi", type=float, default=220.0, help="brightness()")

    ap.add_argument("--dup-thresh", type=float, default=0.85,

                    help=":>,clear")

    args = ap.parse_args()



    if not os.path.isfile(args.video):

        print(f"[ERR] videodoes not exist: {args.video}", file=sys.stderr)

        sys.exit(2)

    # ASCII pathcheck(cv2 pathfailed)

    try:

        args.video.encode("ascii")

    except UnicodeEncodeError:

        print(f"[ERR] videopath ASCII ,cv2 readfailed,copy: {args.video}",

              file=sys.stderr)

        sys.exit(2)



    os.makedirs(args.out_dir, exist_ok=True)



    cap = cv2.VideoCapture(args.video)

    if not cap.isOpened():

        print(f"[ERR] openvideo: {args.video}", file=sys.stderr)

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

        # /clear

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

        print("[ERR] frame(video//blurry)."

              " --min-sharp  --bright retry.", file=sys.stderr)

        sys.exit(1)



    # clear,"" top-N

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



    #  top(),clearframe

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



    print(f"[OK] frame {len(candidates)} →  {len(picked)} ")

    for r in manifest["refs"]:

        print(f"  {r['file']}  frame#{r['src_frame']}  t={r['timestamp']}s  "

              f"={r['sharpness']}  brightness={r['brightness']}")

    print(f"[OK] manifest: {mpath}")

    print("[TIP] [label/logo clear] 1-2 composite;"

          ".")





if __name__ == "__main__":

    main()

