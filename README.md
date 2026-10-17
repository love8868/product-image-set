# 产品图生产管线（MVP）

电商产品详情套图生产管线：官网产品页 → Amazon/京东上架套图、季节海报、官网首页图、手机端图。

技术路线见 `执行清单.md`；行业侦察见 `recon-report.md`。

## EXE 版（Windows，推荐）

1. 从 GitHub Releases 下载 `套图工坊.exe`（Actions 自动编译，见 `.github/workflows/build-exe.yml`）。
2. 双击运行 → 浏览器自动打开 `http://127.0.0.1:5057/`。
3. 填表单：产品 handle 或官网 URL → 勾模块 → 选季节/主题/生图通道 → 点「开始生成」。
4. 结果页看进度，完成后浏览成品图、文案、展示页、验收清单。

**API Key / 兼容地址填在哪**：任务配置页底部的「API Key」卡。OpenAI Key / Gemini Key / OpenAI 兼容地址（中转）三选一或组合填；
不填只能试运行（占位图）。Key 只存本机 `~/.product-image-set/config.json`（600 权限），不会上传。

**源码运行**（Linux/Mac）：`pip install -r requirements.txt && python3 app/server.py`，
浏览器打开 `http://127.0.0.1:5057/`。EXE 打包：`pyinstaller build.spec`。

## 依赖

- Python 3 + `pip install -r requirements.txt`（pillow / pyyaml / requests / flask）
- `rembg` 可选（dry-run 抠图用；不装则回退原图直贴）：`pip install rembg`

## 六阶段用法（以 MANHATTAN 181488 为例）

```bash
cd ~/workspace/product-image-set
H=manhattan-en-10-port-usb-c-desktop-charging-cabinet-30w-per-port-181488

# S0 素材入库
python3 pipeline/ingest.py --handle $H --site https://manhattanproducts.eu
# S1 分析（规则式提取；--vision 预留 gpt-4o，需 Key）
python3 pipeline/analyze.py --workdir products/$H
# S2 文案
python3 pipeline/copy.py --workdir products/$H
# S3 底图生成（dry-run：无 Key 跑完全流程，写 prompt + Pillow 占位底图）
python3 pipeline/generate.py --workdir products/$H --dry-run --season christmas
# S4 排版叠字
python3 pipeline/layout.py --workdir products/$H --season christmas
# S5 校验 → manifest.json + CHECKLIST.md（S6 人工验收门）
python3 pipeline/validate.py --workdir products/$H
```

产物在 `products/<handle>/`：`product_raw.json` `raw/` `product.json` `copy.md`
`prompts/` `draft/` `final/` `manifest.json` `CHECKLIST.md`。

## 统一调度器 run.py（模块按需分配）

```bash
# 查模块表（9 模块：ingest/analyze/plan/copy/ops_copy/douyin/generate/layout/validate）
python3 pipeline/run.py --list

# 单选：只出抖音文案（依赖自动补齐）
python3 pipeline/run.py --handle $H --modules douyin

# 多选：只换复活节海报（generate+layout，自动补依赖）
python3 pipeline/run.py --handle $H --modules generate,layout --season easter --dry-run

# 全选：从头到尾跑完
python3 pipeline/run.py --handle $H --modules all --dry-run --season christmas

# 重跑：--force 强制重跑已存在产物的模块
python3 pipeline/run.py --handle $H --modules layout --force --season christmas
```

`--season`/`--theme`/`--strategy`/`--dry-run`/`--provider` 按模块需要自动透传；
依赖缺失自动补跑，已存在产物默认跳过；每模块状态写入 `manifest.json` 的 `modules` 章节。
策划：`pipeline/plan.py` → `plan.md`/`plan.json`；运营文案包：`pipeline/ops_copy.py`；
抖音文案模块：`pipeline/douyin.py` → `douyin_copy.md`；优化复盘框架：`pipeline/optimize.md`。

## Prompt 模板库（pipeline/prompts/）

`prompts.py` 是纯组装引擎，模板全部 YAML 化（变量 `$var`，string.Template 语法）：

```
pipeline/prompts/
  _base.yaml    全局合同（style_lock + no_drift 防漂移）/ quality / negative /
                no_text / desc_guard / 五段组装模板
  _locks.yaml   3C 保真锁定词（整表引用）
  slots/        图位模板：scene_office / scene_classroom / detail_ports /
                banner_wide / season_poster（每个带 version + changelog +
                layout_target，显式指向 layout.py TEMPLATES 的 key）
  README.md     模板编写规范（变量表/冲突规则/入库标准）
```

