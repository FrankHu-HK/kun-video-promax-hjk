---
module: workflow-a-detail
priority: 中（Workflow A 核心用法已写入 SKILL.md，本文件是详细技术文档）
last_verified: 2026-07-17
---

# Workflow A 详细技术文档（换脸+去水印）

> SKILL.md 已给"新手快速通道"和最简命令。本文件是**4 阶段完整管线**+ **Pro 增强6层设计蓝图**+ **所有参数详解**+ **分步确认协议**的详细技术参考。
> 80% 用户**不需要读这个文件**——直接用 SKILL.md 的最简命令即可。

---

## 阶段 0：素材与模型就位

1. 把用户照片复制为 **ASCII 文件名**（如 `user_photo.jpg`）。
   ⚠️ **坑点**：`cv2.imread` 读不了中文/含中文路径，必须复制成纯 ASCII 名再读。
2. 确认源视频路径、模型路径。如缺模型，跑 `scripts/download_models.py`。

## 阶段 1：换脸（保留原背景/动作）

### 决策门 A-0（生成前必问）

收到目标照片后、运行换脸前，**必须先用结构化问题确认换脸范围**：

- 选项1（**推荐**）：**只换脸**，保留原视频人物的身形/服装/鞋帽（最自然、最低返工风险，契合 Workflow A"100% 保留"定位）
- 选项2：**换成照片整体造型**（脸+发型+服装+鞋帽）——需走扩散重绘（Workflow B 的 ID 锁定 / F 兜底 / 或 facefusion）
- 选项3：**自定义**（如只换脸 + 用照片发型但保留原服装）

**不得默认**。确认后再执行。

### 基础换脸命令

```bash
python scripts/faceswap.py \
  --video "源视频.mp4" \
  --photo "user_photo.jpg" \
  --out "swapped_raw.mp4" \
  --bbox "face_bboxes.json" \
  --models-dir "models" \
  --insight-root ".insightface" \
  --target-side right
```

### `--target-side` 参数详解

| 值 | 行为 | 适用场景 |
|---|---|---|
| `right`（推荐） | 双人同框时换**最靠右的脸**；单人镜头不换 | 90% 用户场景 |
| `left` | 双人同框时换**最靠左的脸**；单人镜头不换 | 左侧人物场景 |
| `largest` | 换**bbox 最宽**的人脸 | ⚠️ 高危：双人脸宽接近时会**逐帧误换**配角 |

> ⚠️ **何时禁用 `largest`**: 当双人脸宽接近（如右143–187px / 左≈149px）时，约 1/3 帧里较宽的是配角，`largest` 会**逐帧误换**。**只要用户要"换右侧/指定侧那个人"，一律用 `right`/`left` 按位置锁定**。

### 性能优化（已内置）

基础换脸脚本已自动 pop 掉用不上的模型（`landmark_3d_68 / landmark_2d_106 / genderage`），CPU 单帧 **8s → 1.4s**（约 5.7 倍提速）。无需额外配置。

### 错误码（基础版）

| 码 | 触发 | 解决 |
|----|------|------|
| E200 | 照片不存在或无法读取 | 检查文件路径/格式 |
| E201 | 照片中未检测到人脸 | 换更清晰的正脸照 |
| E202 | 视频无法打开 | 转 mp4 格式 |
| E203 | 模型加载失败 | 重跑 download_models.py |
| E204 | 单帧处理失败（保持原帧） | 跳过，E104 报告跳过比例 |
| E205 | 输出视频写入失败 | 检查输出目录权限 |

## 阶段 1-Pro：增强换脸（已落地 2 层 A+B，4 层规划中）

> ⚠️ **何时用 Pro**：基础版出现以下任一穿帮时改用 Pro 通道：
> ① **侧脸没换**——人物转侧脸时侧脸仍是原视频的脸
> ② **遮挡露出瞬间闪原脸**——脸被物体挡住后重新露出的一瞬是原脸
> ③ **戴眼镜/饰品换脸不自然**——镜框边缘错位、脸假
> ④ **换脸边界衔接生硬**——能看出方形抠图边

### Pro 增强层设计蓝图（含落地状态）

| 层 | 措施 | 治哪个问题 | 落地状态 |
|----|------|-----------|----------|
| A 检测增强 | det_size 640→1024、det_thresh 0.5→0.3 | ①侧脸漏检 ②遮挡漏检 | ✅ **已落地**（Pro 默认启用） |
| B 椭圆羽化 | 放大椭圆羽化融合蒙版，软化方形硬边 | ③衔接生硬 ②遮挡露出闪原脸 | ✅ **已落地**（enhanced_paste 椭圆羽化） |
| C 时序追踪 | 检测失败帧→上一成功帧 ROI 二次低阈值检测→短间隙位移填充 | ②遮挡露出闪原脸 ①侧脸断续 | ⚙️ **规划中（未实现）** |
| D 智能丢弃 | 过滤掉明显错误的检测（太小/严重超出边界/关键点异常） | ①侧脸断续 ④边界穿帮 | ⚙️ **规划中（未实现）** |
| E 多脸防错 | 多人场景基于上一帧 bbox 的目标一致性选择 | ②遮挡露出 ①侧脸断续 | ⚙️ **规划中（未实现）** |
| F 扩散兜底 | 输出帧自动质量评估 + 低质量帧软羽化混合 | ③④ 极端情况 | ⚙️ **规划中（未实现）** |

### Pro 命令

