---
module: workflow-a-detail
priority: Medium (Workflow A core usage is already in SKILL.md; this file is the detailed technical doc)
last_verified: 2026-07-17
---

# Workflow A Detailed Technical Doc (Face Swap + Watermark Removal)

> SKILL.md already gives the "Beginner Quick Start" and the simplest commands. This file is the detailed technical reference for the **4-stage complete pipeline** + **Pro enhanced 6-layer design blueprint** + **all parameter details** + **step-by-step confirmation protocol**.
> 80% of users **don't need to read this file** - just use the simplest commands in SKILL.md.

---

## Stage 0: Material & Models Ready

1. Copy the user photo to an **ASCII filename** (e.g. `user_photo.jpg`).
   ⚠️ **Pitfall**: `cv2.imread` can't read Chinese / paths containing Chinese; must copy to a pure ASCII name before reading.
2. Confirm source video path and model path. If models are missing, run `scripts/download_models.py`.

## Stage 1: Face Swap (keep original background / motion)

### Decision Gate A-0 (must ask before generation)

After receiving the target photo and before running the swap, **must confirm the swap scope with structured questions**:

- Option 1 (**recommended**): **Only swap face**, keep the original video person's body / clothing / shoes-hat (most natural, lowest rework risk, fits Workflow A's "100% kept" positioning)
- Option 2: **Swap to the photo's full look** (face + hairstyle + clothing + shoes-hat) - needs diffusion repaint (Workflow B's ID lock / F fallback / or facefusion)
- Option 3: **Custom** (e.g. only swap face + use photo hairstyle but keep original clothing)

**Don't default.** Confirm before executing.

### Basic Face Swap Command

```bash
python scripts/faceswap.py \
  --video "source.mp4" \
  --photo "user_photo.jpg" \
  --out "swapped_raw.mp4" \
  --bbox "face_bboxes.json" \
  --models-dir "models" \
  --insight-root ".insightface" \
  --target-side right
```

### `--target-side` Parameter Detail

| Value | Behavior | Applicable scenario |
|---|---|---|
| `right` (recommended) | When two people in frame, swap **the rightmost face**; no swap in single-person shot | 90% of user scenarios |
| `left` | When two people in frame, swap **the leftmost face**; no swap in single-person shot | Left-side person scenario |
| `largest` | Swap the **widest bbox** face | ⚠️ High risk: when two faces are similar width, **per-frame mis-swap** of the supporting actor |

> ⚠️ **When to disable `largest`**: when two faces are similar width (e.g. right 143-187px / left ≈149px), in about 1/3 of frames the wider one is the supporting actor, and `largest` will **mis-swap per frame**. **Whenever the user wants "swap the right / specified-side person", always use `right`/`left` to lock by position**.

### Performance Optimization (built-in)

The basic face swap script already auto-pops unused models (`landmark_3d_68 / landmark_2d_106 / genderage`), CPU per-frame **8s → 1.4s** (about 5.7x speedup). No extra config needed.

### Error Codes (basic version)

| Code | Trigger | Solution |
|----|------|------|
| E200 | Photo doesn't exist or can't be read | Check file path / format |
| E201 | No face detected in photo | Switch to a clearer front-face photo |
| E202 | Video cannot be opened | Convert to mp4 |
| E203 | Model load failed | Re-run download_models.py |
| E204 | Single-frame processing failed (keeps original frame) | Skip, E104 reports skip ratio |
| E205 | Output video write failed | Check output directory permission |

## Stage 1-Pro: Enhanced Face Swap (2 layers A+B landed, 4 layers planned)

> ⚠️ **When to use Pro**: use the Pro channel when the basic version shows any of the following artifacts:
> ① **Side face not swapped** - when the person turns sideways, the side face is still the original video's face
> ② **Occlusion flash reveals original face** - the instant the face reappears after being blocked by an object is the original face
> ③ **Unnatural swap with glasses / accessories** - frame edge misalignment, fake face
> ④ **Stiff swap boundary seam** - visible square cutout edge

### Pro Enhancement Layer Design Blueprint (with landing status)

| Layer | Measure | Fixes which problem | Landing status |
|----|------|-----------|----------|
| A Detection enhancement | det_size 640→1024, det_thresh 0.5→0.3 | ① side-face miss ② occlusion miss | ✅ **Landed** (Pro enabled by default) |
| B Elliptical feathering | Enlarged elliptical feathering fusion mask, softens square hard edges | ③ stiff seam ② occlusion flash reveals original | ✅ **Landed** (enhanced_paste elliptical feathering) |
| C Temporal tracking | Failed-detection frame → previous successful frame ROI second low-threshold detection → short-gap displacement fill | ② occlusion flash ① side-face discontinuity | ⚙️ **Planned (not implemented)** |
| D Smart discard | Filter obviously wrong detections (too small / severely out of bounds / abnormal keypoints) | ① side-face discontinuity ④ boundary artifact | ⚙️ **Planned (not implemented)** |
| E Multi-face error prevention | Multi-person scenario target-consistency selection based on previous frame bbox | ② occlusion flash ① side-face discontinuity | ⚙️ **Planned (not implemented)** |
| F Diffusion fallback | Auto quality evaluation of output frames + low-quality frame soft-feather blending | ③④ extreme cases | ⚙️ **Planned (not implemented)** |

### Pro Command

