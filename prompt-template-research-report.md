# "产品提示词复用与生成模板库"调研报告（侦察兵，2026-10-18）

## 一、业界做法：prompt 模板库的组织维度

### 1.1 截图工具的"25 模板 × 88 变体"机制（来自附录 B4 实测分析）

技术链条：视觉分析 → 三型诊断（视觉/痛点/情感配比）→ 用途规划（12 图位按配比分配）→ **模板匹配**（25 模板 × 88 变体，AI 推荐 1 个 + 备选 2 个）→ 视觉合同（STYLE LOCK，12 张共享、10 条逐条可改）→ **Prompt 批量组装（全局合同 + 单图增量）** → 生图 API。

模板库的组织维度是三维的：
- **类型维**：细节 / 场景人物 / 社媒真实感 / 信息转化 / 创意氛围图（右侧模板库的分类 tab）
- **策略维**：视觉 / 痛点 / 情感（筛选器，决定模板的文案角度和场景选择）
- **变体维**：每个模板 3–4 个变体（如"技术拆解图"展开为蓝风网格 / 极简白底 / Apple 产品拆解风格 / 杂志拆解风格）

核心机制两条（可直接抄）：
1. **诊断与执行解耦**——"AI 诊断与百分比保持不变"，切换策略类型时只重排 12 张图的用途，不重新诊断；
2. **全局合同 + 单图增量**——12 次生图共享同一份 system prompt（视觉合同），差异只来自各自模板变体，一致性从"碰运气"变成架构保证。

### 1.2 通用组织维度（综合多家）

| 维度 | 说明 | 实例来源 |
|---|---|---|
| 图位/用途 | 一张图只干一件事 | dev.to 1500-prompts："One image, one job"——Packshot / Detail / Lifestyle / Campaign 四分法 |
| 品类 | 不同品类换锁定词和场景 | wzj177（服饰向）vs 我们的 3C 改写 |
| 平台/渠道 | 同一图位不同平台美学 | wzj177 image-types.md：淘宝杂志风 / 京东技术风 / Amazon 高端目录风等 6 套 |
| 风格 | 光影/色调/构图基调 | openaisuite.com：marketplace main / lifestyle minimal / colorway series / macro / floating 五个 use case，各配独立 prompt 模板 + 独立 negative prompt |

### 1.3 固定层 + 变量层（最值得抄的思想）

