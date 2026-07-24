# -*- coding: utf-8 -*-
"""
增强版换脸(faceswap_pro)——解决侧脸不换 / 转头遮挡露原脸问题。
相比 faceswap.py 的改进（v2.7.0 · 换脸质量层已落地 A+B + 网络/格式全自动 + 极端姿态诚实告警 + 分段自愈 + 输入预检）：
  —— 换脸质量层（A–F 编号，与下方"工程增强"是两条独立口径）——
  —— 换脸质量层（A–F 编号，与下方"工程增强"是两条独立口径）——
  ✅ 已落地 Layer A: 检测增强（det_size 1024 + det_thresh 0.3，侧脸/小脸更稳）
  ✅ 已落地 Layer B: 椭圆羽化融合（覆盖下巴/脸颊/侧颊 + 逐帧自适应遮挡，大幅减少"露原脸"）
  ⏳ 规划中 Layer C: 时序追踪（多帧 bbox 追踪 + 上一帧预测补帧）
  ⏳ 规划中 Layer D: 智能丢弃（质量差的检测结果自动丢弃）
  ⏳ 规划中 Layer E: 多脸防错（多人场景精准锁定目标侧）
  ⏳ 规划中 Layer F: 扩散兜底（输出帧自动质量评估 + 软羽化兜底）
  —— 工程增强（已落地，不占用 A–F 编号）：分段断点续跑/5预设/极端报告/自适应遮挡 ——
  v2.2.0 网络/格式全自动：网络/格式异常自动调用 auto_format.py 转码，无需用户手动
两种模式：
  --preview-out preview.png    只处理最侧脸的若干帧，输出 原图|旧版|新版 三栏对比图（不出视频）
  正常模式                      全量逐帧出视频 out.mp4 + bbox.json
工程增强：分段断点续跑(--resume，中断后从已完成段精准续跑)、分段自愈(拼接前校验损坏分段并原地重渲一次)、帧级异常容错、
  参数预设(--preset speed/quality/sideface/occlusion)、自适应遮挡融合、
  统一错误码(E100+)、Debug 日志(--debug)、单帧耗时监控(--frame-timeout)。
用法见 SKILL.md 阶段 1（增强）。
依赖: insightface, onnxruntime, opencv-python, numpy
"""
import os
import sys
import json
import time
import argparse
import tempfile
import shutil
import subprocess
import logging
import cv2
import numpy as np

# ============ 统一错误码（与 SKILL.md 异常处理协议呼应） ============
ERROR_CODES = {
    "E100": "照片读取失败（中文路径/文件损坏）",
    "E101": "照片中未检测到人脸",
    "E102": "模型文件缺失（inswapper_128.onnx / buffalo_l）",
    "E103": "视频文件无法打开（路径/编码问题）",
    "E104": "帧处理异常占比过高（源质量或模型异常）",
    "E105": "分段损坏自愈失败（源质量或磁盘异常，建议 --resume 重跑该段）",
}


