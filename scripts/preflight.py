# -*- coding: utf-8 -*-
"""
一键环境预检（开箱即用度 · 新手门槛消除）。
一条命令告诉你：dependency装没装、model下没下、ffmpeg 在不在、能不能直接开跑。
跑法: python scripts/preflight.py [--work-dir .]
outputclear的 ✅/⚠️/❌ 清单 + 直接可copy的下一步命令。
"""
import os
import sys
import argparse
import shutil
import importlib.util

# face swap核心dependency（缺任一则 Workflow A/D/E 跑不了）
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
    ap.add_argument("--work-dir", default=".", help="技能work/taskdirectory（model落地根）")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)

    print("=" * 56)
    print("  kun-video 环境预检（v2.4.0 · 开箱即用度自检）")
    print("=" * 56)

    ok = True

    # 1) Python version
    pv = sys.version_info
    if pv >= PY_MIN:
        print("  ✅ Python %d.%d.%d" % (pv.major, pv.minor, pv.micro))
    else:
        ok = False
        print("  ❌ Python %d.%d.%d 过低，需 >= %d.%d" % (pv.major, pv.minor, pv.micro, PY_MIN[0], PY_MIN[1]))

    # 2) 核心dependency
    missing_core = [p for p in CORE_PKGS if not have(p)]
    if not missing_core:
        print("  ✅ 核心dependencyready: " + " / ".join(CORE_PKGS))
    else:
        ok = False
        print("  ❌ 缺失核心dependency: " + " / ".join(missing_core))
        print("     → pip install " + " ".join(missing_core))

    # 3) 可选dependency
    missing_opt = [p for p in OPT_PKGS if not have(p)]
    if not missing_opt:
        print("  ✅ 扩展dependencyready: " + " / ".join(OPT_PKGS))
    else:
        print("  ⚠️ 缺失扩展dependency(仅下载/贴图需要): " + " / ".join(missing_opt))
        print("     → pip install " + " ".join(missing_opt))

    # 4) model
    ins_ok, buf_ok = model_ready(wd)
    if ins_ok:
        print("  ✅ model inswapper_128.onnx ready")
    else:
        ok = False
        print("  ❌ model inswapper_128.onnx 缺失")
    if buf_ok:
        print("  ✅ model buffalo_l ready")
    else:
        ok = False
        print("  ❌ model buffalo_l 缺失")

    # 5) ffmpeg
    if shutil.which("ffmpeg"):
        print("  ✅ ffmpeg available（remove watermark/composite/BGM 需要）")
    else:
        print("  ⚠️ 未检测到 ffmpeg（remove watermark/composite需自行install并加入 PATH）")

    print("-" * 56)
    if ins_ok and buf_ok and not missing_core:
        print("  ✅ 已ready：可直接开跑，recommended先试新手快速通道 3 条命令")
        print("     python scripts/faceswap.py --video 原video.mp4 --photo target/goal照片.jpg --out face swap后.mp4")
        print("     python scripts/clean_douyin.py --input face swap后.mp4 --output remove watermark后.mp4")
    else:
        ok = False
        print("  ❌ 尚未ready：先补齐上方 ❌ 项，最快一条命令：")
        print("     pip install insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope")
        print("     python scripts/download_models.py --work-dir . --with-mediapipe")
        print("     再跑一次本预检confirm全绿后开跑。")
    print("=" * 56)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
