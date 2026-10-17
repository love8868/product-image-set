# 产品详情套图项目 · 侦察报告（合并版）

> 两轮侦察合并：第一轮覆盖行业做法、平台规范、可复现环节、工具链、交付物形态；第二轮专项覆盖"产品不变形"技术路线（约束：只用 Gemini 和 OpenAI）、GitHub 开源项目。
> 凡标注"官方"的均来自一手来源；其余为社区与从业者经验，已区分标注。平台规则会更新，做图前务必在各自商家后台复核。

---

## 第一部分：行业做法与平台规范

### 1. 行业标准项目流程（6 步）

综合电商美工/代运营/设计工作室的通用做法（来源：[qlaaa 电商运营笔记](http://qlaaa.com/articles/ps-ai-detail-page)、[由前AI 详情页指南](https://www.youqianai.com/detail-page-guide.html)、[之宙网络](https://www.zcosm.com/jishuxuetang/97.html)、Upwork 详情页设计服务页）：

1. **资料收集**：商品图（多角度/细节）、基本参数（名称/材质/尺寸/规格/包装清单）、卖点与受众、使用场景、视觉要求（参考风格、配色、文案方向）。常见遗漏：不同型号图片混用、单位不一致、"希望实现的效果"被当成已验证事实。
2. **确定结构**：先定信息架构再动手——首屏 → 卖点 → 场景 → 细节 → 参数 → 保障/FAQ。数码类常按"产品展示—真实功能—接口/结构—兼容范围和参数"组织；家居类按"整体外观—使用环境—材质细节—尺寸规格"。
3. **素材制作**：拍/精修白底图（抠图换底）、AI 生成场景图（参考图 + 提示词反复迭代）。经验：原片底子越干净后面越省；场景图构图多选 3:4，上下留白方便排版。
4. **排版设计**：PS/Figma 分区块排版，一屏一个主题，**全页字体和字号层级统一**（最容易被忽略的坑）。
5. **校对验收**：文字/单位/规格真实性核对；各屏产品外观、配色一致性；图片尺寸/文件大小/格式符合各平台要求；素材商用权限确认。
6. **交付**：成品图 + 可编辑源文件 + 字体说明 + 命名规范 + 使用说明。

行业趋势：AI 把"文案策划"并入了设计和运营岗；一站式 AI 详情页工具（如由前AI、易尚货）已经做到"上传商品图 → 自动识别分类 → 选模板 → 一分钟生成"，批量处理几十个商品。

### 2. Amazon 图片规范（官方）

官方出处：[Seller Central 产品图片要求讨论帖](https://sellercentral.amazon.com/seller-forums/discussions/t/4b3c4c39-6f8c-4312-aa0e-99982eb8f5e1)（引用官方要求页原文）、[欧洲站帮助页 G1881](https://sellercentral-europe.amazon.com/help/hub/reference/external/G1881?locale=en-GB)、[sell.amazon.com 官方博客](https://sell.amazon.com/blog/product-photos-video)。

**技术要求（所有图片）：**
- 长边 500–10,000 像素；**≥1000 像素才有缩放功能**，官方推荐 2000 像素
- 格式：JPEG（官方首选）、TIFF、PNG、非动态 GIF；**不支持 WebP**
- 清晰、无像素化/锯齿；sRGB 色彩；单张建议 ≤10MB
- 文件名需含产品标识（ASIN/UPC/EAN）

**主图硬性规则（违反会被下架/屏蔽搜索）：**
- 纯白底 RGB 255,255,255（偏灰/米白都会被系统判定违规）
- 产品占画面 **≥85%**
- 无文字、logo、水印、边框、色块、图形叠加
- 只展示实际在售商品，无道具、无多余配件；服装类外不许用模特
- 禁止：用户评价截图、五星图案、"包邮"等承诺性文字、Amazon 徽标/Prime/Alexa 字样、"Amazon's Choice/Best Seller"类徽章

**附加图策略（官方 best practice）：**主图之外的 7–8 个槽位可放生活场景图、信息图（可带文字）、细节特写、尺寸参照图；官方建议至少 6 张图 + 1 个视频；正方形 1:1 显示最稳定。

### 3. 京东图片规范（社区/从业者通行值，官方帮助中心精确页面本次未检索到）

来源：[千图素材平台规格整理](https://www.1000tu.cn/article/2474.html)、[京东商品拍摄指南](https://www.mmker.cn/juhe/13246.html)。

- **主图**：800×800 起步，**推荐 1200×1200**，1:1，JPEG，单张 ≤1MB（多个从业者总结值，做图前请在京东商家后台复核）
- **主图要求**：白底为主、居中完整展示、多张主图须不同角度；不得出现与所售商品无关的物体；不得非等比拉伸变形
- **详情图**：JPG/PNG/GIF，宽度一般按 750 制作，单张 ≤3MB；只支持静态图
- 参考：京东全球购规则页提到 Banner 980×250、商品描述图宽 700（来源：[jd.hk 规则页](https://www.jd.hk/channelGuidePage/UdV4W4W6UdV4U1T1.html)），说明京东系对"宽 700–750"有统一偏好

### 4. 关键差异速览

| 项 | Amazon | 京东 |
|---|---|---|
| 主图底色 | 纯白强制（RGB 255） | 白底为主，相对宽松 |
| 主图尺寸 | 长边≥1000（推荐 2000），1:1 | 800×800 起（推荐 1200），1:1 |
| 主图文字 | 绝对禁止 | 首图建议干净，营销图可用文字 |
| 格式 | JPG/TIFF/PNG/GIF，禁 WebP | JPG 为主 |
| 产品占比 | ≥85% | 主体居中、大小适中 |

---

## 第二部分：可复现环节与工具链

### 5. 可复现环节

| 环节 | 复现方式 | 成熟度 |
|---|---|---|
| 抠图/换白底 | rembg（MIT 开源，CLI+Python API，支持批量）/ BiRefNet（更高精度） | ★★★★★ 高 |
| 批量改尺寸/裁剪/转格式/压缩/去 EXIF | Python Pillow 脚本、ImageMagick；有从业者实测 187 张主图从 3 小时压到 40 秒 | ★★★★★ 高 |
| 文生场景图 | 本项目限定 Gemini（Nano Banana）+ OpenAI（GPT-Image），见第三部分 | ★★★★ 中高（需人工选图） |
| 文案生成/优化/多语言翻译 | LLM（豆包/Kimi/DeepSeek）：卖点提炼、痛点话术、竞品对标、Amazon 英文 listing 翻译 | ★★★★ 高（需人工核对事实） |
| 模板化排版 | Canva 模板库、Figma 组件化、PS 动作（Action）录制重复操作 | ★★★ 中（依赖模板质量） |
| 合规自查 | 脚本校验：尺寸/比例/文件大小/格式/主图纯白度（RGB 是否 255）/产品占比估算 | ★★★★ 高（规则可代码化） |
| 关键词植入（Amazon 后台搜索词） | LLM 按竞品评论/关键词扩展，需人工定策略 | ★★★ 中 |

从业者金句（来自[千图素材](https://www.1000tu.cn/article/2461.html)）："图片加工混了三种活——创作型（修图合成调色）、流水线型（改尺寸裁切转格式）、发布型（适配平台规格）。同一套操作要重复第二遍，就写脚本，别开 PS 慢慢磨。"

JPEG 导出经验值（从业者实测）：质量 82 + 色度抽样 4:4:4（带文字的图）是甜点；质量拉满 100 上传后反而可能被平台二次压缩出块状伪影；锐化只做一次、放在缩小之后。

### 6. 工具链

**修图排版（人工主力）：** Photoshop（行业标准，Action 可批量录制）/ Figma（组件化排版）/ Canva（模板海量；国内同类稿定设计）。

**AI 生图（本项目限定）：** Gemini（Nano Banana，多图参考与一致性最强）/ OpenAI GPT-Image（edits+mask 局部重绘、文字渲染最准）。详见第三部分。

**开源可复现方案：** `rembg`（抠图，MIT，`pip install "rembg[cli]"`，批量 `rembg p in/ out/`）/ BiRefNet（高精度 matting）/ Pillow / ImageMagick / cwebp。

---

## 第三部分：产品一致性技术路线（硬约束专项）

**约束前提**：产品图全部从官网获取；AI 做场景图/海报时产品细节外形不能变形、多产品同框比例必须正确；文生图只用 Gemini 和 OpenAI。

### 7. 四条路线对比

| 路线 | 做法 | 保真度 | 说明 |
|---|---|---|---|
| A. 抠图+AI只画背景再合成 | 抠出产品 → AI 生成背景 → 把原图产品硬贴回去 | ★★★★★（产品像素 100% 不动） | 合成需调光影，否则像"贴纸" |
| B. 实拍基准的局部重绘 | inpaint 蒙版只重绘背景区，产品区不进扩散 | ★★★★（边缘过渡带可能被轻微改写） | GPT-Image 的 edits+mask、Nano Banana 2.1 的 mask/ink-guided editing 都是官方能力 |
| C. ControlNet/IP-Adapter 锁形 | Depth/Canny 锁轮廓，AI 只画周围 | ★★★★（仍是"重绘"产品，非像素级） | SD 生态，与本项目平台约束冲突，仅作对比 |
| D. 主体一致性 | 商用"主体参考"（Nano Banana 多图参考、GPT-Image 最多 10 参考图） | ★★★☆（好但非像素级，适合多场景系列） | 参考图即开即用，无需训练 |

**关键实战教训**（来源：https://www.pedroalonso.net/blog/automating-ecommerce-photography/）：一位开发者实测了路线 A 的完整管线，技术上保真完美，但成品像"贴纸"——产品带着原图的光影，背景是另一套光影，阴影接不上、边缘过锐。他最后转向整图编辑 + 一次出 2-3 版人工挑选。结论：**不要为保真牺牲真实感，验收环节必须有人**。

苏宁的一篇论文指出 diffusion 做电商图的核心痛点叫 **overcompletion（过度补全）**——模型会"好心"把产品也重画一遍，必须用精细 mask 约束（https://arxiv.org/pdf/2409.09681）。

### 8. Gemini vs OpenAI：谁更能保证"产品不变形"

**Gemini（Nano Banana）**
- 立身之本就是角色/产品一致性：同一产品跨场景、多角度保持长相；支持多图融合（产品图+场景参考+风格参考一次合成）。
- Nano Banana 2.1（2026-10 刚发布）：最多 14 张参考图、10 个物体忠实度、4 角色一致性，输出 1K/2K/4K，支持 mask/ink-guided 局部编辑（来源：https://www.techbang.com/posts/134019-google-nano-banana-2-1-image-model-update）。
- 价格约 $0.039/张；输出带 SynthID 隐形水印。
- 已知弱点（Google 自己承认）：输入输出之间角色仍可能不一致；分不清左右等空间关系；小字、长段落不行；长链多轮迭代后细节会轻微失真。

**OpenAI（GPT-Image）**
- **edits 端点 + mask inpainting**：蒙版保护产品区、只重绘背景——两家平台里**唯一"产品像素可以完全不动"的官方能力**，最贴合"不能变形"的硬约束。
- 支持最多 10 张参考图；指令遵循强。
- 第三方实测（111 张产品图抽查）：GPT Image 2 被质检 flag 率 11%，Nano Banana Pro 24%（来源：https://www.productai.photo/blog/what-flagged-ai-product-photos-taught-us，样本小，仅作方向参考）。
- 强项还有文字渲染，海报标题类更稳；弱点：复杂 prompt 延迟可达 2 分钟；价格 $0.02/$0.07/$0.19（low/med/high）。
- 注意：DALL-E 2/3 已于 2026-05-12 退役，GPT Image 是官方继任者。

**分工建议**：

| 场景 | 用谁 |
|---|---|
| 单产品换背景、季节海报底版 | **GPT-Image mask inpainting**（产品区蒙版保护） |
| 多产品同框 | 先按真实尺寸比例人工排好版 → 再做背景融合；或 Nano Banana 多图参考一次合成 + 人工验收 |
| 同一产品多场景系列图 | Nano Banana 多图参考/多轮编辑 |
| 文案多的海报 | GPT-Image 文字更强，但关键文案一律后期叠字，不让模型画字 |

### 9. 多产品同框的比例控制

核心原则：**比例不要交给 AI 碰运气**。先按真实尺寸比例在画布上排好各产品的位置和大小（人工或脚本），AI 只负责背景融合与光影统一。社区验证过的方法（来源：https://jackchen.cn/archives/18633.html）：

1. 写"保持什么 / 改变什么"双清单（如"保持罐身比例、logo、口味文字不变；只改变环境"），每件产品单独给参考图；
2. prompt 里明确尺寸关系；
3. 出图后对照原图逐项验收：①是否原款 ②标志文字逐字正确 ③包装信息完整 ④阴影/反光自然 ⑤裁切安全区。

### 10. 行业避坑与合规红线

- 主流工作流（运营动脉 2026 课程，https://www.yydm.cn/doc-view-57967.html）：参考图 → 反推提示词 → AI 生成背景 → 融图 → **PS 后期**（修复产品、加强光影、排版）。AI 负责探索，人负责定稿。
- **合规红线**（来源：https://k.sina.com.cn/article_7879995964_1d5af323c068017eqw.html）：AI 只做背景替换/场景扩展、产品外观商标色彩 100% 一致 → 不算虚假宣传；一旦扭曲产品（过度美化、比例失真）→ 投诉下架、退货风险。**Amazon 主图要求纯白底——主图永远用实拍/抠图，不要让 AI 重绘**。
- 抠图避坑：检查封闭负空间（杯柄、镂空内侧残留背景是经典翻车点）；抠完放纯白和纯黑底各看一遍查灰边；阴影保留与否按用途选（场景图保留更自然）。

### 11. 推荐路线（只基于 Gemini + OpenAI）

**路线一（主力）：GPT-Image 蒙版保护 + 背景重绘**
官网白底图 → 抠图 → 产品区做蒙版保护 → GPT-Image edits 只生成背景 → 人工验收。理由：唯一产品像素可完全不动的官方能力，最符合硬约束；多产品同框先排版再整体 inpaint 背景。

**路线二（辅助）：Nano Banana 多图参考合成**
多张产品图 + 场景参考一次融合，适合季节限定海报、官网首页 2000×440 这类创意构图。理由：多图融合与一致性是其最强项。但必须人工逐项验收，不合格就换 seed 重出或切回路线一。

**两条路线共用的三条铁律**：① Amazon/京东主图永远用实拍/抠图；② 文字一律后期叠字；③ 每次出图对照原图验收轮廓、比例、颜色、logo、文字、阴影。

---

## 第四部分：GitHub 开源项目（7 个）

| 仓库 | ★ | LICENSE | 做什么 | 可复用/借鉴点 |
|---|---|---|---|---|
| https://github.com/danielgatis/rembg | 25.1k | MIT | 抠图基石工具 | 直接 pip 安装做批量去背；注意默认 u2net 弱，指定 birefnet/isnet 模型 |
| https://github.com/ZhengPeng7/BiRefNet | 4.3k | MIT | 当前精度最高的开源高分辨率 matting | 抠图质量要求高（发丝、半透明、复杂边缘）时用它替代 rembg 默认模型 |
| https://github.com/Gayaya999/ecommerce-detail-page-generator | 40 | MIT | 产品图→多平台详情页；平台路由（京东 750px 长图、Amazon A+）、事实分级防虚构卖点、**AI 只生成无字底图 + Pillow 确定性排版**、自动验证 | **最值得整套借鉴**：双阶段思想（AI 不画字）、平台配置表、Pillow 排版与验证脚本 |
| https://github.com/ninemouth/sellerpilot-product-image-industrial | 34 | MIT | 工业级套图 skill：套图规划、平台规范、QA 门禁、tldraw 批注修订、参考图证据链 | QA 清单与生产流程可直接套用 |
| https://github.com/arjun-go-go/mediaforge | 7 | MIT | 全栈平台：FastAPI+Celery+LangGraph，爆款参考检索（Milvus RAG）、平台规则、质量检查、批量任务；内置淘宝/京东/拼多多/Amazon/Shopee 等平台规则 | 架构参考（较重，按需裁剪）；平台规则表可借鉴 |
| https://github.com/xiaoqahax-ui/comfyui-ecommerce-workflows | 7 | 无 | ComfyUI 电商工作流，对标 Flair/Pixelcut | 流程思路可参考；走 SD 生态，与"只用 Gemini/OpenAI"约束冲突，不直接复用模型链 |
| https://github.com/ronchen0927/AI-E-Commerce-Media-Studio | 7 | 无 | RMBG-1.4 去背 + 指令式编辑 + 图生视频 | RMBG 选型参考；无 LICENSE，代码不宜直接抄 |

排除项：`noisyshade/PhotoRoom-Desktop`（topics 含 photoroom-activated，疑似破解版，已弃用）。

---

## 第五部分：交付物形态

综合[之宙网络](https://www.zcosm.com/jishuxuetang/97.html)的交付清单和[画星人教育的报价单规范](https://www.hxredu.com/news/152.html)，标准交付结构：

```
项目名/
├── 01_成品图/
│   ├── amazon/            # 主图+附图，2000×2000 JPG，sRGB
│   ├── jd/                # 主图 1200×1200 JPG ≤1MB
│   ├── 官网首页/           # 2000×440、移动端 1000×900
│   ├── 季节海报/           # 各节日版本
│   └── 详情页长图/         # 宽 750 切片 JPG
├── 02_源文件/              # PSD / Figma 源文件（分层，可编辑）
├── 03_素材/                # 白底抠图 PNG、场景图、原图
├── 04_文案/                # 文案终稿 .md/.docx（含多语言版本）
├── 05_提示词/              # 文生图 prompt 存档（可复用）
├── 字体说明.txt             # 所用字体及商用授权情况
├── 规格对照表.md            # 各平台尺寸/格式/大小要求
└── 验收清单.md              # 逐条可打勾：张数×内容、尺寸、格式
```

行业铁律（画星人教育）：
- 交付物必须拆到"张数 + 尺寸像素 + 格式"三项可核验，写"尺寸待定"后期返工量相当于重画 30–60%
- **分层源文件单独列一行**（客户可自行改图延展物料，价值独立于成品图）
- 文件命名统一：`项目名-日期-版本号`；确认版锁定后不覆盖
- 交付时同步：字体商用授权证明、第三方素材授权、切图规范

---

## 结论

**可独立复现（脚本/AI 一条龙，成熟度高）：** 抠图换白底（rembg 批量）→ Amazon 主图纯白底合规可程序化校验；全平台批量出图（同一套母版 → 脚本输出各尺寸）；合规自检脚本；文案初稿（LLM）；场景图/海报底图候选（Gemini/OpenAI + 提示词库）。

**需要人工设计介入：** 整体视觉创意与排版；卖点策略（哪些痛点值得讲、讲的顺序、竞品差异化）；最终质检（产品是否被 AI 画变形、错别字、颜色失真、各屏风格一致）；合规兜底（参数真实性核对，AI 会一本正经地编数据）；京东官方规范在商家后台人工复核。

**产品不变形的唯一可靠办法是"AI 不碰产品像素"**：抠图隔离 + 蒙版保护 + AI 只画背景。在"只用 Gemini + OpenAI"的约束下，**GPT-Image 的 mask inpainting 是主力路线，Nano Banana 多图参考做创意海报辅助**；GitHub 上 `ecommerce-detail-page-generator` 的"AI 生无字底图 + Pillow 确定性排版"双阶段思想最值得整套借鉴。

**建议路线**："AI/脚本做 70% 的体力活，人工做 30% 的判断活"。

---

## 附录：wzj177/ecommerce-image-suite 可复用性分析（第三轮侦察）

仓库：https://github.com/wzj177/ecommerce-image-suite（gitee 镜像：https://gitee.com/wanzij177/ecommerce-image-suite）。**LICENSE：Apache 2.0，可商用**（可修改、可闭源分发，需保留版权声明）。

### A1. 关键文件

| 路径 | 作用 |
|---|---|
| `SKILL.md`（69KB） | Agent 编排手册：8 步流水线（前置检查→收集输入→AI 分析→平台选择→生图参数→模特判断→多供应商生成→文案→HTML→视频） |
| `scripts/analyze.py`（310 行） | 商品图视觉分析，输出结构化卖点 JSON；三档降级：通义 qwen-vl-max → 豆包 doubao-vision-pro-32k → OpenAI gpt-4o（无 Gemini，但走 OpenAI 兼容接口，小改可接） |
| `scripts/generate.py`（1874 行） | 套图生成主脚本：prompt 组装 + 5 家供应商 API 调用 + 9 种图类型 |
| `scripts/check_providers.py` | 检测 5 家供应商 API Key 配置情况 |
| `references/platforms.md` | 各平台规范对照表（淘宝/京东/拼多多/抖音/Amazon/Shopify/eBay）+ 中英文案规范 |
| `references/image-types.md`（60KB） | 8+1 种图类型的视觉规格 + 分平台 prompt 模板（淘宝杂志风/京东技术风/Amazon 高端目录风） |
| `references/providers.md` | 5 家供应商 API 文档 + Canvas 文案叠加坐标规范（**文档有、代码没实现**） |
| `references/analysis-prompts.md` / `copy-prompts.md` / `model-prompts.md` | 分析 prompt、文案/HTML 生成模板、模特 prompt |
| `assets/models.json` + 45 张模特图 | 内置 AI 模特库（服饰类用） |
| `example/` | 男装/女装/童装/电器实测样例 + product.json |

### A2. 技术实现要点

- **视觉分析**：调 OpenAI 兼容 chat 接口做视觉理解；输出 JSON 含 product_name、英文产品描述（供生图 prompt）、3-5 条卖点（中英标题/说明/icon/visual_keywords）、目标场景、印花锁定（"exact same print pattern, color and position must not change"）。
- **Prompt 拼装**（generate.py build_prompt）：QUALITY（商拍质感）+ PRODUCT_REF_LOCK（"CRITICAL HIGHEST PRIORITY... You MUST use the reference image as the EXACT basis... You may ONLY change: background scene, camera angle, lighting"）+ TEXT_RENDER（**要求模型直接渲染文字**，中英双语分支）。
- **图像 API**：5 个 generate_* 函数，**OpenAI 和 Gemini 都在支持列表**（符合我们的平台约束）；参考图机制：--product-images 多张，slot 0 正面用于大多数类型；OpenAI 走 /v1/images/edits，Gemini 走原生 inline_data。
- **关键缺失：全仓库没有任何 mask/inpainting 实现**。edits 调用只传 model/prompt/image，不传 mask 参数；所谓"保真"完全依赖 prompt 里的 PRODUCT_REF_LOCK 文字约束——**与我们"蒙版保护、AI 不碰产品像素"的硬约束正面冲突**。
- **服饰偏向明显**：PRODUCT_REF_LOCK 锁的是 silhouette/neckline/sleeves/hem（领口/袖子/下摆），模特库、版型、印花锁全是服装逻辑；做 3C/配件需去服饰化。
- 小坑：`image[]` 字段名是按某代理的 curl 示例写的，直连官方 OpenAI API 字段应为 `image`；输出尺寸写死 1024×1024，无按平台参数化；平台规范只是文档，无代码校验。

### A3. 与 Gayaya999/ecommerce-detail-page-generator 对比（两个不同项目、不同作者）

| 维度 | wzj177/ecommerce-image-suite | Gayaya999/ecommerce-detail-page-generator |
|---|---|---|
| 定位 | Agent 执行的套图生成 skill（9 种独立成图） | 详情页生产 skill（页面模块→长图） |
| 生图哲学 | 整图一次生成，文案由模型直接渲染 | AI 只生无字底图 + Pillow 确定性排版 |
| 保真手段 | prompt 文字锁 + 参考图 edits，无 mask | 事实分级（禁编造卖点）+ 商品锁定约束 + 预留文字负空间 |
| 平台适配 | 文档式规范表，无代码校验 | platform-profiles.json + validate_output.py 自动验证 |
| 脚本 | 自己调 5 家生图 API | 不调生图 API，由 Agent 编排 |
| 品类偏向 | 强服饰偏向 | 相对中性 |

wzj177 开箱即用度高；Gayaya999 工程化更强，且"AI 不画字"路线正好对上我们"文字后期叠字"的铁律。

### A4. 可复用性评估（约束：只用 Gemini/OpenAI；产品不变形；目标 Amazon+京东+官网）

**✅ 直接复用**：references/platforms.md（规范对照表，复核后用）、references/image-types.md（9 种图 prompt 模板，改写产品描述即用）、copy-prompts.md / analysis-prompts.md、analyze.py 设计（供应商链删减到 openai/gemini）、check_providers.py 思路、SKILL.md 8 步流水线骨架、example/ 的 product.json schema。

**🔧 小改可用**（generate.py 框架）：必改项——① 加 mask inpainting（edits 调用补 mask 参数，产品区保护只重绘背景）；② 默认模型 dall-e-3 → gpt-image-1.5，Gemini 模型更新到 Nano Banana 系列；③ PRODUCT_REF_LOCK 去服饰化（改轮廓/接口/按键/材质/Logo 表述）；④ 输出尺寸参数化（Amazon 2000×2000 / 京东 1200×1200 / 官网 2000×440）；⑤ image[] → image（如直连官方 API）；⑥ 删 tongyi/doubao/stability。

**❌ 不适用**：文案由模型直接渲染（与"文字后期叠字"铁律冲突，走 Gayaya999 的无字底图+Pillow 叠字路线）；模特锁定链；generate_video.py；服饰风模板。

**一句话建议**：流程骨架和分析链路值得借鉴，generate.py 改完 mask + 去服饰化 + 尺寸参数化后可作生成底座；但保真核心（mask inpainting）和文字渲染必须换路线——前者仓库根本没有，后者走了相反方向。

---

## 附录 B：第四轮四份专项报告摘要

### B1. prompt 保真写法深挖（侦察兵）

wzj177/ecommerce-image-suite 的保真 prompt 本质是"**六步锁**"：优先级声明（CRITICAL HIGHEST PRIORITY）→ 锚定参考图（MUST use reference as EXACT basis）→ 锁定清单（Keep EXACT same: 逐项枚举）→ 否定清单（DO NOT change）→ 白名单（You may ONLY change: 背景/角度/灯光）→ 身份断言（must look IDENTICAL）。另有"**描述自带尾巴**"（product_description_for_prompt 末尾强制加保护语句）和"**四类负面约束**"（AI 外观/过度后处理/基础质量/电商禁止，3C 版删掉人物向词汇，保留 deformed 等关键项）。

品类转换（服饰→3C）锁定词映射：silhouette→housing outline/form factor；print pattern→logo placement/label artwork；neckline/sleeves/hem→port layout/button placement/LED indicator positions；fabric texture→surface finish；新增 connector type/port count/cable routing/regulatory label 逐字锁定。**3C 独有：机身印刷文字必须逐字锁定（letter by letter, fully legible），服装 prompt 里没有这一项。** TEXT_RENDER 只借鉴排版规格写法（字体/字号/颜色/位置精确到 px），不让模型画字。

### B2. 双平台官方文档核查（搬运工）

| 项 | Gemini（Nano Banana 2.1，2026-10-06 GA） | OpenAI（GPT-Image 1.5 / 2） |
|---|---|---|
| 参考图上限 | 14 张（4 人物 + 10 物体一致性） | /images/edits 一次 16 张 |
| 输出尺寸 | 1K/2K/4K，宽高比 1:1–8:1（15 种） | 1.5：1024²/1024×1536/1536×1024/auto；2：任意尺寸（2K 官方推荐上限，4K 实验性） |
| 蒙版 | 2.1 新增 mask-based editing | /images/edits 的 mask 参数（PNG <4MB，同尺寸，透明区=可编辑区）——**两家里唯一"产品像素完全不动"的官方能力** |
| 保真参数 | 无独立参数，靠参考图+详细 prompt+多轮 | input_fidelity: high/low（1/1.5）；2 代默认高保真 |
| 文字 | 2.1 改进但小字仍是弱项 | 官方列为核心能力，但仍有 placement 限制 |
| 定价 | 2.1 1K 约 $0.034/张 | 输出 $40/1M token，约 $0.011/$0.042/$0.167（low/med/high，1024²） |

官方推荐做法：OpenAI——"change only X + keep everything else the same，每轮重复 preserve 清单" + input_fidelity high + mask 兜底；Gemini——"写细 + 小步迭代 + thought signature 传回" + 2.1 mask 编辑。**用户"靠详细 prompt 保真"的决策有官方背书。** 注意：gpt-image-1 已 deprecated（2026-10-23 停服），新项目用 1.5 或 2；Nano Banana 2.0 计划 2026-10 下旬退役，用 2.1。

官方文档链接：OpenAI Prompt 指南 https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide ；images/edits API https://developers.openai.com/api/reference/go/resources/images/methods/edit/ ；Gemini 最佳实践 https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/gemini-image-generation-best-practices ；Gemini 图像编辑 https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-editing

### B3. 架构评审（军师）

总体判断：保真不二选一，要"**分级**"——默认蒙版求稳（Tier 1），创意场景放开 prompt（Tier 2）+ 强制验收门。prompt-lock 成立，但成立条件是"有门"，没有验收门就是开环赌博。

风险点（按严重）：① 产品上的文字锁不住（logo/丝印/小字会被重画，diffusion 固有弱点）→ 带关键文字的产品必须蒙版；② 概率性（同 prompt 不同 seed 结果不同）；③ overcompletion（模型"好心"重画产品，接口/按键/指示灯最易漂移）；④ 多产品同框比例 prompt 描述不住，必须先脚本排版；⑤ prompt-lock 靠抽卡，单场景成本高于蒙版一次成型。

Pipeline：S0 ingest（调 /products/<handle>.json，Shopify 公开接口已确认可用）→ S1 analyze（事实分级）→ S2 copy（人工审）→ S3 generate（slim 版 ~300 行，不 fork 1874 行）→ S4 layout（Pillow）→ S5 validate（manifest.json）→ S6 人工验收门。

不确定项：规格表是否在 .json 的 body_html 里（P0，实测一个产品即知）；Nano Banana 2.1 mask 参数具体字段格式（P1，实测为准）；GPT-Image mask 形状支持（P1，实测）；京东规范精确值（P2，商家后台复核）；SynthID 水印（P2，备注即可）；字体商用授权（P2，单独确认）。

### B4. 截图工具分析（看图员）

技术链条：① 视觉分析（VLM 识别主体/品类/特征）→ ② 策略诊断（三型打分定配比 32/58/10）→ ③ 用途规划（12 图位按配比分配，切换类型当场重排）→ ④ 模板匹配（25 模板×88 变体，AI 推荐+2 备选）→ ⑤ 视觉合同（12 张共享的风格锁定 10 条，逐条可改）→ ⑥ Prompt 批量组装（全局合同+单图增量）→ ⑦ 生图 API（5 主图+7 详情页）。

核心机制：**诊断与执行解耦**（诊断不变，只重排用途）；**全局合同 + 单图增量**（12 次生图共享同一份 system prompt，一致性从碰运气变成架构保证）。视觉合同锁四类：视觉层（色号/冷暖/字体/光影/布局）、信息层（图注图标统一）、产品层（产品规范=保真 prompt 落点）、跨图层（三张素材统一）。

可借鉴：三型诊断→用途规划（套 Amazon 7-8 图位分配）；视觉合同机制直接复用为 prompt 架构；模板库精简为 8-10 个；产品规范条目写法（具体可核验）；季节主题模板分支。不适用：模型直接渲染文字（与后期叠字铁律冲突）；服饰/社媒向模板砍掉；额度扣费模式无关；"AI 推荐"黑盒改为显式映射表。

---

## 附录 C：多平台项目资源侦察（HuggingFace / 小红书 / B站 / 知乎 / Linux Do）

> GitHub 已调研过，本轮只收五个新平台的增量资源。宁缺毋滥，营销水文已剔除。

### C1. HuggingFace（可直接用的工具/模型）

| 名称 | 链接 | 可复用点 |
|---|---|---|
| briaai/RMBG-2.0 | https://huggingface.co/briaai/RMBG-2.0 | 背景移除基石模型，抠图管线直接用（Tier 1 蒙版路线前置） |
| briaai/RMBG-1.4 | https://huggingface.co/briaai/RMBG-1.4 | 上一代稳定版，批量抠图对速度敏感时用 |
| ZhengPeng7/BiRefNet | https://huggingface.co/ZhengPeng7/BiRefNet | 最高精度开源 matting，发丝/半透明/复杂边缘时用 |

结论：HF 最大价值是抠图/matting 模型；生图侧 HF 以 SD/FLUX 为主，我们不走 HF 生图，不冲突。

### C2. 小红书语境实战内容（搜索引擎不收录站内笔记，用等质量第三方替代）

- **少数派《Nano Banana Pro 辅助跨境电商快速铺图》** https://sspai.com/post/105974 —— **最对标我们项目的一篇**：A+ 页面提示词库 + 批量生成教程，含修图指令（保留主体换背景、透视校正、去手去杂物、接触阴影）；提示词库组织方式与"参考图→反推提示词→批量生成"流水线可直接改写成我们的 prompt 模板。
- **青虎AI《商品图批量改风格实操》** https://news.iqinghu.com/19877.html —— "分批"方法论（改动幅度接近的放一批）+ 提示词三维度（材质/光影/色调）固定句式，用于批量出图规范。
- **由前AI《产品场景图生成与换背景指南》** https://www.youqianai.com/ai-product-scene.html —— 明确承认"换背景后不能保证产品完全不变，需放大检查包装小字"；验收要点并入 S6 checklist。

### C3. B站视频教程

- **《ChatGPT做电商详情页，不到5分钟一整套图》** https://www.bilibili.com/video/BV12Rpt6UEob —— 与我们技术栈完全同构（GPT Image 一次出整套），看它怎么组织"一次出整套"的 prompt 链条。
- **《把 GPT Image 提示词用到烂！提示词工具》** https://www.bilibili.com/video/BV112pg6cEeP —— prompt 结构化/工具化思路，借鉴做 prompt 模板库。
- 《ComfyUI 电商应用教程》（36集）https://www.bilibili.com/video/BV1z1QvBFEdy 、《2025 最强 ComfyUI 电商工作流》https://www.bilibili.com/video/BV1E8hPzMEYL —— 只借工作流编排思路（分析→生成→精修→排版），模型链走 SD 生态与我们约束冲突。

### C4. 知乎语境技术内容

- **guunn《AI 电商主图从实拍到上架：六步流程 + 发布前质检清单》** https://www.guunn.com/ai-dianshang-zhutu-liucheng-zhijian.html —— **本轮质量最高**：六步流程、发布前 9 项质检清单（直接并入 S6）、"先定母图再派生"（= 我们 S3 设计的独立验证）、"图里只留 4-6 字短词，长文案后期排版"（强化叠字铁律）。
- **搜狐《第 2 张主图优化落地》** https://www.sohu.com/a/1077874973_121494008 —— 五图位框架：全貌（结论）→证据→场景→规格→保障；Amazon 附图信息架构直接用。
- **千图网《手机拍的产品图背景不干净怎么修》** https://www.1000tu.cn/article/2362.html —— 白底精修全参数：2000×2000 / JPEG q80 / sRGB / 色阶 245 压白底；Tier 0 实拍直出规范直接用。

### C5. Linux Do

- **《NANO BANANA 生图问题请教》** https://linux.do/t/topic/1828328 —— 出图分辨率/格式的坑（Pro 订阅 2K PNG 8-10MB vs API 4K JPG 3MB，码率差影响文件大小合规）；API 渠道讨论后续接 Gemini API 时可参考。站内搜索需登录，专项帖较少，照实收录。

### C6. 总体结论

**可直接拿来用**：RMBG-2.0/1.4 + BiRefNet（抠图管线）；guunn 9 项质检清单（并入 S6）；搜狐五图位框架（Amazon 附图信息架构）；千图白底精修参数（Tier 0 规范）。

**方法论**：sspai Nano Banana 铺图教程（提示词库组织+批量流水线，与项目同构度最高）；青虎AI 分批方法论；B站"一次出整套"prompt 链条；GPT Image 提示词工具化。

**独立验证已有决策**：guunn"先定母图再派生"/"长文案后期排版"/"人工质检不可省"；各平台一致——保真靠"参考图 + 详细 prompt + 人工验收"，没有一家声称纯 prompt 能 100% 不变形，支持 Tier 0/1/2 分级路线。

**覆盖缺口声明**：小红书站内笔记、知乎站内回答、Linux Do 站内搜索因反爬/登录墙无法直接抓取，已用搜索引擎可达的等质量第三方内容替代。