- 五段组装（顺序写死）：global_lock → product_lock → `[Lane]` → scene+desc → lock → no_text → quality → negative；每次组装自动断言结构。
- `generate.py` 从 `slots/*.yaml` 扫描任务（`trigger: always/season/manual`）；`--season` 时加载 season_poster 并注入 `$season_scene`；`--provider` 可覆盖单任务 provider。
- 每次生成把 `template_id + version + 变量快照` 写入 `manifest.json` 的 `templates` 章节（合并写入）；`validate.py` 做模板版本 drift 警告（只警告）+ slot size vs layout 画布的宽高比交叉检查（>15% 偏差直接报错，以 layout 为准）。
- 改模板：bump `version` + 写 `changelog`；变量只取 product.json official 层，缺失直接报错（带模板文件名 + 变量名）。

## API Key 对接方法（后续）

管线已预留 provider 抽象接口（`pipeline/providers/`），生图时烧 Key 持有人的额度。

| 平台 | 环境变量 | 说明 |
|---|---|---|
| OpenAI（GPT-Image 1.5/2，默认） | `OPENAI_API_KEY` | `pipeline/providers/openai.py` 已实现 `/v1/images/edits` 调用结构（multipart，`image` 参考图 + `mask` 可选，`input_fidelity=high`）。注意官方字段为 `image`（可重复），直连官方 API 无需改；走第三方代理时按其文档调整。 |
| Gemini（Nano Banana 2.1） | `GEMINI_API_KEY` | `pipeline/providers/gemini.py` 已实现 `generateContent` 调用结构（参考图走 `inline_data`）。默认模型 `gemini-nano-banana-2.1`（已按官方文档核实，GA 2026-10-06）；`imageConfig` / mask 字段格式对接时按 ai.google.dev 实测为准。 |

对接后去掉 `--dry-run` 即可真实生图：

```bash
export OPENAI_API_KEY=sk-...        # 或 GEMINI_API_KEY=...
python3 pipeline/generate.py --workdir products/$H --provider openai --season christmas
```

无 Key 时直接调 provider 会抛 `RuntimeError`，明确提示设置环境变量或改用 `--dry-run`。

## Provider 模式

`generate.py --provider` 四选一（`run.py` 用 `--provider` + `--base-url` 透传）：

| provider | 说明 | Key |
|---|---|---|
| `openai` | OpenAI 兼容模式：无 ref/mask 走 `POST {base_url}/images/generations`（JSON），有 ref/mask 走 `POST {base_url}/images/edits`（multipart）。`base_url` 默认 `https://api.openai.com/v1`，可用 `--base-url` 或 `OPENAI_BASE_URL` 环境变量覆盖为官方地址或任何 OpenAI-compatible 中转/代理。返回兼容 `b64_json` 与 `url` 两种格式。 | 需要（`OPENAI_API_KEY`） |
| `gemini` | Gemini 自家 API 方言（`generateContent`），保持现状，不走兼容模式。 | 需要（`GEMINI_API_KEY`） |
| `muse` | 内置生图代跑：不调网，把每个 job 写成 job 卡 `jobs/<job_id>.json`（prompt / negative / size / ref 图 / mask / template 版本 / lane），打印"N 个 job 待回填"后正常退出。 | 不需要 |
| `--dry-run` | 占位模式：Pillow 渐变背景 + 产品直贴，文件名带 `_placeholder`。 | 不需要 |

muse 代跑完整流程：

```bash
# 1. 写 job 卡（不需要 key）
python3 pipeline/generate.py --workdir products/$H --provider muse --season christmas
# 2. 按 jobs/*.json 用内置生图逐张执行（人工）
# 3. 回填（校验 jpg/png、尺寸 ±2px，通过进 draft/）
python3 pipeline/generate.py --workdir products/$H --fill scene_office /path/to/gen.png
# 4. 继续排版
python3 pipeline/layout.py --workdir products/$H --season christmas
```

OpenAI 兼容地址示例：

```bash
export OPENAI_API_KEY=sk-...
python3 pipeline/generate.py --workdir products/$H --provider openai \
  --base-url https://your-proxy.example.com/v1 --season christmas
```

## 保真分级

- **Tier 0**：Amazon 主图/京东首图——实拍/抠图直出，零 AI（合规红线）
- **Tier 1（默认）**：蒙版 inpaint，只画背景（`mask` 参数已在 provider 接口预留）
- **Tier 2**：prompt-lock + 多参考图，做官网大图/创意海报，强制过 `CHECKLIST.md` 人工验收

## 季节/节日

`pipeline/seasons.py`：spring / summer / autumn / winter + christmas / easter /
halloween / black_friday / new_year / valentine。`generate.py --season <key>` 出季节底图，
`layout.py --season <key>` 出季节海报。
