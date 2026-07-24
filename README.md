# 🎬 KUN Video ProMax HJK · AI Viral Video Factory (Local-First)

> A fused, professional-grade **AI video production agent** (v2.9.0) with two layers: a **Local Production Layer** (face-swap, watermark removal, motion transfer, AI voiceover, 4K upscale, batch face-swap) that runs **100% locally — zero cloud, zero foreign servers, zero cost** — and a **Director Planning Layer** (AI director engine, cinematic storyboarding, prompt-engineering compiler, honest quality guard) that is free and dependency-light.

> 🔒 **Two non-negotiable baselines:** (1) Generation/production defaults to fully local, zero-cloud. (2) Quality assessment never exaggerates — it does technical QC + asks for human review, it does **not** fake a score.

---

## ✨ Why this exists

Most "AI video" tools either lock you into a paid cloud, or promise magic and deliver a fake URL. KUN Video ProMax is built the opposite way: real, runnable local pipelines, honest status, and a director brain that actually plans the shot — not just a prompt box.

---

## 🎯 Key Features

### Local Production Layer (real, runnable)
- **Face-swap** (`faceswap_pro.py`) — multi-layer enhancement; atomic checkpoint writes so interrupted runs resume without data loss.
- **Watermark removal** — strip Douyin / fixed-logo watermarks while keeping original motion, background, and audio.
- **Motion transfer (Workflow B)** — real two-step local pipeline: `pose_extract.py` (optical-flow action intensity / clarity / static-ratio pre-check, runs even without mediapipe) → `video_engine.py` chains pre-check → face-swap for genuine output.
- **AI voiceover (Workflow C, v2.9.0)** — `tts_voiceover.py` turns a script into a **real local voiceover** (default `pyttsx3` offline / zero-foreign / zero-cost; optional `edge_tts` free cloud), then `video_engine` composites it over product footage / host image into a talking-head MP4 (optional BGM).
- **4K upscale** (`enhance_4k.py`) — `ffmpeg` upscale + `unsharp` real sharpening, with a clarity-comparison report; optional `cv2.dnn_superres`.
- **Batch face-swap** + resumable runs + auto codec / format transcode.

### Director Planning Layer (free, local)
- **AI director engine** — cinematic shot design and storyboarding.
- **Prompt-engineering compiler** — turns a brief into shoot-ready prompts.
- **Honest quality guard** — technical QC only; flags for human review; never invents a score.
- **Deterministic entry** — `video_engine.py --mode director` launches the director layer without guessing how to start.

### Integrity
- Cloud engines (agnes / nvidia / seedance / kling) are **honestly marked unimplemented** — selecting one returns explicit error `E200` and guides you to local. No fake URLs.
- `kun_setup.py` — one-click install + self-check to cut first-run friction.

---

## 🚀 How to use

This is an **AI-agent skill** (runs inside the WorkBuddy agent platform) and also a **local Python toolkit**.

```bash
# One-click setup / self-check
python kun_setup.py

# Local production examples
python video_engine.py --mode director        # director planning layer
python video_engine.py --mode faceswap ...     # face-swap pipeline
python tts_voiceover.py --text "your script"   # local AI voiceover
python enhance_4k.py --input video.mp4         # 4K upscale
```

> **Requirements:** Python 3.10+, `ffmpeg` on PATH, and the packages listed in `requirements.txt`. Everything runs on your machine.

---

## 🧩 What's inside

| Path | Purpose |
|------|---------|
| `SKILL.md` | Unified skill definition (both layers) |
| `scripts/` | `video_engine.py`, `faceswap_pro.py`, `pose_extract.py`, `tts_voiceover.py`, `enhance_4k.py`, `kun_setup.py` |
| `references/` | Workflow docs, capability-status matrix, honest-status notes |
| `README.md` | This document |

---

## 🌍 Who it's for

- **Short-video creators** wanting local, private, cost-free production.
- **Marketers** needing talking-head / product videos without a studio.
- **Makers** who refuse cloud lock-in and fake outputs.

---

## 💖 Sponsor

If this factory saves you a cloud subscription and actually renders your video, consider sponsoring its development. Sponsorship keeps it **local-first, honest, and free**.

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen)](https://github.com/sponsors/FrankHu-HK)

> GitHub Sponsors is the only official donation channel for this project.

---

## 📄 License

Released under the [MIT License](./LICENSE). Authored by 胡景堃 (Frank Hu).
