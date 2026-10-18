# Prompt 模板库编写规范

`pipeline/prompts/` 是 prompt 模板库，`pipeline/prompts.py` 是组装引擎（只读模板、不写死文案）。

```
prompts/
  _base.yaml    全局：style_lock / no_drift / quality / negative / no_text /
                desc_guard / 五段组装模板（assembly_order + assembly_template）
  _locks.yaml   3C 锁定词：keep_base / do_not_base / lock_template（整表引用）
  slots/*.yaml  图位模板（见下）
  README.md     本文件
```

## slot 模板字段

| 字段 | 说明 |
|---|---|
| id / version / changelog | 模板标识；改模板必须 bump version 并写 changelog（一行：改了什么、为什么） |
| category | 适用品类，如 `[charging_cabinet]`；通用写 `[all]` |
| slot | 图位类型：scene / detail / banner / season |
| trigger | `always`（自动纳入 generate）/ `season`（仅 `--season` 时）/ `manual`（备查，不自动生成） |
| order | 生成顺序（数字越小越先） |
| lane / provider | M=蒙版 inpaint / P=prompt 抽卡；openai / gemini（`--provider` 可覆盖） |
| size | 生成尺寸 `[w, h]`；与 `layout_target` 画布**宽高比必须一致**（validate 交叉检查，偏差 >15% 直接报错） |
| layout_target | 显式指向 `layout.py` TEMPLATES 的 key（解决 generate/layout 两套命名悬空） |
| scene_en | 场景描述（英文），变量用 `$var`（string.Template 语法） |
| composition | 构图说明（中文，给人工看；layout 排版对齐用） |
| negative_add | 追加的 negative（可空） |

## 变量表（`$var`）

| 变量 | 来源 | 说明 |
|---|---|---|
| `$pt` / `$pt_zh` | product.json product_type | 品类词 |
| `$product_desc` | product.json product_desc_en | 产品描述（带 desc_guard 保护尾巴） |
| `$brand` | product.json vendor | 品牌 |
| `$ports` / `$power` | product.json facts（official 层） | 数字变量 |
| `$season_scene` | seasons.py（`--season` 注入） | 季节场景片段 |
| `$scene_extra` | plan.json 同 id slot 的 scene_extra | plan.py 拥有该字段，默认空串 |
| `$keep_list` / `$do_not_list` | _locks.yaml | 保真锁定词（引擎自动填） |
| `$palette` / `$lighting` / `$mood` | _base.yaml style_lock | 全局合同（引擎自动填） |

**变量铁律**：变量只从 product.json **official 层**取；模板文件里不许出现具体产品名、具体数字；缺失变量直接报错（带模板文件名 + 变量名），不生成垃圾 prompt。字面量大括号/美元符与 `$var` 无冲突（string.Template 语法）。

## 冲突规则（文档约定，代码不强制）

1. **下层不许覆盖上层**：slot 模板不许改 `keep_list` / `do_not_list`（保真锁只读）。
2. **季节只碰背景**：季节场景只允许 background / palette / mood 类描述，不许出现产品结构词。
3. **negative 可叠加不可删除**：slot 的 `negative_add` 只能追加，不许删 `_base.yaml` 的保命项。

## 五段组装（顺序写死在 `_base.yaml`）

`global_lock` → `product_lock`（第1次）→ `[Lane]` 标记 → `scene+desc` → `lock`（第2次）→ `no_text` → `quality` → `negative`。`assert_prompt_structure` 每次断言：lock 标记出现 2 次、no_text 在 quality 之前、negative 在末尾、`[Lane]` 标记保留。

## 复用规则

1. 新产品接入：现有 slot 模板直接复用（换 `$variables` 即可），不动模板文件。
2. 新图位：只新增 `slots/<name>.yaml`，复用 `_base.yaml` + `_locks.yaml`。
3. 新季节/节日：只改 `seasons.py`（`$season_scene` 注入位），不动模板。
4. 换品牌主题：只改 `_base.yaml` 的 `style_lock`（读 design/brand-visual-guide.md 的主题变量）。

## 入库标准

新模板入库需要：`version: 1` + `changelog` + 明确的 `layout_target` + 标注适用品类/图位。建议配一张验证过的成图样张（docs/ 或产品 workdir 备注）。
