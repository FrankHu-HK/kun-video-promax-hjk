# -*- coding: utf-8 -*-
"""
抖音录屏videoface swap：保留原video动作/background/音乐，仅把最大人脸替换为target/goal照片。
用法见 SKILL.md stage 1。
dependency: insightface, onnxruntime, opencv-python, numpy

error码体系（E200 系列）：
  E200 = 照片does not exist或无法read
  E201 = 照片中未检测到人脸
  E202 = video无法open或已损坏
  E203 = modelloadfailed（inswapper/buffalo_l 缺失）
  E204 = frameprocessexception（单framefailed→保持原frame，不interrupt整体）
  E205 = outputvideowritefailed
"""
import os, json, argparse, tempfile, shutil, sys, time, subprocess
import cv2
import numpy as np

# error码
ERROR_CODES = {
    "E200": "照片does not exist或无法read",
    "E201": "照片中未检测到人脸",
    "E202": "video无法open或已损坏",
    "E203": "modelloadfailed（inswapper/buffalo_l 缺失）",
    "E204": "frameprocessexception（单framefailed→保持原frame）",
    "E205": "outputvideowritefailed",
}

# retryconfig
MAX_RETRIES = 2
RETRY_DELAY = 2  # 秒


def eprint(msg, code=None):
    """统一erroroutputformat"""
    if code:
        print(f"❌ [{code}] {msg}", flush=True)
    else:
        print(f"❌ {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="源video(含原动作/background)")
    ap.add_argument("--photo", required=True, help="target/goal人脸照片(suggestion先copy为ASCII名)")
    ap.add_argument("--out", default="swapped_raw.mp4", help="face swap后outputvideo")
    ap.add_argument("--bbox", default="face_bboxes.json", help="人脸框recordjson")
    ap.add_argument("--models-dir", default="models", help="含 inswapper_128.onnx 的directory")
    ap.add_argument("--insight-root", default=".insightface", help="含 models/buffalo_l 的根directory")
    ap.add_argument("--det-size", default=640, type=int)
    ap.add_argument("--target-side", default="right",
                    choices=["right", "left", "largest"],
                    help="face swaptarget/goal: right=右侧最大脸, left=左侧最大脸, largest=全局最大脸")
    ap.add_argument("--retry", type=int, default=MAX_RETRIES,
                    help=f"遇到可recovererror时retry次数（默认={MAX_RETRIES}）")
    ap.add_argument("--progress", default=None,
                    help="progressrecordfile（用于断点续跑·规划中）")
    args = ap.parse_args()

    # 1. verifyinputfile
    if not os.path.exists(args.photo):
        eprint(f"照片does not exist: {args.photo}", "E200")
        sys.exit(1)
    if not os.path.exists(args.video):
        eprint(f"videodoes not exist: {args.video}", "E202")
        sys.exit(1)

    # 中文path兜底
    photo = args.photo
    tmp_photo = None
    try:
        photo.encode("ascii")
    except UnicodeEncodeError:
        tmp_photo = os.path.join(tempfile.gettempdir(), "user_photo_tmp.jpg")
        shutil.copy(photo, tmp_photo)
        photo = tmp_photo

    # 2. loadmodel（带retry）
    import insightface
    from insightface.app import FaceAnalysis

    app = None
    swapper = None
    for attempt in range(1, args.retry + 2):
        try:
            print(f"[1/4] load人脸分析model(buffalo_l)...", flush=True)
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
                print(f"⚠️ modelloadfailed（尝试 {attempt}/{args.retry+1}）: {e}", flush=True)
                print(f"   wait {RETRY_DELAY}s 后retry...", flush=True)
                time.sleep(RETRY_DELAY)
            else:
                eprint(f"modelloadfailed（{args.retry+1} 次尝试均failed）: {e}", "E203")
                sys.exit(1)
    if app is None or swapper is None:
        eprint("model未successload", "E203")
        sys.exit(1)

    # 3. extracttarget/goal照片人脸
    print(f"[3/4] extracttarget/goal照片人脸feature...", flush=True)
    user_img = cv2.imread(photo)
    if user_img is None:
        eprint(f"无法read照片(path/decode问题): {args.photo}", "E200")
        sys.exit(1)
    user_faces = app.get(user_img)
    if not user_faces:
        eprint("照片中未检测到人脸", "E201")
        sys.exit(1)
    source_face = sorted(user_faces, key=lambda f: f.bbox[2] - f.bbox[0])[-1]
    print(f"  target/goal人脸框: {[int(v) for v in source_face.bbox]}", flush=True)

    # 4. 逐frameface swap（带frame级exception捕获 + 网络/format自动转码 v2.2.0）
    print(f"[4/4] 逐frameface swap...", flush=True)
    # v2.2.0 自动formatprocess：网络/formatexception时自动调 auto_format.py 转码
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        eprint(f"video无法直接open（{args.video}），自动调用 auto_format.py 转码...", "E202")
        auto_format_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_format.py")
        if os.path.exists(auto_format_script):
            std_path = os.path.splitext(args.video)[0] + "_std.mp4"
            r = subprocess.run(
                ["python", auto_format_script, "--input", args.video, "--output", std_path],
                capture_output=True, timeout=1800,
            )
            if r.returncode == 0 and os.path.exists(std_path):
                print(f"  ✅ 自动转码success: {std_path}", flush=True)
                args.video = std_path
                cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            eprint(f"video无法open: {args.video}", "E202")
            sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  源: {w}x{h}, {fps:.2f}fps, {total} frame", flush=True)

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
            # 单framefailed → 保持原frame，不interrupt整体（对应 E204）
            skip_count += 1
            bboxes.append(None)
            if skip_count == 1:
                print(f"  ⚠️ [E204] 第 {idx+1} frameprocessexception: {e}（保持原framecontinue）", flush=True)
                print(f"    后续frameexception将静默process，最终汇总报告skipframe数", flush=True)

        vw.write(frame)
        idx += 1
        if idx % 30 == 0:
            print(f"  progress {idx}/{total} ({idx*100//total}%)", flush=True)

    cap.release()
    vw.release()

    with open(args.bbox, "w") as f:
        json.dump({"w": w, "h": h, "bboxes": bboxes}, f)

    print(f"DONE -> {args.out} ; 人脸框 -> {args.bbox}", flush=True)
    if skip_count > 0:
        print(f"⚠️ skip {skip_count}/{idx} frame（E204·保持原frame）", flush=True)

    if tmp_photo and os.path.exists(tmp_photo):
        os.remove(tmp_photo)


if __name__ == "__main__":
    main()