```bash
python scripts/faceswap_pro.py \
  --video "source.mp4" \
  --photo "user_photo.jpg" \
  --out "swapped_pro.mp4" \
  --bbox "face_bboxes.json" \
  --fallback "fallback_frames.json" \
  --models-dir "models" --insight-root ".insightface" \
  --target-side right \
  --det-size 1024 --det-thresh 0.3 \
  --yaw-max 70 --gap-max 8
  # To keep framed glasses: add --keep-glasses
  # Debug: --no-feather disables feathering / --no-color disables skin-tone alignment
```

### Pro Output

- `swapped_pro.mp4`: Pro-enhanced (2 layers A+B landed) face swap video
- `fallback_frames.json`: frame ranges needing diffusion fallback repaint (format `{"ranges":[[start_frame,end_frame],...]}`)
- Console prints stats: `swapped` (normal swap) / `roi_rescued` (ROI second rescue) / `filled` (displacement fill) / `fallback` (hand to fallback) / `extreme_yaw` (extreme side face)

### Honest Boundary

- A/B/D/E are safe enhancements **significantly improvable** within the local framework; **① large-angle side face (yaw>70°) is a hard limit of the inswapper_128 architecture** - cannot reconstruct an invisible half-face out of thin air.
- `--keep-glasses` has no dedicated frame-segmentation model, so it **overlays the original eyes together** → eye gaze leans toward the original person; only suitable for scenarios where "must keep the original framed glasses".
- Pro version is slower than the basic version, a "quality-first" channel; use the basic `faceswap.py` when there are no artifacts for speed.
- Enhancements are not verified end-to-end on real material visually (current session model can't read images), only logic self-consistency is guaranteed; please spot-check with real videos.

### Pro Error Codes (E100-E105)

| Code | Meaning | Trigger | Solution |
|----|------|------|------|
| E100 | Photo read failed | Path / format / encoding issue | Check photo |
| E101 | No face | Face too small / occluded / side face | Switch to front-face photo |
| E102 | Model missing | inswapper/buffalo_l not downloaded | Re-run download_models.py |
| E103 | Video cannot be opened | Format / encoding issue | Convert to mp4 |
| E104 | Abnormal frames too high (>20%) | Too many processing failures | Switch to clearer video or photo |
| E105 | Retries exhausted | Model / network issue | Check environment then retry |

## Stage 2: Remove Douyin Full-Text Watermark (OCR + inpaint)

```bash
python scripts/clean_douyin.py \
  --input "swapped_raw.mp4" \
  --output "swapped_clean.mp4" \
  --scale 2 --radius 8
```

**Key points**:
- **Per-frame OCR** (rapidocr, default 2x zoom to improve small-text recall) matches Douyin keywords
- **Only inpaint text pixels** (radius 8, TELEA), zero accidental damage to background
- ⚠️ **Don't do all-1 mask inpaint on the whole block** - that reconstructs ≈ original, text fades but doesn't disappear. Must "OCR locate text bounding box → only fill text pixels"
- ⚠️ **Douyin text moving with the picture** (e.g. Douyin ID, author nickname): must OCR per-frame, **cannot use a fixed rectangular region**

## Stage 2.5: Remove Fixed "Douyin" Logo at Bottom-Right

Some Douyin videos have a **platform-level fixed logo** at bottom-right (constant coordinates, e.g. x≈614-697 / y≈1122-1167); because the text is small, stage 2's OCR occasionally misses it. Use fixed-region inpaint as fallback:

```bash
python fix_logo.py \
  --input swapped_clean.mp4 --output swapped_clean_v2.mp4 \
  --region 1100 1190 595 715 --radius 10      # y0 y1 x0 x1 (with margin)
```

## Stage 3: Compose Original BGM (ffmpeg)

Use the full version of ffmpeg (the ffmpeg bundled with CNTV is a crippled version, unusable):

```bash
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -i swapped_clean_v2.mp4 -i "source.mp4" \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a copy -movflags +faststart output_final.mp4
```

- Audio uses `-c:a copy` to **losslessly keep the original sound** from the source video (AAC 48kbps copied directly)
- Video transcodes from mp4v to libx264 for better compatibility and quality
- `-pix_fmt yuv420p` ensures phone playback

## Stage 4: Full-Video Re-Verification

```bash
python scripts/verify_final.py \
  --video output_final.mp4 \
  --bbox face_bboxes.json \
  --models-dir "models" --insight-root ".insightface" \
  --step 1          # step=1 full-video OCR (strictest); step=3 samples ~161 frames (faster)
```

Judgment:
- **Douyin watermark residue rate ≤ 2%** is controllable; for "carefully checked" delivery you should achieve **0 residue** (use stage 2.5 logo fallback)
- Also outputs face-swap coverage stats (total frames / swapped / right-side swapped / skipped frames)
- Current session model **cannot read images**; picture quality (likeness, naturalness, cutout feel) **must be visually inspected by the user**

## Extreme Side Face / Occlusion Practical Tips

| Situation | Recommended solution |
|------|---------|
| Ordinary side face (yaw≤70°) | Pro enhancement + detection size 1024 |
| Extreme side face (yaw>70°) | inswapper architecture hard limit, **no perfect solution** - split frames and process with Photoshop |
| Partial occlusion (glasses / hand block) | Pro enhancement (improvable) |
| Full occlusion (sunglasses + mask) | Skip that segment or process split frames |
| Want to keep glasses | `--keep-glasses` (has eye-gaze shift risk) |
| Background replacement need | **Revert to original background** (most stable) or turn to professional tools (Jianying / Premiere green-screen keying) |
