# -*- coding: utf-8 -*-
"""
一键环境预检（开箱即用度 · 新手门槛消除）。
一条命令告诉你：依赖装没装、模型下没下、ffmpeg 在不在、能不能直接开跑。
跑法: python scripts/preflight.py [--work-dir .]
输出清晰的 ✅/⚠️/❌ 清单 + 直接可复制的下一步命令。
"""
import os
import sys
import argparse
import shutil
import importlib.util

# 换脸核心依赖（缺任一则 Workflow A/D/E 跑不了）
CORE_PKGS = ["insightface", "onnxruntime", "cv2", "numpy", "mediapipe"]
# 仅下载/扩展用途
OPT_PKGS = ["modelscope", "PIL"]

PY_MIN = (3, 8)


def have(pkg):
    return importlib.util.find_spec(pkg) is not None


def model_ready(work_dir):
    inswapper = os.path.join(work_dir, "models", "inswapper_128.onnx")
    buf_dir = os.path.join(work_dir, ".insightface", "models", "buffalo_l")
    ins_ok = os.path.exists(inswapper)
    buf_ok = os.path.isdir(buf_dir) and any(f.endswith(".onnx") for f in os.listdir(buf_dir))
    return ins_ok, buf_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=".", help="技能工作目录（模型落地根）")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)

    print("=" * 56)
    print("  kun-video 环境预检（v2.4.0 · 开箱即用度自检）")
    print("=" * 56)

    ok = True

    # 1) Python 版本
    pv = sys.version_info
    if pv >= PY_MIN:
        print("  ✅ Python %d.%d.%d" % (pv.major, pv.minor, pv.micro))
    else:
        ok = False
        print("  ❌ Python %d.%d.%d 过低，需 >= %d.%d" % (pv.major, pv.minor, pv.micro, PY_MIN[0], PY_MIN[1]))

    # 2) 核心依赖
    missing_core = [p for p in CORE_PKGS if not have(p)]
    if not missing_core:
        print("  ✅ 核心依赖就绪: " + " / ".join(CORE_PKGS))
    else:
        ok = False
        print("  ❌ 缺失核心依赖: " + " / ".join(missing_core))
        print("     → pip install " + " ".join(missing_core))

    # 3) 可选依赖
    missing_opt = [p for p in OPT_PKGS if not have(p)]
    if not missing_opt:
        print("  ✅ 扩展依赖就绪: " + " / ".join(OPT_PKGS))
    else:
        print("  ⚠️ 缺失扩展依赖(仅下载/贴图需要): " + " / ".join(missing_opt))
        print("     → pip install " + " ".join(missing_opt))

    # 4) 模型
    ins_ok, buf_ok = model_ready(wd)
    if ins_ok:
        print("  ✅ 模型 inswapper_128.onnx 就绪")
    else:
        ok = False
        print("  ❌ 模型 inswapper_128.onnx 缺失")
    if buf_ok:
        print("  ✅ 模型 buffalo_l 就绪")
    else:
        ok = False
        print("  ❌ 模型 buffalo_l 缺失")

    # 5) ffmpeg
    if shutil.which("ffmpeg"):
        print("  ✅ ffmpeg 可用（去水印/合成/BGM 需要）")
    else:
        print("  ⚠️ 未检测到 ffmpeg（去水印/合成需自行安装并加入 PATH）")

    print("-" * 56)
    if ins_ok and buf_ok and not missing_core:
        print("  ✅ 已就绪：可直接开跑，推荐先试新手快速通道 3 条命令")
        print("     python scripts/faceswap.py --video 原视频.mp4 --photo 目标照片.jpg --out 换脸后.mp4")
        print("     python scripts/clean_douyin.py --input 换脸后.mp4 --output 去水印后.mp4")
    else:
        ok = False
        print("  ❌ 尚未就绪：先补齐上方 ❌ 项，最快一条命令：")
        print("     pip install insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope")
        print("     python scripts/download_models.py --work-dir . --with-mediapipe")
        print("     再跑一次本预检确认全绿后开跑。")
    print("=" * 56)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
