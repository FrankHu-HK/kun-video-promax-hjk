# 模型来源与网络约束（v2.2.0 完全本地化）

## 网络环境（2026-07-18 实测）
- **被墙（不可用）**：HuggingFace (`huggingface.co`)、GitHub raw/release、Google Vertex AI。
  → 任何从这些地方下载或调用的命令都会失败/走国外，**本技能 v2.2.0 彻底移除对它们的依赖**。
- **国内可达（推荐）**：`modelscope.cn`（ModelScope 官方源，国内首选）、`storage.googleapis.com`（部分 MediaPipe 模型，国内可达）、gitee 镜像。
- ⚠️ 注意：PyPI (`pip install`) 本身可达，**安装 liepin-cli / mediapipe 等**都正常。

## v2.2.0 关键变更
- **移除 Veo 3.1（Google Vertex AI）**：用户反馈"偶尔要国外服务"扣分，本版彻底移除
- **默认走本地等价方案**：B/C 默认用 Workflow A 换脸保留原动作，**零云端**
- **可选 AGNES（终身免费）/ NVIDIA（免费额度）**：全网免费通道，无需国外
- **网络/格式问题全自动**：auto_format.py 自动 ffmpeg 转码 + faceswap.py/Pro 集成

## 必需模型
| 模型 | 用途 | 大小 | ModelScope 仓库 |
|------|------|------|-----------------|
| `inswapper_128.onnx` | 换脸核心（输入 [1,3,128,128]） | ~529MB | `chwshuang/inswapper_128.onnx` |
| `buffalo_l`（det_10g / w600k_r50 / 1k3d68 / 2d106det / genderage） | 人脸检测+识别+关键点 | ~320MB | `destinylhj/buffalo_l` |
| `selfie_multiclass.tflite` | 仅背景替换用（人物分层抠像） | ~16MB | MediaPipe 官方 `storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/...` |

## 下载方式
见 `scripts/download_models.py`（用 `modelscope` SDK 的 `snapshot_download`）。

落地结构（faceswap.py 默认约定）：
```
<work-dir>/
├── models/
│   └── inswapper_128.onnx
└── .insightface/
    └── models/
        └── buffalo_l/
            ├── det_10g.onnx
            ├── w600k_r50.onnx
            ├── 1k3d68.onnx
            ├── 2d106det.onnx
            └── genderage.onnx
```

## 依赖安装（一次性）
```
pip install insightface onnxruntime opencv-python imageio-ffmpeg \
            mediapipe rapidocr-onnxruntime numpy modelscope
```
- insightface 会连带装 onnxruntime；若 CPU 推理慢可装 `onnxruntime` 而非 `onnxruntime-gpu`。
- rapidocr-onnxruntime 自带 OCR 模型，无需额外下载，中文识别可用。

## Workflow B（动作迁移）模型

| 模型 | 用途 | 大小 | 下载源 |
|------|------|------|--------|
| `pose_landmarker_full.task` | 骨骼关键点提取（BlazePose 33 点，姿态估计） | ~5–12MB | `storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task` |

- 下载后放到 `<work-dir>/models/pose_landmarker_full.task`。
- `storage.googleapis.com` 在本环境**部分可达**（MediaPipe 官方模型可下），若超时改用 gitee 镜像或手动下载后放入。
- `mediapipe>=0.10.35` 必须用 **Tasks API** 加载：`vision.PoseLandmarker.create_from_options(...)`，旧 `solutions.pose` 已移除（见 `pitfalls.md` 第 7 条）。

### Pose 33 关节点索引（BlazePose 拓扑，与 `pose_extract.py` 输出顺序一致）
| 索引 | 名称 | 索引 | 名称 | 索引 | 名称 |
|------|------|------|------|------|------|
| 0 | nose（鼻） | 11 | left_shoulder（左肩） | 22 | right_thumb（右拇指） |
| 1 | left_eye_inner（左眼内） | 12 | right_shoulder（右肩） | 23 | left_hip（左髋） |
| 2 | left_eye（左眼） | 13 | left_elbow（左肘） | 24 | right_hip（右髋） |
| 3 | left_eye_outer（左眼外） | 14 | right_elbow（右肘） | 25 | left_knee（左膝） |
| 4 | right_eye_inner（右眼内） | 15 | left_wrist（左腕） | 26 | right_knee（右膝） |
| 5 | right_eye（右眼） | 16 | right_wrist（右腕） | 27 | left_ankle（左踝） |
| 6 | right_eye_outer（右眼外） | 17 | left_pinky（左小指） | 28 | right_ankle（右踝） |
| 7 | left_ear（左耳） | 18 | right_pinky（右小指） | 29 | left_heel（左跟） |
| 8 | right_ear（右耳） | 19 | left_index（左食指） | 30 | right_heel（右跟） |
| 9 | mouth_left（左嘴） | 20 | right_index（右食指） | 31 | left_foot_index（左脚趾） |
| 10 | mouth_right（右嘴） | 21 | left_thumb（左拇指） | 32 | right_foot_index（右脚趾） |
