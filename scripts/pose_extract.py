# -*- coding: utf-8 -*-
"""
pose_extract.py — motion transfer Workflow B stage B1：参考video「动作可迁移性」预检
============================================================================
realavailable（非死代码）：逐frame分析参考video，output可量化的「动作quality」评估，
供 video_engine.py 在face swap前判断"这段参考video适不适合做motion transfer"。

两种分析引擎（自动择一/并用）：
  1. 光流动作强度（默认，零modeldependency）：
     用 cv2 Farneback 光流估算frame间运动幅度 → 动作强度；
     用 Laplacian 方差估算clear度 → blurry占比。
  2. MediaPipe posekeypoint（可选，--model 指定 .task 时enable）：
     extract BlazePose 33 点，补充"关节可见度/动作幅度"维度。
     ※ 未装 mediapipe 或缺model时自动降级为纯光流分析，不阻塞。

output motion_qc.json 字段：
  motion_score     0-100 综合动作可迁移性score/rating
  avg_motion       平均frame间运动幅度（像素，越大动作越明显）
  static_ratio     静态frame占比（动作幅度低于阈值的frameaspect ratio，越小越好）
  avg_sharpness    Laplacian 方差均值（越大越clear）
  blur_ratio       blurryframe占比（clear度低于阈值的frameaspect ratio）
  verdict          一句话结论（适合迁移 / 动作偏弱 / 存在blurryocclusion）
  keypoints        可选：MediaPipe 逐frameskeleton/keypoints点（--model 且 mediapipe available时）
  fps / total_frames / sampled_frames

用法：
  python pose_extract.py --video ref_video.mp4 --out motion_qc.json
  python pose_extract.py --video ref_video.mp4 --out motion_qc.json \
      --model models/pose_landmarker_full.task   # 额外做posekeypoint分析
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

import cv2
import numpy as np


# ---------- tool ----------
def ascii_copy(path):
    """copy中文pathfile到临时 ASCII 名，返回 (availablepath, 临时path或None)。"""
    if all(ord(c) < 128 for c in path):
        return path, None
    fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(path)[1])
    os.close(fd)
    shutil.copy(path, tmp)
    return tmp, tmp


def motion_via_optical_flow(video_path, step=2, motion_thresh=0.6, sharp_thresh=40.0):
    """光流 + Laplacian：零modeldependency的动作/clear度分析。

    关键：动作信号用「运动像素占比」衡量（不被静止background稀释），
    而非整frame光流均值（小target/goal/细微动作会被误判为静止）。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit("[error] 无法openvideo: %s" % video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    prev_gray = None
    moving_ratios = []   # 每frame"运动像素占比"
    mean_flows = []      # 每frame运动像素上的平均光流幅度（information用）
    sharps = []
    idx = -1
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        idx += 1
        if idx % step != 0:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharps.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag = np.linalg.norm(flow, axis=2)
            moving_mask = mag > 0.5           # 该像素是否明显move
            mr = float(np.mean(moving_mask))
            moving_ratios.append(mr)
            if mr > 0:
                mean_flows.append(float(np.mean(mag[moving_mask])))
        prev_gray = gray
    cap.release()

    sampled = len(sharps)
    if not moving_ratios:
        return {
            "avg_motion": 0.0, "static_ratio": 1.0,
            "avg_moving_ratio": 0.0,
            "avg_sharpness": float(np.mean(sharps)) if sharps else 0.0,
            "blur_ratio": float(np.mean([1 if s < sharp_thresh else 0 for s in sharps])) if sharps else 1.0,
            "sampled": sampled,
        }
    avg_mr = float(np.mean(moving_ratios))
    # 单frame运动像素占比 < 1.5% 视为"基本静止frame"
    static_ratio = float(np.mean([1 if mr < 0.015 else 0 for mr in moving_ratios]))
    avg_motion = float(np.mean(mean_flows)) if mean_flows else 0.0
    avg_sharp = float(np.mean(sharps))
    blur_ratio = float(np.mean([1 if s < sharp_thresh else 0 for s in sharps]))
    return {
        "avg_motion": round(avg_motion, 3),
        "static_ratio": round(static_ratio, 3),
        "avg_moving_ratio": round(avg_mr, 4),
        "avg_sharpness": round(avg_sharp, 3),
        "blur_ratio": round(blur_ratio, 3),
        "sampled": sampled,
    }


def motion_score_from_metrics(m):
    """综合动作可迁移性score/rating 0-100（纯启发式，可解释）。

    以"运动像素占比"为核心信号（不被静止background稀释）；
    静态frame多 / blurryframe多 分别扣分。
    """
    avg_mr = m.get("avg_moving_ratio", 0.0)
    # 运动像素占比 0.15(15%)≈主体明显动作 → 拿满 55 分
    motion_part = min(avg_mr / 0.15, 1.0) * 55.0
    static_penalty = m["static_ratio"] * 20.0      # 最多扣 20
    blur_penalty = m["blur_ratio"] * 25.0          # 最多扣 25
    score = max(0.0, min(100.0, motion_part + 25.0 - static_penalty - blur_penalty))
    return round(score, 1)


def verdict_from(m, score):
    if m["blur_ratio"] > 0.5:
        return "参考videoblurry/occlusion偏多，face swap后观感可能下降，suggestion换更clear的素材"
    if m["static_ratio"] > 0.6:
        return "参考video动作偏弱（多为静态/慢动作），迁移后观感平淡，suggestion选动作明显的素材"
    if score >= 60:
        return "适合迁移：动作clear、画面清楚，face swap后能保留明显动作"
    if score >= 35:
        return "基本available：动作与clear度中等，face swap可跑但suggestion挑选动作更明显的片段"
    return "动作或clear度偏弱，迁移效果有限，suggestion更换参考video"


def extract_pose_keypoints(video_path, model_path, step=1):
    """可选：MediaPipe posekeypointextract（需 mediapipe + .task model）。"""
    try:
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core import base_options as base_options_module
        from mediapipe.tasks.python.vision import (
            PoseLandmarker, PoseLandmarkerOptions, RunningMode,
        )
    except Exception as e:
        print("[hint/tip] 未enableposekeypoint分析（mediapipe 不available: %s），改用纯光流分析。" % type(e).__name__)
        return None

    if not os.path.exists(model_path):
        print("[hint/tip] posemodeldoes not exist: %s，skipkeypoint分析，仅用光流。" % model_path)
        return None

    POSE_NAMES = ["nose", "left_eye_inner", "left_eye", "left_eye_outer",
                  "right_eye_inner", "right_eye", "right_eye_outer",
                  "left_ear", "right_ear", "mouth_left", "mouth_right",
                  "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                  "left_wrist", "right_wrist", "left_pinky", "right_pinky",
                  "left_index", "right_index", "left_thumb", "right_thumb",
                  "left_hip", "right_hip", "left_knee", "right_knee",
                  "left_ankle", "right_ankle", "left_heel", "right_heel",
                  "left_foot_index", "right_foot_index"]

    BaseOptions = base_options_module.BaseOptions
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )
    landmarker = PoseLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = vision.Image(image_format=vision.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(mp_image, idx)
            kp = []
            if result.pose_landmarks:
                for lm in result.pose_landmarks[0]:
                    kp.append({"x": round(float(lm.x), 5), "y": round(float(lm.y), 5),
                               "z": round(float(lm.z), 5),
                               "visibility": round(float(lm.visibility), 4)})
            frames.append({"frame": idx, "keypoints": kp})
        idx += 1
    cap.release()
    return {"model": "pose_landmarker_full (BlazePose 33)",
            "keypoint_names": POSE_NAMES, "frames": frames}


def main():
    ap = argparse.ArgumentParser(description="参考video动作可迁移性预检（光流+可选pose）")
    ap.add_argument("--video", required=True, help="参考videopath")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--model", default="", help="pose_landmarker_full.task path（可选，enablepose分析）")
    ap.add_argument("--step", type=int, default=2, help="抽frame步长，越大越快")
    ap.add_argument("--motion-thresh", type=float, default=0.6, help="静态判定阈值（光流幅度）")
    ap.add_argument("--sharp-thresh", type=float, default=40.0, help="blurry判定阈值（Laplacian 方差）")
    args = ap.parse_args()

    video_path, tmp_video = ascii_copy(args.video)
    out_tmp = None
    if tmp_video:
        out_tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name

    metrics = motion_via_optical_flow(
        video_path, step=args.step,
        motion_thresh=args.motion_thresh, sharp_thresh=args.sharp_thresh)
    score = motion_score_from_metrics(metrics)
    verdict = verdict_from(metrics, score)

    result = {
        "source_video": os.path.basename(args.video),
        "motion_score": score,
        "verdict": verdict,
        "avg_motion": metrics["avg_motion"],
        "avg_moving_ratio": metrics["avg_moving_ratio"],
        "static_ratio": metrics["static_ratio"],
        "avg_sharpness": metrics["avg_sharpness"],
        "blur_ratio": metrics["blur_ratio"],
        "sampled_frames": metrics["sampled"],
    }

    # 可选pose分析
    if args.model:
        pose = extract_pose_keypoints(video_path, args.model, step=max(1, args.step))
        if pose:
            result["pose"] = pose

    out_path = out_tmp if out_tmp else args.out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if out_tmp and out_tmp != args.out:
        shutil.move(out_tmp, args.out)
    if tmp_video:
        os.remove(tmp_video)

    print("[done] 动作可迁移性score/rating=%s/100  动作强度=%.2f  静态占比=%.1f%%  blurry占比=%.1f%%"
          % (score, metrics["avg_motion"], metrics["static_ratio"] * 100, metrics["blur_ratio"] * 100))
    print("[结论] %s" % verdict)
    print("[output] %s" % args.out)


if __name__ == "__main__":
    main()
