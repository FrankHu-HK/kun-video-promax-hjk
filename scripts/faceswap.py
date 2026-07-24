# -*- coding: utf-8 -*-
"""
videoface swap：video/background/，target/goal。
 SKILL.md stage 1。
dependency: insightface, onnxruntime, opencv-python, numpy

error（E200 ）：
  E200 = does not existread
  E201 = 
  E202 = videoopen
  E203 = modelloadfailed（inswapper/buffalo_l ）
  E204 = frameprocessexception（framefailed→frame，interrupt）
  E205 = outputvideowritefailed
"""
import os, json, argparse, tempfile, shutil, sys, time, subprocess
import cv2
import numpy as np

# error
ERROR_CODES = {
    "E200": "does not existread",
    "E201": "",
    "E202": "videoopen",
    "E203": "modelloadfailed（inswapper/buffalo_l ）",
    "E204": "frameprocessexception（framefailed→frame）",
    "E205": "outputvideowritefailed",
}

# retryconfig
MAX_RETRIES = 2
RETRY_DELAY = 2  # 


def eprint(msg, code=None):
    """erroroutputformat"""
    if code:
        print(f"❌ [{code}] {msg}", flush=True)
    else:
        print(f"❌ {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="video(/background)")
    ap.add_argument("--photo", required=True, help="target/goal(suggestioncopyASCII)")
    ap.add_argument("--out", default="swapped_raw.mp4", help="face swapoutputvideo")
    ap.add_argument("--bbox", default="face_bboxes.json", help="recordjson")
    ap.add_argument("--models-dir", default="models", help=" inswapper_128.onnx directory")
    ap.add_argument("--insight-root", default=".insightface", help=" models/buffalo_l directory")
    ap.add_argument("--det-size", default=640, type=int)
    ap.add_argument("--target-side", default="right",
                    choices=["right", "left", "largest"],
                    help="face swaptarget/goal: right=, left=, largest=")
    ap.add_argument("--retry", type=int, default=MAX_RETRIES,
                    help=f"recovererrorretry（={MAX_RETRIES}）")
    ap.add_argument("--progress", default=None,
                    help="progressrecordfile（·）")
    args = ap.parse_args()

    # 1. verifyinputfile
    if not os.path.exists(args.photo):
        eprint(f"does not exist: {args.photo}", "E200")
        sys.exit(1)
    if not os.path.exists(args.video):
        eprint(f"videodoes not exist: {args.video}", "E202")
        sys.exit(1)

    # path
    photo = args.photo
    tmp_photo = None
    try:
        photo.encode("ascii")
    except UnicodeEncodeError:
        tmp_photo = os.path.join(tempfile.gettempdir(), "user_photo_tmp.jpg")
        shutil.copy(photo, tmp_photo)
        photo = tmp_photo

    # 2. loadmodel（retry）
    import insightface
    from insightface.app import FaceAnalysis

    app = None
    swapper = None
    for attempt in range(1, args.retry + 2):
        try:
            print(f"[1/4] loadmodel(buffalo_l)...", flush=True)
            app = FaceAnalysis(name="buffalo_l", root=os.path.abspath(args.insight_root),
                               providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(args.det_size, args.det_size))
            for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:
                app.models.pop(_k, None)

            print(f"[2/4] load inswapper_128 face swapmodel...", flush=True)
            swapper = insightface.model_zoo.get_model(
                os.path.join(args.models_dir, "inswapper_128.onnx"),
                download=False, download_zip=False, providers=["CPUExecutionProvider"])
            break
        except Exception as e:
            if attempt <= args.retry:
                print(f"⚠️ modelloadfailed（ {attempt}/{args.retry+1}）: {e}", flush=True)
                print(f"   wait {RETRY_DELAY}s retry...", flush=True)
                time.sleep(RETRY_DELAY)
            else:
                eprint(f"modelloadfailed（{args.retry+1} failed）: {e}", "E203")
                sys.exit(1)
    if app is None or swapper is None:
        eprint("modelsuccessload", "E203")
        sys.exit(1)

    # 3. extracttarget/goal
    print(f"[3/4] extracttarget/goalfeature...", flush=True)
    user_img = cv2.imread(photo)
    if user_img is None:
        eprint(f"read(path/decode): {args.photo}", "E200")
        sys.exit(1)
    user_faces = app.get(user_img)
    if not user_faces:
        eprint("", "E201")
        sys.exit(1)
    source_face = sorted(user_faces, key=lambda f: f.bbox[2] - f.bbox[0])[-1]
    print(f"  target/goal: {[int(v) for v in source_face.bbox]}", flush=True)

    # 4. frameface swap（frameexception + /format v2.2.0）
    print(f"[4/4] frameface swap...", flush=True)
    # v2.2.0 formatprocess：/formatexception auto_format.py 
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        eprint(f"videoopen（{args.video}）， auto_format.py ...", "E202")
        auto_format_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_format.py")
        if os.path.exists(auto_format_script):
            std_path = os.path.splitext(args.video)[0] + "_std.mp4"
            r = subprocess.run(
                ["python", auto_format_script, "--input", args.video, "--output", std_path],
                capture_output=True, timeout=1800,
            )
            if r.returncode == 0 and os.path.exists(std_path):
                print(f"  ✅ success: {std_path}", flush=True)
                args.video = std_path
                cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            eprint(f"videoopen: {args.video}", "E202")
            sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  : {w}x{h}, {fps:.2f}fps, {total} frame", flush=True)

    try:
        vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    except Exception as e:
        eprint(f"outputvideoinitializefailed: {e}", "E205")
        sys.exit(1)

    bboxes = []
    idx = 0
    skip_count = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        try:
            faces = app.get(frame)
            target = None
            if faces:
                if args.target_side == "largest":
                    target = max(faces, key=lambda f: f.bbox[2] - f.bbox[0])
                elif args.target_side == "right":
                    target = max(faces, key=lambda f: (f.bbox[0] + f.bbox[2]) / 2) if len(faces) >= 2 else None
                else:  # left
                    lefts = [f for f in faces if (f.bbox[0] + f.bbox[2]) / 2 < w * 0.5]
                    target = max(lefts, key=lambda f: f.bbox[2] - f.bbox[0]) if lefts else None
            if target is not None:
                frame = swapper.get(frame, target, source_face, paste_back=True)
                bboxes.append([int(v) for v in target.bbox])
            else:
                bboxes.append(None)
        except Exception as e:
            # framefailed → frame，interrupt（ E204）
            skip_count += 1
            bboxes.append(None)
            if skip_count == 1:
                print(f"  ⚠️ [E204]  {idx+1} frameprocessexception: {e}（framecontinue）", flush=True)
                print(f"    frameexceptionprocess，skipframe", flush=True)

        vw.write(frame)
        idx += 1
        if idx % 30 == 0:
            print(f"  progress {idx}/{total} ({idx*100//total}%)", flush=True)

    cap.release()
    vw.release()

    with open(args.bbox, "w") as f:
        json.dump({"w": w, "h": h, "bboxes": bboxes}, f)

    print(f"DONE -> {args.out} ;  -> {args.bbox}", flush=True)
    if skip_count > 0:
        print(f"⚠️ skip {skip_count}/{idx} frame（E204·frame）", flush=True)

    if tmp_photo and os.path.exists(tmp_photo):
        os.remove(tmp_photo)


if __name__ == "__main__":
    main()
