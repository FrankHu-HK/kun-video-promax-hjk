# -*- coding: utf-8 -*-

"""

( · ).

:dependency,model,ffmpeg ,.

: python scripts/preflight.py [--work-dir .]

outputclear ✅/⚠️/❌  + copy.

"""

import os

import sys

import argparse

import shutil

import importlib.util



# face swapdependency( Workflow A/D/E )

CORE_PKGS = ["insightface", "onnxruntime", "cv2", "numpy", "mediapipe"]

# /

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

    ap.add_argument("--work-dir", default=".", help="work/taskdirectory(model)")

    args = ap.parse_args()

    wd = os.path.abspath(args.work_dir)



    print("=" * 56)

    print("  kun-video (v2.4.0 · )")

    print("=" * 56)



    ok = True



    # 1) Python version

    pv = sys.version_info

    if pv >= PY_MIN:

        print("  ✅ Python %d.%d.%d" % (pv.major, pv.minor, pv.micro))

    else:

        ok = False

        print("  ❌ Python %d.%d.%d , >= %d.%d" % (pv.major, pv.minor, pv.micro, PY_MIN[0], PY_MIN[1]))



    # 2) dependency

    missing_core = [p for p in CORE_PKGS if not have(p)]

    if not missing_core:

        print("  ✅ dependencyready: " + " / ".join(CORE_PKGS))

    else:

        ok = False

        print("  ❌ dependency: " + " / ".join(missing_core))

        print("     → pip install " + " ".join(missing_core))



    # 3) dependency

    missing_opt = [p for p in OPT_PKGS if not have(p)]

    if not missing_opt:

        print("  ✅ dependencyready: " + " / ".join(OPT_PKGS))

    else:

        print("  ⚠️ dependency(/): " + " / ".join(missing_opt))

        print("     → pip install " + " ".join(missing_opt))



    # 4) model

    ins_ok, buf_ok = model_ready(wd)

    if ins_ok:

        print("  ✅ model inswapper_128.onnx ready")

    else:

        ok = False

        print("  ❌ model inswapper_128.onnx ")

    if buf_ok:

        print("  ✅ model buffalo_l ready")

    else:

        ok = False

        print("  ❌ model buffalo_l ")



    # 5) ffmpeg

    if shutil.which("ffmpeg"):

        print("  ✅ ffmpeg available(remove watermark/composite/BGM )")

    else:

        print("  ⚠️  ffmpeg(remove watermark/compositeinstall PATH)")



    print("-" * 56)

    if ins_ok and buf_ok and not missing_core:

        print("  ✅ ready:,recommended 3 ")

        print("     python scripts/faceswap.py --video video.mp4 --photo target/goal.jpg --out face swap.mp4")

        print("     python scripts/clean_douyin.py --input face swap.mp4 --output remove watermark.mp4")

    else:

        ok = False

        print("  ❌ ready: ❌ ,:")

        print("     pip install insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope")

        print("     python scripts/download_models.py --work-dir . --with-mediapipe")

        print("     confirm.")

    print("=" * 56)

    sys.exit(0 if ok else 1)





if __name__ == "__main__":

    main()