```bash
python scripts/faceswap_pro.py \
  --video "源视频.mp4" \
  --photo "user_photo.jpg" \
  --out "swapped_pro.mp4" \
  --bbox "face_bboxes.json" \
  --fallback "fallback_frames.json" \
  --models-dir "models" --insight-root ".insightface" \
  --target-side right \
  --det-size 1024 --det-thresh 0.3 \
  --yaw-max 70 --gap-max 8
  # 戴框架眼镜且要保留眼镜: 加 --keep-glasses
  # 调试: --no-feather 关羽化 / --no-color 关肤色对齐
```

### Pro 输出

- `swapped_pro.mp4`：Pro 增强（已落地 2 层 A+B）后的换脸视频
- `fallback_frames.json`：需扩散兜底重绘的帧区间（格式 `{"ranges":[[起始帧,结束帧],...]}`）
- 控制台打印统计：`swapped`(正常换) / `roi_rescued`(ROI二次救回) / `filled`(位移填充) / `fallback`(交兜底) / `extreme_yaw`(极端侧脸)

### 诚实边界

- A/B/D/E 是本地框架内**可显著改善**的稳妥增强；**①大角度侧脸(yaw>70°) 是 inswapper_128 架构硬上限**——无法凭空重建看不见的半张脸。
- `--keep-glasses` 因无专用镜框分割模型，会**连同原眼睛一起叠回**→眼神偏向原人物；仅适合"必须保留原框架眼镜"的场景。
- Pro 版速度慢于基础版，属"质量优先"通道；无穿帮时用基础版 `faceswap.py` 更快。
- 增强未在真实素材端到端验证画面（当前会话模型不能读图），仅保证逻辑自洽；请用真实视频抽检。

### Pro 错误码（E100-E105）

| 码 | 含义 | 触发 | 解决 |
|----|------|------|------|
| E100 | 照片读取失败 | 路径/格式/编码问题 | 检查照片 |
| E101 | 无人脸 | 脸太小/遮挡/侧脸 | 换正脸照 |
| E102 | 模型缺失 | inswapper/buffalo_l 未下载 | 重跑 download_models.py |
| E103 | 视频无法打开 | 格式/编码问题 | 转 mp4 |
| E104 | 异常帧过高（>20%） | 处理失败过多 | 换更清晰的视频或照片 |
| E105 | 重试耗尽 | 模型/网络问题 | 检查环境后重试 |

## 阶段 2：去抖音全文字水印（OCR + inpaint）

```bash
python scripts/clean_douyin.py \
  --input "swapped_raw.mp4" \
  --output "swapped_clean.mp4" \
  --scale 2 --radius 8
```

**关键要点**：
- **逐帧 OCR**（rapidocr，默认放大 2 倍提升小字召回）匹配抖音关键词
- **仅对文字像素做 inpaint**（半径 8，TELEA），背景零误伤
- ⚠️ **不要对整块区域做全 1 mask inpaint**——那会重建≈原图，文字淡而不消。必须"OCR 定位文字边界框 → 只填充文字像素"
- ⚠️ **随画面移动的抖音文字**（如抖音号、作者昵称）：必须逐帧 OCR 定位，**不能用固定矩形区域**

## 阶段 2.5：去右下角固定「抖音」logo

某些抖音视频右下角有**平台级固定 logo**（坐标恒定，如 x≈614–697 / y≈1122–1167），因字小阶段2的 OCR 偶发漏检。用固定区域 inpaint 兜底：

```bash
python fix_logo.py \
  --input swapped_clean.mp4 --output swapped_clean_v2.mp4 \
  --region 1100 1190 595 715 --radius 10      # y0 y1 x0 x1（含余量）
```

## 阶段 3：合成原 BGM（ffmpeg）

用完整版 ffmpeg（CNTV 自带的 ffmpeg 是阉割版，不可用）：

```bash
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -i swapped_clean_v2.mp4 -i "源视频.mp4" \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a copy -movflags +faststart output_final.mp4
```

- 音频用 `-c:a copy` 从源视频**无损保留原音**（AAC 48kbps 直接 copy）
- 视频从 mp4v 转 libx264 提升兼容性与画质
- `-pix_fmt yuv420p` 保证手机可播

## 阶段 4：全片复验

```bash
python scripts/verify_final.py \
  --video output_final.mp4 \
  --bbox face_bboxes.json \
  --models-dir "models" --insight-root ".insightface" \
  --step 1          # step=1 全片OCR(最严)；step=3 抽样约161帧(较快)
```

判定：
- **抖音水印残留率 ≤ 2%** 为可控；为"认真检查"交付应做到 **0 残留**（用阶段 2.5 兜底 logo）
- 同时输出换脸覆盖统计（总帧/已换脸/右侧换脸/跳过帧）
- 当前会话模型**不支持读图**，画面质量（像不像、自然度、有无抠图感）**必须用户目检**

## 极端侧脸/遮挡处理实战技巧

| 情况 | 推荐方案 |
|------|---------|
| 普通侧脸（yaw≤70°） | Pro 增强 + 检测尺寸 1024 |
| 极端侧脸（yaw>70°） | inswapper 架构硬限，**无完美方案**——拆帧 Photoshop 处理 |
| 部分遮挡（眼镜/手挡） | Pro 增强（可改善） |
| 全遮挡（墨镜+口罩） | 跳过该段或拆帧处理 |
| 戴眼镜想保留 | `--keep-glasses`（有眼神偏移风险） |
| 背景替换需求 | **回退原背景**（最稳）或转专业工具（剪映/Premiere 绿幕抠像） |
