# -*- coding: utf-8 -*-
"""
kun_setup.py (v2.9.0) - 一键安装 / 环境就绪自检
================================================
降低首次安装摩擦（开箱即用度）。检测并补全本地视频生产层所需依赖：
  - ffmpeg        ：音视频合成/升频必需（系统命令，需自行安装或用包管理器）
  - pyttsx3       ：AI 口播默认离线配音引擎（零云端零国外）
  - edge_tts      ：AI 口播可选升级引擎（微软国外免费云，音质更好，非默认）

原则：只装"本地零云端"必需项；edge_tts 作为可选升级单独询问，不强行安装。
      不改变系统环境之外的一切，缺什么装什么，装完给中文就绪报告。

用法：
  python scripts/kun_setup.py            # 检测 + 自动装缺失的 pyttsx3
  python scripts/kun_setup.py --with-edge # 一并装可选升级 edge_tts
  python scripts/kun_setup.py --check-only # 只检测不安装
"""
import os
import sys
import shutil
import subprocess
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def _have(cmd):
    return shutil.which(cmd) is not None


def _pip_install(pkg):
    """尝试 pip 安装，返回是否成功。"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
        return True
    except Exception as e:
        logging.error("  安装 %s 失败: %s", pkg, e)
        return False


def _import_ok(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def check_ffmpeg():
    if _have("ffmpeg"):
        logging.info("  ✅ ffmpeg 已就绪（音视频合成/升频可用）")
        return True
    logging.warning("  ❌ 未检测到 ffmpeg（换脸合成/4K升频/口播合成都依赖它）")
    logging.warning("     安装方式（任选其一）：")
    logging.warning("       Windows:  winget install Gyan.FFmpeg  (或巧克力: choco install ffmpeg)")
    logging.warning("       macOS:    brew install ffmpeg")
    logging.warning("       Linux:    sudo apt install ffmpeg")
    return False


def check_pyttsx3(install):
    if _import_ok("pyttsx3"):
        logging.info("  ✅ pyttsx3 已就绪（AI 口播默认离线配音，零云端零国外）")
        return True
    logging.warning("  ❌ 未安装 pyttsx3（AI 口播默认离线引擎）")
    if install:
        if _pip_install("pyttsx3"):
            logging.info("  ✅ pyttsx3 安装完成")
            return True
        logging.error("     pyttsx3 自动安装失败，请手动: pip install pyttsx3")
    else:
        logging.warning("     运行: pip install pyttsx3  （或重新执行本脚本不加 --check-only）")
    return False


def check_edge_tts(install):
    if _import_ok("edge_tts"):
        logging.info("  ✅ edge_tts 已就绪（AI 口播可选升级，国外免费云，音质更好）")
        return True
    logging.warning("  ❌ 未安装 edge_tts（可选升级，非默认；走微软国外免费云）")
    if install:
        if _pip_install("edge_tts"):
            logging.info("  ✅ edge_tts 安装完成（记得只在接受国外云时选用）")
            return True
        logging.error("     edge_tts 自动安装失败，请手动: pip install edge_tts")
    else:
        logging.warning("     如需更自然音质: pip install edge_tts，并在口播时 --backend edge_tts")
    return False


def main():
    ap = argparse.ArgumentParser(description="KUN Video 一键安装 / 环境自检")
    ap.add_argument("--with-edge", action="store_true", help="一并安装可选升级 edge_tts（国外免费云）")
    ap.add_argument("--check-only", action="store_true", help="只检测不安装")
    args = ap.parse_args()

    install = not args.check_only
    logging.info("=" * 56)
    logging.info("🔧 KUN Video 环境就绪自检（本地零云端优先）")
    logging.info("=" * 56)

    ok_ff = check_ffmpeg()
    ok_py = check_pyttsx3(install)
    ok_ed = check_edge_tts(install and args.with_edge)

    logging.info("-" * 56)
    all_ok = ok_ff and ok_py
    if all_ok:
        logging.info("🎉 核心依赖已齐（ffmpeg + pyttsx3），可直接跑：换脸/去水印/4K升频/AI口播")
    else:
        logging.warning("⚠️ 仍有缺失项，按上方指引补全后再用。")
    if not ok_ed and not (install and args.with_edge):
        logging.info("   可选：--with-edge 安装 edge_tts 升级口播音质（国外云）。")
    logging.info("=" * 56)


if __name__ == "__main__":
    main()
