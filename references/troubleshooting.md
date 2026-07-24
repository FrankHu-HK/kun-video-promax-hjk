---
module: troubleshooting
priority: 高（这是用户遇到错误时第一查的文档）
last_verified: 2026-07-20
version: 2.4.2
---

# 故障速查详细版（Troubleshooting Guide）v2.4.2

> **使用方式**：你看到的现象 → 直接对号入座 → 按"原因→方案"排查。
> 本文档**不假设你有技术背景**——所有术语都在解释一遍。
> **v2.4.2 更新**：极端侧脸/遮挡问题已有实际解决方案；新增高级功能故障排查章节。
>
> 如果这里没有覆盖你的情况，把"具体报错文字+你跑的命令"发给我。

---

## 📌 效果参考说明

> 本文件不再内嵌图片（发布平台不渲染 PNG）。各场景预期观感见 SKILL.md「效果预期对照（文字版）」。

## 速查表（按现象分类）

---

### ① 照片相关（E1xx 错误）

#### 现象：❌ "照片读不了 / 无法读取照片"
**白话翻译**：脚本打不开你的照片文件。

**可能原因**：
- 文件被其他程序占用（预览中打开）
- 格式太冷门（HEIC、RAW）
- 路径含特殊字符或太长

**解决方案**：
1. 关闭所有预览程序
2. 用 Windows 画图或在线工具转成 JPG
3. 重命名为简单英文数字名（`photo.jpg`），放简单路径（`D:\photo.jpg`）

#### 现象：❌ "照片中未检测到人脸"（E101）
**白话翻译**：没在照片里找到脸。

**可能原因**：
- 脸被头发/墨镜/口罩挡住
- 脸太小（全身远景照）
- 太模糊 / 强烈侧脸或仰拍俯拍

**解决方案**：
1. 换一张**正面或近正面**清晰人像照
2. 尺寸 ≥512×512 像素
3. 完整露出额头、眼睛、鼻子、嘴巴
4. 光线均匀，不要逆光

---

### ② 视频相关（E2xx 错误）

#### 现象：❌ "视频无法打开"（E202/E103）
**白话翻译**：读不了视频文件。

**原因与解决**：
1. **转码为 mp4**（格式工厂 / HandBrake，H.264 编码）—— 最常见解法
2. 先用播放器确认能正常打开
3. 文件名不含特殊字符

#### 现象：❌ "视频输出失败"（E205）

**原因与解决**：
1. 输出目录有写权限？→ 别放 `C:\Program Files\`
2. 磁盘空间 ≥1–2GB？
3. 输出路径简化：`D:\output\result.mp4`

---

### ③ 模型相关（E102 等）

#### 现象：❌ "模型加载失败"（E102）

```bash
# 重跑模型下载
python scripts/download_models.py --work-dir . --with-mediapipe
```
检查 `models/inswapper_128.onnx` 和 `buffalo_l/` 是否存在。

#### 现象：❌ "下载很慢/失败"
1. 能访问 modelscope.cn？
2. 手动下载放 `models/`
3. MediaPipe 自动切 gitee/ModelScope 镜像

---

### ④ 换脸效果问题（⚠️ v2.4.2 大更新）

#### 现象：换脸后脸"假" / "贴图感强"

| 排序 | 原因 | 解决 |
|------|------|------|
| ① | 照片角度差 | 选角度接近的照片 |
| ② | 未用 Pro 版 | 改 faceswap_pro.py |
| ③ | 参数未优化 | 加 `--preset quality` |
| ④ | 视频画质低 | 先 enhance_4k.py 升频 |

```bash
python scripts/faceswap_pro.py --video in.mp4 --photo face.jpg --out out.mp4 --preset quality
```

#### 现象：普通侧脸漏换（≤70°偏转）

**v2.4.2 方案**：

```bash
# sideface 预设：加大覆盖 + 自适应蒙版 + 极端帧自动裁剪
python scripts/faceswap_pro.py --video in.mp4 --photo face.jpg --out out.mp4 --preset sideface
```

底层机制（第 462–463 行）逐帧自适应：
- yaw 越大 → mask_scale 越大（最大 1.8x）、feather 越柔和（最大 0.2）
- 不再是固定参数，而是**每帧根据实际偏转角动态调整**

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

#### 现象：⭐ 极端侧脸（>70°）效果差 —— v2.4.2 已有实际方案

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**旧答案（v2.4.0）："无完美方案"**
**新答案（v2.4.2）：三层防护**

| 层级 | 机制 | 效果 |
|------|------|------|
| L1 | `--preset sideface`（mask_scale=1.40, feather=0.11） | 覆盖范围 +50%，边缘更柔 |
| L2 | 逐帧自适应 ms/feather 公式 | 动态跟随偏转角放大 |
| L3 | `--auto-trim-extreme`（自动裁掉极端帧） | 输出干净版本不含极端帧段 |

```bash
python scripts/faceswap_pro.py --video extreme_video.mp4 --photo face.jpg \
    --out result.mp4 --preset sideface --segment-secs 10
