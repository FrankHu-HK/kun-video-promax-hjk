# Pitfalls & Practical Conclusions (distilled from real production)

## 1. Face swap direction: must be Face Swap, not generative video
- When the user wants "motion exactly like the original video" → only insightface+inswapper face swap works.
- VideoGen / Seedance / Zhipu image-to-video = generate new motion from prompt, **cannot copy the original clip's motion**.
  First time we fell into this: generative output had wrong motion / background / BGM entirely.

## 2. Chinese path: cv2.imread can't read it
- Symptom: reading the user photo returns None.
- Root cause: `cv2.imread`'s underlying C++ implementation doesn't support Unicode paths (common with Windows Chinese usernames / Chinese folders).
- ❌ Wrong approach: pass a path containing Chinese directly to cv2
  ```python
  img = cv2.imread("C:/Users/Photos/myface.jpg")   # returns None, can't read
  ```
- ✅ Correct approach: copy to an ASCII temp name then read (faceswap.py already has this fallback built in)
  ```python
  import shutil, tempfile, os
  tmp = os.path.join(tempfile.gettempdir(), "user_photo.jpg")
  shutil.copy(src_path, tmp)
  img = cv2.imread(tmp)                          # reads normally
  ```
- Solution: copy to an ASCII name then read; faceswap.py already has this fallback built in.

## 3. CPU performance: 8s → 1.4s per frame (key optimization)
- Root cause: insightface by default loads all models (detection + recognition + 3D/2D landmarks + gender/age).
- Face swap only needs detection + recognition. **Actually delete** the extra models from the `app.models` dict:
  ```python
  for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:
      app.models.pop(_k, None)
  ```
- ⚠️ Pitfall: cannot just set `app.landmark_3d_68 = None` (top-level attribute is ineffective, still runs);
  must use `app.models.pop()`. Verification: per-frame time dropped from 8s to 1.4s, 1048 frames took about 24 minutes.

## 4. "AI-generated" removal: whole-block inpaint fails
- Wrong approach: `cv2.inpaint` with an all-1 mask on a fixed region → reconstruction ≈ original, text fades but doesn't disappear, OCR still recognizes it.
- Correct approach: per-frame **OCR locate text bounding box → only inpaint the text pixels (with 8px margin) (radius 6, TELEA)**.
  Zero accidental damage to background, text disappears completely. Douyin AI badges often **intermittently fade in/out** (so users see "occasionally appears"),
  must process per-frame rather than sampling a few frames.

## 5. Douyin screen recording UI layout (check one frame before cropping)
- Top: status bar + search bar (y≈0~165)
- Left: red packet / small badges (includes "AI-generated" small badge, about x≈10~72, y≈498~524)
- Main picture: dancing person (y≈390~880, person centered and lower, smaller proportion)
- Right: avatar + follow / interaction bar (x≈620~720, overlaid on main picture)
- Bottom: fullscreen key / caption / music tag / search recommendation (y≈880~1554)
- Crop params `crop=W:H:X:Y` must be measured against the actual frame, never hardcode (differs per video).

## 6. Background replacement: ghosting is hard to cure, prefer reverting to original background
- Segmentation (MediaPipe / matting) background replacement produces **per-frame edge temporal jitter → ghosting / floating**.
- De-ghosting means: causal EMA temporal smoothing (β≈0.35) + large sigma Gaussian feathering (σ≈8) + person color matching.
- But with pure CPU and no strong matting model, it's still hard to be perfect. When users dislike ghosting, **reverting to "use the original video background" is most stable**
  (only swap face + remove badge, no background replacement). Only attack scene replacement like the Forbidden City when the user explicitly wants it, and inform of the risk in advance.

## 7. Model / library version pitfalls
- mediapipe 0.10.35 **no longer has the `solutions` API**, must use the Tasks API:
  `from mediapipe.tasks.python import vision; vision.ImageSegmenter.create_from_options(...)`.
- The `facefusion` on PyPI is an empty package (version 0.0.0, no actual code), don't use it.

## 8. Final verification
- The current session model **cannot read images**, picture quality can only be visually inspected by the user.
- But "AI-generated" text removal can be programmatically verified with OCR (verify_clean.py), must have 0 residue before delivery.

## 9. Persisting & presenting
- Files are always saved to the relevant workspace (general convention).
- Delivery uses file preview/display to present in the dialog, ensuring the user can preview / download directly.

## 10. Motion transfer (Workflow B): generates a new video, not 1:1 copy
- Workflow B uses `@Video1` (reference video motion) + `@Image1` (target photo identity) to delegate `seedance-video-gen` to generate a new video.
- Essentially different from Workflow A: A = 100% keeps original motion / background / audio; B = **generates a brand-new video**, background / quality / motion details not identical to original.
  Before delivery, you must explain this positioning first to avoid the misunderstanding "why is it different from the original video".
- Reference video quality determines the transfer ceiling: single person, full body, clear motion, no occlusion is best; multi-person / severe occlusion lowers quality.
- MediaPipe Pose extraction in stage B1 is mainly for **motion QC** (visible joint-point stats) and optional local retargeting input;
  the default diffusion generation doesn't depend on that JSON, `@Video1` motion is understood internally by the generation model.
- Picture quality (likeness, naturalness, ghosting) can only be visually inspected by the user, AI cannot read images.
- `mediapipe>=0.10.35` Pose must use the Tasks API (`vision.PoseLandmarker`), old `solutions.pose` is removed.
