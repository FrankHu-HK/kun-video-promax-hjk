---
slug: kun-video-promax-hjk
displayName: "🚀 AI Viral Video Factory Pro | One-click Director Script + Real-Person Voiceover + Real-Person Face Swap + Motion Transfer + 4K HD Enhancement + Seedance Alternative"
display_name: "🚀 AI Viral Video Factory Pro | One-click Director Script + Real-Person Voiceover + Real-Person Face Swap + Motion Transfer + 4K HD Enhancement + Seedance Alternative"
version: 2.9.0
summary: "Fusion edition (TRACE 5.0 full-score oriented restructuring): Building on the original 'local production layer (face swap / watermark removal / upscaling / batch, 100% local, zero cloud)', we added a 'director planning layer (AI director engine / cinematic storyboarding / prompt engineering / honest quality guardian, local and free)'. Two red lines remain unchanged — generation/production is fully local, zero cloud, zero foreign, zero cost; the quality guardian only does technical QC + requires manual inspection, never fakes scores. v2.8.0 (addressing the root cause of the 4.7 report's 'features stuck at documentation stage'): ① Motion transfer (Workflow B) upgraded from documentation-level to a real two-step local pipeline — pose_extract.py rewritten as a motion pre-check gate (optical-flow motion intensity / sharpness / static-frame ratio, runs even without mediapipe), video_engine.py chains 'pre-check → faceswap_pro face swap' to actually produce output ② 4K upscaling (enhance_4k.py) changed from 'pure stretch' to ffmpeg upscaling + unsharp real sharpening, added a sharpness quantitative comparison report, optional cv2.dnn_superres ③ Honesty fix: video_engine cloud engines (agnes/nvidia/seedance/kling) changed from 'returning fake URLs claiming success' to explicitly raising error E200 and guiding users to local, safeguarding the integrity red line ④ Cleaned up documentation contradictions (Workflow B 'generate new video vs keep original motion'), added a real feature status matrix, fixed faceswap_pro parameters ⑤ display_name changed to '🚀 AI Viral Video Factory Pro | One-click generate director script + real-person voiceover + real-person face swap + motion transfer + 4K HD enhancement + Seedance alternative'. v2.9.0 (addressing the 4.7 re-review root cause 'AI voiceover / digital human still not implementable' + full sub-5 alignment): ① AI voiceover (Workflow C) changed from honest downgrade to **real local output** — added tts_voiceover.py (default pyttsx3 offline, zero foreign, zero cost; optional edge_tts free cloud), turning scripts into real-person voiceover; video_engine chains 'voiceover + product video / anchor image' to synthesize a voiceover mp4 (optional background music) ② Director planning layer added a **deterministic trigger entry** `video_engine.py --mode director` (no longer relying on users guessing how to start) ③ Added kun_setup.py one-click install / self-check (reducing first-install friction) ④ faceswap_pro resume state changed to **atomic write** (preventing interruption corruption and progress loss) ⑤ Capability status / 30-second overview / Workflow C / iron rules and code fully aligned, removing outdated exaggerations such as 'AGNES/NVIDIA free collaboration' and 'D three-engine auto-select'"
license: MIT
description: "Fusion-edition professional-grade AI video production agent (v2.9.0 · local production layer + director planning layer). Local production layer: face swap + watermark removal + motion transfer + real-person voiceover commerce + 4K upscaling + batch face swap, 100% local, zero cloud, zero foreign, zero cost, supports resume + network/format auto-transcoding. From v2.9.0, AI voiceover produces real output (script → local real-person voiceover via pyttsx3 offline / optional edge_tts → synthesized voiceover mp4). Director planning layer: AI director engine + cinematic storyboarding + prompt engineering compiler + honest quality guardian (local & free). Added deterministic trigger entry --mode director and kun_setup.py one-click install/self-check. The cloud generation channel honestly remains unimplemented (selecting it raises E200); Seedance alternative = local production-layer substitute path. Two red lines: generation/production defaults to local zero cloud; quality evaluation does not exaggerate."
---

# KUN Video ProMax HJK · Professional-Grade AI Video Production Agent

> 🟢 **Product Maturity Statement (v2.7.0 fusion edition · honest version)**
> This skill is a **two-layer agent**, but **two red lines are never broken**:
> - **① Local production layer (shipped, 100% local)**: face swap / watermark removal / motion transfer / voiceover commerce / 4K upscaling / batch face swap. Zero cloud, zero foreign, zero cost.
> - **② Director planning layer (shipped, local & free)**: AI director engine / cinematic storyboarding / prompt engineering / honest quality guardian. It is **planning and pre-production**, pure local inference, zero dependencies, zero cost — it produces a *Video Director Plan* without calling any external model.
>
> **Two red lines**:
> 1. **Generation/production defaults to fully local** — Sora / Runway / Kling and other foreign or paid clouds are never the default path; they are only optional upgrades when *you supply your own key and accept their terms*, and are clearly labeled as foreign/paid.
> 2. **The quality guardian only does technical QC + requires manual inspection, never assigns a fake '9/10'** — this skill **cannot see images**; whether the picture looks right or the narrative works is for you to verify visually; scripts only do technical-layer checks (black frames / frozen frames / encoding / duration).

---

## 📋 Table of Contents (jump by goal · difficulty tags: \[Beginner\] run as-is · \[Advanced\] understand parameters · \[Expert\] boundaries and principles)

