# 坑点与实战结论（提炼自真实生产）

## 1. 换脸方向：必须 Face Swap，不是生成式视频
- 用户要“动作和原视频一模一样”→ 只能用 insightface+inswapper 换脸。
- VideoGen / Seedance / 智谱图生视频 = 按提示词生成新动作，**无法复制原片段动作**。
  第一次就栽在这：生成式产物动作/背景/BGM 全错。

## 2. 中文路径：cv2.imread 读不了
- 现象：读用户照片返回 None。
- 根因：`cv2.imread` 底层 C++ 实现不支持 Unicode 路径（Windows 中文用户名/中文文件夹常见）。
- ❌ 错误做法：直接把含中文的路径传给 cv2
  ```python
  img = cv2.imread("C:/用户/照片/我的脸.jpg")   # 返回 None，读不了
  ```
- ✅ 正确做法：复制到 ASCII 临时名再读（faceswap.py 已内置此兜底）
  ```python
  import shutil, tempfile, os
  tmp = os.path.join(tempfile.gettempdir(), "user_photo.jpg")
  shutil.copy(原路径, tmp)
  img = cv2.imread(tmp)                          # 正常读取
  ```
- 解决：复制为 ASCII 名再读；faceswap.py 已内置兜底。

## 3. CPU 性能：每帧 8s → 1.4s（关键优化）
- 根因：insightface 默认加载全部模型（检测+识别+3D/2D关键点+性别年龄）。
- 换脸只需检测+识别。从 `app.models` 字典**真删**多余模型：
  ```python
  for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:
      app.models.pop(_k, None)
  ```
- ⚠️ 坑：不能只设 `app.landmark_3d_68 = None`（顶层属性无效，仍在跑）；
  必须 `app.models.pop()`。验证：单帧耗时从 8s 降到 1.4s，1048 帧约 24 分钟。

## 4. “AI生成”去除：整块 inpaint 会失败
- 错误做法：对固定区域做全 1 mask 的 `cv2.inpaint` → 重建≈原图，文字淡而不消，OCR 仍可识别。
- 正确做法：逐帧 **OCR 定位文字边界框 → 仅对文字像素(留 8px 余量)做 inpaint（半径 6，TELEA）**。
  背景零误伤，文字彻底消失。抖音 AI 角标常**间歇淡入淡出**（所以用户看到“偶尔出现”），
  必须逐帧处理而非抽几帧。

## 5. 抖音录屏 UI 布局（裁切前必看一帧）
- 顶部：状态栏 + 搜索栏（y≈0~165）
- 左侧：红包/小角标（含“AI生成”小角标，约 x≈10~72, y≈498~524）
- 主画面：跳舞人物（y≈390~880，人物居中偏下、占比较小）
- 右侧：头像+关注 / 互动栏（x≈620~720，叠加主画面）
- 底部：全屏键 / 文案 / 音乐标签 / 搜索推荐（y≈880~1554）
- 裁切参数 `crop=W:H:X:Y` 必须按实际帧测算，切勿硬编码（不同视频不同）。

## 6. 背景替换：重影难根治，优先回退原背景
- 抠像（MediaPipe / matting）换背景会产生**逐帧边缘时序抖动 → 重影/浮空**。
- 去重影手段：因果式 EMA 时序平滑（β≈0.35）+ 大 sigma 高斯羽化（σ≈8）+ 人物色彩匹配。
- 但纯 CPU、无强 matting 模型时仍难完美。用户反感重影时，**回退“用原视频背景”最稳**
  （只换脸+去角标，不做背景替换）。用户明确要故宫等换景时再攻坚，并提前告知风险。

## 7. 模型/库版本坑
- mediapipe 0.10.35 **已无 `solutions` API**，必须用 Tasks API：
  `from mediapipe.tasks.python import vision; vision.ImageSegmenter.create_from_options(...)`。
- PyPI 上的 `facefusion` 是空壳包（version 0.0.0，无实际代码），勿用。

## 8. 成品验证
- 当前会话模型**不支持读图**，画面质量只能用户目检。
- 但“AI生成”文字去除可用 OCR 程序化验证（verify_clean.py），必须 0 残留才交付。

## 9. 落盘与呈现
- 文件一律落 `工作区` 相关工作区（通用约定）。
- 交付用 present_files 在对话框呈现，确保用户能直接预览/下载。

## 10. 动作迁移（Workflow B）：生成新视频，非 1:1 复制
- Workflow B 用 `@Video1`(参考视频动作) + `@Image1`(目标照身份) 委托 `seedance-video-gen` 生成新视频。
- 与 Workflow A 本质不同：A=100% 保留原动作/背景/音乐；B=**生成全新视频**，背景/画质/动作细节非原样。
  给用户交付前必须先讲清这一定位，避免"怎么和原视频不一样"的误解。
- 参考视频质量决定迁移上限：单人、全身、动作清晰、无遮挡最佳；多人/遮挡严重会降低质量。
- 阶段 B1 的 MediaPipe Pose 提取主要用于**运动质检**（可见关节点统计）与可选本地重定向输入；
  默认扩散生成不依赖该 JSON，`@Video1` 由生成模型内部理解运动。
- 画面质量（像不像、自然度、有无鬼影）只能用户目检，AI 不能读图。
- `mediapipe>=0.10.35` Pose 必须用 Tasks API（`vision.PoseLandmarker`），旧 `solutions.pose` 已移除。
