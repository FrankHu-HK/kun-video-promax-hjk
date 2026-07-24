---
module: troubleshooting
priority: High (this is the first doc users check when hitting errors)
last_verified: 2026-07-20
version: 2.4.2
---

# Troubleshooting Guide (detailed) v2.4.2

> **How to use**: the symptom you see → directly match it → troubleshoot by "cause → solution".
> This document **does not assume you have a technical background** — all terms are explained once.
> **v2.4.2 update**: extreme side-face / occlusion issues now have real solutions; added an advanced-feature troubleshooting section.
>
> If your case isn't covered here, send me "the specific error text + the command you ran".

---

## 📌 Effect Reference Note

> This file no longer embeds images (publishing platforms don't render PNG). Expected look per scenario is in SKILL.md's "Effect Expectation Comparison (text version)".

## Quick Table (by symptom category)

---

### ① Photo-related (E1xx errors)

#### Symptom: ❌ "Photo unreadable / cannot read photo"
**Plain translation**: the script can't open your photo file.

**Possible causes**:
- File locked by another program (open in preview)
- Too obscure format (HEIC, RAW)
- Path contains special characters or is too long

**Solutions**:
1. Close all preview programs
2. Use Windows Paint or an online tool to convert to JPG
3. Rename to a simple English alphanumeric name (`photo.jpg`), put in a simple path (`D:\photo.jpg`)

#### Symptom: ❌ "No face detected in photo" (E101)
**Plain translation**: no face found in the photo.

**Possible causes**:
- Face blocked by hair / sunglasses / mask
- Face too small (full-body wide shot)
- Too blurry / strong side face or low/high angle

**Solutions**:
1. Switch to a **front or near-front** clear portrait photo
2. Size ≥512×512 pixels
3. Fully expose forehead, eyes, nose, mouth
4. Even lighting, no backlight

---

### ② Video-related (E2xx errors)

#### Symptom: ❌ "Video cannot be opened" (E202/E103)
**Plain translation**: can't read the video file.

**Cause & solution**:
1. **Transcode to mp4** (Format Factory / HandBrake, H.264 codec) — the most common fix
2. First confirm it opens normally in a player
3. Filename contains no special characters

#### Symptom: ❌ "Video output failed" (E205)

**Cause & solution**:
1. Write permission on output directory? → Don't put it in `C:\Program Files\`
2. Disk space ≥1–2GB?
3. Simplify output path: `D:\output\result.mp4`

---

### ③ Model-related (E102 etc.)

#### Symptom: ❌ "Model load failed" (E102)

```bash
# Re-run model download
python scripts/download_models.py --work-dir . --with-mediapipe
```
Check whether `models/inswapper_128.onnx` and `buffalo_l/` exist.

#### Symptom: ❌ "Download very slow / failed"
1. Can you reach modelscope.cn?
2. Manually download into `models/`
3. MediaPipe auto-switches to gitee/ModelScope mirror

---

### ④ Face swap quality issues (⚠️ v2.4.2 major update)

#### Symptom: face looks "fake" / "strong cutout feel" after swap

| Rank | Cause | Solution |
|------|------|------|
| ① | Bad photo angle | Pick a photo with a closer angle |
| ② | Didn't use Pro version | Switch to faceswap_pro.py |
| ③ | Parameters not optimized | Add `--preset quality` |
| ④ | Low video quality | First upscale with enhance_4k.py |

```bash
python scripts/faceswap_pro.py --video in.mp4 --photo face.jpg --out out.mp4 --preset quality
```

#### Symptom: ordinary side face missed (≤70° yaw)

**v2.4.2 solution**:

```bash
# sideface preset: wider coverage + adaptive mask + extreme-frame auto-trim
python scripts/faceswap_pro.py --video in.mp4 --photo face.jpg --out out.mp4 --preset sideface
```

Underlying mechanism (lines 462–463) per-frame adaptive:
- larger yaw → larger mask_scale (max 1.8x), softer feather (max 0.2)
- no longer fixed parameters, but **dynamically adjusted per frame based on actual yaw**

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

#### Symptom: ⭐ Extreme side face (>70°) poor result — v2.4.2 already has a real solution

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**Old answer (v2.4.0): "no perfect solution"**
**New answer (v2.4.2): three-layer protection**

| Layer | Mechanism | Effect |
|------|------|------|
| L1 | `--preset sideface` (mask_scale=1.40, feather=0.11) | Coverage +50%, softer edges |
| L2 | Per-frame adaptive ms/feather formula | Dynamically follows yaw to enlarge |
| L3 | `--auto-trim-extreme` (auto-cut extreme frames) | Clean output without extreme-frame segments |

```bash
python scripts/faceswap_pro.py --video extreme_video.mp4 --photo face.jpg \
    --out result.mp4 --preset sideface --segment-secs 10
```

After completion, view `<output>_extreme_report.json` to learn the extreme-frame ratio and positions of each time segment. **If a segment's extreme-frame ratio >15%**, consider manually splitting that segment for separate processing or lowering expectations.

**Honesty statement**: for extreme side faces >80° or pure profile, the inswapper architecture itself still has physical limits. v2.4.2's three-layer protection significantly improves ≤75° scenarios, but >85° pure profile still recommends human intervention.

#### Symptom: ⭐ Face occluded (mask/sunglasses/hand) with obvious seams / ghosting at the edge

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**v2.4.2 solution**:

```bash
python scripts/faceswap_pro.py --video masked_video.mp4 --photo face.jpg \
    --out result.mp4 --preset occlusion
```

occlusion preset params: mask_scale=1.30 (penetrate occlusion area), feather=0.13 (strong feathering). Combined with the per-frame adaptive formula, larger occlusion area → wider and softer mask.

**Combination strategy**: side face + occlusion together → prefer `sideface` (larger mask_scale = 1.40 vs 1.30).

**Honesty statement**: fully blocked face (only eyes or lower visible) → AI physically cannot infer facial structure, no tool can help.

#### Symptom: traces at the background edge after swap
1. Pro version elliptical feathering fusion already landed → switch to faceswap_pro.py
2. Or keep the original video background (recommended, zero ghosting risk)

---

### ⑤ Watermark removal issues

#### Symptom: watermark residue remains after removal

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

1. Manual ROI: `--roi x y w h`
2. Raise parameters: `--scale 4 --radius 12`
3. Fixed logo fallback: `fix_logo.py`
4. Re-verify: `verify_final.py --video output.mp4 --bbox face_bboxes.json --step 1`

#### Symptom: picture becomes blurry after watermark removal
→ Lower `--radius` to 5–8 (too-large inpaint radius causes blur)

---

### ⑥ 🔥 Advanced Feature Troubleshooting (new in v2.4.2)

#### Symptom: `--resume` still runs from the start?

**Checkpoints**:
1. Does the `.resume_state.json` file exist and is readable? (should be at the same path as the output file)
2. Is the `"done"` list in the file non-empty?
3. Did you add `--resume` in the same command with a consistent output path?

**Debug command**:
```bash
# View resume state content
cat output.mp4.resume_state.json
# Should see {"done": [0, 1], "segs": {...}, ...}
```

If the state file is corrupted or empty → delete it and re-run (will start from the beginning but at least won't get stuck)

#### Symptom: concat stage error "ffmpeg concat failed"

**Cause**: ffmpeg unavailable or output path contains special characters

**Fallback**: code has built-in cv2 fallback (concat_videos line 231). If both fail:
1. Confirm ffmpeg installed and in PATH: `ffmpeg -version`
2. Manually concat seg files:
   ```bash
   # Generate concat list
   ls seg_*.mp4 | sort > concat_list.txt
   # add "file '" before each line with sed
   ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4
   ```

#### Symptom: `--workers N` parallel runs out of memory / OOM

**Cause**: each subprocess takes ~1–2GB memory, too-high workers exceeds physical memory.

**Solution**:
1. Lower workers count: `--workers 2` or `--workers 1` (serial)
2. Reduce concurrency: first `--workers 2` to test stability then gradually increase
3. Monitor memory: Windows Task Manager to see Python process memory usage

#### Symptom: batch_state.json locked / write failed

**Cause**: two parallel batch processes writing the same state file conflict

**Solution**:
1. Ensure only one batch process is running
2. If a lock remained from an abnormal exit last time → delete the old batch_state.json and re-run
3. `--resume` reads the old state, ensure only one process writes

#### Symptom: `--preset xxx` error "invalid choice"

**Available values**: auto / speed / quality / sideface / occlusion

```bash
# Correct examples
--preset quality      ✅
--preset sideface     ✅
--preset fast         ❌ (doesn't exist)
```

#### Symptom: extreme_report.json not generated

**Condition**: only generated after faceswap_pro.py finishes running (normal exit). Not generated on interruption.

**Solution**: run once completely and normally to generate it. To view progress mid-way, directly read the stats of each seg in `.resume_state.json`.

---

### ⑦ Cloud generation issues (Workflow B/C)

#### Symptom: ❌ "API Key invalid" / "auth failed"
1. Confirm the corresponding key is configured in the environment
2. Check if expired / disabled
3. Default channel Seedance needs no key

#### Symptom: ❌ "generation timeout" / "task failed"
1. Retry 1–2 times (default max 2 retries)
2. Check input material compliance
3. Switch engine (local → AGNES → NVIDIA → Seedance → Kling)

#### Symptom: generation result unnatural / wrong motion
1. Reference video motion clear and simple
2. Target photo angle matches
3. Retry with a different model (Kling motion most realistic)

---

### ⑧ General Troubleshooting Flow

```
[Step 1] Read the error code (E1xx/E2xx/E102)
  ↓ Look up the corresponding item in this quick table
[Step 2] Read the specific error message
  - Path issue?   → Use English path
  - File issue?   → Check file exists / format
  - Model issue?   → Re-run download_models.py
  - Advanced feature?   → See "⑥ Advanced Feature Troubleshooting"
[Step 3] Run diagnostic commands
  python scripts/auto_qc.py --input your_output.mp4
  python scripts/verify_final.py --video your_output.mp4 --bbox face_bboxes.json
[Step 4] Still not working?
  → Collect: error code + full command + screenshot → send me to help you check
```

---

### ⑨ Quality improvement issues

#### Symptom: still blurry / compression artifacts after 4K upscaling

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

1. Confirm input is not already a corrupted low-quality source (upscaling can't create detail out of thin air)
2. Recommended flow: **upscale first → then swap** (avoids secondary compression loss)
3. enhance_4k.py uses ffmpeg lanczos, clear improvement for 1080p→4K; sources below 720p have limited effect
4. For stronger effect: pre-process with Topaz Video AI (paid) or Real-ESRGAN (open source)

---

### ⑩ Batch advanced version issues

#### Symptom: batch stops entirely when one video fails halfway

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**Cause**: default behavior — any video failure aborts all.

**Solution**: add `--continue-on-error`:
```bash
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ \
    --out-dir out/ --workers 4 --continue-on-error --retry 2
```

#### Symptom: batch resume skipped all videos (all show skipped)

**Cause**: `batch_state.json` recorded last time's success status, `--resume` skips all.

**Solution**:
- Confirm product was indeed correctly generated → means last time actually succeeded
- To re-run all → **don't add `--resume`**, or delete `out_dir/batch_state.json`
- To re-run only failures → edit batch_state.json to change the corresponding video status from "success" to "fail"

#### Symptom: ETA inaccurate / progress stuck

**Cause**: ETA estimated from average rate of completed tasks; inaccurate when first few tasks fluctuate a lot.

**Normal phenomenon**: ETA converges to accurate after 3–5 tasks complete. If stuck for a long time (>10 min no log) → possible subprocess deadlock, Ctrl+C restart.

---

### ⑪ Preventive Check List (must pass before running)

| Check item | Status | Notes |
|--------|------|------|
| Python ≥3.10 | □ | mediapipe needs it |
| All dependencies installed (8 core packages) | □ | `download_models.py` one-click install |
| Models downloaded (models/) | ⬜ | Must run first time |
| Input mp4 format | □ | Transcode mov/avi first |
| Photo ≥512×512 clear front | ⬜ | Small / blurry / side-face photos work poorly |
| Filename English alphanumeric | ⬜ | Chinese path has fallback but explicit is better |
| Output directory writable | □ | ≥2GB disk space |
| Long video prepared to use `--resume` | ⬜ | Prevent wasted interruption |

**All checked ✓ → high chance of smooth run.**

---

## Error Code Quick Reference

| Code | Scope | Meaning | Script |
|----|------|------|------|
| E100–E105 | Pro face swap | faceswap_pro.py see [workflow-a-detail.md](workflow-a-detail.md) |
| E200–E205 | Basic face swap | faceswap.py see [workflow-a-detail.md](workflow-a-detail.md) |
| E400–E402 | Batch face swap | batch_faceswap.py (see Q10 advanced usage) |
| E001–E010 | Input validation | empty / missing param / conflict / too long etc. |

## Get More Help

- **FAQ** → [FAQ.md](FAQ.md)
- **10 practical pitfalls** → [pitfalls.md](pitfalls.md)
- **Model download sources** → [models_sources.md](models_sources.md)
- **Core command quick reference** → [../SKILL.md](../SKILL.md)
