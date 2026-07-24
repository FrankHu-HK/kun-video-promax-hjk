<div align="center">

  <img src="banner.svg" alt="KUN Video ProMax banner" width="100%" />

  <h1>KUN Video ProMax</h1>

  <p><b>Local-first AI video factory</b> - face-swap, motion transfer, AI voiceover, 4K upscale, and a director planning layer. 100% local, zero cloud, zero cost.</p>

</div>



<p align="center">

  <a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/stargazers"><img src="https://img.shields.io/github/stars/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Stars"></a>

  <a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/network/members"><img src="https://img.shields.io/github/forks/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Forks"></a>

  <a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/issues"><img src="https://img.shields.io/github/issues/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Issues"></a>

  <a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/blob/master/LICENSE"><img src="https://img.shields.io/github/license/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="License"></a>

  <a href="https://img.shields.io/github/last-commit/FrankHu-HK/kun-video-promax-hjk?style=flat-square"><img src="https://img.shields.io/github/last-commit/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Last commit"></a>

  <a href="https://github.com/sponsors/FrankHu-HK"><img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen" alt="Sponsor"></a>

</p>



<p align="center">

  <img src="https://img.shields.io/badge/Platform-Local%20First-0ea5e9?style=flat-square" alt="Local First">

  <img src="https://img.shields.io/badge/Zero%20Cloud-Yes-22c55e?style=flat-square" alt="Zero Cloud">

  <img src="https://img.shields.io/github/languages/top/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Language">

</p>



<p align="center">

  English

</p>



---



## What is KUN Video ProMax?



KUN Video ProMax is a fused, professional-grade **AI video production agent** (v2.9.0) with two layers:



- **Local Production Layer** - face-swap, watermark removal, motion transfer, AI voiceover, 4K upscale, and batch face-swap that run **100% on your machine**. No cloud, no foreign servers, no subscription.

- **Director Planning Layer** - an AI director engine, cinematic storyboarding, a prompt-engineering compiler, and an honest quality guard that is free and dependency-light.



> 🔒 **Two non-negotiable baselines:** (1) Generation/production defaults to fully local, zero-cloud. (2) Quality assessment never exaggerates - it does technical QC + asks for human review, it does **not** fake a score.



## Why KUN Video ProMax?



### The problem with most "AI video" tools



- **Cloud lock-in** - your footage leaves your machine and you pay per render.

- **Fake outputs** - some tools return a fake URL and call it "done".

- **Document-only features** - promised capabilities that were never actually wired to a pipeline.



### Core approach: real pipelines, honest status



This project ships **runnable local pipelines**, not promises:



- Cloud engines (agnes / nvidia / seedance / kling) are **honestly marked unimplemented** - selecting one returns explicit error `E200` and guides you to local. No fake URLs.

- `kun_setup.py` - one-click install + self-check to cut first-run friction.



## Features



- **Face-swap** (`faceswap_pro.py`) - multi-layer enhancement with **atomic checkpoint writes** so interrupted runs resume without data loss.

- **Watermark removal** - strip Douyin / fixed-logo watermarks while keeping original motion, background, and audio.

- **Motion transfer (Workflow B)** - a real two-step local pipeline: `pose_extract.py` (optical-flow action intensity / clarity / static-ratio pre-check, runs even without mediapipe) → `video_engine.py` chains pre-check → face-swap for genuine output.

- **AI voiceover (Workflow C, v2.9.0)** - `tts_voiceover.py` turns a script into a **real local voiceover** (default `pyttsx3` offline / zero-foreign / zero-cost; optional `edge_tts` free cloud), then `video_engine` composites it over product footage / host image into a talking-head MP4.

- **4K upscale** (`enhance_4k.py`) - `ffmpeg` upscale + `unsharp` real sharpening, with a clarity-comparison report; optional `cv2.dnn_superres`.

- **Batch face-swap** + resumable runs + auto codec / format transcode.

- **Director Planning Layer** - `video_engine.py --mode director` launches the director brain (storyboard + prompt compile) without guessing how to start.

- **Honest quality guard** - technical QC only; flags for human review; never invents a score.



## Quick Start



### Prerequisites



- **Python 3.10+**

- **ffmpeg** on `PATH`

- Packages listed in `requirements.txt`



### Install & run



```bash

# One-click setup / self-check

python kun_setup.py



# Director planning layer

python video_engine.py --mode director



# Local face-swap pipeline

python video_engine.py --mode faceswap --input src.mp4 --target face.jpg



# Real local AI voiceover

python tts_voiceover.py --text "your script"



# 4K upscale

python enhance_4k.py --input video.mp4

```



## Development



1. Fork and clone the repo.

2. `python -m venv .venv && pip install -r requirements.txt`

3. `python kun_setup.py` to validate the environment.

4. Run the self-check scripts in `scripts/` before opening a PR.



## Roadmap



See [ROADMAP.md](ROADMAP.md).



## Contributing



Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and the DCO sign-off rule.



<a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/graphs/contributors">

  <img src="https://contrib.rocks/image?repo=FrankHu-HK/kun-video-promax-hjk" />

</a>



## 💖 Sponsor



If this factory saves you a cloud subscription and actually renders your video, consider sponsoring its development. Sponsorship keeps it **local-first, honest, and free**.



[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen)](https://github.com/sponsors/FrankHu-HK)



## License



[MIT](LICENSE) - Copyright 2026 Frank Hu (Hu Jingkun).

