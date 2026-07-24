---
module: workflow-b-detail
priority: Medium (Workflow B core usage is already in SKILL.md; this file is the detailed technical doc)
last_verified: 2026-07-18
---

# Workflow B Detailed Technical Doc (Motion Transfer)

> SKILL.md already gives the "in plain words" explanation and model selection guide. This file is the detailed technical reference for the **complete 4-stage pipeline** + **three-model routing detailed parameters** + **first-success-rate engineering**.

---

## Essential Difference from Workflow A (must explain first)

- **Workflow A (face swap)**: "swap face" on the original video, motion / background / music / duration **100% kept** (100% overlap)
- **Workflow B (motion transfer)**: driven by the reference video's **motion**, generates a **brand-new video** - the target person (@Image1) "performs" the motion in the reference video (@Video1). The new video's background, quality, and motion details **won't be 1:1 identical to the original reference video**, which is an inherent property of the generative diffusion pipeline, not a defect
- **Selection principle**: want "exactly like the original video" → Workflow A; want "make the target person do the reference video's motion (background / quality can differ)" → Workflow B

## Stage B0: Material Ready & ASCII-ized

1. Copy reference video and target person photo to **ASCII filenames** (e.g. `ref_video.mp4`, `target.jpg`)
   ⚠️ Same pitfall as Workflow A: `cv2`/`mediapipe` easily fail on Chinese paths, must ASCII-ize first
2. Confirm dependencies installed: `mediapipe`, `opencv-python`, `numpy`
3. Confirm MediaPipe Pose model `pose_landmarker_full.task` is in place

## Stage B1: Skeleton Keypoint Extraction (Pose Estimation)

```bash
python scripts/pose_extract.py \
  --video "ref_video.mp4" \
  --out "pose_keypoints.json" \
  --model "models/pose_landmarker_full.task" \
  --step 1          # step=1 per-frame; step=N sample frames (faster)
```

Key points:
- Use **MediaPipe PoseLandmarker (Tasks API, BlazePose 33-point topology)** for per-frame inference
- Output per-frame 33 joint-point normalized coordinates `(x, y, z, visibility)` sequence → `pose_keypoints.json`
- **Role positioning**: motion QC + structured motion representation
  - QC: visible joint points ≥80% before entering generation (first-success-rate pre-gate)
  - Motion representation: can be fed to the generation model as a motion description

## Stage B2: Select Model + Motion Transfer

### Decision Gate B-0 (must ask before generation)

After receiving the target photo and before delegating generation, **must confirm handling of hairstyle / clothing / shoes-hat**:
- Option 1 (**recommended**): **Use the photo's full look** - ID lock most stable, output most like the target person
- Option 2: **Lock face only** - clothing / hairstyle / shoes-hat by prompt or separately specified
- Option 3: **Custom**

### v2.2.0 Major Change: Fully Localized

**Defaults to local equivalent** (zero cloud, zero cost, zero foreign service):
```bash
python scripts/video_engine.py --workflow B --video ref.mp4 --photo target.jpg --engine local
# automatically uses Workflow A face swap + keeps original video motion / background / music
```

**Engine routing table (v2.2.0)**:

| Engine | Paid? | Foreign? | Applicable | Notes |
|------|--------|--------|------|------|
| **local (default)** | ❌ **Zero cost** | ❌ **Zero foreign** | **Recommended** | Keeps original motion, zero cloud |
| agnes | ❌ Lifetime free | ❌ Domestic | Want "generate brand-new video" | Needs AGNES_API_KEY |
| nvidia | ❌ Free quota | ❌ Domestic | Want "generate brand-new video" | Needs NVIDIA_API_KEY |
| seedance | ⚠️ Trial version (paid over quota) | ❌ Domestic | ByteDance Seedance | Needs VOLCENGINE_API_KEY |
| kling | 💰 Paid | ❌ Domestic | Kuaishou Kling 3.0 | Needs KLING_API_KEY |

> **v2.2.0 removed Veo 3.1** (Google Vertex AI, foreign service) - user feedback "occasionally needs foreign service" cost points.

### Old Engine Detailed Comparison (historical reference only, v2.2.0 prefers local/agnes/nvidia)

| Dimension | Seedance 2.0 (ByteDance) | Kling 3.0/O3 (Kuaishou) |
|------|------|------|
| Motion transfer | ✓ Jimeng "motion imitation" | ✓✓ Motion Control benchmark |
| Native audio | ✗ None | △ Some versions have it |
| Resolution | 1080p | ✓✓ Native 4K 3840×2160 |
| Max duration | 8 sec | ✓✓ Iterative extension up to 3 min |
| Cost-performance | ✓✓ Extreme ($0.022/sec Fast) | Medium-high ($0.09/sec) |

### Routing Decision Table (v2.2.0)

| User need signal | Engine | Reason |
|-------------|--------|------|
| "Default" / "keep original motion" / "zero cost" | **local** | **Zero cloud zero cost zero foreign, recommended** |
| "Generate new video, free" | agnes | Lifetime free, domestically reachable |
| "Generate new video, larger free quota" | nvidia | NVIDIA free quota |
| "4K / long video / most realistic motion" | kling | Native 4K + Motion Control (needs paid key) |
| "9:16 vertical / fast output" | seedance | Native vertical + ultra-fast (trial version) |

### Step 2: Call Engine

#### local (default · zero cloud)
- Auto-calls `faceswap.py` (Workflow A face swap), **keeps original video motion / background / music**
- Zero cloud, zero cost, zero foreign service

#### AGNES (lifetime free)
- Async API, poll by task ID
- Suitable for users who want "generate brand-new video" and don't want to pay

#### NVIDIA (with free quota)
- NVIDIA NIM video generation API
- Only paid after free quota used up

#### Seedance 2.0 (domestic free trial)
- ByteDance Jimeng "motion imitation"
- Has free trial quota, paid over quota

#### Kling 3.0/O3 (needs paid key)
- Kuaishou open platform, **needs paid key**
- Native 4K, up to 3 min
- Applicable: want 4K / long video / most realistic motion

### Step 3: Solidify Parameter Presets (improve first-success-rate)

| Parameter | Vertical content | Horizontal content |
|------|---------|---------|
| Ratio | `--ratio 9:16` | `--ratio 16:9` |
| Duration | Seedance/AGNES 8s / Kling up to 3min | Same as left |
| seed | Fixed value for reproducibility; change seed on retry | Same as left |
| Prompt | Emphasize: keep reference motion, face from @Image1, avoid distortion | Same as left |

## Stage B3: Final Acceptance (technical-layer auto QC)

```bash
python scripts/auto_qc.py \
  --video "generated.mp4" \
  --expect-duration 8 \
  --out "qc_report.json"
# exit code 0=pass, 1=fail (triggers auto-retry)
```

- **Technical-layer QC** (machine automatic): file complete / openable, not all-black, not frozen-frame, duration met, encoding readable → auto-retry on fail
- **Picture quality** (user visual inspection): likeness, naturalness, distortion / ghosting - must be visually inspected by you finally
- Attach `pose_keypoints.json`'s "motion coverage / visibility stats" as objective motion-quality evidence

## First-Success-Rate Engineering (auto-retry on fail)

- First generation → QC fail → **auto-change seed** → second generation → fail → **downgrade model** → third
- Max 2 retries + 1 model switch, avoid infinite loop
- Still fail after retries → report to user "suggest manual parameter tuning or changing material"
