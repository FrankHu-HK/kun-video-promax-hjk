# -*- coding: utf-8 -*-
"""
下载换脸所需模型（国内源优先，避免被墙）。
本脚本只下载"本地可跑"部分（换脸 + 姿态提取），云端生成模型由可选升级通道（AGNES 终身免费 / NVIDIA 免费额度 / Seedance 国内免费试用 / Kling 需付费 Key）提供，**v2.2.0 彻底移除 Veo 3.1 等国外服务**。

运行: python scripts/download_models.py --work-dir <工作目录> [--with-mediapipe] [--retry 3] [--force]
  - 默认下载 inswapper_128.onnx + buffalo_l（均走 modelscope 国内源，国内稳定可达）
  - 网络韧性：modelscope 失败自动指数退避重试（默认 3 次），全失败再回退 hf-mirror 国内镜像兜底
  - 离线幂等：模型已存在则跳过，避免重复下载（--force 可强制重下）
  - --with-mediapipe：额外尝试下载 Workflow B 姿态模型 pose_landmarker_full.task
    （主源 storage.googleapis.com 国内偶有超时，失败会给出国内镜像/手动下载指引，不中断主流程）

国内网络约束（详见 references/models_sources.md）：
  - HuggingFace / GitHub 被墙，勿尝试从此处下载（仅 hf-mirror.com 镜像作为兜底通道）
  - 换脸模型一律优先走 modelscope（国内可达）
  - MediaPipe 模型主源在 google，国内波动时走 gitee 镜像或 ModelScope 社区镜像手动补
依赖: pip install modelscope
"""
import os
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")

# MediaPipe 姿态模型：主源 + 国内备选说明（主源失败不崩溃，给出可操作指引）
MEDIAPIPE_MAIN = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                  "pose_landmarker_full/float16/latest/pose_landmarker_full.task")
MEDIAPIPE_SIZE_MB = 12

# 各模型在 hf-mirror.com 的兜底仓库（modelscope 全失败时尝试）
HF_MIRROR = {
    "inswapper": "ezioruan/inswapper_128.onnx",
    "buffalo": "junior90/buffalo_l",
}


def _model_present(local_dir, kind):
    """离线幂等判断：模型是否已就位，避免重复下载。"""
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
        logging.warning("  hf-mirror 兜底需 huggingface_hub（pip install huggingface_hub），跳过该通道")
        return None
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    logging.info("  [hf-mirror] 兜底下载 %s ...", desc)
    return hf_dl(repo_id, local_dir=local_dir)


def download_model(repo, local_dir, desc, kind, retry=3, force=False):
    """带重试 + 镜像兜底 + 离线幂等的模型下载。返回是否成功。"""
    os.makedirs(local_dir, exist_ok=True)
    if not force and _model_present(local_dir, kind):
        logging.info("  ✅ %s 已存在，跳过下载（--force 可强制重下）", desc)
        return True

    last_err = None
    for attempt in range(1, retry + 1):
        try:
            _download_modelscope(repo, local_dir, desc)
            if _model_present(local_dir, kind):
                logging.info("  ✅ %s 下载成功", desc)
                return True
        except Exception as e:
            last_err = e
            wait = 4 * (2 ** (attempt - 1))  # 4s, 8s, 16s 指数退避
            logging.warning("  modelscope 第 %d/%d 次失败: %s（%ds 后重试）", attempt, retry, e, wait)
            if attempt < retry:
                time.sleep(wait)

    # modelscope 全失败 → 回退 hf-mirror 国内镜像兜底
    mirror_repo = HF_MIRROR.get(kind)
    if mirror_repo:
        try:
            _download_hf_mirror(mirror_repo, local_dir, desc)
            if _model_present(local_dir, kind):
                logging.info("  ✅ %s 经 hf-mirror 兜底下载成功", desc)
                return True
        except Exception as e:
            logging.warning("  hf-mirror 兜底也失败: %s", e)

    logging.error("  %s 下载失败: %s", desc, last_err)
    return False


def download_mediapipe(work_dir):
    """下载姿态模型；主源失败给出国内镜像/手动指引，不阻塞。"""
    import urllib.request
    dst = os.path.join(work_dir, "models", "pose_landmarker_full.task")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    logging.info("[3/3] 下载 pose_landmarker_full.task（主源 google，约 %dMB）...", MEDIAPIPE_SIZE_MB)
    try:
        urllib.request.urlretrieve(MEDIAPIPE_MAIN, dst)
        logging.info("  -> %s", dst)
        return True
    except Exception as e:
        logging.warning("  主源下载失败（国内网络波动常见）: %s", e)
        logging.warning("  ⚙️ 国内兜底方案（任选其一，手动下载后放到 %s）：", dst)
        logging.warning("    1) gitee 搜索 mediapipe-models 镜像仓库，取 pose_landmarker_full.task")
        logging.warning("    2) ModelScope 社区镜像搜索 'pose_landmarker_full' 手动拉取")
        logging.warning("    3) 用代理/非高峰时段重试本命令")
        logging.warning("  ⚠️ 该文件缺失仅影响 Workflow B 姿态质检，换脸(Workflow A)不受影响。")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=".", help="模型落地根目录")
    ap.add_argument("--with-mediapipe", action="store_true", help="额外下载 Workflow B 姿态模型")
    ap.add_argument("--retry", type=int, default=3, help="modelscope 重试次数（默认 3）")
    ap.add_argument("--force", action="store_true", help="强制重新下载（忽略已存在的模型）")
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
        "buffalo_l (检测+识别)", kind="buffalo",
        retry=args.retry, force=args.force)

    # 修正：buffalo_l 仓库可能多包一层目录，确保 .insightface/models/buffalo_l/*.onnx 就位
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
        logging.info("✅ 换脸模型就绪；%s", "姿态模型也已就绪" if args.with_mediapipe else "Workflow B 姿态模型待补(用 --with-mediapipe)")
    else:
        logging.error("❌ 部分模型下载失败，请按上方提示处理（优先 modelscope 源；已自动尝试 hf-mirror 兜底）")


if __name__ == "__main__":
    main()