def setup_logging(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def build_source_face(app, photo):
    # 中文路径兜底
    tmp_photo = None
    try:
        photo.encode("ascii")
    except UnicodeEncodeError:
        tmp_photo = os.path.join(tempfile.gettempdir(), "user_photo_tmp.jpg")
        shutil.copy(photo, tmp_photo)
        photo = tmp_photo
    img = cv2.imread(photo)
    if img is None:
        raise SystemExit("E100: 无法读取照片: " + photo)
    faces = app.get(img)
    if not faces:
        raise SystemExit("E101: 照片中未检测到人脸")
    src = sorted(faces, key=lambda f: f.bbox[2] - f.bbox[0])[-1]
    if tmp_photo and os.path.exists(tmp_photo):
        os.remove(tmp_photo)
    return src


def pick_target(faces, side, w):
    if not faces:
        return None
    if side == "largest":
        return max(faces, key=lambda f: f.bbox[2] - f.bbox[0])
    if side == "right":
        # 单人镜头（仅1张脸）回退到唯一人脸，避免整片不换脸；双人同框仍锁最右侧
        if len(faces) == 1:
            return faces[0]
        return max(faces, key=lambda f: (f.bbox[0] + f.bbox[2]) / 2)
    # left：单人回退唯一脸；多人取画面左半侧最宽脸
    if side == "left" and len(faces) == 1:
        return faces[0]
    lefts = [f for f in faces if (f.bbox[0] + f.bbox[2]) / 2 < w * 0.5]
    return max(lefts, key=lambda f: f.bbox[2] - f.bbox[0]) if lefts else None


def yaw_proxy(face):
    """用 5 点关键点估侧脸程度: 鼻尖相对两眼中点的横向偏移 / 眼距。越大越侧。"""
    kps = face.kps
    le, re, nose = kps[0], kps[1], kps[2]
    eye_mid_x = (le[0] + re[0]) / 2.0
    eye_dist = abs(re[0] - le[0]) + 1e-3
    return abs(nose[0] - eye_mid_x) / eye_dist


def enhanced_paste(swapper, frame, target, source_face, mask_scale, feather):
    """自定义放大羽化椭圆蒙版贴回，覆盖更大区域(侧脸/下巴/脸颊)。"""
    bgr_fake, M = swapper.get(frame, target, source_face, paste_back=False)
    S = bgr_fake.shape[0]  # 128
    h, w = frame.shape[:2]
    # 对齐空间(128)中构造覆盖大半张脸的椭圆
    mask = np.zeros((S, S), np.float32)
    cx, cy = S * 0.5, S * 0.52
    ax, ay = S * 0.46 * mask_scale, S * 0.60 * mask_scale
    cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 1.0, -1)
    IM = cv2.invertAffineTransform(M)
    fake_w = cv2.warpAffine(bgr_fake, IM, (w, h), borderValue=0.0)
    mask_w = cv2.warpAffine(mask, IM, (w, h), borderValue=0.0)
    # 羽化(按脸尺寸自适应)
    face_px = max(target.bbox[2] - target.bbox[0], 20)
    sigma = max(face_px * feather, 3)
    mask_w = cv2.GaussianBlur(mask_w, (0, 0), sigmaX=sigma, sigmaY=sigma)
    mask_w = np.clip(mask_w, 0, 1)[:, :, None]
    out = (mask_w * fake_w.astype(np.float32) + (1 - mask_w) * frame.astype(np.float32)).astype(np.uint8)
    return out


def make_app(insight_root, det_size, det_thresh):
    import insightface
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l", root=os.path.abspath(insight_root),
                       providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(det_size, det_size), det_thresh=det_thresh)
    for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:
        app.models.pop(_k, None)
    return app


def _load_progress(out_path):
    """读取断点续跑进度（已成功处理帧数）。"""
    prog = out_path + ".progress"
    if os.path.exists(prog):
        try:
            with open(prog) as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0
    return 0


def _save_progress(out_path, n):
    prog = out_path + ".progress"
    try:
        with open(prog, "w") as f:
            f.write(str(n))
    except Exception as e:
        logging.warning("进度写入失败(不影响主流程): %s", e)


# ============ v2.2.0 网络/格式自动处理 ============
def safe_open_video(video_path, workdir=None):
    """自动检测视频格式，必要时调用 auto_format.py 转码。
    网络/格式问题全自动处理，不再要求用户手动转码。

    返回 (VideoCapture, 实际打开的路径)。如果原本是标准 mp4(H.264)，
    原地打开；否则先转码到 workdir/<name>_std.mp4 再打开。
    """
    if not os.path.exists(video_path):
        raise SystemExit(f"E103: 视频文件不存在: {video_path}")
    # 1) 直接尝试打开
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        ok, frame = cap.read()
        if ok and frame is not None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            logging.info("  ✅ 视频已是标准格式，直接打开: %s", video_path)
            return cap, video_path
        cap.release()
    # 2) 自动转码
    logging.warning("  ⚠️ 视频无法直接打开（%s），自动调用 auto_format.py 转码", video_path)
    auto_format_script = os.path.join(os.path.dirname(__file__), "auto_format.py")
    if not os.path.exists(auto_format_script):
        raise SystemExit("E103: 视频无法打开且 auto_format.py 不存在，请手动用 ffmpeg 转码")
    out_dir = workdir or os.path.dirname(video_path) or "."
    base = os.path.splitext(os.path.basename(video_path))[0]
    std_path = os.path.join(out_dir, f"{base}_std.mp4")
    r = subprocess.run(
        ["python", auto_format_script, "--input", video_path, "--output", std_path],
        capture_output=True, timeout=1800,
    )
    if r.returncode != 0 or not os.path.exists(std_path):
        logging.error("  auto_format.py 转码失败:\n%s", (r.stderr or b"").decode("utf-8", errors="ignore")[:500])
        raise SystemExit(f"E103: 视频无法打开且自动转码失败: {video_path}")
    logging.info("  ✅ 自动转码成功: %s", std_path)
    cap = cv2.VideoCapture(std_path)
    if not cap.isOpened():
        raise SystemExit(f"E103: 转码后仍无法打开: {std_path}")
    return cap, std_path


