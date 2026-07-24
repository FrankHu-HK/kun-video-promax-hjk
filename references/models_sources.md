# Model Sources & Network Constraints (v2.2.0 fully localized)

## Network Environment (measured 2026-07-18)
- **Blocked (unavailable)**: HuggingFace (`huggingface.co`), GitHub raw/release, Google Vertex AI.
  → Any command downloading or calling from these will fail / go through foreign servers, **this skill v2.2.0 completely removed dependency on them**.
- **Domestically reachable (recommended)**: `modelscope.cn` (ModelScope official source, domestic first choice), `storage.googleapis.com` (some MediaPipe models, domestically reachable), gitee mirror.
- ⚠️ Note: PyPI (`pip install`) itself is reachable; **installing liepin-cli / mediapipe etc.** all works normally.

## v2.2.0 Key Changes
- **Removed Veo 3.1 (Google Vertex AI)**: user feedback "occasionally needs foreign service" cost points, this version completely removed it
- **Defaults to local equivalent**: B/C default to Workflow A face swap keeping original motion, **zero cloud**
- **Optional AGNES (lifetime free) / NVIDIA (free quota)**: all-domestic free channels, no foreign needed
- **Network / format issues fully automatic**: auto_format.py auto ffmpeg transcode + faceswap.py/Pro integration

## Required Models
| Model | Purpose | Size | ModelScope repo |
|------|------|------|-----------------|
| `inswapper_128.onnx` | Core face swap (input [1,3,128,128]) | ~529MB | `chwshuang/inswapper_128.onnx` |
| `buffalo_l` (det_10g / w600k_r50 / 1k3d68 / 2d106det / genderage) | Face detection + recognition + landmarks | ~320MB | `destinylhj/buffalo_l` |
| `selfie_multiclass.tflite` | Only for background replacement (person segmentation) | ~16MB | MediaPipe official `storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/...` |

## Download Method
See `scripts/download_models.py` (uses `modelscope` SDK's `snapshot_download`).

Landing structure (faceswap.py default convention):
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

## Dependency Installation (one-time)
```
pip install insightface onnxruntime opencv-python imageio-ffmpeg \
            mediapipe rapidocr-onnxruntime numpy modelscope
```
- insightface brings onnxruntime along; if CPU inference is slow you can install `onnxruntime-gpu` instead of `onnxruntime`.
- rapidocr-onnxruntime bundles OCR models, no extra download needed, Chinese recognition works.

## Workflow B (Motion Transfer) Model

| Model | Purpose | Size | Download source |
|------|------|------|--------|
| `pose_landmarker_full.task` | Skeleton keypoint extraction (BlazePose 33 points, pose estimation) | ~5–12MB | `storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task` |

- After download place at `<work-dir>/models/pose_landmarker_full.task`.
- `storage.googleapis.com` is **partially reachable** in this environment (MediaPipe official models downloadable); if it times out, use the gitee mirror or manually download then place it.
- `mediapipe>=0.10.35` must load via **Tasks API**: `vision.PoseLandmarker.create_from_options(...)`, the old `solutions.pose` is removed (see `pitfalls.md` item 7).

### Pose 33 Keypoint Index (BlazePose topology, consistent with `pose_extract.py` output order)
| Index | Name | Index | Name | Index | Name |
|------|------|------|------|------|------|
| 0 | nose | 11 | left_shoulder | 22 | right_thumb |
| 1 | left_eye_inner | 12 | right_shoulder | 23 | left_hip |
| 2 | left_eye | 13 | left_elbow | 24 | right_hip |
| 3 | left_eye_outer | 14 | right_elbow | 25 | left_knee |
| 4 | right_eye_inner | 15 | left_wrist | 26 | right_knee |
| 5 | right_eye | 16 | right_wrist | 27 | left_ankle |
| 6 | right_eye_outer | 17 | left_pinky | 28 | right_ankle |
| 7 | left_ear | 18 | right_pinky | 29 | left_heel |
| 8 | right_ear | 19 | left_index | 30 | right_heel |
| 9 | mouth_left | 20 | right_index | 31 | left_foot_index |
| 10 | mouth_right | 21 | left_thumb | 32 | right_foot_index |