```

完成后查看 `<output>_extreme_report.json` 了解各时间段段的极端占比和位置。**如果某段极端帧占比 >15%**，考虑手动拆分该段单独处理或降低期望。

**诚实声明**：极端侧脸 >80° 或完全侧面轮廓的情况，inswapper 架构本身仍有物理限制。v2.4.2 的三层防护在 ≤75° 场景下效果显著提升，但 >85° 的纯轮廓场景仍建议人工介入。

#### 现象：⭐ 脸部被遮挡（口罩/墨镜/手）边缘有明显接缝/鬼影

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**v2.4.2 方案**：

```bash
python scripts/faceswap_pro.py --video masked_video.mp4 --photo face.jpg \
    --out result.mp4 --preset occlusion
```

occlusion 预设参数：mask_scale=1.30（穿透遮挡区）、feather=0.13（强羽化）。配合逐帧自适应公式，遮挡区域越大蒙版越宽越柔。

**组合策略**：同时有侧脸+遮挡 → 优先用 `sideface`（mask_scale 更大 = 1.40 vs 1.30）。

**诚实声明**：全脸完全被挡住（仅露出眼睛以下或更低）→ AI 物理无法推断面部结构，任何工具都无能为力。

#### 现象：换脸后背景边缘有痕迹
1. Pro 版椭圆羽化融合已落地 → 改用 faceswap_pro.py
2. 或保留原视频背景（推荐，零重影风险）

---

### ⑤ 去水印问题

#### 现象：去水印后还有残留

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

1. 手动 ROI：`--roi x y w h`
2. 提高参数：`--scale 4 --radius 12`
3. 固定 logo 兜底：`fix_logo.py`
4. 复验：`verify_final.py --video output.mp4 --bbox face_bboxes.json --step 1`

#### 现象：去水印后画面变模糊
→ 降低 `--radius` 到 5–8（inpaint 半径过大导致模糊）

---

### ⑥ 🔥 高级功能故障排查（v2.4.2 新增）

#### 现象：`--resume` 后仍从头开始跑？

**检查点**：
1. `.resume_state.json` 文件是否存在且可读？（应与输出文件同路径）
2. 文件内容中 `"done"` 列表是否非空？
3. 是否在同一次命令中加了 `--resume` 且输出路径一致？

**调试命令**：
```bash
# 查看 resume state 内容
cat output.mp4.resume_state.json
# 应该看到 {"done": [0, 1], "segs": {...}, ...}
```

若 state 文件损坏或空 → 删除它重新跑（会从头开始但至少不会卡住）

#### 现象：拼接阶段报错 "ffmpeg concat failed"

**原因**：ffmpeg 不可用或输出路径含特殊字符

**回退机制**：代码内置 cv2 回退（concat_videos 第 231 行）。若两者都失败：
1. 确认 ffmpeg 已安装并在 PATH：`ffmpeg -version`
2. 手动拼接 seg 文件：
   ```bash
   # 生成 concat list
   ls seg_*.mp4 | sort > concat_list.txt
   # sed 在每行前加 "file '"
   ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4
   ```

#### 现象：`--workers N` 并行时内存不足 / OOM

**原因**：每个子进程占 ~1–2GB 内存，workers 过高超出物理内存。

**解决**：
1. 降低 workers 数：`--workers 2` 或 `--workers 1`（串行）
2. 减少并发：先 `--workers 2` 测试稳定再逐步加
3. 监控内存：Windows 任务管理器看 Python 进程内存占用

#### 现象：batch_state.json 被锁定 / 写入失败

**原因**：两个并行 batch 进程写同一 state 文件冲突

**解决**：
1. 确保只有一个 batch 进程运行
2. 若上次异常退出锁残留 → 删除旧的 batch_state.json 重新跑
3. `--resume` 时会读取旧 state，确保只有一个进程写入

#### 现象：`--preset xxx` 报错 "invalid choice"

**可用值**：auto / speed / quality / sideface / occlusion

```bash
# 正确示例
--preset quality      ✅
--preset sideface     ✅
--preset fast         ❌ （不存在）
```

#### 现象：extreme_report.json 未生成

**条件**：仅在 faceswap_pro.py 运行完成（正常退出）后才生成。中断时不会生成。

**解决**：正常完整跑完一次即可生成。如需中途查看进度，直接读 `.resume_state.json` 中各 seg 的 stats。

---

### ⑦ 云端生成问题（Workflow B/C）

#### 现象：❌ "API Key 无效" / "鉴权失败"
1. 确认环境配置了对应 Key
2. 检查是否过期/禁用
3. 默认通道 Seedance 无需 Key

#### 现象：❌ "生成超时" / "任务失败"
1. 重试 1–2 次（默认最多 2 次重试）
2. 检查输入素材合规性
3. 换引擎（local → AGNES → NVIDIA → Seedance → Kling）

#### 现象：生成结果不自然 / 动作不对
1. 参考视频动作清晰简单
2. 目标照角度匹配
3. 换不同模型重试（Kling 动作最像）

---

### ⑧ 通用排查流程

```
[步骤1] 看错误码（E1xx/E2xx/E102）
  ↓ 查本速查表对应条目
