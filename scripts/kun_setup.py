# -*- coding: utf-8 -*-

"""

kun_setup.py (v2.9.0) - install / ready

================================================

install().videoproductiondependency:

  - ffmpeg        :videocomposite/(,install)

  - pyttsx3       :AI ()

  - edge_tts      :AI (,,)



:"";edge_tts ,install.

      ,,ready.



:

  python scripts/kun_setup.py            #  +  pyttsx3

  python scripts/kun_setup.py --with-edge #  edge_tts

  python scripts/kun_setup.py --check-only # install

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

    """ pip install,success."""

    try:

        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

        return True

    except Exception as e:

        logging.error("  install %s failed: %s", pkg, e)

        return False





def _import_ok(mod):

    try:

        __import__(mod)

        return True

    except Exception:

        return False





def check_ffmpeg():

    if _have("ffmpeg"):

        logging.info("  ✅ ffmpeg ready(videocomposite/available)")

        return True

    logging.warning("  ❌  ffmpeg(face swapcomposite/4K/compositedependency)")

    logging.warning("     install():")

    logging.warning("       Windows:  winget install Gyan.FFmpeg  (: choco install ffmpeg)")

    logging.warning("       macOS:    brew install ffmpeg")

    logging.warning("       Linux:    sudo apt install ffmpeg")

    return False





def check_pyttsx3(install):

    if _import_ok("pyttsx3"):

        logging.info("  ✅ pyttsx3 ready(AI ,)")

        return True

    logging.warning("  ❌ install pyttsx3(AI )")

    if install:

        if _pip_install("pyttsx3"):

            logging.info("  ✅ pyttsx3 installdone")

            return True

        logging.error("     pyttsx3 installfailed,: pip install pyttsx3")

    else:

        logging.warning("     run: pip install pyttsx3  ( --check-only)")

    return False





def check_edge_tts(install):

    if _import_ok("edge_tts"):

        logging.info("  ✅ edge_tts ready(AI ,,)")

        return True

    logging.warning("  ❌ install edge_tts(,;)")

    if install:

        if _pip_install("edge_tts"):

            logging.info("  ✅ edge_tts installdone()")

            return True

        logging.error("     edge_tts installfailed,: pip install edge_tts")

    else:

        logging.warning("     natural: pip install edge_tts, --backend edge_tts")

    return False





def main():

    ap = argparse.ArgumentParser(description="KUN Video install / ")

    ap.add_argument("--with-edge", action="store_true", help="install edge_tts()")

    ap.add_argument("--check-only", action="store_true", help="install")

    args = ap.parse_args()



    install = not args.check_only

    logging.info("=" * 56)

    logging.info("🔧 KUN Video ready()")

    logging.info("=" * 56)



    ok_ff = check_ffmpeg()

    ok_py = check_pyttsx3(install)

    ok_ed = check_edge_tts(install and args.with_edge)



    logging.info("-" * 56)

    all_ok = ok_ff and ok_py

    if all_ok:

        logging.info("🎉 dependency(ffmpeg + pyttsx3),:face swap/remove watermark/4K/AI")

    else:

        logging.warning("⚠️ ,.")

    if not ok_ed and not (install and args.with_edge):

        logging.info("   :--with-edge install edge_tts ().")

    logging.info("=" * 56)





if __name__ == "__main__":

    main()