def safe_open_cap_with_retry(video_path, workdir=None, max_retry=3):
    """带重试的安全打开（处理网络挂掉/格式异常）。"""
    last_err = None
    for attempt in range(max_retry):
        try:
            cap, used_path = safe_open_video(video_path, workdir)
            if cap.isOpened():
                return cap, used_path
        except SystemExit as e:
            last_err = str(e)
        logging.warning("  打开视频尝试 %d 失败: %s", attempt + 1, last_err)
        if attempt < max_retry - 1:
            import time as _t
            wait = 5 * (2 ** attempt)
            logging.info("  退避 %ds 后重试...", wait)
            _t.sleep(wait)
    raise SystemExit(f"E103: 视频无法打开（重试 {max_retry} 次）: {video_path}")


def _load_resume_state(path):
    """读取分段断点续跑状态（已完成段 + 每段的 bbox/统计）。"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                return {}
            return d
        except Exception:
            # 中断损坏的旧状态：丢弃，避免续跑误判"已全部完成"
            logging.warning("断点状态文件损坏，已忽略（将重新生成）: %s", path)
            return {}
    return {}


def _save_resume_state(path, state):
    try:
        # 原子写：先写临时文件再 os.replace，避免中途崩溃导致状态文件损坏丢失进度
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception as e:
        logging.warning("断点状态写入失败(不影响主流程): %s", e)


def concat_videos(seg_files, out_path, fps, w, h):
    """合并分段视频为成片（v2.6.0 自动愈合）：
    ① 先 ffmpeg 无损 copy（重试 2 次）② 失败则 ffmpeg 重新编码(libx264/aac，兼容异常分段)
    ③ 仍失败回退 cv2 逐帧重写。极端分段损坏也不再整段崩。"""
    seg_files = [s for s in seg_files if os.path.exists(s)]
    if not seg_files:
        return False
    ff = "ffmpeg"
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    def _write_list():
        list_path = out_path + ".concat.txt"
        with open(list_path, "w", encoding="utf-8") as f:
            for s in seg_files:
                f.write("file '%s'\n" % os.path.abspath(s).replace("\\", "/"))
        return list_path

    # ① 无损 copy，重试 2 次（应对偶发分段写入竞争）
    for attempt in range(2):
        list_path = _write_list()
        try:
            r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                                "-c", "copy", out_path], capture_output=True, timeout=900)
            if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                return True
        except Exception as e:
            logging.warning("  ffmpeg 拼接尝试 %d 失败: %s", attempt + 1, e)
        finally:
            try:
                os.remove(list_path)
            except Exception:
                pass
    # ② 重新编码（最稳，兼容异常/不完整分段）
    list_path = _write_list()
    try:
        r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
                            out_path], capture_output=True, timeout=1200)
        if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            logging.info("  ✅ ffmpeg 重新编码拼接成功（兼容异常分段）")
            return True
    except Exception as e:
        logging.warning("  ffmpeg 重新编码拼接失败: %s", e)
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass
    # ③ 回退 cv2 逐帧重写
    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for s in seg_files:
        c = cv2.VideoCapture(s)
        while True:
            ok, fr = c.read()
            if not ok:
                break
            vw.write(fr)
        c.release()
    vw.release()
    return os.path.exists(out_path)


def render_segment(cap, si, seg_frames, fps, w, h, app, swapper, args, source_face, max_yaw_in, skipped_in):
    """渲染单个分段(段 si)为 seg_xxx.mp4(+可选_trim)。主循环与分段自愈共用。
    返回各累计量 dict，调用方负责并入全局统计。"""
    seg_dir = args.out + ".segs"
    seg_base = os.path.join(seg_dir, "seg_%03d" % si)
    seg_file = seg_base + ".mp4"
    seg_trim_file = seg_base + "_trim.mp4"
    cap.set(cv2.CAP_PROP_POS_FRAMES, si * seg_frames)
    vw_seg = cv2.VideoWriter(seg_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    vw_seg_trim = None
    if args.auto_trim_extreme:
        vw_seg_trim = cv2.VideoWriter(seg_trim_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    seg_bboxes = []
    seg_extreme = 0
    seg_face = 0
    seg_trim_kept = 0
    seg_max_yaw = max_yaw_in
    seg_skipped = skipped_in
    f_in_seg = 0
    while f_in_seg < seg_frames:
        ok, frame = cap.read()
        if not ok:
            break
        t0 = time.time()
        is_extreme = False
        try:
            faces = app.get(frame)
            t = pick_target(faces, args.target_side, w)
            if t is not None:
                y = yaw_proxy(t)
                seg_face += 1
                if y > seg_max_yaw:
                    seg_max_yaw = y
                if y > args.yaw_warn:
                    seg_extreme += 1
                    is_extreme = True
                # 自适应遮挡：侧脸越大覆盖越多、边缘更柔，应对眼镜/口罩边缘
                ms = min(args.mask_scale * (1.0 + 0.15 * y), 1.8)
                fe = min(args.feather + 0.05 * y, 0.2)
                frame = enhanced_paste(swapper, frame, t, source_face, ms, fe)
                seg_bboxes.append([int(v) for v in t.bbox])
            else:
                seg_bboxes.append(None)
            vw_seg.write(frame)
            if vw_seg_trim is not None and not is_extreme:
                vw_seg_trim.write(frame)
                seg_trim_kept += 1
        except Exception as e:
            logging.warning("  段 %d 帧 %d 处理异常，保留原帧跳过: %s", si, f_in_seg, e)
            vw_seg.write(frame)
            if vw_seg_trim is not None:
                vw_seg_trim.write(frame)
            seg_bboxes.append(None)
            seg_skipped += 1
        dt = time.time() - t0
        if dt > args.frame_timeout:
            logging.warning("  段 %d 帧 %d 耗时 %.1fs 超阈值", si, f_in_seg, dt)
        f_in_seg += 1
    vw_seg.release()
    if vw_seg_trim is not None:
        vw_seg_trim.release()
    return dict(seg_bboxes=seg_bboxes, seg_extreme=seg_extreme, seg_face=seg_face,
                seg_trim_kept=seg_trim_kept, seg_max_yaw=seg_max_yaw, seg_skipped=seg_skipped)


def _seg_is_valid(seg_file, w, h, fps):
    """校验分段文件可正常解码且至少含 1 帧。"""
    if not os.path.exists(seg_file) or os.path.getsize(seg_file) == 0:
        return False
    c = cv2.VideoCapture(seg_file)
    if not c.isOpened():
        c.release()
        return False
    ok, _ = c.read()
    c.release()
    return ok


def heal_segments(seg_dir, n_segs, src_video, seg_frames, fps, w, h, app, swapper, args, source_face):
    """拼接前自愈(v2.7.0 运行稳定性)：任一分段损坏/缺失，重新打开源视频就地重渲一次。"""
    healed = 0
    for si in range(n_segs):
        seg_file = os.path.join(seg_dir, "seg_%03d.mp4" % si)
        if _seg_is_valid(seg_file, w, h, fps):
            continue
        logging.warning("  ⚠️ 分段 %d 损坏/缺失，自动原地重渲一次(E105自愈)", si + 1)
        try:
            cap2 = safe_open_cap_with_retry(
                src_video, workdir=os.path.dirname(os.path.abspath(args.out)) or tempfile.gettempdir())
        except SystemExit as e:
            logging.error("  自愈打开源视频失败: %s", e)
            continue
        render_segment(cap2, si, seg_frames, fps, w, h, app, swapper, args, source_face, 0.0, 0)
        cap2.release()
        if _seg_is_valid(seg_file, w, h, fps):
            healed += 1
            logging.info("  ✅ 分段 %d 自愈成功", si + 1)
        else:
            logging.error("  E105: 分段 %d 自愈仍失败，请 --resume 重跑该段或检查源视频", si + 1)
    return healed


def wizard():
    """交互式参数向导（v2.6.0 · 触发方式友好度）：按大白话问题选，自动拼出命令，不用啃文档。"""
    print("=" * 56)
    print("  kun-video 换脸参数向导（不用看文档，按提示选）")
    print("=" * 56)

    def ask(q, opts):
        print("\n" + q)
        for i, o in enumerate(opts, 1):
            print("  %d) %s" % (i, o))
        while True:
            try:
                c = int(input("  请选(输入数字): ").strip())
                if 1 <= c <= len(opts):
                    return c - 1
            except Exception:
                pass
            print("  请输入 1-%d 的数字" % len(opts))

    video = input("\n  你的视频文件路径(如 原视频.mp4): ").strip()
    photo = input("  目标人脸照片路径(如 照.jpg): ").strip()
    out = input("  输出文件名(直接回车用 pro.mp4): ").strip() or "pro.mp4"
    a = ask("  视频里人物主要是？", ["正脸/近正面", "侧脸多/大偏转角", "戴墨镜口罩等遮挡", "不确定/混合"])
    preset_map = {0: "quality", 1: "sideface", 2: "occlusion", 3: "auto"}
    preset = preset_map[a]
    cmd = "python scripts/faceswap_pro.py --video %s --photo %s --out %s --preset %s" % (
        video, photo, out, preset)
    if a == 1:
        cmd += " --auto-trim-extreme"
    print("\n✅ 为你生成的命令（复制即可跑）：")
    print("  " + cmd)
    print("\n  想直接跑？把上面整行复制执行即可；要换基础版把 faceswap_pro 换成 faceswap。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--photo", required=True)
    ap.add_argument("--out", default="swapped_raw.mp4")
    ap.add_argument("--bbox", default="face_bboxes.json")
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--insight-root", default=".insightface")
    ap.add_argument("--det-size", default=1024, type=int)
    ap.add_argument("--det-thresh", default=0.3, type=float)
    ap.add_argument("--target-side", default="right", choices=["right", "left", "largest"])
    ap.add_argument("--mask-scale", default=1.15, type=float, help="椭圆蒙版放大系数(越大覆盖越多,过大易糊到发际/脖子)")
    ap.add_argument("--feather", default=0.06, type=float, help="羽化强度(占脸宽比例)")
    # 预览模式
    ap.add_argument("--preview-out", default=None, help="给定则只出对比图,不出视频")
    ap.add_argument("--preview-count", default=6, type=int)
    ap.add_argument("--preview-stride", default=7, type=int, help="预览选帧采样步长")
    # 工程增强参数
    ap.add_argument("--resume", action="store_true", help="断点续跑：复用已生成的前 N 帧，仅处理后续帧")
    ap.add_argument("--debug", action="store_true", help="开启 Debug 级日志")
    ap.add_argument("--frame-timeout", default=30.0, type=float, help="单帧处理耗时告警阈值(秒)，超过记日志")
    ap.add_argument("--max-skip-ratio", default=0.3, type=float, help="跳过帧占比超此值则报错 E104（源质量异常）")
    # 极端姿态诚实告警（架构硬上限，主动提示降级）
    ap.add_argument("--yaw-warn", default=0.7, type=float, help="侧脸告警阈值(近似 yaw>70° 的归一化偏移)，超此值记为一帧极端侧脸")
    ap.add_argument("--extreme-ratio-warn", default=0.15, type=float, help="极端侧脸帧占比超此值，结尾输出降级建议")
    ap.add_argument("--auto-trim-extreme", action="store_true",
                    help="极端侧脸占比超阈值时，额外生成「去侧脸版」(剔除极端帧)，减少手动裁剪")
    ap.add_argument("--preset", default="auto",
                    choices=["auto", "speed", "quality", "sideface", "occlusion"],
                    help="参数预设(便捷调参): speed更快/quality更清/sideface侧脸多/occlusion有遮挡")
    ap.add_argument("--segment-secs", default=15, type=int,
                    help="断点续跑分段时长(秒)，越大段越少、续跑粒度越粗")
    ap.add_argument("--wizard", action="store_true",
                    help="交互式参数向导：按大白话问题选场景，自动拼出命令，不用看文档")
    args = ap.parse_args()

    # 向导模式：不加载模型，直接给出命令后退出（降低调参门槛）
    if args.wizard:
        wizard()
        sys.exit(0)

    setup_logging(args.debug)

    import insightface
    logging.info("[1/3] 加载模型 det_size=%d det_thresh=%.2f ...", args.det_size, args.det_thresh)
    try:
        app = make_app(args.insight_root, args.det_size, args.det_thresh)
    except Exception as e:
        raise SystemExit("E102: 模型加载失败: " + str(e))
    try:
        swapper = insightface.model_zoo.get_model(
            os.path.join(args.models_dir, "inswapper_128.onnx"),
            download=False, download_zip=False, providers=["CPUExecutionProvider"])
    except Exception as e:
        raise SystemExit("E102: 未找到 inswapper_128.onnx: " + str(e))
    logging.info("[2/3] 提取目标照片人脸特征...")
    source_face = build_source_face(app, args.photo)
    logging.info("  目标人脸框: %s", [int(v) for v in source_face.bbox])

    # v2.7.0 输入预处理自检(异常处理)：目标照片侧脸/遮挡提前预警，避免白跑数分钟
    try:
        _py = yaw_proxy(source_face)
        if _py > args.yaw_warn:
            logging.warning("=" * 60)
            logging.warning("⚠️ 目标照片疑似侧脸/遮挡(yaw≈%.2f > %.2f)：换脸效果可能不理想。", _py, args.yaw_warn)
            logging.warning("   建议：①换正面/近正面照(最佳) ②加 --preset sideface 或 --preset occlusion")
            logging.warning("   仍想试？继续按当前参数跑；极端侧脸(>85°)救不回属模型硬上限。")
            logging.warning("=" * 60)
    except Exception:
        pass

    cap, used_video = safe_open_cap_with_retry(
        args.video, workdir=os.path.dirname(os.path.abspath(args.out)) or tempfile.gettempdir())
    args.video = used_video  # 记录实际打开的视频路径（可能已转码）
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # ============ 预览模式（整体保护） ============
    if args.preview_out:
        try:
            logging.info("[3/3] 预览: 扫描侧脸帧(stride=%d)...", args.preview_stride)
            cand = []
            idx = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if idx % args.preview_stride == 0:
                    faces = app.get(frame)
                    t = pick_target(faces, args.target_side, w)
                    if t is not None:
                        cand.append((yaw_proxy(t), idx, frame.copy(), t))
                idx += 1
            cap.release()
            cand.sort(key=lambda x: -x[0])
            picks = cand[:args.preview_count]
            picks.sort(key=lambda x: x[1])
            rows = []
            for yaw, fidx, frame, t in picks:
                old = swapper.get(frame.copy(), t, source_face, paste_back=True)
                new = enhanced_paste(swapper, frame.copy(), t, source_face, args.mask_scale, args.feather)
                x1, y1, x2, y2 = [int(v) for v in t.bbox]
                pad = int((x2 - x1) * 0.6)
                cx1, cy1 = max(0, x1 - pad), max(0, y1 - pad)
                cx2, cy2 = min(w, x2 + pad), min(h, y2 + pad)
                def crop(im):
                    c = im[cy1:cy2, cx1:cx2]
                    return cv2.resize(c, (320, 320))
                trip = np.hstack([crop(frame), crop(old), crop(new)])
                cv2.putText(trip, "frame %d yaw=%.2f  [orig | old-swap | NEW-enhanced]" % (fidx, yaw),
                            (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                rows.append(trip)
            grid = np.vstack(rows)
            cv2.imwrite(args.preview_out, grid)
            logging.info("PREVIEW DONE -> %s 帧: %s", args.preview_out, [p[1] for p in picks])
            return
        except Exception as e:
            logging.error("预览模式失败: %s", e)
            raise SystemExit("E103: 预览处理异常: " + str(e))

    # ============ 全量模式（分段断点续跑 + 帧级容错 + 自适应遮挡） ============
    logging.info("[3/3] 逐帧换脸（分段断点续跑 + 增强蒙版 + 帧级容错）...")
    logging.info("  源: %dx%d, %.2ffps, %d 帧", w, h, fps, total)

    # —— 参数预设（便捷调参，不用啃文档）——
    PRESETS = {
        "speed":     dict(det_size=512,  mask_scale=1.10, feather=0.05),
        "quality":   dict(det_size=1024, mask_scale=1.25, feather=0.09),
        "sideface":  dict(det_size=1024, mask_scale=1.40, feather=0.11, auto_trim_extreme=True),
        "occlusion": dict(det_size=1024, mask_scale=1.30, feather=0.13),
        "auto":      dict(),
    }
    _DEF = {"det_size": 1024, "mask_scale": 1.15, "feather": 0.06}
    if args.preset in PRESETS and args.preset != "auto":
        for _k, _v in PRESETS[args.preset].items():
            if _k == "auto_trim_extreme":
                if not args.auto_trim_extreme:
                    args.auto_trim_extreme = bool(_v)
                continue
            if getattr(args, _k) == _DEF.get(_k):
                setattr(args, _k, _v)
        logging.info("  已应用预设 --preset %s（det_size=%d mask_scale=%.2f feather=%.2f）",
                     args.preset, args.det_size, args.mask_scale, args.feather)

    # —— 分段断点续跑 ——
    seg_secs = max(1, int(args.segment_secs))
    seg_frames = max(1, int(round(fps * seg_secs))) if fps and fps > 0 else 1
    n_segs = (total + seg_frames - 1) // seg_frames if total > 0 else 1
    seg_dir = args.out + ".segs"
    os.makedirs(seg_dir, exist_ok=True)
    state_path = args.out + ".resume_state.json"
    state = _load_resume_state(state_path)
    done = set(state.get("done", []))
    if args.resume and done:
        _nxt = min(d for d in range(n_segs) if d not in done)
        logging.info("  断点续跑：已完成 %d/%d 段，将从第 %d 段继续", len(done), n_segs, _nxt + 1)

    bboxes_all = []
    skipped = 0
    extreme_frames = 0
    face_frames = 0
    max_yaw = 0.0
    trim_kept = 0
    extreme_segments = []

    for si in range(n_segs):
        seg_base = os.path.join(seg_dir, "seg_%03d" % si)
        seg_file = seg_base + ".mp4"
        # 断点续跑：已完成且文件仍在，直接复用统计，不重复渲染
        if args.resume and si in done and os.path.exists(seg_file):
            seg_bboxes = state.get("segs", {}).get(str(si), [])
            bboxes_all.extend(seg_bboxes)
            _st = state.get("stats", {}).get(str(si), {})
            extreme_frames += _st.get("extreme", 0)
            face_frames += _st.get("face", 0)
            max_yaw = max(max_yaw, _st.get("max_yaw", 0.0))
            trim_kept += _st.get("trim_kept", 0)
            extreme_segments.append((si, _st.get("start_ts", 0.0), _st.get("end_ts", 0.0), _st.get("ratio", 0.0)))
            logging.info("  [段 %d/%d] ✅ 已完成，跳过(断点续跑)", si + 1, n_segs)
            continue
        # 渲染该分段（主循环与分段自愈共用同一渲染函数，行为一致）
        res = render_segment(cap, si, seg_frames, fps, w, h, app, swapper, args, source_face, max_yaw, skipped)
        seg_bboxes = res["seg_bboxes"]
        seg_extreme = res["seg_extreme"]
        seg_face = res["seg_face"]
        seg_trim_kept = res["seg_trim_kept"]
        max_yaw = max(max_yaw, res["seg_max_yaw"])
        skipped += res["seg_skipped"]
        bboxes_all.extend(seg_bboxes)
        seg_ratio = (seg_extreme / seg_face) if seg_face > 0 else 0.0
        extreme_segments.append((si, si * seg_secs, si * seg_secs + seg_secs, seg_ratio))
        done.add(si)
        state.setdefault("segs", {})[str(si)] = seg_bboxes
        state.setdefault("stats", {})[str(si)] = dict(extreme=seg_extreme, face=seg_face,
                                                       max_yaw=max_yaw, trim_kept=seg_trim_kept,
                                                       start_ts=si * seg_secs, end_ts=si * seg_secs + seg_secs,
                                                       ratio=seg_ratio)
        state["done"] = sorted(done)
        _save_resume_state(state_path, state)
        extreme_frames += seg_extreme
        face_frames += seg_face
        trim_kept += seg_trim_kept
        logging.info("  [段 %d/%d] ✅ 完成（有脸%d 极端%d 占比%.0f%%）", si + 1, n_segs, seg_face, seg_extreme, seg_ratio * 100)

    cap.release()

    # —— v2.7.0 分段自愈：拼接前校验，损坏/缺失分段自动原地重渲一次 ——
    healed = heal_segments(seg_dir, n_segs, args.video, seg_frames, fps, w, h, app, swapper, args, source_face)
    if healed:
        logging.info("  🛠️ 已自愈 %d 个异常分段，继续拼接", healed)

    # 合并分段 → 成片（ffmpeg 无损拼接，失败回退 cv2）
    concat_videos([os.path.join(seg_dir, "seg_%03d.mp4" % i) for i in range(n_segs)],
                  args.out, fps, w, h)
    trimmed_path = None
    if args.auto_trim_extreme:
        trimmed_path = os.path.splitext(args.out)[0] + "_trimmed.mp4"
        concat_videos([os.path.join(seg_dir, "seg_%03d_trim.mp4" % i) for i in range(n_segs)
                       if os.path.exists(os.path.join(seg_dir, "seg_%03d_trim.mp4" % i))],
                      trimmed_path, fps, w, h)
    try:
        shutil.rmtree(seg_dir)
        if os.path.exists(state_path):
            os.remove(state_path)
    except Exception:
        pass

    with open(args.bbox, "w") as f:
        json.dump({"w": w, "h": h, "bboxes": bboxes_all}, f)

    # 极端侧脸报告（JSON，接地气下一步 + 时间段定位）
    extreme_ratio = (extreme_frames / face_frames) if face_frames > 0 else 0.0
    if extreme_ratio <= args.extreme_ratio_warn:
        plain = "整体可用：正脸/近正脸替换几乎无痕，可直接用成品。"
    elif trimmed_path is not None and trim_kept > 0:
        plain = "侧脸偏多：已自动生成去侧脸版（剔除废片段），建议优先用该版本；要更高质量请换正面素材。"
    else:
        plain = "侧脸偏多：换脸模型对扭头>70°天生救不回，建议换正面素材，或重跑加 --auto-trim-extreme 自动裁掉废片段。"
    _ext_report = dict(face_frames=face_frames, extreme_frames=extreme_frames,
                       extreme_ratio=round(extreme_ratio, 3), max_yaw=round(max_yaw, 3),
                       trimmed_available=bool(trimmed_path and os.path.exists(trimmed_path)),
                       plain_summary=plain,
                       extreme_segments=[dict(seg=s, start="%.1fs" % st, end="%.1fs" % et, ratio=round(r, 3))
                                         for (s, st, et, r) in extreme_segments if r > args.extreme_ratio_warn])
    try:
        with open(os.path.splitext(args.out)[0] + "_extreme_report.json", "w") as f:
            json.dump(_ext_report, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    skip_ratio = (skipped / total) if total > 0 else 0.0
    if skip_ratio > args.max_skip_ratio:
        logging.error("E104: 跳过帧占比 %.1f%% 超阈值 %.1f%%，请检查源视频质量或模型",
                      skip_ratio * 100, args.max_skip_ratio * 100)

    # ============ 极端姿态诚实告警（接地气，给具体下一步） ============
    extreme_ratio = (extreme_frames / face_frames) if face_frames > 0 else 0.0
    logging.info("姿态统计: 有脸帧=%d, 极端侧脸帧(扭头>70度)=%d (%.1f%%), 最大侧脸偏移=%.2f",
                 face_frames, extreme_frames, extreme_ratio * 100, max_yaw)
    if extreme_ratio > args.extreme_ratio_warn:
        logging.warning("=" * 64)
        logging.warning("⚠️ 你这段视频里，人物「扭头太狠」的镜头占了 %.1f%%（侧脸超过70度）", extreme_ratio * 100)
        logging.warning("   换脸模型(inswapper)对这种镜头天生救不回来——不是你操作问题，是模型架构硬上限。")
        logging.warning("   三个实在办法（任选其一）：")
        logging.warning("   ① 剪掉这些侧脸段，只保留正脸/近正脸部分再换脸（最省事）")
        logging.warning("   ② 用 Photoshop 把目标照片的肤色/光照调得和视频接近，能改善一点")
        logging.warning("   ③ 想要高质量脸，换专业 matting/扩散方案；别指望一键无痕")
        if trimmed_path is not None and trim_kept > 0:
            logging.warning("   ✅ 已自动生成「去侧脸版」：%s （已剔除废片段，可直接用）", trimmed_path)
        else:
            logging.warning("   想让我自动裁剪掉这些废片段？重跑加 --auto-trim-extreme 即可")
        logging.warning("   先预览核对：python scripts/faceswap_pro.py --video <原视频> --photo <照> --preview-out preview.png")
        logging.warning("=" * 64)

    logging.info("DONE -> %s ; bbox -> %s ; 跳过帧=%d (%.1f%%)",
                  args.out, args.bbox, skipped, skip_ratio * 100)

    # ============ 白话运行结论（创造力/接地气 · v2.6.0） ============
    logging.info("=" * 56)
    logging.info("📋 运行结论（人话版）: %s", plain)
    logging.info("   成果文件: %s", args.out)
    if trimmed_path is not None and trim_kept > 0:
        logging.info("   去侧脸版: %s （已剔除废片段，可直接用）", trimmed_path)
    logging.info("   极端姿态报告: %s_extreme_report.json（含白话结论 plain_summary）",
                 os.path.splitext(args.out)[0])
    logging.info("=" * 56)


if __name__ == "__main__":
    main()
