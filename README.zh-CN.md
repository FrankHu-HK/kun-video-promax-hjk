<div align="center">
  <img src="banner.svg" alt="KUN Video ProMax 横幅" width="100%" />
  <h1>KUN Video ProMax</h1>
  <p><b>本地优先的 AI 视频工厂</b> —— 换脸、去水印、动作迁移、AI 口播、4K 升频，外加导演策划层。100% 本地、零云端、零费用。</p>
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
  <img src="https://img.shields.io/badge/运行环境-本地优先-0ea5e9?style=flat-square" alt="Local First">
  <img src="https://img.shields.io/badge/零云端-是-22c55e?style=flat-square" alt="Zero Cloud">
  <img src="https://img.shields.io/github/languages/top/FrankHu-HK/kun-video-promax-hjk?style=flat-square" alt="Language">
</p>

<p align="center">
  [简体中文] | <a href="README.md">English</a>
</p>

---

## KUN Video ProMax 是什么？

KUN Video ProMax 是一个融合版、专业级 **AI 视频生产智能体**（v2.9.0），包含两层：

- **本地生产层** —— 换脸、去水印、动作迁移、AI 口播、4K 升频、批量换脸，全部 **100% 跑在你的机器上**。无云端、无国外服务器、无订阅费。
- **导演策划层** —— AI 导演引擎、电影级分镜、提示词工程编译器，以及免费、轻依赖的"诚实质量守护"。

> 🔒 **两条不可谈判的底线：**（1）生成/生产默认全本地、零云端；（2）质量评估绝不夸大 —— 只做技术 QC + 要求人工目检，绝不编造分数。

## 为什么选 KUN Video ProMax？

### 大多数"AI 视频"工具的痛点

- **云端绑架** —— 你的素材离开本机，按次渲染收费。
- **假产出** —— 有些工具返回一个假链接就号称"完成"。
- **只停留在文档** —— 承诺的能力从未真正接上管线。

### 核心思路：真实管线 + 诚实状态

本项目交付的是 **可运行的本地管线**，而不是承诺：

- 云端引擎（agnes / nvidia / seedance / kling）**诚实标注为未实现** —— 选中即返回明确错误 `E200` 并引导你用本地方案，绝不返回假链接。
- `kun_setup.py` —— 一键安装 + 自检，降低首装摩擦。

## 核心特性

- **换脸**（`faceswap_pro.py`）—— 多层增强，**原子写检查点**，中断可续跑不丢进度。
- **去水印** —— 去除抖音 / 固定 logo 水印，同时保留原始动作、背景与音频。
- **动作迁移（Workflow B）** —— 真实两步本地管线：`pose_extract.py`（光流动作强度 / 清晰度 / 静态占比预检，无 mediapipe 也能跑）→ `video_engine.py` 串联"预检 → 换脸"真实出片。
- **AI 口播（Workflow C，v2.9.0）** —— `tts_voiceover.py` 把话术变 **真实本地配音**（默认 `pyttsx3` 离线 / 零国外 / 零费用；可选 `edge_tts` 免费云），再合成口播 MP4。
- **4K 升频**（`enhance_4k.py`）—— `ffmpeg` 升频 + `unsharp` 真实锐化，附清晰度对比报告；可选 `cv2.dnn_superres`。
- **批量换脸** + 断点续跑 + 格式自动转码。
- **导演策划层** —— `video_engine.py --mode director` 直接启动导演大脑（分镜 + 提示词编译），不用猜怎么开口。
- **诚实质量守护** —— 只做技术 QC，标记需人工目检，绝不编造分数。

## 快速开始

### 环境要求

- **Python 3.10+**
- **ffmpeg** 已加入 PATH
- `requirements.txt` 中列出的依赖包

### 安装与运行

```bash
# 一键安装 / 自检
python kun_setup.py

# 导演策划层
python video_engine.py --mode director

# 本地换脸管线
python video_engine.py --mode faceswap --input src.mp4 --target face.jpg

# 真实本地 AI 配音
python tts_voiceover.py --text "你的话术"

# 4K 升频
python enhance_4k.py --input video.mp4
```

## 开发

1. Fork 并克隆仓库。
2. `python -m venv .venv && pip install -r requirements.txt`
3. `python kun_setup.py` 校验环境。
4. 提交 PR 前先运行 `scripts/` 中的自检脚本。

## 路线图

见 [ROADMAP.md](ROADMAP.md)。

## 贡献

欢迎 Pull Request。开发设置与 DCO 签署规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。

<a href="https://github.com/FrankHu-HK/kun-video-promax-hjk/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=FrankHu-HK/kun-video-promax-hjk" />
</a>

## 💖 赞助

如果这个工厂帮你省下云端订阅、还真的把视频渲染出来了，欢迎赞助其开发。赞助让它保持 **本地优先、诚实、免费**。

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen)](https://github.com/sponsors/FrankHu-HK)

## 许可证

[MIT](LICENSE) — Copyright 2026 Frank Hu（胡景堃）。