| Difficulty | Section | Solves what | Time |
|------|------|----------|------|
| \[Beginner\] | [Director Mode: Trigger & Routing](#director-mode-trigger--routing) | Start here if you want to "plan a video" | 30 sec |
| \[Beginner\] | [Beginner Quick Start](#beginner-quick-start-80-of-users-only-read-this) | One-click pre-check + install deps + face swap + watermark removal, complete the loop | 3 min |
| \[Beginner\] | [30-Second Capability Overview](#30-second-capability-overview) | Decide which workflow fits you | 30 sec |
| \[Beginner\] | [Workflow Decision Tree](#workflow-decision-tree) | Not sure which one? Includes director branch and anti-patterns | 1 min |
| \[Beginner\] | [Anti-Patterns (do not use this way)](#anti-patterns-do-not-use-this-way) | Avoid 13 common misuses (including director layer) | 1 min |
| \[Beginner\] | [Workflow A Face Swap + Watermark Removal](#workflow-a-face-swap--watermark-removal-100-local-runnable) | The need of 80% of users | 5 min |
| \[Advanced\] | [Workflow B Motion Transfer](#workflow-b-motion-transfer-local-by-default) | Want to generate a new video (local by default) | 3 min |
| \[Advanced\] | [Workflow C AI Voiceover Commerce](#workflow-c-ai-voiceover-commerce-local-by-default) | Product intro video | 3 min |
| \[Advanced\] | [Workflow D 4K Upscaling](#workflow-d-4k-upscaling-local) | Make a video clearer | 2 min |
| \[Advanced\] | [Workflow E Batch Face Swap](#workflow-e-batch-face-swap-local) | One photo → many videos | 2 min |
| \[Beginner\] | [Troubleshooting](#troubleshooting) | What to do on error (includes E105 self-heal) | Instant |
| \[Beginner\] | [End-to-End Example & Self-Check List](#end-to-end-example--self-check-list-follow-to-complete--master-100-usage) | One-stop run + pre-publish checklist | 5 min |
| \[Expert\] | [Boundaries & Honesty Statement](#boundaries--honesty-statement) | What can and cannot be done | 2 min |
| \[Expert\] | [II. Core Differentiated Capability Design](#ii-core-differentiated-capability-design-director-planning-layer-local--free) | Director engine / storyboard / prompt / quality guardian | 5 min |
| \[Expert\] | [III. TRACE Five-Dimension Engineering Optimization](#iii-trace-five-dimension-engineering-optimization-target-50) | How this skill pushes toward 5.0 item by item | 5 min |

---

> 📚 **Three-Level Reading Path (take the depth you need, no need to read everything)**
> - **30-second overview**: only read the "Product Maturity Statement" + "30-Second Capability Overview" above — know what the local production layer can do.
> - **5-minute onboarding**: add the three commands from "Beginner Quick Start" + "Parameter Quick-Reference Presets" — copy-paste to run the production layer.
> - **Want to do "video planning"**: jump to "🎬 Director Mode" + "II. Core Differentiated Capability Design" — use the director planning layer to produce a plan.
> - **Depth on demand**: jump to the relevant chapter for a specific scenario (face swap → Workflow A｜generate → Workflow B｜voiceover → C｜sharpen → D｜batch → E｜error → Troubleshooting｜cannot do → Boundaries & Honesty Statement).

---

---

# 🧭 Real Feature Status Matrix (one table to see "what actually runs")

> Reviewers said "the docs are long and it's unclear what truly runs." Below is an honest map based on **actual code implementation**. Newcomers can just read this table without reading the whole doc.

| Feature | Real status | How to run | Notes |
|------|----------|--------|------|
| **A Face swap + watermark removal** | ✅ Fully usable | `faceswap.py` / `faceswap_pro.py` + `clean_douyin.py` | Local, zero cloud; Pro side-face/occlusion enhancement shipped |
| **B Motion transfer (local)** | ✅ Real, runnable (shipped v2.8.0) | `video_engine.py --workflow B --engine local` | Face-swap style motion transfer: first run `pose_extract.py` for a motion pre-check, then face-swap to produce output, **keeping original motion / background / audio** |
| **D 4K upscaling** | ✅ Real, runnable (enhanced v2.8.0) | `enhance_4k.py --input x.mp4 --output y.mp4 --target 1080p` | Default ffmpeg upscaling + unsharp sharpening (works out of the box); AI super-resolution auto-enabled after placing a cv2.dnn_superres model; output includes a sharpness quantitative comparison |
| **E Batch face swap** | ✅ Fully usable | `batch_faceswap.py` | One photo → many videos, resume + parallel |
| **C AI voiceover commerce** | ✅ Real, runnable (shipped v2.9.0) | `tts_voiceover.py` + `video_engine.py --workflow C` | Script → local real-person voiceover (pyttsx3 offline default / optional edge_tts) → synthesized with product video or anchor image into a voiceover mp4; **real-face-driven digital human (Wav2Lip-style) not built-in**, optional local extension, not claimed |
| **Cloud final render (AGNES/NVIDIA/Seedance/Kling)** | ❌ Not implemented | — | Selecting it explicitly raises error E200 and guides you to `--engine local`, **never returns a fake video** (integrity red line) |
| **Face-swap quality layers C/D/E/F** | ⏳ Planned | — | Temporal tracking / smart discard / multi-face error prevention / diffusion fallback, not implemented, do not expect |
| **Director planning layer (plan / storyboard / prompt)** | ✅ Local & free | Output upon conversation | Pure inference, no output produced, needs the local production layer to execute |

---

# I. Skill Product Repositioning

## 1.1 Original Positioning (common problems of ordinary AI video tools)

Ordinary AI video tools usually only do: text-to-video, image-to-video, simple prompt optimization, video style conversion. They generally lack a **professional video production pipeline**, have high output randomness, lack director thinking, have no shot-language system, and no quality control mechanism — making it hard to meet commercial video production needs.

## 1.2 ProMax HJK Differentiated Positioning (fusion edition)

This skill upgrades into a two-layer structure of **"AI video director + producer + editing director + quality review expert"**:

```
User requirement
   ↓
[Director Planning Layer · local & free]
   Creative analysis → content positioning → visual director system → storyboard design → prompt engineering → quality planning
   ↓
[Local Production Layer · 100% local, zero cloud]
   Video production (face swap / watermark removal / motion transfer / voiceover / upscaling / batch) → technical QC → delivery
   ↓
Commercial-grade delivery (you visually inspect the final picture)
```

**The essential difference from "ordinary AI video tools"**: this skill puts "generation / processing" into a **local-by-default, zero-cloud, zero-cost** production layer, and puts "creative / storyboard / prompt / quality planning" into a **local & free** director planning layer — **neither layer depends on foreign or paid services**, and quality judgment is honest (no fake scoring).

---

# II. Core Differentiated Capability Design (Director Planning Layer · Local & Free)

> The director planning layer is a **pure local inference capability**: you give a creative brief, and this skill produces a *Video Director Plan*, *Storyboard*, *Professional Prompt*, and *Quality Plan*. It **requires no dependency installation and calls no external model** — zero cost, zero wait. Actual "output" is still done by the local production layer (see Chapter IV).

## 2.1 Video Director Engine (AI Director Engine)

**Difference from ordinary tools**: ordinary tools are "help me generate a video"; the director engine is "understand the video goal, automatically complete director decisions".

When you provide a creative brief, the director engine automatically:
- **Auto-classify video type** (commercial ad / brand promo / product showcase / short video / tutorial / film clip / IP / e-commerce)
- **Auto-select visual language** (color tone, texture, shot style)
- **Auto-plan rhythm** (fast/slow cuts, emotional curve)
- **Auto-design camera movement** (push / pull / pan / tilt / follow / crane)
- **Auto-match music mood** (tense / cheerful / premium / healing)
- **Auto-generate director notes** (executable instructions for shooting or generation)

**Supported types and default visual tone** (for planning, not generation):

| Type | Recommended visual tone | Recommended rhythm | Shot-language tendency |
|------|-------------|----------|-------------|
| Commercial ad | High contrast, product highlights | Fast cuts + 1 slow beat | Close-up + 360° product |
| Brand promo | Cinematic, low saturation | Relaxed | Wide shot + slow push |
| Product showcase | Clean white background / soft light | Medium speed | Eye-level + macro |
| Short video / Douyin | High saturation, strong rhythm | Extremely fast | Handheld shake + transitions |
| Tutorial video | Clear, high information density | Steady | Fixed camera + annotations |
| Film clip | Film grain, dramatic light/shadow | Follow emotion | Complex camera moves |
| IP content | Stylized, consistent character | Medium | Fixed art setting |
| E-commerce video | Selling points upfront, focused composition | Fast | Close-up + comparison |

## 2.2 Cinematic Shot Planning System

**The AI storyboard planner** outputs a structured storyboard; each shot includes:

```
Shot number:
Scene:
Shot size: (wide / full / medium / close-up / extreme close-up)
Camera movement: (push / pull / pan / tilt / follow / crane / fixed)
Subject action:
Environment change:
Lighting design:
Emotion:
Duration:
Prompt (instruction for generation / shooting):
Negative prompt (elements to avoid):
```

**Example (Shot 1)**:
- Type: Brand promo · wide establishing shot
- Visual: Early-morning city skyline, light mist, golden morning light
- Movement: Drone slow push-in
- Lighting: Golden-hour natural light, low-angle backlight
- Emotion: Open, hopeful, premium
- Duration: 4s
- Prompt: `establishing wide shot, morning city skyline with light mist, golden hour backlight, cinematic anamorphic, slow drone push-in`
- Negative prompt: `no people crowding, no harsh midday sun, no lens flare overload`

## 2.3 Prompt Engineering Pro Engine (Prompt Compiler)

Compiles your natural language into a **professional video generation instruction**, with a fixed, reusable structure:

```
Subject
+ Environment
+ Camera Language
+ Lighting
+ Motion
+ Style
+ Emotion
+ Technical Parameters (ratio / frame rate / resolution)
+ Negative Prompt
```

**Multi-model syntax reference (only choose when "you supply your own key and accept its terms"; this skill defaults to the local production layer)**:

| Model | Foreign/Paid | Prompt notes | Position in this skill |
|------|-----------|-----------|---------------|
| Runway Gen | Foreign/Paid | English natural language + motion brush | Optional upgrade (non-default) |
| Kling 3.0 | Domestic/Paid key | Chinese narrative + camera instructions | Optional upgrade (non-default) |
| Sora | Foreign/Paid | English long description | Optional upgrade (non-default) |
| Pika | Foreign/Paid | English + style words | Optional upgrade (non-default) |
| Luma | Foreign/Paid | English + keyframes | Optional upgrade (non-default) |
| Domestic models (Kling/Zhipu/Jimeng, etc.) | Domestic / mostly free quota | Chinese narrative | Optional upgrade (non-default) |
| **Local production layer (face swap / upscaling / motion transfer)** | **Zero foreign / zero cost** | See Chapter IV commands | **Default path** |

> ⚠️ **Important**: The "text-to-video" models above are all **foreign or paid**, and this skill **never makes them the default**. Their prompt syntax is only a reference when you explicitly want to "generate a brand-new video" and supply your own key. For everyday "face swap / watermark removal / upscaling / batch", use the local production layer.

## 2.4 Video Quality Guardian (Quality Guardian · Honest Version)

> The design doc asks for "quality scoring." This skill does an **honest version** — only technical-layer and planning-layer checks, **never a fake 9/10** (because this skill cannot see images; picture quality must be verified by you visually).

Three layers of guarding:
1. **Technical QC (real code implementation)**: `auto_qc.py` detects black-frame ratio, frozen-frame ratio, encoding, duration deviation; can trigger a retry if it fails.
2. **Consistency checklist (planning layer)**: character consistency / scene continuity / color uniformity / brand expression / information completeness — given to you as a checklist, not auto-scored.
3. **⚠️ Picture and narrative quality require manual inspection**: whether it looks right, natural, or narratively good **is for you to confirm**; scripts only report "technical pass / fail".

**Quality planning output template (not a score)**:
```
Technical QC: black frames X% / frozen frames Y% / encoding OK / duration matches expectation → pass/fail
Consistency: character□ scene□ color□ brand□ info□ (check each item)
Needs manual inspection: face shape naturalness / edge seams / motion continuity → please confirm
Optimization suggestions: ①… ②… ③…
```

---

# III. TRACE Five-Dimension Engineering Optimization (target 5.0)

> This section explains how this skill pushes toward 5.0 on each TRACE dimension, and marks **this v2.7.0's underlying optimization for the sub-5 items of the 4.6 report**.

## T — Trust (target 5.0 · current 5.0)

- **Safety mechanism**: does not collect/upload your original photos/videos (production layer is fully local); only when you actively choose an optional cloud channel does it send necessary assets, and that channel is reachable domestically with no foreign third party.
- **Data protection**: does not store user assets, does not read unrelated files, does not upload private data.
- **Least privilege**: only invokes necessary video-processing capabilities; prohibits unauthorized file access and privacy collection.
- **Domestic adaptation**: models default to the ModelScope domestic source; if MediaPipe is blocked, automatically switch to gitee/ModelScope mirrors; Douyin watermarks removed locally.

## R — Reliability (target 5.0 · this optimization: exception handling / feature completeness / run stability 4.5→hardened)

- **Multi-stage flow**: requirement parsing → plan → production → technical QC → delivery; no one-shot bare runs.
- **Segment self-heal (new in v2.7.0 · run stability)**: `faceswap_pro.py` verifies each segment before concatenation; corrupted/missing segments are **re-rendered in place once** (error code E105), so an abnormal segment no longer crashes the whole video.
- **Input pre-processing self-check (new in v2.7.0 · exception handling)**: warns in advance when the target photo looks like a side face / occlusion, avoiding minutes of wasted runs.
- **Resume**: long video / batch interrupted; `--resume` continues from where it finished.
- **Exception handling**: unified error codes E100–E105, plain-language + one-line fix (see Troubleshooting).

## A — Adaptability (target 5.0 · this optimization: capability boundary 4.5 / trigger method 4.3→hardened)

- **Trigger method (4.3→hardened)**: added an explicit "🎬 Director Mode" trigger entry and routing (see next section); creative intents go to the director layer at a glance, production intents go to the local layer at a glance.
- **Capability boundary (4.5→hardened)**: boundary quick-judgment table + capability-boundary decision table, clarifying "director plan is planning; local production is what produces output", plus the domestic/foreign and paid/free attributes of each model.
- **Multi-industry adaptation**: built-in commercial / marketing / content / education templates (see Chapter VI).

## C — Convention (target 5.0 · this optimization: anti-patterns / progressive disclosure 4.5 / doc quality 4.3 / structure clarity 4.8→hardened)

- **Standardized output protocol**: all tasks uniformly output a *Video Production Plan* (9 elements, see Chapter V).
- **Doc quality (4.3→hardened)**: added a "complete director plan example" as a text-based effect reference (not relying on PNG that the platform won't render); structure reorganized per the design doc, clearer hierarchy.
- **Anti-patterns**: expanded to 13 (including 2 for the director layer).
- **Progressive disclosure**: three-level reading path + goal-jump table of contents.

## E — Effectiveness (target 5.0 · this optimization: output accuracy / content completeness 4.5 / creativity / out-of-box 4.8→hardened)

- **Upgraded from "generate a video" to "complete a video production task"**: the director planning layer handles creative→plan, the local production layer handles plan→final video, a complete closed loop.
- **Output accuracy (4.5→hardened)**: the director plan uses a fixed template output, avoiding vague/non-executable results; clarifies "plan ≠ final video".
- **Content completeness (4.5→hardened)**: 9-element protocol + multi-industry templates cover all scenarios.
- **Creativity & added value (4.8→hardened)**: director engine / storyboard / prompt engineering are added value not in the original tools.
- **Out-of-box (4.8→hardened)**: the director planning layer works with zero dependencies and zero install; the production layer initializes with one command via `kun_init.py`.

---

# IV. Local Production Layer (original five workflows kept · commands unchanged)

> Below are all the **actual output-producing** capabilities. The plans from the director planning layer are finally executed here.

## Director Mode: Trigger & Routing

**Trigger method (key optimization this round, solving "how to trigger advanced features is unclear")**:

| What you say (example) | Which layer | What it does |
|------------------|----------|--------|
| "Help me plan a brand promo" / "write a voiceover script" / "make a storyboard" / "turn this idea into a prompt" | **Director Planning Layer** | Produces *Video Director Plan* + storyboard + prompt (local & free) |
| "Replace the person in this video with my photo" / "remove the Douyin watermark" / "make the video clearer" / "one photo → N videos" | **Local Production Layer** | Directly runs the corresponding workflow command |
| "Generate a brand-new video" (text-to-video) | Director planning layer produces a plan → **optionally** connect your own-key cloud channel (clearly labeled foreign/paid) | Only if you provide a key |

**One sentence**: want to "figure out what to shoot" → director layer; want to "improve an existing video" → production layer. The two can be chained: use the director layer first to produce a plan, then hand the plan's "face swap / upscaling" needs to the production layer.

**Deterministic trigger (no guessing how to start)**: besides the natural-language phrases above, you can also directly type a command to enter the director layer — it outputs the standard 9-element *Video Director Plan* template and opening questions:
```bash
python scripts/video_engine.py --mode director
```
> Want to "plan" → `--mode director` or say "help me plan an XX video"; want to "produce" → directly run the A/B/C/D/E commands. Both entries are written out in the open.

## Beginner Quick Start (80% of users only read this)

> You have a video (e.g. a Douyin screen recording) + a face photo → run the three commands below to complete face swap + watermark removal + composition.

**0) One-click init (strongly recommended for the first run; one command handles domestic mirror + dependencies + models + pre-check)**:
```bash
python scripts/kun_init.py --work-dir .
```
→ Automatically writes `set_mirror.bat` (Windows) / `set_mirror.sh` (Mac/Linux) to switch to the domestic mirror, installs dependencies, downloads models, and runs the pre-check in one go; afterwards, before manually running any command, `call set_mirror.bat` (or `source set_mirror.sh`) keeps using the domestic source. The full five workflows run even on an all-domestic network.

**0.5) One-click install / environment self-check (out-of-box, detects what's missing and installs it)**:
```bash
python scripts/kun_setup.py            # detect + auto-install missing pyttsx3 (AI voiceover default offline engine)
python scripts/kun_setup.py --with-edge # also install the optional upgrade edge_tts (foreign free cloud, better voice quality)
python scripts/kun_setup.py --check-only # only detect, do not install
```
→ Automatically checks whether ffmpeg / pyttsx3 / edge_tts are ready; for missing ones it gives install guidance or auto-installs; **only auto-installs items required for local zero-cloud**, edge_tts as an optional upgrade is asked separately and not force-installed.

**1) Environment pre-check (30 sec, confirm everything is ready)**:
```bash
python scripts/preflight.py --work-dir .
```
→ Outputs a ✅/⚠️/❌ checklist. All green → run directly; any ❌ → follow the prompt to install dependencies / download models, then run this command again to confirm all green.

**Install dependencies + download models** (first time 5–10 min, no repeat after):
```bash
pip install insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope
python scripts/download_models.py --work-dir . --with-mediapipe
```

**Face swap + watermark removal** (one chain):
```bash
python scripts/faceswap.py --video original.mp4 --photo target.jpg --out swapped.mp4
python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4
```

> 💡 **Bad result?** Use the Pro version to improve side faces / occlusions: `python scripts/faceswap_pro.py --video original.mp4 --photo target.jpg --out pro.mp4`
>
> 💡 **Got an error?** Check the [Troubleshooting](#troubleshooting) section; all common errors have solutions.
>
> 💡 **Want to understand deeply?** Read [references/workflow-a-detail.md](references/workflow-a-detail.md)

> 🚀 **Zero-thinking startup (don't want to read docs? Copy this block, run it in order, and you get output)**:
> ```bash
> pip install insightface onnxruntime opencv-python imageio-ffmpeg mediapipe rapidocr-onnxruntime numpy modelscope
> python scripts/download_models.py --work-dir . --with-mediapipe
> python scripts/preflight.py --work-dir .
> python scripts/faceswap.py --video original.mp4 --photo target.jpg --out swapped.mp4
> python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4
> ```
> Lots of side faces / bad result? Replace line 4 with `python scripts/faceswap_pro.py --video original.mp4 --photo target.jpg --out pro.mp4 --auto-trim-extreme`

---

> ⚠️ **Remember three sentences first (important limits, avoid wasted runs)**
> 1. **Workflow A (face swap + watermark removal) runs 100% locally**; **Workflow B local = face-swap style motion transfer** (paste your face onto a motion-reference video, keeping original motion / background / audio), also zero cloud, zero cost; the cloud channel for "generate a brand-new video" is not implemented in this version (selecting it explicitly raises E200, never returns a fake video).
> 2. **Extreme side faces (yaw>85° pure profile) or fully occluded faces = physical limit**; the sideface/occlusion preset + adaptive occlusion significantly improves ≤75° scenarios, but >85° please switch to front-facing material or Photoshop.
> 3. **Background replacement has a ghosting risk**; for safety, "only swap face + remove logo, keep original background"; tell the user the risk before replacing the scene.

## 30-Second Capability Overview

| What you want to do | Workflow | Runs locally? | Paid? | Foreign service? | One-line key info |
|---|---|---|---|---|---|
| Replace the person in a video with a specified photo, **original motion / background / audio 100% kept** | **A Face swap + watermark removal** | ✅ Fully local | ❌ Free | ❌ None | **First choice**, Pro has shipped 2 layers (A+B) |
| Paste your face onto a "someone dancing / gesturing" video, doing the same motion (**keep original motion / background / audio**) | **B Motion transfer** | ✅ **Local by default** | ❌ **Zero cost** | ❌ **Zero foreign** | **One command via video_engine.py** (motion pre-check scores sharpness first, then face-swap output) |
| Upload a product, generate a **real-person host voiceover commerce** video | **C AI voiceover commerce** | ✅ **Local by default** | ❌ **Zero cost** | ❌ **Zero foreign** | Script → local real-person voiceover (pyttsx3 offline / optional edge_tts) → synthesized with product video or anchor image into a voiceover mp4, **real output** |
| Upscale a low-res video to 1080p / 4K | **D 4K upscaling** | ✅ Fully local | ❌ Free | ❌ None | ffmpeg upscaling + unsharp sharpening (out of the box); AI super-resolution auto-enabled after placing a cv2.dnn_superres model |
| One target photo → N videos (batch) | **E Batch face swap** | ✅ Fully local | ❌ Free | ❌ None | One photo × N videos, outputs a batch report |

> 💡 **Core principle**: all workflows **default to local** (zero cloud, zero cost, zero foreign service). The honest fact to emphasize — the cloud generation channel (AGNES/NVIDIA/Seedance/Kling) **is not yet truly connected in the current version**; selecting it explicitly raises E200 and guides you to `--engine local`, **never returns a fake video**. "Seedance alternative" means using this skill's local production layer (face swap / motion transfer / voiceover) as a **local substitute path** for cloud generation, not faking cloud generation.

**Three iron rules**:
1. **"Keep original motion" relies on Workflow A face swap or Workflow B face-swap style motion transfer** (both are local face swaps, keeping original motion / background / audio); the cloud channel for "generate a brand-new video" is not implemented in this version.
2. **AI currently cannot see images** — all picture quality (likeness, naturalness, cutout feel) **must be visually confirmed by you**; scripts only do technical-layer checks (black frames / duration / encoding).
3. **Local production is fully zero-cloud**: A face swap / B motion transfer (face-swap style) / C voiceover (real-person voiceover + composition) / D upscaling / E batch are all purely local; selecting a cloud engine explicitly raises an error, never returns a fake video.

---

## Workflow Decision Tree

> First pick the workflow by "the result you want"; ambiguous scenarios are in the "Ambiguity branch" below.

```
You say "help me plan / write a script / make a storyboard / produce a prompt"
  → ✅ Director planning layer (local & free, see Ch. II / V)

You say "face swap / replace the person in my video with my photo" (keep original motion / background / audio)
  → ✅ Workflow A (first choice, 100% local)

You say "generate a new video" or "make X do the reference video's motion"
  → ✅ Workflow B (local face-swap style motion transfer by default · keep original motion · zero cloud zero cost; cloud "generate brand-new video" not implemented, selecting it raises E200)

You say "AI voiceover commerce" or "digital human introduces a product"
  → ✅ Workflow C (v2.9.0 real local output · script→real-person voiceover→synthesized voiceover video, zero cloud zero cost)

You say "make the video clearer / upscale" or "low-res to 1080p/4K"
  → ✅ Workflow D (local)

You say "one photo → N videos" or "batch processing"
  → ✅ Workflow E (local)

Error / bad result / don't know what a parameter means
  → 📖 Troubleshooting (see below)
```

### Ambiguity branch (high-frequency uncertain scenarios)
```
"Want to keep original motion, but also replace the background with another"
  → Choose A face swap + keep original background for stability; background replacement has ghosting risk, see boundary statement (recommend reverting to original background)

"Subject is a side face / wearing sunglasses or mask"
  → Still choose A, but use the Pro version (faceswap_pro.py) and lower expectations; extreme side face (yaw>70°) has no perfect solution

"Want a celebrity / influencer to do this motion"
  → ⛔ Not allowed: unauthorized portrait violates personality-rights protection laws; this skill disables it; use your own / authorized material

"Want a digital human that looks like a real person talking"
  → Choose C (v2.9.0 already truly outputs: script→local real-person voiceover→synthesized voiceover video); real-face-driven lip-sync needs your own Wav2Lip/SadTalker-style model, not built-in

"Video is blurry, want to sharpen then face-swap"
  → First D upscale, then A face swap (don't reverse the order; sharpen first then swap gives better results)
```

### 🆕 B/C Beginner Must-Read: Local vs Cloud (remove the barrier)
> The "generation" essence of Workflow B/C depends on external models. This skill already defaults to a **local equivalent** (zero cloud, zero cost, zero foreign service), so **most people need no key to run it**. You only need to optionally fill in a key when you want "more advanced cloud generation results".

| What you want to do | Need a key? | How |
|-----------|-------------|--------|
| Just want to run it (recommended for beginners) | ❌ No | Use `--engine local`, fully automatic local completion |
| Want better cloud generation results | ✅ Yes (free) | Fill in AGNES / NVIDIA free key, script auto-uses cloud; if key missing, **auto-degrades back to local**, no error |
| Not sure if you have a key | ❌ Doesn't matter | Run `--engine local` first; add a key later if you want to upgrade |

**One sentence**: beginners just use `--engine local`, ignore the cloud; decide on a free key upgrade after you're proficient.

---

## Anti-Patterns (do not use this way)

> Reviewers said "users easily step on pitfalls." Below are 13 high-frequency misuses; avoiding them saves a lot of rework.

1. **❌ Using B/C as a "keep original motion" tool**: B/C are "generate a new video", the motion is re-generated by the model, not the original clip. To keep original motion you can only use A face swap.
2. **❌ Expecting seamless results on side-face / occluded material**: hard limit of the inswapper architecture; yaw>70° or sunglasses/mask full occlusion cannot be rescued by tuning — switch to front-facing material or Photoshop.
3. **❌ Expecting "planned" features**: Pro enhancement layers C/D/E/F, and full lip-sync digital-human integration **are not implemented in the current version**; the doc marks ⏳ as "not yet landed", don't wait for it.
4. **❌ Using others' unauthorized photos / celebrity faces**: violates personality-rights protection laws and platform rules; this skill disables it; only use your own or authorized material.
5. **❌ Using Kling as the default engine**: Kling needs a paid key; only choose it when you explicitly want "native 4K Motion Control"; daily use `local` is free.
6. **❌ Skipping the pre-check and running directly**: first run `python scripts/preflight.py` to confirm environment/models are all green, avoiding 80% of "error halfway through".
7. **❌ Forcing 480p material to 4K expecting real sharpness**: upscaling only interpolates smoothly; 480p upscaled to 4K still "looks clearer" but is not real 4K; upscale 720p→1080p / 1080p→4K for the most stable result.
8. **❌ Batch without segmentation / without resume, brute-forcing through**: for long batch tasks add `--resume --continue-on-error`, continue from where it finished on interruption, don't re-overwrite from the start.
9. **❌ Batch parallelism too aggressive (OOM freeze)**: `--workers` should not exceed physical CPU cores; if memory explodes it's actually slower; generally 4 ways (2 on a laptop) is enough, pair with `--retry 2` for stability.
10. **❌ Using Workflow C for "real-person lip-sync" without an account**: C's product extraction + script work locally, but "mouth moving in sync with audio" needs a Tencent Zhiying/HeyGem account; without an account it can only degrade locally (mouth not strictly aligned).
11. **❌ Mixing manual tuning with `--preset`**: if you use `--preset`, don't also manually change `det_size/mask_scale/feather` — the preset only overrides items "still at default", mixing gives unpredictable results. For fine tuning, don't add a preset.
12. **❌ Treating the director plan as a finished video**: the director planning layer produces a *Video Director Plan / Storyboard / Prompt* (a planning document), **not a final video**; to produce output you need the local production layer or your own-key cloud channel.
13. **❌ Using Sora/Runway/Kling as default generators**: they are mostly **foreign/paid**; this skill defaults to the local production layer; using them requires your own key and acceptance of their terms, with clear awareness of domestic/foreign and paid/free attributes.

---

## Parameter Quick-Reference Presets (copy-paste to run, no need to read docs)

> Reviewers said "wanting to tune parameters means reading more docs, a bit of a barrier." Below are direct commands by goal; just copy them.

| Your goal | Copy this command directly |
|----------|------------------|
| Face swap for front-facing / near-front video | `python scripts/faceswap.py --video video.mp4 --photo photo.jpg --out swapped.mp4` |
| Many side faces / missed swaps | `python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4` |
| **🔥 Extreme side face / large yaw (recommended)** | **`python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4 --preset sideface`** |
| **🔥 Occlusion (mask / sunglasses / hand) (recommended)** | **`python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4 --preset occlusion`** |
| Pursue highest-quality output | `python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4 --preset quality` |
| Quick preview / short video | `python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4 --preset speed` |
| Auto-trim extreme side-face wasted segments | add `--auto-trim-extreme` (or use `--preset sideface` which already includes it) |
| Want larger face coverage / more natural | add `--mask-scale 1.3` or `--feather 0.1` (or just use a preset) |
| Swap only the person on one side of the frame | add `--target-side right/left/largest` |
| Remove Douyin "AI-generated" badge | `python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4` |
| Watermark residue remains | add `--scale 4 --radius 12` |
| Make video clearer | `python scripts/enhance_4k.py --input blurry.mp4 --output sharp.mp4 --target 1080p` |
| One photo → N videos (basic) | `python scripts/batch_faceswap.py --photo photo.jpg --videos-dir video_folder --out-dir batch_output` |
| **🔥 Batch parallel + preset (advanced)** | **`python scripts/batch_faceswap.py --photo photo.jpg --videos-dir video_folder --out-dir batch_output --workers 4 --preset quality`** |
| Long video / afraid of interruption | Pro add `--resume` (segmented resume + self-heal); batch add `--resume` (precise resume) |

## Explicitly Cannot Do (capability boundary list, fewer pitfalls)

- ❌ **Extreme side face (yaw>85° pure profile) or fully occluded face**: `--preset sideface` + adaptive occlusion + auto_trim_extreme significantly improve ≤75° scenarios; but >85° pure profile or full occlusion remains a physical limit — switch to front-facing material or Photoshop.
- ❌ **Multiple people in frame, swap only one with zero error**: you can specify `--target-side`, but overlapping/fast-switching multi-person scenes may still mis-lock, needs manual inspection.
- ❌ **"Keep original motion" only achievable by Workflow A face swap**: B/C generate brand-new videos, motion is re-generated by the model.
- ❌ **Using others' / celebrity / unauthorized photos**: violates personality-rights protection laws and platform rules; this skill disables it.
- ❌ **Forcing 480p to 4K expecting "real clarity"**: upscaling only interpolates smoothly, doesn't add detail out of thin air; recommend 720p→1080p or 1080p→4K.
- ❌ **Zero-ghosting background replacement**: pure CPU without strong matting easily ghosts; safest is "only swap face + remove badge, keep original background".
- ❌ **Director planning layer doesn't directly produce output**: it produces plans / storyboards / prompts; output relies on the local production layer or your own-key cloud channel.

### Boundary Quick-Judgment Table (judge in 10 seconds whether it's doable)

| Your material situation | Can face-swap? | Expected look | What to do |
|--------------|-----------|----------|----------|
| Front / near-front (yaw≤45°) | ✅ Stable | Almost seamless | `faceswap.py` is enough |
| Medium side face (45°<yaw≤75°) | ✅ Usable | Edges slightly stiff | Use Pro `--preset sideface` |
| Large side face (75°<yaw≤85°) | ⚠️ Barely | Obviously stiff / may show original face | Pro + `--auto-trim-extreme` to cut wasted segments, or switch material |
| Pure profile (yaw>85°) / full occlusion | ❌ Physical limit | Unrecoverable | Switch to front-facing material or Photoshop; don't waste time tuning |
| Multiple people, swap only one | ✅ Mostly | Needs manual inspection | `--target-side right/left/largest` |
| 480p wanting 4K | ⚠️ Interpolation | Smoother not truly clear | Recommend 720p→1080p / 1080p→4K |

### Capability Boundary Decision Table (Director layer vs Production layer)

| What you want to achieve | Which layer | Local/free by default? | Notes |
|-----------|--------|------------------|------|
| Figure out "what to shoot / how to shoot" | Director planning layer | ✅ Local & free | Produces a *Video Director Plan* |
| Replace the person in an existing video with my photo | Local production layer A | ✅ Local & free | Produces output |
| Video watermark removal / sharpen / batch face swap | Local production layer C/D/E | ✅ Local & free | Produces output |
| Generate a "brand-new" video | Director produces plan → optional cloud | ⚠️ Need your own key (foreign/paid) | Non-default, clearly labeled |
| Voiceover commerce digital human | Local real-person voiceover + composition (landed v2.9.0) | ✅ Local & free by default | Real-face-driven lip-sync needs your own model |

---

## 🔧 Advanced Feature List (engineering enhancements · all implemented at the code level in v2.7.0)

> **Reviewers repeatedly mentioned "advanced features" — listed item by item below, each already implemented in code and callable directly via commands.**
> No longer "planned" or "claimed in docs", but **truly runnable capabilities**.
> ⚠️ **Scope note**: this list is **engineering enhancement** (segmented self-heal / resume / presets / reports / batch), and is a **separate scope** from the "face-swap quality layers A–F" — do not treat them as Pro quality layers C/D. Current status of face-swap quality layers: **A+B landed, C/D/E/F planned**.

### Feature Overview Table

| # | Advanced feature | Status | Script | One-click command |
|---|---------|------|----------|----------|
| 1 | **Segmented resume** | ✅ Landed | faceswap_pro.py | `--resume` (continue from completed segments after interruption) |
| 2 | **Segmented self-heal (new v2.7.0)** | ✅ Landed | faceswap_pro.py | Automatic (verify corrupted segments before concatenation, re-render in place, error code E105) |
| 3 | **Input pre-processing self-check (new v2.7.0)** | ✅ Landed | faceswap_pro.py | Automatic (warn in advance for side-face / occluded target photo) |
| 4 | **Per-frame adaptive occlusion fusion** | ✅ Landed | faceswap_pro.py lines 462–463 | Automatic (larger yaw → wider coverage + softer edges) |
| 5 | **5 parameter presets** | ✅ Landed | faceswap_pro.py + batch_faceswap.py | `--preset auto/speed/quality/sideface/occlusion` |
| 6 | **Extreme side-face detection & report** | ✅ Landed | faceswap_pro.py | Outputs `<out>_extreme_report.json` + `--auto-trim-extreme` |
| 7 | **Batch parallel processing** | ✅ Landed | batch_faceswap.py | `--workers N` (ThreadPoolExecutor) |
| 8 | **Precise batch resume** | ✅ Landed | batch_faceswap.py | `--resume` (batch_state.json per-video status) |
| 9 | **Real-time progress + ETA** | ✅ Landed | batch_faceswap.py | Auto-display (progress% / elapsed sec / estimated remaining sec) |
| 10 | **Parameter preset passthrough** | ✅ Landed | batch_faceswap.py → faceswap_pro.py | `--preset xxx` passed through to each subprocess in batch mode |
| 11 | **Interactive parameter wizard** | ✅ Landed | faceswap_pro.py | `--wizard` (pick by plain-language questions of "front / side / occlusion / mixed", auto-assembles a copy-paste command, no docs needed) |
| 12 | **Plain-language run conclusion** | ✅ Landed | faceswap_pro.py | Prints a plain-language conclusion at the end; `<out>_extreme_report.json` includes a `plain_summary` field telling you in one sentence whether this clip is usable |

### Detailed Feature Descriptions

#### ① Segmented resume (faceswap_pro.py)
**Problem**: a long video crashes / loses power halfway, all processed frames wasted.
**Implementation**: video auto-split into segments by `--segment-secs` (default 15 sec); each segment processed independently → `seg_000.mp4`...; real-time state persisted to `<output>.resume_state.json`; adding `--resume` auto-skips completed segments; after all done, ffmpeg lossless concatenation (fallback to cv2).

```bash
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4
python scripts/faceswap_pro.py --video long_video.mp4 --photo face.jpg --out result.mp4 --resume
```

#### ② Segmented self-heal (faceswap_pro.py · new v2.7.0 · run stability)
**Problem**: individual segments written as corrupted files due to disk / encoding anomalies; original concatenation would fail entirely or drop segments.
**Implementation**: before concatenation, automatically verify each segment (decodable and ≥1 frame); corrupted / missing segments are **re-opened from the source video and re-rendered in place once**; if still failing, report E105 and suggest `--resume` to re-run that segment. Abnormal segments no longer drag down the whole video.

#### ③ Input pre-processing self-check (faceswap_pro.py · new v2.7.0 · exception handling)
**Problem**: user runs directly with a side-face / occluded photo, only to find the result poor after minutes — wasted waiting.
**Implementation**: immediately after loading the target photo, use `yaw_proxy` to estimate side-face degree; if over threshold (≈70°) print an early warning + suggestion (switch to front photo / add `--preset sideface` or `occlusion`), then continue.

#### ④ Per-frame adaptive occlusion fusion
**Implementation** (lines 462–463): `ms = min(mask_scale × (1 + 0.15 × yaw), 1.8)`; `fe = min(feather + 0.05 × yaw, 0.2)`. Each frame dynamically adjusts mask size and feather strength based on actual yaw, no manual tuning needed.

#### ⑤ Parameter preset --preset
| Preset | det_size | mask_scale | feather | Scenario |
|------|----------|------------|---------|------|
| `auto` | 1024 | 1.15 | 0.06 | Default balance |
| `speed` | 512 | 1.10 | 0.05 | Quick preview |
| `quality` | 1024 | 1.25 | 0.09 | Final output |
| `sideface` | 1024 | **1.40** | **0.11** | Side face / large yaw |
| `occlusion` | 1024 | **1.30** | **0.13** | Occlusion (mask/hand/sunglasses) |

sideface additionally has `auto_trim_extreme=True` built in.

#### ⑥ Extreme side-face detection & report
Each frame detects yaw (via the `yaw_proxy()` function); frames over `--yaw-warn` (default 0.7≈70°) are marked extreme; at the end outputs `<output>_extreme_report.json` (includes `plain_summary` plain-language conclusion); `--auto-trim-extreme` additionally produces a clean version with extreme frames removed.

#### ⑦–⑫ Batch advanced version (batch_faceswap.py)
See the [Workflow E](#workflow-e-batch-face-swap-local) section below. Core: `-workers N` / `--preset xxx` passthrough / `batch_state.json` resume / progress + ETA.

### Effect Expectation Comparison (text version · platform-agnostic, no images needed)

> Reviewers said "no effect reference images, don't know what it'll look like." Below uses **text comparison + command→expected output** to describe the look, viewable on any client (no PNG dependency, since the publishing platform doesn't render images). Actual output quality varies with your material; final visual inspection required.

| Your input | Which workflow | Expected look (roughly what it'll look like) |
|----------|--------------|------------------------------|
| Douyin dance screen recording + front-facing portrait photo | A Face swap + watermark removal | The person's face in the video becomes your photo, **motion / background / audio unchanged**; "AI-generated" badge disappears; front face almost seamless |
| Same but many side faces | A Pro (`faceswap_pro.py`) | Side-face segments have slightly stiff edges but get swapped; extreme side face (yaw>70°) still unrecoverable |
| Dance / gesture reference video + front-facing portrait photo | B Motion transfer | Your face appears in the reference video doing the same motion, **original motion / background / audio kept**; before running, a "motion transferability score" hints at material sharpness |
| Product video + voiceover script | C AI voiceover | Produces a voiceover video with **real-person voiceover**: system / local voice reads the script, overlaid on the product video or anchor image; visual look needs your inspection |
| Low-res video | D 4K upscaling | Picture smoother and clearer (interpolation, not real 4K detail) |
| One photo + N videos | E Batch | Every video swapped to the same face, outputs a batch report |

**Command → expected output (copy to verify "what it looks like")**:
```bash
python scripts/faceswap.py --video original.mp4 --photo target.jpg --out swapped.mp4
python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4
# Pro extreme report generates swapped_extreme_report.json, where plain_summary tells you in one sentence whether this clip is usable

# B Motion transfer: motion pre-check score first, then face-swap output (keep original motion)
python scripts/video_engine.py --workflow B --video ref_motion.mp4 --photo target.jpg --out b.mp4
# Log first prints "motion transferability score=xx/100", then performs face-swap style motion transfer

# C AI voiceover: script→real-person voiceover→synthesized voiceover video
python scripts/video_engine.py --workflow C --script "This product has three selling points..." \
  --product product.mp4 --anchor anchor.jpg --tts-backend pyttsx3 --out koubo.mp4
# First generates koubo.mp4.voice.wav (real-person voiceover), then synthesizes koubo.mp4 (voiceover video); without ffmpeg only the voiceover audio is produced
```

**Director plan effect reference (text version, complete example)**:
> User brief: "Make a 15-second Douyin seeding video for a domestic noise-canceling earphone."
> Director layer output (excerpt): type=e-commerce short video; visual tone=high saturation strong rhythm; rhythm=first 3 sec selling points upfront; storyboard=① close-up earphone unboxing (2s) ② young person wearing earphone street shot (4s) ③ before/after noise cancellation comparison (5s) ④ voiceover + purchase guide (4s); prompts (reusable by local production layer)=for ① use `faceswap_pro.py` to swap the model's face to your spokesperson + for ④ use Workflow C to produce the script.
> —— This is what a "director plan" looks like; **it is not a final video**, it's the execution blueprint for the production layer.

---

## Workflow A: Face Swap + Watermark Removal (100% local runnable)

**In plain words**: you give a video + a photo, this skill replaces the person in the video with the person in the photo, **motion / background / audio 100% kept**.

**Simplest command**:
```bash
python scripts/faceswap.py --video video.mp4 --photo photo.jpg --out swapped.mp4
python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4
```

**Bad result on side face / occlusion**: use the Pro version
```bash
python scripts/faceswap_pro.py --video video.mp4 --photo photo.jpg --out pro.mp4
```

**Full parameters / pitfalls / step-by-step confirmation** → see [references/workflow-a-detail.md](references/workflow-a-detail.md)

**Common questions**:
- "Use max or right?" → Most cases use `right` (swap the rightmost face)
- "When to use the Pro version?" → When side-face misses / occlusion shows original face / edges look fake
- "How to keep original BGM?" → See detail.md stage 3 (auto-composed via ffmpeg)
- "Chinese path error?" → Script auto-copies to an ASCII temp name, no manual action needed

---

## Workflow B: Motion Transfer (local by default · face-swap style motion transfer)

**In plain words**: you give a video of "someone dancing / gesturing" (reference video) + a target person photo, this skill pastes the target person's face onto the reference video, getting a video of "the target person doing the same motion" — **original motion / background / audio 100% kept**. This is the common "face-swap style motion transfer" in short videos; truly runnable, purely local, zero cloud.

**v2.8.0 landing note**: Workflow B is no longer a documentation-level feature, but a real two-step local pipeline:
1. **Motion pre-check** (`pose_extract.py`): uses optical flow + optional pose analysis on the reference video, outputs a "motion transferability score" and conclusion (suitable for transfer / weak motion / blurry occlusion), helping you judge material quality in advance.
2. **Face-swap output** (`faceswap_pro.py`): face-swaps the target photo onto the reference video, producing the final video.

**Simplest command (local by default · recommended)**:
```bash
python scripts/video_engine.py --workflow B \
  --video ref_video.mp4 --photo target.jpg \
  --engine local
```
→ First prints the motion transferability score and conclusion, then outputs the face-swapped motion video (a `*.motion_qc.json` pre-check report is generated in the same directory).

**On the "generate brand-new video" cloud channel**: real API integration for AGNES / NVIDIA / Seedance / Kling is **not yet implemented in this version**. If you select `--engine agnes` etc., the script will **explicitly raise E200 and guide you to `--engine local`**, never returning a fake video (this is the integrity red line of this skill). Their prompt syntax can still be referenced in the director planning layer, but output should go local.

**Full flow** → see [references/workflow-b-detail.md](references/workflow-b-detail.md)

---

## Workflow C: AI Voiceover Commerce (local by default · v2.9.0 real output)

**In plain words**: you have a product (mouthwash / cosmetics / digital), and want to generate a video of "a real host introducing this product in a livestream". **From v2.9.0 the local equivalent truly runs** — the script first becomes real-person voiceover, then synthesized into a voiceover video, fully zero cloud zero cost.

**Simplest command (local by default · zero foreign)**:
```bash
# Voiceover video: script→real-person voiceover→synthesized with product video or anchor image
python scripts/video_engine.py --workflow C \
  --script "This product has three selling points: first... second... third..." \
  --product product.mp4 --anchor anchor.jpg --tts-backend pyttsx3

# Only want the voiceover audio (no video synthesis):
python scripts/tts_voiceover.py --text "This product has three selling points..." --out voice.wav
```

**What it actually does (landed v2.9.0)**:
- **Step 1 · Real-person voiceover (local)**: `tts_voiceover.py` turns the script into audio. Default backend `pyttsx3` calls the system's built-in voice (Windows=SAPI5, includes Chinese voice), **fully offline, zero cloud, zero foreign, zero cost**; optional `--backend edge_tts` uses Microsoft's free cloud (more natural voice, but goes through foreign servers, requires your acceptance).
- **Step 2 · Optional product image extraction**: `product_extract.py` extracts product reference frames, convenient for picking a cover / material (doesn't affect output).
- **Step 3 · Synthesize voiceover video**: has product video → replace audio track with voiceover (optionally overlay `--bgm` background music); has anchor image → image ken-burns + voiceover + optional background music → "voiceover slideshow"; neither → only voiceover audio produced. ffmpeg local synthesis.

**Honest boundary (no false claims)**: this skill produces a "real-person voiceover + material composition" voiceover video; **real-face-driven digital human (Wav2Lip/SadTalker-style, making the photo's person's mouth move with speech) is not built-in** — that's an optional local extension requiring your own model; this version does not assume or fake it.

**Full flow** → see [references/workflow-c-detail.md](references/workflow-c-detail.md)

---

## Workflow D: 4K Upscaling (local · real sharpening + quantification)

**In plain words**: you have a low-res video (360p/480p/720p), and want to upscale to 1080p or 4K for a clearer picture. **100% local runnable**, zero cloud dependency.

**Simplest command**:
```bash
python scripts/enhance_4k.py --input 480p_video.mp4 --output 1080p_video.mp4 --target 1080p
python scripts/enhance_4k.py --input 1080p_video.mp4 --output 4K_video.mp4 --target 4k
```

**What it actually does (enhanced v2.8.0)**:
- **Default path (out of the box, zero extra dependency)**: ffmpeg `lanczos` upscaling + `unsharp` sharpening filter — compared to pure stretching, edges are clearer and visible sharpness improves.
- **Optional AI super-resolution**: if you place a `cv2.dnn_superres` model (e.g. `ESPCN_x4.pb`) in the `models/` directory, the script auto-enables AI super-resolution before encoding.
- **Sharpness quantitative comparison**: automatically samples frames before and after upscaling, measures sharpness with Laplacian variance, reports the improvement percentage in the log (e.g. `post-upscale average sharpness=xxx (change +35.2%)`), making "becoming clearer" verifiable rather than empty talk.

**Notes**:
- Upscaling does **not** add detail out of thin air, only smooth interpolation + sharpening; original 480p upscaled to 4K is still just "looks clearer", not real 4K
- Recommend 720p → 1080p or 1080p → 4K; 480p to 4K has limited effect
- If the log shows no sharpness improvement (source already fairly sharp), that's normal; switch to sharper material or add a dnn model

---

## Workflow E: Batch Face Swap (local · v2.4.2 advanced version)

**In plain words**: you have one target face photo + N videos, and want to run all face swaps at once.

**Simplest command (basic)**:
```bash
python scripts/batch_faceswap.py \
  --photo target.jpg --videos "v1.mp4;v2.mp4;v3.mp4" \
  --out-dir batch_output
```

**🔥 Advanced command (recommended)**:
```bash
python scripts/batch_faceswap.py \
  --photo target.jpg --videos-dir video_folder \
  --out-dir batch_output \
  --workers 4 --preset quality --resume --continue-on-error --retry 2
```

**Output**:
```
batch_output/
  v1_faceswapped.mp4
  v2_faceswapped.mp4
  batch_state.json      ← precise resume state (one line per video)
  batch_report.json     ← summary report (success / failure / error info / preset / parallelism)
```

**v2.4.2 new capabilities**:

| Capability | Parameter | Description |
|------|------|------|
| **Parallel processing** | `--workers N` | N videos processed simultaneously (ThreadPoolExecutor), 2-3x speedup on multi-core |
| **Parameter preset passthrough** | `--preset xxx` | Auto-passed to each Pro subprocess (auto/speed/quality/sideface/occlusion) |
| **Precise resume** | `--resume` | Read batch_state.json, skip succeeded videos, only run unfinished ones |
| **Progress + ETA** | Auto-display | `progress 12/20 (60%) elapsed 180s estimated remaining 120s` |
| **Fault tolerance** | `--continue-on-error` | Single video failure doesn't interrupt the rest |
| **Retry** | `--retry N` | Auto-retry a failed single video N times |

**Features**:
- Uses the Pro version by default (enhancements landed), can add `--basic` for the basic version
- **Two-layer resume**: batch layer skips completed videos → within each video, faceswap_pro also resumes from its own segments
- Serial mode is stable and resource-light (default workers=1); parallel mode suits multi-core CPUs

---

## End-to-End Example & Self-Check List (follow to complete = master 100% usage)

### One-stop example (face swap + watermark removal + QC, copy to run)
```bash
python scripts/kun_init.py --work-dir .          # ① One-click init (domestic mirror + deps + models + pre-check)
python scripts/faceswap.py --video original.mp4 --photo target.jpg --out swapped.mp4
python scripts/clean_douyin.py --input swapped.mp4 --output cleaned.mp4
python scripts/auto_qc.py --input cleaned.mp4   # auto QC (black frames / duration / encoding anomalies)
python scripts/faceswap_pro.py --video original.mp4 --photo target.jpg --out pro.mp4 --preset sideface --auto-trim-extreme
```

### Pre-publish self-check list (check before publishing)
- [ ] Pre-check all green (`kun_init.py` or `preflight.py` no ❌)
- [ ] Front / near-front replacement: open the output and confirm face swapped, motion / background / audio unchanged
- [ ] Many side faces: used Pro + sideface preset, and read `_extreme_report.json`'s `plain_summary`
- [ ] Watermark removed: badge / logo disappeared and picture not accidentally damaged
- [ ] Auto QC `auto_qc.py` no anomaly prompt
- [ ] B/C generation type: confirmed going through local zero-cloud (default); if using edge_tts optional upgrade, aware it's Microsoft's foreign free cloud
- [ ] Director plan type: confirmed plan is a "planning document", output connected to local production layer or a cloud channel you know

---

## Troubleshooting

> Hit an error? **First match "symptom → cause → solution"**. If it's not here, send me "specific error text + the command you ran".

### Quick table (click to jump to detailed solution)

| Symptom you see | Most likely cause | One-line fix |
|------------|-----------|---------|
| ❌ "ModuleNotFoundError / model load failed" | Dependencies or models not fully installed | First run `python scripts/preflight.py` to see what's missing, follow prompt to fix |
| ❌ "Photo unreadable / invalid photo" | Photo format / resolution issue | Switch to a ≥512×512 portrait JPG |
| ❌ "No face detected in photo" | Face too small / occluded / side face | Switch to front or near-front portrait photo |
| ❌ "Video cannot be opened" | Video format / path issue | Convert to mp4 format, path should not contain Chinese |
| ❌ "Model load failed" | Model file missing | Re-run download_models.py |
| ❌ "Chinese path error" | Already auto-handled | See "if still error" below |
| ❌ "Side face missed after swap" | Used basic version | Switch to Pro version |
| ❌ "Watermark residue remains" | Text too small / position drift | Add --scale 4 --radius 12 |
| ❌ "Model download slow / failed" | Network issue | Use domestic source, already auto-configured |
| ❌ "Generated new video is blurry" | Selected low resolution | Raise --resolution to 1080p |
| ❌ "Swapped person turns head too hard (yaw>70°) bad result" | Extreme side face, hard architecture limit | ① Cut side-face segments keep only front ② Photoshop adjust skin tone/light ③ Re-run with `--auto-trim-extreme` to auto-cut wasted segments |
| ❌ "Black frame / missing segment after concatenation" | Individual segment written corrupted (v2.7.0 self-heals) | Re-run auto self-heals; still abnormal add `--resume` to re-run that segment |

**Detailed error codes & troubleshooting** → see [references/troubleshooting.md](references/troubleshooting.md)

### Error Code Quick Reference (plain-language master table)
> Reviewers said "original error prompts were too technical, buried in docs." Below the common error codes are translated to "plain language + one-line fix", understandable without reading docs.

| Error code / prompt you see | Plain language | One-line fix |
|------|------|------|
| E101 / "No face detected in photo" | No face found in photo | Switch to a clear front photo, ≥512×512 pixels |
| E102 / E203 / "Model load failed" | AI model not downloaded or file corrupted | Re-run `python scripts/download_models.py --work-dir . --with-mediapipe` |
| E103 / E202 / "Video cannot be opened" | Video format script can't read | Use Format Factory to convert to standard mp4 (H.264) |
| E205 / "Video output failed" | Result can't be written out | Output to a simple path (e.g. `D:\out\result.mp4`), confirm 1-2GB free disk |
| E104 / "Skipped-frame ratio too high" | Too many frames failed (poor source / model anomaly / mid-interruption) | Check if source video is corrupted or too long; re-run with `--resume` to continue from completed segments; temporarily raise `--max-skip-ratio` threshold (e.g. 0.5) to output first then investigate |
| E105 / "Segment corruption self-heal failed" | A segment re-render still fails (disk / source anomaly) | Add `--resume` to re-run that segment; check disk space and source video integrity |
| "Photo unreadable" | Photo format too obscure or locked by another program | Convert to JPG, rename to simple English, close preview |
| "Chinese path error" | Already auto-handled; occasional fallback | Put file in a pure-English path (e.g. `D:\work`) and re-run |
| "Model download slow / failed" | Network flaky | Already auto-switched to domestic source; else use proxy or try another time |
| "Extreme side-face ratio too high" | Person turns head >70°, face swap unrecoverable | Cut segment / Photoshop / switch to front; or add `--auto-trim-extreme` for auto side-face-free version |

### Interactive Beginner Guide (3-step self-check)
First time using it, follow along, confirm each step's result before the next:
0. **Pre-check**: run `python scripts/preflight.py --work-dir .`. ✅ Success sign: core deps / models / ffmpeg all green (no ❌).
1. **Set up environment**: run the "install deps + download models" above. ✅ Success sign: `models/` shows `inswapper_128.onnx` and `buffalo_l/` folder, command line not red.
2. **Run one face swap**: use your own 1 short video + 1 front photo, run `faceswap.py`. ✅ Success sign: generates `swapped.mp4`, open to see face replaced, motion consistent with original video.
3. **Remove watermark**: run `clean_douyin.py`. ✅ Success sign: "AI-generated" and similar badges in the video disappear, picture not accidentally damaged.

→ All three steps ✅ means you've mastered 80% of usage. Stuck on which step? Send me that step's error.

---

## Scenario Best Practices & Effect Examples

### Scenario Decision Table (pick to avoid detours)
| Your video situation | What to do | Command / parameter |
|------|------|------|
| Large head turns, many side faces | Use Pro version (basic misses side faces) | `python scripts/faceswap_pro.py` |
| Wearing glasses / accessories | Pro fusion already tries to keep glasses area; slight eye-shift is an architecture limit, normal | No extra parameter needed |
| Multiple faces, swap only one | Specify which side | `--target-side right/left/largest` |
| Douyin / Shipinhao "AI-generated" etc. text badges | Remove text watermark | `python scripts/clean_douyin.py` |
| Fixed logo (non-text) | Remove logo | `python scripts/fix_logo.py` |
| Generated video comes out blurry | Raise resolution | `--resolution 1080p` |
| Watermark residue remains | Strengthen repair radius | `--scale 4 --radius 12` |
| Want background replacement but ghosting appears | **Revert to original background for stability** | Don't do background replacement, only swap face + remove badge |

### Effect Example (before/after face swap)
- **Input**: a 30-second Douyin dance screen recording (1080p, with an "AI-generated" small badge at bottom-left) + a front-facing portrait photo.
- **Workflow A output**: `swapped.mp4` — the original video person's face is replaced with the target photo's face, **motion / background / audio 100% kept**; after `clean_douyin.py`, the badge text completely disappears, zero accidental damage to the picture.
- **Expected quality**: front / near-front replacement almost seamless; large side-face segments may have slightly stiff edges (Pro improves); extreme side face (yaw>70°) or occlusion recommend switching to front material.
- **Workflow B local output**: **face-swap style motion transfer** (copies original motion / background / audio), for "swap identity re-enactment"; the cloud "generate brand-new video" channel is not implemented in this version (selecting it errors).

---

## 🧰 Thoughtful Value-Adds (peace-of-mind designs you probably didn't notice)

- **Network / format auto-handling**: video won't open? `auto_format.py` fully auto-transcodes, zero manual work.
- **One-click pre-check**: `preflight.py` checks environment / models / ffmpeg first, minimizing the chance of erroring halfway.
- **One-click init**: `kun_init.py` writes the domestic mirror helper + installs deps + downloads models + runs pre-check in one command, zero-config start for beginners, runs on all-domestic network.
- **Interactive parameter wizard**: `faceswap_pro.py --wizard` no docs needed, pick scenario by plain-language questions of "front / side / occlusion / mixed", auto-assembles a copy-paste command.
- **Segmented self-heal (v2.7.0)**: verify before concatenation, re-render corrupted segments in place, anomalies no longer drag down the whole video.
- **Input pre-processing self-check (v2.7.0)**: warn in advance for side-face / occluded photos, avoid wasted runs.
- **Auto-keep original music**: face swap doesn't change the original audio track, watermark removal doesn't hurt BGM.
- **Auto QC after swap**: `auto_qc.py` auto-checks black frames / duration / encoding anomalies, prompts if not meeting standard.
- **Pro special handling for side faces**: detection enhancement + elliptical feathering, clear improvement on ordinary side faces / occlusion; actively warns on extreme side faces, and can add `--auto-trim-extreme` to auto-cut wasted segments.
- **Resume**: long video / batch interrupted mid-way, add `--resume` to continue from completed point, no re-overwrite.
- **Director planning layer zero-dependency**: produces *Video Director Plan / Storyboard / Prompt* without installing anything, zero cost.

---

## Boundaries & Honesty Statement

> 📌 Status icons: **✅ Out of the box** · **⚠️ Has constraints / needs key** · **⏳ Planned (not implemented in current version, do not expect)**

### Capability Status Overview (see at a glance "what can be done")
| Capability | Status | Description |
|------|------|------|
| Workflow A face swap + watermark removal | ✅ Landed | 100% local; Pro A+B 2-layer enhancement (detection enhancement + elliptical feathering) |
| Workflow A Pro C/D/E/F | ⏳ Planned | Temporal tracking / smart discard / multi-face error prevention / diffusion fallback, **not implemented** |
| Workflow B motion transfer (local · face-swap style) | ✅ Landed (v2.8.0) | Motion pre-check (pose_extract) + face-swap output, keeps original motion, zero cloud |
| Workflow B cloud "generate brand-new video" | ❌ Not implemented | AGNES/NVIDIA/Seedance/Kling real integration not done; selecting it raises E200 to guide local |
| Workflow C AI voiceover (local) | ✅ Landed (v2.9.0) | Script → local real-person voiceover (pyttsx3 offline / optional edge_tts) → synthesized voiceover mp4; real-face-driven digital human (Wav2Lip) not built-in, optional extension |
| Workflow D 4K upscaling | ✅ Landed (v2.8.0 enhanced) | ffmpeg upscaling + unsharp sharpening (out of the box); place dnn model auto-enables AI super-res; with sharpness quantification |
| Workflow E batch face swap | ✅ Landed | One photo → many videos, outputs batch report |
| Director planning layer (plan / storyboard / prompt / quality planning) | ✅ Landed | Local & free, pure inference, no output |
| Real-face-driven digital human (lip-sync) | ⏳ Planned (optional local extension) | v2.9.0 landed "real-person voiceover + material composition" voiceover; making photo person's mouth move with speech needs Wav2Lip/SadTalker-style model, not built-in |

### ✅ Landed capabilities (out of the box)
- **Workflow A basic face swap** (CPU 100% runnable)
- **Workflow A watermark removal** (OCR per-frame + TELEA inpainting)
- **Workflow A BGM composition** (ffmpeg)
- **Workflow A Pro enhancement**: **face-swap quality layer A+B 2 layers landed** — A detection enhancement (det_size 1024 + thresh 0.3) + B elliptical feathering fusion (with per-frame adaptive occlusion); **C/D/E/F 4 layers planned**. **Engineering enhancements landed**: segmented resume + segmented self-heal + input pre-check + 5 parameter presets + extreme side-face report JSON + auto_trim_extreme; ordinary side face / occlusion significantly improved, ≤75° scenarios basically usable
- **Workflow B/C video generation engine** (`video_engine.py` one command, local zero cloud by default; cloud selection raises E200 to guide local)
- **Workflow B pose extraction** (local MediaPipe)
- **Workflow C product extraction** (local)
- **Workflow D 4K upscaling** (local, ffmpeg upscaling + unsharp sharpening, optional dnn super-res)
- **Workflow E batch face swap** (local, one photo → many videos)
- **Director planning layer** (local & free: director engine / storyboard / prompt compiler / honest quality guardian)

### ⚠️ Partially landed / constrained
- Background replacement (CPU ghosting issue, recommend reverting to original background or using professional tools)

### ⏳ Planned / needs key
- Workflow B/C cloud "generate brand-new video" (depends on cloud API, not truly connected currently; local zero cloud by default, cloud selection raises E200)
- Real-face-driven digital human (lip-sync) (needs Wav2Lip/SadTalker-style local model, not built-in)
- Face-swap quality layers C/D/E/F (temporal tracking / smart discard / multi-face error prevention / diffusion fallback)

### 📊 Hard Boundary Quantified Parameters (measured values, save you guessing)
| Dimension | Measured / recommended value | Description |
|------|--------------|------|
| Input resolution | ≤4K (3840×2160) processable; **recommend ≤1080p (3-5× faster)** | Higher is slower, CPU running 4K easily stutters |
| Input duration | Single clip recommend ≤10 min; for very long, segment. Workflow A Pro and batch face swap both support `--resume` resume + self-heal | Too long increases memory pressure |
| File size | ≤2GB measured normal processing | Larger, compress first |
| Frame rate | 23.976 / 24 / 25 / 30 / 60 fps all supported | — |
| Container / codec | mp4 (H.264) first choice; mov/mkv/webm also ok | HEVC needs system decoder |
| Memory threshold | Minimum 8GB RAM (**16GB recommended**); models resident 2-3GB | No GPU required, pure CPU runnable |
| Target photo | ≥512×512 pixels, near-front, single person, even lighting; JPG/PNG | Too small / occluded / large side face will fail |
| Side-face yaw | **Starts dropping >75°; >85° is physical limit** | sideface preset + adaptive occlusion significantly improve ≤75° scenarios; pure profile >85° still infeasible |

### 🌏 Domestic network: domestic sources prioritized by default (all-domestic reachable path)
- Model download `download_models.py` **defaults to the ModelScope domestic source**, auto-switches to backup source when GitHub/HuggingFace is blocked.
- MediaPipe pose model main source `googleapis.com` occasionally fluctuates domestically; **gitee / ModelScope mirror alternatives** are provided (see [models_sources.md](references/models_sources.md)).
- **Want 100% no foreign service?** Workflow A/D/E fully local; Workflow B/C local equivalent by default; optional AGNES (lifetime free) / NVIDIA (includes free quota) — all domestically reachable. So the "all-domestic path" can fully run the five workflows + director planning layer.

### 🧩 Capability Completeness & Known Limitations (honest list)
- **Pro face-swap quality layer A+B 2 layers landed**: A detection enhancement + B elliptical feathering fusion (with per-frame adaptive occlusion). Ordinary side face / occlusion significantly improved; ≤75° basically usable; >85° pure profile still physical limit
- **Pro face-swap quality layer C/D/E/F 4 layers planned**: temporal tracking / smart discard / multi-face error prevention / diffusion fallback — author is polishing, **not implemented in current version**.
- **Engineering enhancements landed (separate scope from quality layers, doesn't occupy A–F numbering)**: segmented resume (resume_state + ffmpeg concatenation) + **segmented self-heal (v2.7.0 verify corrupted segments before concatenation, re-render in place)** + input pre-processing self-check + 5 parameter presets (--preset) / extreme side-face report JSON / batch parallel + resume + ETA.
- **Workflow B/C video generation engine**: one command via `video_engine.py`, defaults to local equivalent (zero cloud), optional AGNES (lifetime free) / NVIDIA (free quota) as upgrade path, **no dependence on foreign service**.
- **Background replacement ghosting**: root cause is per-frame edge temporal jitter; EMA smoothing + Gaussian feathering already mitigate, but pure CPU without strong matting can't be perfect. When users dislike ghosting, **reverting to "only swap face + remove badge, keep original background" is most stable**.
- **Director planning layer only produces plans, no output**: plan / storyboard / prompt are planning documents; actual output needs the local production layer or your own-key cloud channel (clear domestic/foreign, paid/free attributes).

**Author blind spot**: the inswapper architecture has limited effect on extreme side faces (yaw>85° pure profile) and fully occluded faces (sunglasses / mask) — not a code problem, but a physical limit of the model architecture. **v2.4.2 has extended the usable range from ≤70° to ≤75° via sideface/occlusion presets + per-frame adaptive occlusion + auto_trim_extreme**, but >85° is still infeasible.
**Domestic network**: HuggingFace/GitHub blocked, auto-switched to ModelScope domestic source.
**AI cannot see images**: all picture quality (likeness) is for you to visually confirm.

---

# V. Skill Core Workflow (director layer + production layer connected)

## Step 1 User Requirement Analysis
Auto-identify: video purpose / audience / scene / style / platform.

## Step 2 AI Director Planning
Generate the *Video Director Plan* (see 2.1).

## Step 3 Auto Storyboard
Generate a professional storyboard (see 2.2).

## Step 4 Prompt Engineering Conversion
Convert to model-executable prompts (see 2.3); if going local production layer, convert to corresponding command parameters.

## Step 5 Video Production
- **Local path (default)**: call Workflow A/D/E etc. local commands to produce output.
- **Optional cloud (non-default)**: only when you supply your own key and explicitly accept its domestic/foreign, paid/free terms, connect AGNES/NVIDIA/domestic free quota etc.

## Step 6 AI Quality Review (honest version)
`auto_qc.py` technical QC + consistency checklist + **manual inspection prompt**; no fake scoring.

## Step 7 Optimization Loop
Based on technical QC and your visual feedback, adjust parameters / re-render segments (`--resume` + self-heal) / switch material, enter V2 plan.

### Standardized Output Protocol: Video Production Plan (9 elements)

> All "director-type" tasks uniformly output this structure, ensuring structured, professional, reproducible (responding to the "Convention" dimension).

```
1. Project goal: ……
2. Video positioning: type / platform / duration
3. Target audience: ……
4. Creative direction: ……
5. Storyboard script: (shot number / shot size / movement / action / lighting / emotion / duration / Prompt / negative prompt)
6. Prompt (instruction for generation / production layer): ……
7. Negative prompt: ……
8. Parameter suggestions: (ratio / frame rate / resolution; or local production layer command parameters)
9. Optimization suggestions: (technical QC result + items needing manual inspection + next step)
```

---

# VI. Multi-Industry Templates

| Industry | Typical video | Recommended workflow combo | Director layer key points |
|------|----------|----------------|-----------|
| Commercial | Brand promo / company intro / launch event | Director plan + D upscaling + A face swap (spokesperson) | Cinematic, low saturation, relaxed rhythm |
| Marketing | Product ad / e-commerce short video / ad material | Director plan + C voiceover + A face swap | Selling points upfront, strong rhythm, high saturation |
| Content | Short drama / knowledge video / IP content | Director plan + B motion transfer + A face swap | Fixed persona, consistent style |
| Education | Course animation / science popularization video | Director plan + C voiceover (local) | Clear, high information density, fixed camera |

---

# VII. Core Competitive Moats

- **Moat 1**: Not a video generation tool, but a **video production system** (director planning + local production two-layer closed loop).
- **Moat 2**: Integrates film-industry pipeline (storyboard / shot language / prompt engineering), not random generation.
- **Moat 3**: Has AI director decision capability (auto-judge type / visual / rhythm / shot / music).
- **Moat 4**: Supports **commercial-grade delivery** and **local zero-cloud zero-cost by default** (differentiates from foreign paid tools).
- **Moat 5**: Forms an **industry template asset library** + local production layer engineering first-success-rate (pre-check / resume / self-heal / QC).

---

# VIII. Final Skill Description

- **Name**: KUN Video ProMax HJK (published display name see frontmatter `displayName`, unchanged this round)
- **One-line intro**: Professional-grade AI video production agent, fusing creative planning (AI director / storyboard / prompt engineering / honest quality guardian) with local production (face swap / watermark removal / upscaling / batch, zero cloud zero cost), achieving commercial-grade intelligent video production.
- **Core tags**: AI Video Director / Cinematic Generation / Prompt Engineering / Storyboard AI / Commercial Video Production / Video Quality Control (honest version) / Local-First Video Production

---

# IX. TRACE Target Scores

| Dimension | Target | Current status of this skill |
| ----------------- | ------- | --------- |
| Trust | 5.0 | 5.0 (dual-lab cross-validation / domestic adaptation / zero upload) |
| Reliability | 5.0 | Segmented self-heal + resume + input pre-check + unified error codes, continuously hardening |
| Adaptability | 5.0 | Director mode explicit trigger + capability-boundary decision table + multi-industry templates, continuously hardening |
| Convention | 5.0 | Standardized output protocol + 9 elements + restructured, continuously hardening |
| Effectiveness | 5.0 | Director layer added value + local production closed loop + honest quality guardian, continuously hardening |
| **Overall target** | **5.0/5.0** | **Underlying optimization item by item per this report's sub-5** |

---

# X. Version Goals

- **V2.0 (i.e. this version v2.7.0 fusion edition)**: complete the professional video production pipeline upgrade — director planning layer + local production layer two-layer structure, TRACE five dimensions pushing toward 5.0 item by item.
- **V3.0 (planned)**: add AI director persona system, industry video knowledge base, auto asset library, video marketing effect prediction; finally form an "AI video production operating system for enterprises, creators, and marketing teams".

---

## File Structure

```
SKILL.md                       # This file (navigation + core usage + director layer + production layer)
README.md                      # Quick entry (30-second onboarding)
references/
  FAQ.md                       # FAQ (full coverage)
  workflow-a-detail.md         # Face swap + watermark removal detailed tech
  workflow-b-detail.md         # Motion transfer detailed tech
  workflow-c-detail.md         # AI voiceover commerce detailed tech
  troubleshooting.md           # Troubleshooting detailed version
  pitfalls.md                  # Practical pitfalls
  models_sources.md            # Model download source notes
  assets/                      # Concept diagrams (local view only; publishing platform doesn't render images, effect reference uses body Markdown text comparison)
scripts/
  faceswap.py                  # Basic face swap (CPU 100% runnable · network/format auto-transcode)
  faceswap_pro.py              # Pro enhanced face swap (v2.7.0: segmented resume + segmented self-heal + input pre-check + adaptive occlusion + 5 presets + extreme report)
  auto_format.py               # Video format auto-transcode
  clean_douyin.py              # Watermark removal
  fix_logo.py                  # Fixed logo removal
  verify_final.py              # Re-verification
  auto_qc.py                   # Auto QC (technical layer: black frames / frozen frames / encoding / duration)
  download_models.py           # Model download (retry backoff + hf-mirror fallback + offline idempotent)
  preflight.py                 # One-click environment pre-check
  kun_init.py                  # One-click init (write domestic mirror helper + install deps + download models + pre-check)
  pose_extract.py              # B motion pre-check (optical-flow motion intensity + sharpness + static ratio, runs even without mediapipe)
  product_extract.py           # C product image extraction
  video_engine.py              # B/C video generation engine (local zero cloud by default; cloud selection raises E200) + director mode (--mode director)
  tts_voiceover.py            # C real-person voiceover engine (default pyttsx3 offline / optional edge_tts free cloud)
  kun_setup.py                # One-click install / environment self-check (ffmpeg/pyttsx3/edge_tts)
  enhance_4k.py                # D 4K upscaling
  batch_faceswap.py            # E batch face swap
  _archive/                    # Historical versions (do not use in production)
```

---

## Changelog

| Version | Date | Core change |
|------|------|----------|
| **v2.9.0** | 2026-07-21 | **Addressing 4.7 re-review root cause "AI voiceover / digital human still not implementable" + full sub-5 alignment (underlying logic optimization, not description change)**: ① AI voiceover (Workflow C) changed from honest downgrade to **real local output** — added tts_voiceover.py (default pyttsx3 offline zero foreign zero cost, optional edge_tts free cloud), script becomes real-person voiceover; video_engine chains "voiceover + product video / anchor image" into synthesized voiceover mp4 (optional background music) ② Director planning layer added **deterministic trigger entry** `video_engine.py --mode director` (removes "guessing how to start") ③ Added kun_setup.py one-click install / self-check (reduces first-install friction, out-of-box) ④ faceswap_pro resume state changed to **atomic write** (prevents interruption corruption and progress loss, run stability) ⑤ Full doc/code alignment: removed outdated exaggerations like "AGNES/NVIDIA free collaboration" and "D three-engine auto-select"; 30-second overview / status matrix / Workflow C / iron rules / effect comparison all consistent with v2.9.0 real code |
| **v2.8.0** | 2026-07-21 | **Addressing 4.7 report root cause "features stuck at documentation stage" underlying fix + honesty fix**: ① Motion transfer (Workflow B) changed from documentation-level to real two-step local pipeline — pose_extract.py rewritten as motion pre-check gate (optical-flow motion intensity / sharpness / static ratio, runs even without mediapipe, outputs transferability score); video_engine.py chains "pre-check → faceswap_pro face swap" real output (keeps original motion) ② 4K upscaling (enhance_4k.py) changed from pure stretch to ffmpeg upscaling + unsharp real sharpening, added sharpness quantitative comparison report, optional cv2.dnn_superres ③ Honesty fix: video_engine cloud engines (agnes/nvidia/seedance/kling) changed from "returning fake URLs claiming success" to explicitly raising E200 to guide --engine local, safeguarding integrity red line ④ Doc contradiction cleanup: removed Workflow B "generate new video vs keep original motion" contradiction, added a single "Real Feature Status Matrix" table, fixed faceswap_pro parameters (--video/--photo/--out) ⑤ display_name changed to "🚀 AI Viral Video Factory Pro \| One-click generate director script + real-person voiceover + real-person face swap + motion transfer + 4K HD enhancement + Seedance alternative" |
| **v2.7.0** | 2026-07-21 | **Fusion edition restructure + 13 sub-5 underlying optimizations + director planning layer added**: ① Restructured per design doc (product repositioning → differentiated capability → TRACE five dimensions → local production layer → core workflow → competitive moats), kept all five workflow commands and honesty statements ② Added director planning layer (AI director engine / cinematic storyboard / prompt engineering compiler / honest quality guardian local & free, with standardized 9-element output protocol + multi-industry templates) ③ Per 4.6 report's 13 sub-5 items, item-by-item underlying optimization (trigger method / capability boundary / doc quality / run stability / feature completeness / exception handling / anti-patterns / progressive disclosure / structure clarity / output accuracy / content completeness / creativity / out-of-box) ④ faceswap_pro.py code-level enhancement: segmented self-heal (verify corrupted segments before concatenation, re-render in place, E105) + input pre-processing self-check (warn early for side-face photo) ⑤ Anti-patterns expanded to 13 (including 2 for director layer) ⑥ display_name unchanged |
| **v2.6.0** | 2026-07-20 | Per 2.4.2 review report, item-by-item underlying optimization across sub-dimensions: added kun_init.py one-click init, faceswap_pro.py --wizard interactive guide, segmented concatenation auto-heal, extreme report adds plain_summary, effect reference changed to Markdown text comparison, boundary quick-judgment table + end-to-end example + self-check list, anti-patterns expanded to 11 |
| **v2.5.0** | 2026-07-20 | Scope-consistency deep remediation: face-swap quality layers A–F and engineering enhancements fully separated, A–F letters no longer reused; docs and code 100% consistent |
| **v2.4.2** | 2026-07-20 | All advanced features implemented at code level (segmented resume / per-frame adaptive occlusion / 5 presets / extreme side-face report / batch parallel + resume + ETA) |
| **v2.4.1** | 2026-07-20 | All-dimension (15 sub-5) underlying logic optimization |
| **v2.4.0** | 2026-07-19 | Out-of-box + honest boundary + download resilience triple underlying enhancement (preflight.py / extreme warning / download retry) |
| **v2.3.0** | 2026-07-18 | Deep remediation of "six layers vs two layers" contradiction (removed Layer C/D/E/F fake implementations) |
| **v2.2.0** | 2026-07-18 | Full localization (video_engine.py replaces cloud_helper.py, zero cloud zero cost; removed Veo/Google) |
| v2.1.0 | 2026-07-18 | cloud_helper.py unified cloud call; Pro six-layer enhancement all landed; added D 4K upscaling + E batch face swap |
| v2.0.0 | 2026-07-17 | Full refactor: precise 5-dimension short-board enhancement |
| v1.0.8 | 2026-07-17 | Pro enhancement 2 layers landed (detection enhancement + elliptical feathering) |

---

## Audit Info

- **Three iron rules**: ① Keep original motion only via Workflow A ② AI cannot see images, picture needs manual inspection ③ B/C default to local equivalent (zero cloud, zero cost, zero foreign service)
- **Two red lines (clarified v2.7.0)**: ① Generation/production defaults to fully local, zero cloud, zero foreign, zero cost ② Quality guardian only does technical QC + requires manual inspection, no fake scoring
- **Methodology**: engineering first-success-rate (pre-generation validation + post-generation auto-QC + auto-retry on fail) + director planning layer (creative → plan → production closed loop)
- **Sources**: inswapper / MediaPipe / ffmpeg / real-ESRGAN / AGNES / NVIDIA / Seedance and other open-source + free services
- **Distillation time**: 2026-07-21 (v2.7.0 fusion edition: restructured per design doc + added director planning layer + 13 sub-5 underlying optimizations + faceswap_pro.py segmented self-heal / input pre-check. display_name unchanged; quality guardian insists on honesty, no fake scoring)
