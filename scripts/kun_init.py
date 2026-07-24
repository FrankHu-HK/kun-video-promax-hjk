# -*- coding: utf-8 -*-

"""

kun-video initialize(v2.6.0 ·  + )

done:writeconfig → dependency → model → .

(hf-mirror.com model +  pypi dependency),

work/task.



:

  python scripts/kun_init.py [--work-dir .]

feature:

  - write set_mirror.bat(Windows) / set_mirror.sh(Linux/Mac) work/taskdirectory,

     `call set_mirror.bat`( `source set_mirror.sh`) 

  - failedinterrupt,

"""

import os

import sys

import argparse

import subprocess



MIRROR_ENV = {

    "HF_ENDPOINT": "https://hf-mirror.com",

    "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",

}

# face swap+remove watermark++batch dependency

PKGS = "insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope"





def _write_mirror_helpers(work_dir):

    """config,user."""

    bat = os.path.join(work_dir, "set_mirror.bat")

    sh = os.path.join(work_dir, "set_mirror.sh")

    try:

        with open(bat, "w", encoding="utf-8") as f:

            f.write("@echo off\n")

            f.write("set HF_ENDPOINT=https://hf-mirror.com\n")

            f.write("set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple\n")

            f.write("echo [kun-video] (HF-Mirror + pypi)\n")

        with open(sh, "w", encoding="utf-8") as f:

            f.write("#!/usr/bin/env bash\n")

            f.write("export HF_ENDPOINT=https://hf-mirror.com\n")

            f.write("export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple\n")

            f.write("echo '[kun-video] (HF-Mirror + pypi)'\n")

        os.chmod(sh, 0o755)

        return True

    except Exception as e:

        print("  ⚠️ writefailed(): %s" % e)

        return False





def _run(cmd, env=None):

    e = dict(os.environ)

    if env:

        e.update(env)

    print("\n$ " + " ".join(cmd))

    try:

        r = subprocess.run(cmd, env=e)

        return r.returncode == 0

    except Exception as e:

        print("  ⚠️ exception: %s" % e)

        return False





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--work-dir", default=".", help="work/taskdirectory(model)")

    args = ap.parse_args()

    wd = os.path.abspath(args.work_dir)

    os.makedirs(wd, exist_ok=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))



    print("=" * 60)

    print("  kun-video initialize(v2.6.0 · )")

    print("=" * 60)

    print("  model : HF_ENDPOINT=%s" % MIRROR_ENV["HF_ENDPOINT"])

    print("  dependency : PIP_INDEX_URL=%s" % MIRROR_ENV["PIP_INDEX_URL"])



    # 0) ()

    if _write_mirror_helpers(wd):

        print("\n[0/4] write:")

        print("  Windows:  `call set_mirror.bat`")

        print("  Mac/Linux:  `source set_mirror.sh`")



    # 1) dependency

    print("\n[1/4] installdependency( pypi )...")

    ok_pip = _run([sys.executable, "-m", "pip", "install", "-U"] + PKGS.split(), env=MIRROR_ENV)



    # 2) model( + hf-mirror )

    print("\n[2/4] model(modelscope  + hf-mirror )...")

    ok_model = _run([sys.executable, os.path.join(script_dir, "download_models.py"),

                     "--work-dir", wd, "--with-mediapipe"], env=MIRROR_ENV)



    # 3) 

    print("\n[3/4] ...")

    ok_pre = _run([sys.executable, os.path.join(script_dir, "preflight.py"), "--work-dir", wd], env=MIRROR_ENV)



    # 4) 

    print("\n" + "=" * 60)

    print("  initialize")

    print("=" * 60)

    print("  dependencyinstall : %s" % ("✅" if ok_pip else "⚠️ failed,retry pip "))

    print("  model : %s" % ("✅" if ok_model else "⚠️ failed, download_models.py "))

    print("   : %s" % ("✅" if ok_pre else "⚠️  ❌ ,hint/tip kun_init.py"))

    print("\n  ():")

    print("    python scripts/faceswap.py --video video.mp4 --photo .jpg --out face swap.mp4")

    print("    python scripts/clean_douyin.py --input face swap.mp4 --output remove watermark.mp4")

    print("  parameter?: python scripts/faceswap_pro.py --wizard")

    print("=" * 60)





if __name__ == "__main__":

    main()

