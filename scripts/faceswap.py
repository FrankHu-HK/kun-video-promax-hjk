# -*- coding: utf-8 -*-
"""
抖音录屏视频换脸：保留原视频动作/背景/音乐，仅把最大人脸替换为目标照片。
用法见 SKILL.md 阶段 1。
依赖: insightface, onnxruntime, opencv-python, numpy

错误码体系（E200 系列）：
  E200 = 照片不存在或无法读取
  E201 = 照片中未检测到人脸
  E202 = 视频无法打开或已损坏
  E203 = 模型加载失败（inswapper/buffalo_l 缺失）
  E204 = 帧处理异常（单帧失败→保持原帧，不中断整体）
  E205 = 输出视频写入失败
"""
import os, json, argparse, tempfile, shutil, sys, time, subprocess
import cv2
import numpy as np

# 错误码
ERROR_CODES = {
    "E200": "照片不存在或无法读取",
    "E201": "照片中未检测到人脸",
    "E202": "视频无法打开或已损坏",
    "E203": "模型加载失败（inswapper/buffalo_l 缺失）",
    "E204": "帧处理异常（单帧失败→保持原帧）",
    "E205": "输出视频写入失败",
}

# 重试配置
MAX_RETRIES = 2
RETRY_DELAY = 2  # 秒


def eprint(msg, code=None):
    """统一错误输出格式"""
    if code:
        print(f"❌ [{code}] {msg}", flush=True)
    else:
        print(f"❌ {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="源视频(含原动作/背景)")
    ap.add_argument("--photo", required=True, help="目标人脸照片(建议先复制为ASCII名)")
    ap.add_argument("--out", default="swapped_raw.mp4", help="换脸后输出视频")
    ap.add_argument("--bbox", default="face_bboxes.json", help="人脸框记录json")
    ap.add_argument("--models-dir", default="models", help="含 inswapper_128.onnx 的目录")
    ap.add_argument("--insight-root", default=".insightface", help="含 models/buffalo_l 的根目录")
    ap.add_argument("--det-size", default=640, type=int)
    ap.add_argument("--target-side", default="right",
                    choices=["right", "left", "largest"],
                    help="换脸目标: right=右侧最大脸, left=左侧最大脸, largest=全局最大脸")
    ap.add_argument("--retry", type=int, default=MAX_RETRIES,
                    help=f"遇到可恢复错误时重试次数（默认={MAX_RETRIES}）")
    ap.add_argument("--progress", default=None,
                    help="进度记录文件（用于断点续跑·规划中）")
    args = ap.parse_args()

    # 1. 验证输入文件
    if not os.path.exists(args.photo):
        eprint(f"照片不存在: {args.photo}", "E200")
        sys.exit(1)
    if not os.path.exists(args.video):
        eprint(f"视频不存在: {args.video}", "E202")
        sys.exit(1)

    # 中文路径兜底
    photo = args.photo
    tmp_photo = None
    try:
        photo.encode("ascii")
    except UnicodeEncodeError:
        tmp_photo = os.path.join(tempfile.gettempdir(), "user_photo_tmp.jpg")
        shutil.copy(photo, tmp_photo)
        photo = tmp_photo

    # 2. 加载模型（带重试）
    import insightface
    from insightface.app import FaceAnalysis

    app = None
    swapper = None
    for attempt in range(1, args.retry + 2):
        try:
            print(f"[1/4] 加载人脸分析模型(buffalo_l)...", flush=True)
            app = FaceAnalysis(name="buffalo_l", root=os.path.abspath(args.insight_root),
                               providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(args.det_size, args.det_size))
            for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:
                app.models.pop(_k, None)

            print(f"[2/4] 加载 inswapper_128 换脸模型...", flush=True)
            swapper = insightface.model_zoo.get_model(
                os.path.join(args.models_dir, "inswapper_128.onnx"),
                download=False, download_zip=False, providers=["CPUExecutionProvider"])
            break
        except Exception as e:
            if attempt <= args.retry:
                print(f"⚠️ 模型加载失败（尝试 {attempt}/{args.retry+1}）: {e}", flush=True)
                print(f"   等待 {RETRY_DELAY}s 后重试...", flush=True)
                time.sleep(RETRY_DELAY)
            else:
                eprint(f"模型加载失败（{args.retry+1} 次尝试均失败）: {e}", "E203")
                sys.exit(1)
    if app is None or swapper is None:
        eprint("模型未成功加载", "E203")
        sys.exit(1)

    # 3. 提取目标照片人脸
    print(f"[3/4] 提取目标照片人脸特征...", flush=True)
    user_img = cv2.imread(photo)
    if user_img is None:
        eprint(f"无法读取照片(路径/解码问题): {args.photo}", "E200")
        sys.exit(1)
    user_faces = app.get(user_img)
    if not user_faces:
        eprint("照片中未检测到人脸", "E201")
        sys.exit(1)
    source_face = sorted(user_faces, key=lambda f: f.bbox[2] - f.bbox[0])[-1]
    print(f"  目标人脸框: {[int(v) for v in source_face.bbox]}", flush=True)

    # 4. 逐帧换脸（带帧级异常捕获 + 网络/格式自动转码 v2.2.0）
    print(f"[4/4] 逐帧换脸...", flush=True)
    # v2.2.0 自动格式处理：网络/格式异常时自动调 auto_format.py 转码
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        eprint(f"视频无法直接打开（{args.video}），自动调用 auto_format.py 转码...", "E202")
        auto_format_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_format.py")
        if os.path.exists(auto_format_script):
            std_path = os.path.splitext(args.video)[0] + "_std.mp4"
            r = subprocess.run(
                ["python", auto_format_script, "--input", args.video, "--output", std_path],
                capture_output=True, timeout=1800,
            )
            if r.returncode == 0 and os.path.exists(std_path):
                print(f"  ✅ 自动转码成功: {std_path}", flush=True)
                args.video = std_path
                cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            eprint(f"视频无法打开: {args.video}", "E202")
            sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  源: {w}x{h}, {fps:.2f}fps, {total} 帧", flush=True)

    try:
        vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    except Exception as e:
        eprint(f"输出视频初始化失败: {e}", "E205")
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
            # 单帧失败 → 保持原帧，不中断整体（对应 E204）
            skip_count += 1
            bboxes.append(None)
            if skip_count == 1:
                print(f"  ⚠️ [E204] 第 {idx+1} 帧处理异常: {e}（保持原帧继续）", flush=True)
                print(f"    后续帧异常将静默处理，最终汇总报告跳过帧数", flush=True)

        vw.write(frame)
        idx += 1
        if idx % 30 == 0:
            print(f"  进度 {idx}/{total} ({idx*100//total}%)", flush=True)

    cap.release()
    vw.release()

    with open(args.bbox, "w") as f:
        json.dump({"w": w, "h": h, "bboxes": bboxes}, f)

    print(f"DONE -> {args.out} ; 人脸框 -> {args.bbox}", flush=True)
    if skip_count > 0:
        print(f"⚠️ 跳过 {skip_count}/{idx} 帧（E204·保持原帧）", flush=True)

    if tmp_photo and os.path.exists(tmp_photo):
        os.remove(tmp_photo)


if __name__ == "__main__":
    main()