[步骤2] 读错误信息具体提示
  - 路径问题?   → 改英文路径
  - 文件问题?   → 检查文件存在/格式
  - 模型问题?   → 重跑 download_models.py
  - 高级功能?   → 见「⑥ 高级功能故障排查」
[步骤3] 跑诊断命令
  python scripts/auto_qc.py --input your_output.mp4
  python scripts/verify_final.py --video your_output.mp4 --bbox face_bboxes.json
[步骤4] 仍然不行?
  → 收集：错误码 + 完整命令 + 截图 → 发我帮你查
```

---

### ⑨ 画质提升问题

#### 现象：4K 升频后还是模糊 / 有压缩伪影

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

1. 确认输入不是已损坏的低质量源（升频无法凭空创造细节）
2. 推荐流程：**先升频 → 再换脸**（避免二次压缩损失）
3. enhance_4k.py 使用 ffmpeg lanczos，对 1080p→4K 提升明显；720p 以下源效果有限
4. 如需更强效果：先用 Topaz Video AI（付费）或 Real-ESRGAN（开源）预处理

---

### ⑩ 批量高级版问题

#### 现象：批量跑到一半某个视频失败导致全部停止

（文字对照见 SKILL.md「效果预期对照」，发布平台不渲染图片）

**原因**：默认行为——任一视频失败则中止全部。

**解决**：加 `--continue-on-error`：
```bash
python scripts/batch_faceswap.py --photo face.jpg --videos-dir videos/ \
    --out-dir out/ --workers 4 --continue-on-error --retry 2
```

#### 现象：批量续跑跳过了所有视频（全显示 skipped）

**原因**：`batch_state.json` 记录上次的 success 状态，`--resume` 全部跳过。

**解决**：
- 确认产物确实已正确生成 → 说明上次其实成功了
- 要重跑全部 → **不加 `--resume`**，或删掉 `out_dir/batch_state.json`
- 只重跑失败的 → 编辑 batch_state.json 将对应视频状态从 "success" 改为 "fail"

#### 现象：ETA 时间不准 / 进度卡住

**原因**：ETA 根据已完成任务的平均速率估算，前几个任务波动大时不准。

**正常现象**：完成 3–5 个任务后 ETA 会趋于准确。如果长时间卡住（>10分钟无日志）→ 可能子进程死锁，Ctrl+C 重启。

---

### ⑪ 预防性检查清单（跑前必过）

| 检查项 | 状态 | 备注 |
|--------|------|------|
| Python ≥3.10 | □ | mediapipe 需要 |
| 依赖装全（8 个核心包） | □ | `download_models.py` 一键安装 |
| 模型已下载（models/） | ⬜ | 首次必须跑 |
| 输入 mp4 格式 | □ | mov/avi 先转码 |
| 照片 ≥512×512 清晰正面 | ⬜ | 小/模糊/侧脸照效果差 |
| 文件名英文数字 | ⬜ | 中文路径有兜底但显式更好 |
| 输出目录可写 | □ | ≥2GB 磁盘空间 |
| 长视频准备用 `--resume` | ⬜ | 防中断白费 |

**全部勾选 ✓ → 大概率顺利。**

---

## 错误码速查

| 码 | 范围 | 含义 | 脚本 |
|----|------|------|------|
| E100–E105 | Pro 换脸 | faceswap_pro.py 详见 [workflow-a-detail.md](workflow-a-detail.md) |
| E200–E205 | 基础换脸 | faceswap.py 详见 [workflow-a-detail.md](workflow-a-detail.md) |
| E400–E402 | 批量换脸 | batch_faceswap.py（见 Q10 高级用法）|
| E001–E010 | 输入验证 | 空/缺参/矛盾/超长等 |

## 获取更多帮助

- **常见问题** → [FAQ.md](FAQ.md)
- **10 条实战坑点** → [pitfalls.md](pitfalls.md)
- **模型下载源** → [models_sources.md](models_sources.md)
- **核心命令速查** → [../SKILL.md](../SKILL.md)