来源：[dev.to "Building a Repeatable Prompt Template for Product Shots"](https://dev.to/aigcer/building-a-repeatable-prompt-template-for-product-shots-ggb)（1 天前发布，很新）：

> 把 prompt 拆成两层。**固定层**描述品牌视觉：背景、灯光、机位、情绪；**变量层**只描述产品：名称、材质、颜色、尺寸。换产品时只动变量层，整个目录共享同一套视觉 DNA。

骨架示例：
```
[PRODUCT]: matte ceramic mug, sage green, 350 ml     ← 变量层（换 SKU 只改这里）
[SCENE]: seamless warm-gray backdrop, soft shadow    ← 固定层
[LIGHT]: large softbox from upper left               ← 固定层
[CAMERA]: 50mm, eye level, centered                  ← 固定层
[STYLE]: clean e-commerce photography                ← 固定层
```

另外两条实战经验：
- **材质词比风格词管用**："frosted glass bottle with brushed aluminum cap" 比 "nice bottle" 更能控制反光和质感；
- **构图一次定死**：产品居中还是三分线、留白多少，写进模板。

### 1.4 配套机制：swipe files + 模板审计

来源：[backstroke.com 终极指南](https://www.backstroke.com/blog/ultimate-guide-ai-prompt-library-ai-product-images)：
- **Field Kit / swipe files**：预写好的公式卡，团队"复制-粘贴-微调"，新手起点一致、品牌安全；
- **Prompt library auditing**：模板库要定期审计——模板不是写完就完，要有质检。

## 二、开源实现盘点

| 项目 | 链接 | LICENSE | 结构 | 可复用点 |
|---|---|---|---|---|
| wzj177/ecommerce-image-suite `references/image-types.md` | https://github.com/wzj177/ecommerce-image-suite | Apache 2.0 | 9 图类型 × 6 平台风格；每模板四节：视觉规格→文案→6 平台 prompt→替换变量 | 已调研；平台风格维度的组织方式 |
| peterRooo/awesome-gpt-image-2-prompts（GPT Image Lab） | https://github.com/peterRooo/awesome-gpt-image-2-prompts | 未注明（注意） | JSON 数组，字段：`id/title/category/language/quality_grade/prompt/image_url/source_url/author_name/published_at`；2985 条目 | 元数据设计最值得抄：category 分类 + quality_grade 质量分级 + source_url 来源追溯 + image_url 效果样张 |
| bogdanbarbulescu/prompt | https://github.com/bogdanbarbulescu/prompt | MIT | `prompts.json` 按 category 分组，`{variable_name}` 占位符 + VariableFillModal 变量填充弹窗 | `{变量}` 语法 + 填充界面，未来 EXE/网页版可直接抄 |
| Pixonara 画廊（dev.to 1500-prompts 作者） | 见 dev.to/gedianming_jeremy_3cb00c8/i-curated-1500-ai-product-photography-prompts | — | 按 product photography / food & drink / poster design 组织，每条 prompt 配完整成图 | "每条模板配一张验证过的成图"——模板入库标准 |
| ComfyUI PromptListWithTemplates 节点 | https://www.runcomfy.com/comfyui-nodes/santodan-custom-nodes-comfyui/prompt-list-with-templates | — | prompt 列表存取为 JSON 模板，save/load/delete | JSON 模板存取模式 |
| Pimcore HF 集成 | https://docs.pimcore.com/platform/next/Copilot_Showcases/.../Hugging_Face_Image_to_Image_Prompt/ | — | Twig `prompt_template: "{{ subject.getId() }}..."` + `negative_prompt` 参数化 | `{{变量}}` 模板引擎语法的工业界实例 |

**诚实缺口**：HuggingFace 上没有专门的"电商产品图 prompt 模板数据集"；小红书/B 站的模板多为截图/口播分享、非结构化数据，不适合直接复用。

## 三、复用机制设计

### 3.1 变量设计

| 变量 | 来源 | 示例 |
|---|---|---|
| `{product_desc}` | analyze.py product.json（official 层） | "10-Port USB-C Desktop Charging Cabinet - 30W per Port" |
| `{pt_en}` / `{pt_zh}` | product.json product_type | "Charging Cabinet" / "充电柜" |
| `{ports}` / `{power}` | product.json facts（official） | "10" / "30W" |
| `{brand}` | product.json vendor | "Manhattan" |
| `{scene_extra}` | plan.json / 调用参数 | 由图位/季节决定 |
| `{keep_list}` / `{do_not_list}` | _locks/3c.yaml | 锁定词表 |

**变量铁律**：变量只从 product.json **official 层**取；模板文件里不许出现具体产品名、具体数字；缺失变量直接报错不生成。变量语法沿用现有 Python `str.format` 的 `{var}` 风格，不引入 Jinja2。

### 3.2 组合规则（叠加顺序 + 冲突规则）

组装顺序（五段）：
```
① base.style_lock_global      # 全局合同：品牌/配色/灯光/情绪（所有图共享）
② category.product_words      # 品类覆盖：3c.yaml 的锁定词 + 品类场景偏好
③ slot.scene                  # 图位模板：场景描述 + 构图（单图增量）
④ season.increment            # 季节增量：只改背景氛围/配色提示（可选）
⑤ lock + no_text + quality + negative   # 保真锁 + 无字指令 + 器材背书 + 负面
```

冲突规则（四条）：
1. **下层不许覆盖上层**：slot 模板和 season 增量**不许改** keep_list / do_not_list（保真锁只读）；
2. **season 只碰背景**：季节增量只允许 background / palette / mood 类词汇，不许出现产品结构词；
3. **品类覆盖用"增删"不用"重写"**：3c.yaml 定义 `keep_add` / `keep_remove`，在 base 锁词表上做差量；
4. **negative 可叠加不可删除**：slot 可追加 negative，不许删 base 的保命项。

### 3.3 版本管理

1. 每个模板文件带 `version` + `changelog` 字段；改模板必须 bump version 并写 changelog；
2. 每次生成时把 `template_id + version + 变量快照` 写入 manifest.json；
3. 新模板入库标准：必须配一张**验证过的成图**样张 + 标注适用品类/图位，否则不入库；
4. 定期审计：抽查模板产出，不稳定的模板降级或下架。

## 四、给 prompts.py 的升级建议

### 4.1 目录结构

```
pipeline/prompts/
  _base.yaml                       # 全局：style_lock 模板、quality、negative、no_text、组装顺序
  _locks/
    3c.yaml                        # 3C 锁定词：keep/do_not（keep_add/keep_remove 差量）
    apparel.yaml                   # 预留
  categories/
    charging_cabinet.yaml          # 品类覆盖
    cable.yaml
    patch_panel.yaml
  slots/
    scene_office.yaml              # 图位模板：scene_en、构图、尺寸、lane、provider
    scene_classroom.yaml
    detail_ports.yaml
    banner_wide.yaml
    season_poster.yaml
  README.md                        # 模板编写规范
```

`prompts.py` 保留为**组装引擎**，SCENES 硬编码迁移为 `slots/*.yaml` 后删除。

### 4.2 模板 schema（YAML）示例

```yaml
# slots/scene_office.yaml
id: scene_office
version: 1
category: [charging_cabinet]
slot: scene
platform: [amazon, jd]
lane: M
provider: openai
size: [1024, 1024]
scene_en: >
  Modern office desk scene, the {pt_en} placed on a light wooden desk
  next to a laptop and notebook, soft daylight from a window,
  shallow depth of field, product as the clear hero in the foreground
composition: "产品前景居中偏右，左侧留 40% 负空间（给信息图叠字用）"
negative_add: []
changelog:
  - "v1: 从 prompts.py SCENES['office_desk'] 迁移"
```

```yaml
# _locks/3c.yaml
id: lock_3c
version: 1
keep_base:
  - housing outline and form factor
  - all colors and surface finish
  - logo placement and label artwork, letter by letter, fully legible
  - port layout and connector types
  - button and LED indicator positions
  - port count and numbering
  - cable routing and connector shape
do_not_base:
  - the logo, label text, color scheme, housing shape
  - port positions, port count or numbering
  - surface texture or finish
```

### 4.3 充电柜模板实例（detail_ports / season_poster，略）

### 4.4 复用规则清单

1. 新产品接入：只新增 `categories/<品类>.yaml`，不动 slot 模板；
2. 新图位：只新增 `slots/<name>.yaml`，复用 `_base.yaml` + `_locks/3c.yaml`；
3. 新季节/节日：只改 `seasons.py`，不动模板；
4. 换品牌主题：只改 `_base.yaml` 的 style_lock；
5. 模板改动 → bump version + changelog；生成记录 template_id+version 进 manifest；
6. 变量缺失 → 报错不生成；模板里不许出现具体产品名/数字。

### 4.5 迁移路径（分三步）

1. **Step 1**：`prompts.py` 拆出组装引擎函数，SCENES 改为从 `slots/*.yaml` 加载（行为不变，只换数据源）；
2. **Step 2**：`_base.yaml` + `_locks/3c.yaml` 落地，`build_prompt` 改走五段组装顺序；
3. **Step 3**：`categories/` 品类覆盖 + manifest 记录 template 版本 + 模板 README 规范文档。
