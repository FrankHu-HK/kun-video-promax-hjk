# -*- coding: utf-8 -*-
"""
下载face swap所需model（国内源优先，避免被墙）。
本脚本只下载"本地可跑"部分（face swap + poseextract），云端generatemodel由可选升级通道（AGNES 终身免费 / NVIDIA 免费额度 / Seedance 国内免费试用 / Kling 需付费 Key）提供，**v2.2.0 彻底移除 Veo 3.1 等国外服务**。

run: python scripts/download_models.py --work-dir <work/taskdirectory> [--with-mediapipe] [--retry 3] [--force]
  - 默认下载 inswapper_128.onnx + buffalo_l（均走 modelscope 国内源，国内stable可达）
  - 网络韧性：modelscope failed自动指数退避retry（默认 3 次），全failed再回退 hf-mirror 国内镜像兜底
  - 离线幂等：modelalready exists则skip，避免重复下载（--force 可强制重下）
  - --with-mediapipe：额外尝试下载 Workflow B posemodel pose_landmarker_full.task
    （主源 storage.googleapis.com 国内偶有timeout，failed会给出国内镜像/手动下载指引，不interrupt主workflow）

国内网络约束（详见 references/models_sources.md）：
  - HuggingFace / GitHub 被墙，勿尝试从此处下载（仅 hf-mirror.com 镜像作为兜底通道）
  - face swapmodel一律优先走 modelscope（国内可达）
  - MediaPipe model主源在 google，国内波动时走 gitee 镜像或 ModelScope 社区镜像手动补
dependency: pip install modelscope
"""
import os
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# MediaPipe posemodel：主源 + 国内备选annotation（主源failed不crash，给出可操作指引）
MEDIAPIPE_MAIN = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                  "pose_landmarker_full/float16/latest/pose_landmarker_full.task")
MEDIAPIPE_SIZE_MB = 12

# 各model在 hf-mirror.com 的兜底仓库（modelscope 全failed时尝试）
HF_MIRROR = {
    "inswapper": "ezioruan/inswapper_128.onnx",
    "buffalo": "junior90/buffalo_l",
}


def _model_present(local_dir, kind):
    """离线幂等判断：model是否已就位，避免重复下载。"""
    if kind == "inswapper":
        return os.path.exists(os.path.join(local_dir, "inswapper_128.onnx"))
    if kind == "buffalo":
        if not os.path.isdir(local_dir):
            return False
        return any(f.endswith(".onnx") for f in os.listdir(local_dir))
    return False


def _download_modelscope(repo, local_dir, desc):
    from modelscope import snapshot_download
    logging.info("  [modelscope] 下载 %s ...", desc)
    return snapshot_download(repo, local_dir=local_dir)


def _download_hf_mirror(repo_id, local_dir, desc):
    try:
        from huggingface_hub import snapshot_download as hf_dl
    except ImportError:
        logging.warning("  hf-mirror 兜底需 huggingface_hub（pip install huggingface_hub），skip该通道")
        return None
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    logging.info("  [hf-mirror] 兜底下载 %s ...", desc)
    return hf_dl(repo_id, local_dir=local_dir)


def download_model(repo, local_dir, desc, kind, retry=3, force=False):
    """带retry + 镜像兜底 + 离线幂等的model下载。返回是否success。"""
    os.makedirs(local_dir, exist_ok=True)
    if not force and _model_present(local_dir, kind):
        logging.info("  ✅ %s already exists，skip下载（--force 可强制重下）", desc)
        return True

    last_err = None
    for attempt in range(1, retry + 1):
        try:
            _download_modelscope(repo, local_dir, desc)
            if _model_present(local_dir, kind):
                logging.info("  ✅ %s 下载success", desc)
                return True
        except Exception as e:
            last_err = e
            wait = 4 * (2 ** (attempt - 1))  # 4s, 8s, 16s 指数退避
            logging.warning("  modelscope 第 %d/%d 次failed: %s（%ds 后retry）", attempt, retry, e, wait)
            if attempt < retry:
                time.sleep(wait)

    # modelscope 全failed → 回退 hf-mirror 国内镜像兜底
    mirror_repo = HF_MIRROR.get(kind)
    if mirror_repo:
        try:
            _download_hf_mirror(mirror_repo, local_dir, desc)
            if _model_present(local_dir, kind):
                logging.info("  ✅ %s 经 hf-mirror 兜底下载success", desc)
                return True
        except Exception as e:
            logging.warning("  hf-mirror 兜底也failed: %s", e)

    logging.error("  %s 下载failed: %s", desc, last_err)
    return False


def download_mediapipe(work_dir):
    """下载posemodel；主源failed给出国内镜像/手动指引，不阻塞。"""
    import urllib.request
    dst = os.path.join(work_dir, "models", "pose_landmarker_full.task")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    logging.info("[3/3] 下载 pose_landmarker_full.task（主源 google，约 %dMB）...", MEDIAPIPE_SIZE_MB)
    try:
        urllib.request.urlretrieve(MEDIAPIPE_MAIN, dst)
        logging.info("  -> %s", dst)
        return True
    except Exception as e:
        logging.warning("  主源下载failed（国内网络波动常见）: %s", e)
        logging.warning("  ⚙️ 国内兜底方案（任选其一，手动下载后放到 %s）：", dst)
        logging.warning("    1) gitee 搜索 mediapipe-models 镜像仓库，取 pose_landmarker_full.task")
        logging.warning("    2) ModelScope 社区镜像搜索 'pose_landmarker_full' 手动拉取")
        logging.warning("    3) 用代理/非高峰时段retry本命令")
        logging.warning("  ⚠️ 该file缺失仅影响 Workflow B pose质检，face swap(Workflow A)不受影响。")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=".", help="model落地根directory")
    ap.add_argument("--with-mediapipe", action="store_true", help="额外下载 Workflow B posemodel")
    ap.add_argument("--retry", type=int, default=3, help="modelscope retry次数（默认 3）")
    ap.add_argument("--force", action="store_true", help="强制重新下载（忽略already exists的model）")
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
        "buffalo_l (检测+detect)", kind="buffalo",
        retry=args.retry, force=args.force)

    # 修正：buffalo_l 仓库可能多包一层directory，确保 .insightface/models/buffalo_l/*.onnx 就位
    if ok2:
        base = os.path.join(wd, ".insightface", "models", "buffalo_l")
        onnxs = [f for f in os.listdir(base)] if os.path.isdir(base) else []
        if not any(f.endswith(".onnx") for f in onnxs):
            import shutil
            for root, _d, files in os.walk(base):
                for f in files:
                    if f.endswith(".onnx"):
                        shutil.copy(os.path.join(root, f), base)
                        logging.info("  归位: %s", f)

    if args.with_mediapipe:
        download_mediapipe(wd)

    if ok1 and ok2:
        logging.info("✅ face swapmodelready；%s", "posemodel也已ready" if args.with_mediapipe else "Workflow B posemodel待补(用 --with-mediapipe)")
    else:
        logging.error("❌ 部分model下载failed，请按上方hint/tipprocess（优先 modelscope 源；已自动尝试 hf-mirror 兜底）")


if __name__ == "__main__":
    main()
