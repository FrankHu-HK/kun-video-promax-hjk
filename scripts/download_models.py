# -*- coding: utf-8 -*-

"""

face swapmodel(,).

""(face swap + poseextract),generatemodel(AGNES  / NVIDIA  / Seedance  / Kling  Key),**v2.2.0  Veo 3.1 **.



run: python scripts/download_models.py --work-dir <work/taskdirectory> [--with-mediapipe] [--retry 3] [--force]

  -  inswapper_128.onnx + buffalo_l( modelscope ,stable)

  - :modelscope failedretry( 3 ),failed hf-mirror 

  - :modelalready existsskip,(--force )

  - --with-mediapipe: Workflow B posemodel pose_landmarker_full.task

    ( storage.googleapis.com timeout,failed/,interruptworkflow)



( references/models_sources.md):

  - HuggingFace / GitHub ,( hf-mirror.com )

  - face swapmodel modelscope()

  - MediaPipe model google, gitee  ModelScope 

dependency: pip install modelscope

"""

import os

import time

import argparse

import logging



logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")



# MediaPipe posemodel: + annotation(failedcrash,)

MEDIAPIPE_MAIN = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"

                  "pose_landmarker_full/float16/latest/pose_landmarker_full.task")

MEDIAPIPE_SIZE_MB = 12



# model hf-mirror.com (modelscope failed)

HF_MIRROR = {

    "inswapper": "ezioruan/inswapper_128.onnx",

    "buffalo": "junior90/buffalo_l",

}





def _model_present(local_dir, kind):

    """:model,."""

    if kind == "inswapper":

        return os.path.exists(os.path.join(local_dir, "inswapper_128.onnx"))

    if kind == "buffalo":

        if not os.path.isdir(local_dir):

            return False

        return any(f.endswith(".onnx") for f in os.listdir(local_dir))

    return False





def _download_modelscope(repo, local_dir, desc):

    from modelscope import snapshot_download

    logging.info("  [modelscope]  %s ...", desc)

    return snapshot_download(repo, local_dir=local_dir)





def _download_hf_mirror(repo_id, local_dir, desc):

    try:

        from huggingface_hub import snapshot_download as hf_dl

    except ImportError:

        logging.warning("  hf-mirror  huggingface_hub(pip install huggingface_hub),skip")

        return None

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    logging.info("  [hf-mirror]  %s ...", desc)

    return hf_dl(repo_id, local_dir=local_dir)





def download_model(repo, local_dir, desc, kind, retry=3, force=False):

    """retry +  + model.success."""

    os.makedirs(local_dir, exist_ok=True)

    if not force and _model_present(local_dir, kind):

        logging.info("  ✅ %s already exists,skip(--force )", desc)

        return True



    last_err = None

    for attempt in range(1, retry + 1):

        try:

            _download_modelscope(repo, local_dir, desc)

            if _model_present(local_dir, kind):

                logging.info("  ✅ %s success", desc)

                return True

        except Exception as e:

            last_err = e

            wait = 4 * (2 ** (attempt - 1))  # 4s, 8s, 16s 

            logging.warning("  modelscope  %d/%d failed: %s(%ds retry)", attempt, retry, e, wait)

            if attempt < retry:

                time.sleep(wait)



    # modelscope failed →  hf-mirror 

    mirror_repo = HF_MIRROR.get(kind)

    if mirror_repo:

        try:

            _download_hf_mirror(mirror_repo, local_dir, desc)

            if _model_present(local_dir, kind):

                logging.info("  ✅ %s  hf-mirror success", desc)

                return True

        except Exception as e:

            logging.warning("  hf-mirror failed: %s", e)



    logging.error("  %s failed: %s", desc, last_err)

    return False





def download_mediapipe(work_dir):

    """posemodel;failed/,."""

    import urllib.request

    dst = os.path.join(work_dir, "models", "pose_landmarker_full.task")

    os.makedirs(os.path.dirname(dst), exist_ok=True)

    logging.info("[3/3]  pose_landmarker_full.task( google, %dMB)...", MEDIAPIPE_SIZE_MB)

    try:

        urllib.request.urlretrieve(MEDIAPIPE_MAIN, dst)

        logging.info("  -> %s", dst)

        return True

    except Exception as e:

        logging.warning("  failed(): %s", e)

        logging.warning("  ⚙️ (, %s):", dst)

        logging.warning("    1) gitee  mediapipe-models , pose_landmarker_full.task")

        logging.warning("    2) ModelScope  'pose_landmarker_full' ")

        logging.warning("    3) /retry")

        logging.warning("  ⚠️ file Workflow B pose,face swap(Workflow A).")

        return False





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--work-dir", default=".", help="modeldirectory")

    ap.add_argument("--with-mediapipe", action="store_true", help=" Workflow B posemodel")

    ap.add_argument("--retry", type=int, default=3, help="modelscope retry( 3)")

    ap.add_argument("--force", action="store_true", help="(already existsmodel)")

    args = ap.parse_args()



    wd = os.path.abspath(args.work_dir)

    os.makedirs(wd, exist_ok=True)



    ok1 = download_model(

        "chwshuang/inswapper_128.onnx",

        os.path.join(wd, "models"),

        "inswapper_128.onnx", kind="inswapper",

        retry=args.retry, force=args.force)

    ok2 = download_model(

        "destinylhj/buffalo_l",

        os.path.join(wd, ".insightface", "models", "buffalo_l"),

        "buffalo_l (+detect)", kind="buffalo",

        retry=args.retry, force=args.force)



    # :buffalo_l directory, .insightface/models/buffalo_l/*.onnx 

    if ok2:

        base = os.path.join(wd, ".insightface", "models", "buffalo_l")

        onnxs = [f for f in os.listdir(base)] if os.path.isdir(base) else []

        if not any(f.endswith(".onnx") for f in onnxs):

            import shutil

            for root, _d, files in os.walk(base):

                for f in files:

                    if f.endswith(".onnx"):

                        shutil.copy(os.path.join(root, f), base)

                        logging.info("  : %s", f)



    if args.with_mediapipe:

        download_mediapipe(wd)



    if ok1 and ok2:

        logging.info("✅ face swapmodelready;%s", "posemodelready" if args.with_mediapipe else "Workflow B posemodel( --with-mediapipe)")

    else:

        logging.error("❌ modelfailed,hint/tipprocess( modelscope ; hf-mirror )")





if __name__ == "__main__":

    main()

