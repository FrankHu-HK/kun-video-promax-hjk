# -*- coding: utf-8 -*-
"""
kun-video 一键initialize（v2.6.0 · 国内适配 + 开箱即用度）
一条命令done：write国内镜像config → 装dependency → 下model → 预检。
默认优先国内源（hf-mirror.com model镜像 + 清华 pypi dependency镜像），
全国内网络也能完整跑通五work/task流。

跑法:
  python scripts/kun_init.py [--work-dir .]
feature:
  - 自动write set_mirror.bat(Windows) / set_mirror.sh(Linux/Mac) 到work/taskdirectory，
    之后手动跑任何命令前先 `call set_mirror.bat`(或 `source set_mirror.sh`) 即可持续走国内源
  - 每一步failed不interrupt，最后汇总告诉你哪步要补
"""
import os
import sys
import argparse
import subprocess

MIRROR_ENV = {
    "HF_ENDPOINT": "https://hf-mirror.com",
    "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
}
# face swap+remove watermark+升频+batch 核心dependency
PKGS = "insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope"


def _write_mirror_helpers(work_dir):
    """持久化国内镜像config，user后续手动跑也生效。"""
    bat = os.path.join(work_dir, "set_mirror.bat")
    sh = os.path.join(work_dir, "set_mirror.sh")
    try:
        with open(bat, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("set HF_ENDPOINT=https://hf-mirror.com\n")
            f.write("set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple\n")
            f.write("echo [kun-video] 已切换到国内镜像(HF-Mirror + 清华pypi)\n")
        with open(sh, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env bash\n")
            f.write("export HF_ENDPOINT=https://hf-mirror.com\n")
            f.write("export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple\n")
            f.write("echo '[kun-video] 已切换到国内镜像(HF-Mirror + 清华pypi)'\n")
        os.chmod(sh, 0o755)
        return True
    except Exception as e:
        print("  ⚠️ 镜像助手writefailed(不影响本次): %s" % e)
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
        print("  ⚠️ 执行exception: %s" % e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=".", help="技能work/taskdirectory（model落地根）")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    os.makedirs(wd, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("  kun-video 一键initialize（v2.6.0 · 国内镜像优先）")
    print("=" * 60)
    print("  model镜像 : HF_ENDPOINT=%s" % MIRROR_ENV["HF_ENDPOINT"])
    print("  dependency镜像 : PIP_INDEX_URL=%s" % MIRROR_ENV["PIP_INDEX_URL"])

    # 0) 持久化镜像助手（之后手动跑也走国内源）
    if _write_mirror_helpers(wd):
        print("\n[0/4] 已write国内镜像助手:")
        print("  Windows: 跑命令前先 `call set_mirror.bat`")
        print("  Mac/Linux: 跑命令前先 `source set_mirror.sh`")

    # 1) 装dependency
    print("\n[1/4] installdependency（清华 pypi 镜像）...")
    ok_pip = _run([sys.executable, "-m", "pip", "install", "-U"] + PKGS.split(), env=MIRROR_ENV)

    # 2) 下model（国内源 + hf-mirror 兜底）
    print("\n[2/4] 下载model（modelscope 国内源 + hf-mirror 兜底）...")
    ok_model = _run([sys.executable, os.path.join(script_dir, "download_models.py"),
                     "--work-dir", wd, "--with-mediapipe"], env=MIRROR_ENV)

    # 3) 预检
    print("\n[3/4] 环境预检...")
    ok_pre = _run([sys.executable, os.path.join(script_dir, "preflight.py"), "--work-dir", wd], env=MIRROR_ENV)

    # 4) 汇总
    print("\n" + "=" * 60)
    print("  initialize汇总")
    print("=" * 60)
    print("  dependencyinstall : %s" % ("✅" if ok_pip else "⚠️ 部分failed，可手动retry上面的 pip 命令"))
    print("  model下载 : %s" % ("✅" if ok_model else "⚠️ failed，重跑 download_models.py 或挂代理"))
    print("  环境预检 : %s" % ("✅" if ok_pre else "⚠️ 有 ❌ 项，按预检hint/tip补齐后重跑 kun_init.py"))
    print("\n  下一步（已全绿即可直接出片）:")
    print("    python scripts/faceswap.py --video 你的video.mp4 --photo 你的照.jpg --out face swap后.mp4")
    print("    python scripts/clean_douyin.py --input face swap后.mp4 --output remove watermark后.mp4")
    print("  想按场景自动选parameter？跑: python scripts/faceswap_pro.py --wizard")
    print("=" * 60)


if __name__ == "__main__":
    main()
