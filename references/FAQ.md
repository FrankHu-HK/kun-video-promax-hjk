# Video Face Swap / Motion Transfer / AI Voiceover Commerce · FAQ v2.4.2

> Answers to high-frequency questions. This skill is only for legal and compliant personal / professional content creation, and is **strictly prohibited** from being used for any video production that infringes on others' portrait rights, spreads false information, or violates laws and regulations.
>
> **v2.4.2 update**: added a "Advanced Features" Q&A section (Q9–Q13), covering resume, extreme side-face optimization, occlusion handling, batch advanced version, and parameter presets. Each comes with a text effect description (publishing platforms don't render images; refer to the SKILL.md text comparison).

---

## 📌 Effect Reference Note

> This file no longer embeds images (publishing platforms don't render PNG). The **expected look** for each scenario is in SKILL.md's "Effect Expectation Comparison (text version)" — described with text + command→expected-output.

## I. Basic Questions

### Q1 · Face looks unnatural / has cutout feel after swap?

Most common causes in priority order:

| Rank | Cause | Solution |
|------|------|----------|
| ① | Target photo resolution insufficient or bad angle | Use a **front or near-front** clear portrait photo of ≥512×512 |
| ② | Didn't use Pro version enhanced fusion | Switch to `faceswap_pro.py` and add `--preset quality` |
| ③ | Video itself is low quality | First use enhance_4k.py to upscale then swap (expected look in SKILL.md "Effect Expectation Comparison" text version) |
| ④ | Large lighting / skin-tone difference | Photoshop pre-process the target photo (align skin tone and lighting direction) |

**Recommended command** (Pro + quality preset):
```bash
python scripts/faceswap_pro.py --video input.mp4 --photo target.jpg --out result.mp4 --preset quality
```

### Q2 · Watermark residue remains after removal?

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

clean_douyin.py's OCR positioning may miss small or drifting text:

1. **Manually specify ROI region**:
   ```bash
   python scripts/clean_douyin.py --input input.mp4 --output clean.mp4 --roi 1200 800 200 60
   ```
2. **Increase zoom factor**: `--scale 4 --radius 12` (defaults may be insufficient)
3. **Fixed logo fallback**: `python scripts/fix_logo.py --video ...` to handle badges / logos
4. **Dynamic overlay text**: split frames per-frame → Photoshop batch → ffmpeg reassemble

Verify command:
```bash
python scripts/verify_final.py --video output.mp4 --bbox face_bboxes.json --step 1
```

### Q3 · Face swap too slow?

Python + inswapper does per-frame inference on CPU, 1080p is slow by default. Choose a strategy as needed:

| Strategy | Command | Applicable scenario |
|------|------|----------|
| **Turbo mode** | `--preset speed` | Quick preview / short clips |
| **Balanced mode** | `--preset auto` (default) | Daily use |
| **Quality mode** | `--preset quality` | Final output |
| **Lower resolution** | First scale to 720p with ffmpeg then swap | Save time on very long videos |
| **Segmented test** | First run first 30 sec to confirm OK | Most time-saving debugging |

**speed preset** internally auto-sets det_size=512 (about 40% faster than default 1024), single frame drops from ~1.4s to ~0.8s.

### Q4 · Chinese path error?

The insightface/opencv underlying C++ doesn't support Unicode paths. All scripts have a built-in ASCII temp-directory fallback — copy the input file to a temp directory for processing then move it back. If it still errors:

1. Input filename contains Chinese / spaces / special chars → rename to pure English alphanumeric (e.g. `photo.jpg`)
2. Output path contains spaces → use a simple path (e.g. `D:\output\result.mp4`)
3. Model files incomplete → re-run `python scripts/download_models.py`

### Q5 · Model download failed / can't connect to ModelScope?

The script already prioritizes the domestic ModelScope source. If download fails:

1. Check whether the network can reach `modelscope.cn`
2. Manually download `inswapper_128.onnx` and `buffalo_l` into the `models/` directory
3. MediaPipe model downloads from googleapis.com by default → script auto-switches to gitee/ModelScope mirror
4. HuggingFace/GitHub currently unreachable (blocked)

---

## II. 🔥 Advanced Feature Usage (new in v2.4.2)

> This section answers how to use the "advanced features" repeatedly mentioned in the review report. Each feature is implemented in the underlying code and callable directly via commands.

### Q6 · How to tune parameters conveniently? How to use the `--preset` parameter presets? (★ Recommended)

v2.4.2 added **5 parameter presets**; one `--preset xxx` auto-configures underlying parameters like det_size / mask_scale / feather, no need to tune each manually.

| Preset | det_size | mask_scale | feather | Applicable scenario |
|------|----------|------------|---------|----------|
| `auto` | 1024 | 1.15 | 0.06 | Default balance (compatible with old commands) |
| `speed` | **512** | 1.10 | 0.05 | Quick preview, short video |
| `quality` | 1024 | 1.25 | 0.09 | Final output, high-quality needs |
| **`sideface`** | 1024 | **1.40** | **0.11** | **Side-face video, large yaw** |
| **`occlusion`** | 1024 | **1.30** | **0.13** | **With occlusion (mask/hand/sunglasses)** |

**Usage examples**:
```bash
# Side-face video → auto widen coverage + softer edges + enable extreme-frame auto-trim
python scripts/faceswap_pro.py --video sideface_video.mp4 --photo face.jpg --out out.mp4 --preset sideface

# Masked occlusion → adaptive occlusion fusion
python scripts/faceswap_pro.py --video masked_video.mp4 --photo face.jpg --out out.mp4 --preset occlusion

# Pursue highest quality
python scripts/faceswap_pro.py --video final.mp4 --photo face.jpg --out out.mp4 --preset quality

# Batch face swap also supports preset passthrough
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir output/ --preset quality --workers 4
```

**You'll feel it next time**: no need to remember det_size/mask_scale/feather values, just pick a preset name; side-face and occlusion scenarios improve noticeably.

### Q7 · Extreme side face (large yaw) swap looks bad? → Use sideface preset + adaptive occlusion

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**Symptom**: person in video often turns to the side (>70°), after swap the side face is still the original or has obvious seams.

**v2.4.2 solution** (three-layer protection):

1. **`--preset sideface`**: auto-sets mask_scale=1.40 (wider coverage), feather=0.11 (softer edges), and enables `--auto-trim-extreme`
2. **Per-frame adaptive occlusion** (underlying code lines 462–463): each frame dynamically enlarges the mask based on actual yaw
   ```
   ms = min(mask_scale × (1 + 0.15 × yaw), 1.8)   // larger side face → wider coverage
   fe = min(feather + 0.05 × yaw, 0.2)            // softer edges
   ```
3. **auto_trim_extreme**: auto-detects extreme side-face frames (yaw > 70% threshold), generates a "clean version with extreme frames removed" (seg_XXX_trim.mp4) for you to pick when finalizing concatenation

**Recommended command**:
```bash
python scripts/faceswap_pro.py --video your_video.mp4 --photo target.jpg \
    --out result.mp4 --preset sideface --segment-secs 10
```

After completion it also outputs `<out>_extreme_report.json`, listing the extreme-frame ratio and specific positions of each time segment, convenient for locating problem segments.

### Q8 · Face occluded (mask/sunglasses/hand blocking)? → occlusion preset

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**Symptom**: person wears a mask, sunglasses, or hand covering half the face; after swap obvious seams / ghosting appear at the occlusion edge.

**v2.4.2 solution**:

1. **`--preset occlusion`**: mask_scale=1.30 (wider coverage to penetrate occlusion area), feather=0.13 (strong feathering to soften edges)
2. **Adaptive occlusion formula same as above** (ms/feather adjust dynamically with yaw): larger occlusion area → wider mask, softer edges
3. **Combination advice**: if the video has both side face + occlusion, prefer `sideface` (its mask_scale is larger)

**Recommended command**:
```bash
python scripts/faceswap_pro.py --video masked_video.mp4 --photo target.jpg \
    --out result.mp4 --preset occlusion
```

**Note**: when the whole face is fully blocked (only eyes or less visible), no AI face swap can help — this is a physical limit, not a code defect.

### Q9 · Swap interrupted / crashed halfway, how to resume? → Segmented resume

**Symptom**: processing a long video crashes midway, power loss, or manual Ctrl+C interruption, the previously processed frames wasted.

**v2.4.2 solution — segmented resume (underlying implementation)**:

The script auto-splits the video by `--segment-secs` (default 15 sec) into multiple segments. Each segment is processed independently and saved as `seg_000.mp4`, `seg_001.mp4` ... while maintaining a state file `<output>.resume_state.json`:

```json
{
  "done": [0, 1, 2],
  "segs": { "0": [...], "1": [...] },
  "stats": { "0": {"extreme": 3, "face": 120, ...} }
}
```

**Run again with `--resume`**:
```bash
# Normal run (first time)
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4

# Resume after interruption (just add --resume, auto-skips completed segments)
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4 --resume
```

Resume logic:
- Read `.resume_state.json`, skip segments already in the `done` list
- Only process unfinished segments
- After all segments complete, auto-concatenate into full output with ffmpeg lossless (fallback to cv2)
- **Two-layer resume**: if you use batch_faceswap.py's `--resume`, it skips completed **entire videos**; and each video's internal faceswap_pro.py also receives `--resume`, resuming from its own segments

**You'll feel it next time**: long videos no longer fear mid-crash. After a power restart just add `--resume` to continue; processed segments won't re-run.

### Q10 · How to run batch processing efficiently? → Advanced version (parallel + preset + precise resume)

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

**v2.4.2 batch face swap adds 3 advanced capabilities**:

#### 10a. Parallel processing `--workers N`

```bash
# Serial (default, stable, memory-light)
python scripts/batch_faceswap.py --photo face.jpg --videos "v1.mp4;v2.mp4;v3.mp4" --out-dir out/

# 4-way parallel (recommended for multi-core CPU, ~2-3x faster)
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4 --preset quality
```

- Uses Python `ThreadPoolExecutor`, each video starts an independent faceswap subprocess
- Progress displayed in real time: `progress 12/20 (60%) elapsed 180s estimated remaining 120s`
- Note: too-high `--workers` may cause out-of-memory (each subprocess takes ~1-2GB), recommend ≤ CPU core count

#### 10b. Parameter preset passthrough `--preset`

In batch mode directly passed to each Pro subprocess (see Q6 preset table):
```bash
--preset quality   # all videos use quality mode
--preset sideface  # all videos use side-face optimization mode
```

#### 10c. Precise resume `--resume` (batch_state.json)

```bash
# First run (normal)
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4

# Resume after interruption (read batch_state.json, skip completed videos)
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ --out-dir out/ --workers 4 --resume
```

- State file `out_dir/batch_state.json` records **precise status of each video** (success/fail/pending)
- On resume, skip entries with status="success" and non-empty product
- Pair with `--continue-on-error` to tolerate individual failures and continue the rest

---

## III. Workflow Differences

### Q11 · What do Workflow A/B/C/D/E each do?

| Workflow | Function | Technical route | Keeps original motion? |
|--------|------|----------|--------------|
| **A** Face swap | Replace original face with target photo | inswapper local face swap | ✅ 100% kept |
| **B** Motion transfer | Target person "performs" reference motion | Generative (local equivalent / optional cloud) | ❌ Brand-new generation |
| **C** AI voiceover | Product → virtual host intro | Generative (local equivalent / optional cloud) | ❌ Brand-new generation |
| **D** 4K upscaling | Low-res → high clarity | ffmpeg lanczos / enhance_4k.py | ✅ Content kept |
| **E** Batch face swap | One photo × N videos | A's batch wrapper | ✅ Each 100% kept |

**Iron rule**: to keep original motion you can only use A/E, not B/C.

### Q12 · Does Workflow B/C need external services?

B/C v2.2.0 **defaults to local equivalent** (zero cloud, zero cost, zero foreign service). Optional cloud upgrade channel (AGNES/NVIDIA/Seedance/Kling) — all domestically reachable. **Most scenarios need no cloud.**

### Q13 · After motion transfer the person's motion is unnatural / like "noodle limbs"?

1. Check the reference video: single person, full body, clear motion, no occlusion
2. Reduce motion complexity (large jumps / fast spins work poorly)
3. Switch to Kling 3.0 (Motion Control benchmark)
4. First run `pose_extract.py` for motion QC (joint points ≥80% before entering generation)

### Q14 · How to use lip-sync digital human?

Workflow C's lip-sync is in two steps: ① generate the person video ② digital-human tool does lip-sync. Recommended: Tencent Zhiying (SaaS) or HeyGem (can be local). This skill only provides material preparation.

---

## IV. Installation & Environment

### Q15 · Which dependencies to install?

Core packages: opencv-python, insightface, onnxruntime, mediapipe, pillow, numpy, imageio[ffmpeg], tqdm. Full list in `download_models.py`.

One-click install:
```bash
python scripts/download_models.py --work-dir . --with-mediapipe
```

### Q16 · Can it run on CPU?

✅ Yes. inswapper face swap runs purely on CPU (1080p 30fps about 5–15 sec/frame), recommend at least 8GB RAM. Pro version det_size=1024 needs more memory. GPU acceleration: install `onnxruntime-gpu` instead of `onnxruntime`.

### Q17 · Which video formats are supported?

Input: mp4/mov/avi/mkv/webm (OpenCV VideoCapture supported). Output: unified mp4 (H.264). Special formats convert to mp4 first.

---

## V. Quality Improvement

### Q18 · How to do 4K upscaling? How does it look?

(Text comparison in SKILL.md "Effect Expectation Comparison", publishing platform doesn't render images)

Two ways:

1. **ffmpeg lanczos built-in upscaling** (Workflow D default):
   ```bash
   python scripts/enhance_4k.py --input 1080p.mp4 --output 4k.mp4
   ```

2. **Upscale before face swap** (recommended flow): upscale to 4K first → then swap → effect far better than swap-then-upscale (avoids secondary compression loss)

---

## VI. Security & Compliance

### Q19 · Can this skill be used commercially?

MIT license, free to use and modify. But output must comply with: ① **Do not infringe portrait rights** ② **Do not produce false information** (AI synthesis must be labeled) ③ **Follow platform rules**. The creator is legally responsible for the output.

### Q20 · Can I swap a foreign celebrity / politician's face?

**Absolutely not.** Unauthorized celebrity portraits are illegal, and political figures involve national security red lines. Only your own or authorized photos are allowed.

### Q21 · Will my photos / videos be uploaded to the cloud?

Workflow A/D/E **execute 100% locally**, no data upload. B/C default to local equivalent, no API call. When choosing the cloud channel, only necessary parameters / material are sent to the corresponding domestic API, **no raw data sent to foreign third parties**.

### Q22 · Will the output video be detected as AI-generated by platforms?

Watermark removal only removes platform-added text / badges. AI-generated content (B/C) should be labeled "AI-generated" per platform rules when published. This skill is not an "evasion detection" tool.
