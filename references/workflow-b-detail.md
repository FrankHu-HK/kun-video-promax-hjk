---
module: workflow-b-detail
priority: 中（Workflow B 核心用法已写入 SKILL.md，本文件是详细技术文档）
last_verified: 2026-07-18
---

# Workflow B 详细技术文档（动作迁移 · Motion Transfer）

> SKILL.md 已给"用大白话说"和模型选型指南。本文件是**完整4阶段管线**+**三模型路由详细参数**+**一次成功率工程化**的详细技术参考。

---

## 与 Workflow A 的本质区别（务必先讲清）

- **Workflow A（换脸）**：在原视频上"换脸"，动作/背景/音乐/时长 **100% 保留**（重合度 100%）
- **Workflow B（动作迁移）**：以参考视频的**动作为驱动**，生成一段**全新视频**——目标人物（@Image1）"表演"参考视频（@Video1）里的动作。新视频的背景、画质、动作细节**不会与原参考视频 1:1 一致**，这是生成式扩散管线的固有特性，不是缺陷
- **选型原则**：要"和原视频一模一样"→ Workflow A；要"让目标人物做出参考视频的动作（背景/画质可不同）"→ Workflow B

## 阶段 B0：素材就位与 ASCII 化

1. 参考视频、目标人物照复制为 **ASCII 文件名**（如 `ref_video.mp4`、`target.jpg`）
   ⚠️ 同 Workflow A 坑点：`cv2`/`mediapipe` 读中文路径易失败，必须先 ASCII 化
2. 确认已装依赖：`mediapipe`、`opencv-python`、`numpy`
3. 确认 MediaPipe Pose 模型 `pose_landmarker_full.task` 已就位

## 阶段 B1：骨骼关键点提取（Pose Estimation）

```bash
python scripts/pose_extract.py \
  --video "ref_video.mp4" \
  --out "pose_keypoints.json" \
  --model "models/pose_landmarker_full.task" \
  --step 1          # step=1 逐帧；step=N 抽帧（加快）
```

要点：
- 用 **MediaPipe PoseLandmarker（Tasks API，BlazePose 33 点拓扑）** 逐帧推理
- 输出每帧 33 个关节点归一化坐标 `(x, y, z, visibility)` 序列 → `pose_keypoints.json`
- **作用定位**：运动质检 + 结构化运动表示
  - 质检：可见关节点≥80% 才进入生成（一次成功率前置关卡）
  - 运动表示：可作为运动描述喂给生成模型

## 阶段 B2：选模型 + 动作迁移

### 决策门 B-0（生成前必问）

收到目标照后、委托生成前，**必须确认发型/服装/鞋帽的处置**：
- 选项1（**推荐**）：**沿用照片整体造型**——ID 锁定最稳、成片最像目标本人
- 选项2：**仅锁脸**——服装/发型/鞋帽由提示词或另定
- 选项3：**自定义**

### v2.2.0 重大变更：完全本地化

**默认走本地等价方案**（零云端、零付费、零国外服务）：
```bash
python scripts/video_engine.py --workflow B --video ref.mp4 --photo target.jpg --engine local
# 自动用 Workflow A 换脸+保留原视频动作/背景/音乐
```

**引擎路由表（v2.2.0）**：

| 引擎 | 付费？ | 国外？ | 适用 | 备注 |
|------|--------|--------|------|------|
| **local（默认）** | ❌ **零付费** | ❌ **零国外** | **推荐** | 保留原动作，零云端 |
| agnes | ❌ 终身免费 | ❌ 国内 | 想要"生成全新视频" | 需 AGNES_API_KEY |
| nvidia | ❌ 免费额度 | ❌ 国内 | 想要"生成全新视频" | 需 NVIDIA_API_KEY |
| seedance | ⚠️ 试用版（超量付费） | ❌ 国内 | 字节 Seedance | 需 VOLCENGINE_API_KEY |
| kling | 💰 需付费 | ❌ 国内 | 快手 Kling 3.0 | 需 KLING_API_KEY |

> **v2.2.0 移除 Veo 3.1**（Google Vertex AI，国外服务）——用户反馈"偶尔要国外服务"扣分。

### 旧版引擎详细对比（仅作历史参考，v2.2.0 优先用 local/agnes/nvidia）

| 维度 | Seedance 2.0（字节） | Kling 3.0/O3（快手） |
|------|------|------|
| 动作迁移 | ✓ 即梦"动作模仿" | ✓✓ Motion Control 标杆 |
| 原生音频 | ✗ 无 | △ 部分版本有 |
| 分辨率 | 1080p | ✓✓ 原生 4K 3840×2160 |
| 最长时长 | 8 秒 | ✓✓ 迭代扩展达 3 分钟 |
| 性价比 | ✓✓ 极致（$0.022/秒 Fast） | 中高（$0.09/秒） |

### 路由决策表（v2.2.0）

| 用户需求信号 | 选引擎 | 理由 |
|-------------|--------|------|
| "默认" / "保留原动作" / "零付费" | **local** | **零云端零付费零国外，推荐** |
| "要生成新视频，免费" | agnes | 终身免费，国内可达 |
| "要生成新视频，免费额度更大" | nvidia | NVIDIA 免费额度 |
| "4K / 长视频 / 动作最像" | kling | 原生 4K + Motion Control（需付费 Key） |
| "9:16 竖屏 / 快速出片" | seedance | 原生竖屏 + 极速（试用版） |

### 步骤 2：调用引擎

#### local（默认 · 零云端）
- 自动调用 `faceswap.py`（Workflow A 换脸），**保留原视频动作/背景/音乐**
- 零云端、零付费、零国外服务

#### AGNES（终身免费）
- 异步 API，按任务 ID 拉取
- 适合想要"生成全新视频"且不愿付费的用户

#### NVIDIA（含免费额度）
- NVIDIA NIM 视频生成 API
- 免费额度用完后才需付费

#### Seedance 2.0（国内免费试用）
- 字节即梦"动作模仿"
- 有免费试用额度，超量后付费

#### Kling 3.0/O3（需付费 Key）
- 快手开放平台，**需付费 Key**
- 原生 4K，最长 3 分钟
- 适用：要 4K / 长视频 / 动作最像

### 步骤 3：固化参数预设（提高一次成功率）

| 参数 | 竖屏内容 | 横屏内容 |
|------|---------|---------|
| 比例 | `--ratio 9:16` | `--ratio 16:9` |
| 时长 | Seedance/AGNES 8s / Kling 最长 3min | 同左 |
| seed | 固定值保证可复现；重试时换 seed | 同左 |
| 提示词 | 强调：保持参考动作、面部来自 @Image1、避免畸变 | 同左 |

## 阶段 B3：成品验收（技术层自动质检）

```bash
python scripts/auto_qc.py \
  --video "generated.mp4" \
  --expect-duration 8 \
  --out "qc_report.json"
# 退出码 0=通过，1=不通过(触发自动重试)
```

- **技术层质检**（机器自动）：文件完整/可打开、非全黑、非静帧、时长达标、编码可读 → 不达标自动重试
- **画面质量**（用户目检）：像不像、自然度、有无畸变/鬼影——必须你最终目检
- 附 `pose_keypoints.json` 的"动作覆盖率/可见度统计"作为运动质量客观佐证

## 一次成功率工程化（不达标自动重试）

- 第一次生成 → QC 失败 → **自动换 seed** → 第二次生成 → 失败 → **降级换模型** → 第三次
- 最多 2 次重试 + 1 次模型切换，避免无限循环
- 重试仍失败 → 报告用户"建议手动调参或换素材"
