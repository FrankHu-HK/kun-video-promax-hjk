# -*- coding: utf-8 -*-
"""
kun-video 一键初始化（v2.6.0 · 国内适配 + 开箱即用度）
一条命令完成：写入国内镜像配置 → 装依赖 → 下模型 → 预检。
默认优先国内源（hf-mirror.com 模型镜像 + 清华 pypi 依赖镜像），
全国内网络也能完整跑通五工作流。

跑法:
  python scripts/kun_init.py [--work-dir .]
特性:
  - 自动写入 set_mirror.bat(Windows) / set_mirror.sh(Linux/Mac) 到工作目录，
    之后手动跑任何命令前先 `call set_mirror.bat`(或 `source set_mirror.sh`) 即可持续走国内源
  - 每一步失败不中断，最后汇总告诉你哪步要补
"""
import os
import sys
import argparse
import subprocess

MIRROR_ENV = {
    "HF_ENDPOINT": "https://hf-mirror.com",
    "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
}
# 换脸+去水印+升频+批量 核心依赖
PKGS = "insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope"


def _write_mirror_helpers(work_dir):
    """持久化国内镜像配置，用户后续手动跑也生效。"""
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
        print("  ⚠️ 镜像助手写入失败(不影响本次): %s" % e)
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
        print("  ⚠️ 执行异常: %s" % e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=".", help="技能工作目录（模型落地根）")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    os.makedirs(wd, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("  kun-video 一键初始化（v2.6.0 · 国内镜像优先）")
    print("=" * 60)
    print("  模型镜像 : HF_ENDPOINT=%s" % MIRROR_ENV["HF_ENDPOINT"])
    print("  依赖镜像 : PIP_INDEX_URL=%s" % MIRROR_ENV["PIP_INDEX_URL"])

    # 0) 持久化镜像助手（之后手动跑也走国内源）
    if _write_mirror_helpers(wd):
        print("\n[0/4] 已写入国内镜像助手:")
        print("  Windows: 跑命令前先 `call set_mirror.bat`")
        print("  Mac/Linux: 跑命令前先 `source set_mirror.sh`")

    # 1) 装依赖
    print("\n[1/4] 安装依赖（清华 pypi 镜像）...")
    ok_pip = _run([sys.executable, "-m", "pip", "install", "-U"] + PKGS.split(), env=MIRROR_ENV)

    # 2) 下模型（国内源 + hf-mirror 兜底）
    print("\n[2/4] 下载模型（modelscope 国内源 + hf-mirror 兜底）...")
    ok_model = _run([sys.executable, os.path.join(script_dir, "download_models.py"),
                     "--work-dir", wd, "--with-mediapipe"], env=MIRROR_ENV)

    # 3) 预检
    print("\n[3/4] 环境预检...")
    ok_pre = _run([sys.executable, os.path.join(script_dir, "preflight.py"), "--work-dir", wd], env=MIRROR_ENV)

    # 4) 汇总
    print("\n" + "=" * 60)
    print("  初始化汇总")
    print("=" * 60)
    print("  依赖安装 : %s" % ("✅" if ok_pip else "⚠️ 部分失败，可手动重试上面的 pip 命令"))
    print("  模型下载 : %s" % ("✅" if ok_model else "⚠️ 失败，重跑 download_models.py 或挂代理"))
    print("  环境预检 : %s" % ("✅" if ok_pre else "⚠️ 有 ❌ 项，按预检提示补齐后重跑 kun_init.py"))
    print("\n  下一步（已全绿即可直接出片）:")
    print("    python scripts/faceswap.py --video 你的视频.mp4 --photo 你的照.jpg --out 换脸后.mp4")
    print("    python scripts/clean_douyin.py --input 换脸后.mp4 --output 去水印后.mp4")
    print("  想按场景自动选参数？跑: python scripts/faceswap_pro.py --wizard")
    print("=" * 60)


if __name__ == "__main__":
    main()
