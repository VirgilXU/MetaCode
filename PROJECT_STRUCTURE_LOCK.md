# MetaCode 项目结构化交接与开发约束文件

> 文件定位：这是新窗口 AI 的第一读取入口，也是 MetaCode 项目的结构化约束文件。
>
> 保护规则：未经用户明确授权，任何 AI 或自动化流程只能读取本文件，不得修改、覆盖、重排、删减本文件内容。

---

## 0. 文件元数据

```yaml
file_id: metacode.project.structure.lock
file_name: PROJECT_STRUCTURE_LOCK.md
project_name: MetaCode
project_root: D:\Virgil\Virgil\元代码项目Software DNA\源码
github_repository: https://github.com/VirgilXU/MetaCode
current_stage: Stage 10
latest_known_commit: 52d1471 Stage 10 observatory API and auto refresh
created_at: 2026-06-11
created_for: 新窗口 AI 快速接续开发
language: zh-CN
encoding: UTF-8
local_file_attribute_after_creation: read_only
```

---

## 1. 强制读取协议

新窗口 AI 接手本项目时，必须按以下顺序工作：

```text
1. 先读取 PROJECT_STRUCTURE_LOCK.md。
2. 再执行 git status --short --branch，确认工作区状态。
3. 再扫描 README.md、docs/项目进度记录.md、最新 Stage 验证报告。
4. 再扫描与当前任务直接相关的代码文件。
5. 只做最小必要改动，不改变既有目录结构。
6. 每完成一个阶段，新增验证报告，更新项目记录。
7. 如需修改本文件，必须先取得用户明确授权。
```

禁止事项：

```text
未经授权，不得修改 PROJECT_STRUCTURE_LOCK.md。
未经授权，不得重命名核心目录。
未经授权，不得移动 metacodes、workflows、core、dashboard、monitoring、docs、tests。
未经授权，不得删除历史日志、阶段报告、监控导出文件。
未经授权，不得大规模重构已有功能。
```

---

## 2. 本文件写入与版本规则

### 2.1 默认权限

```yaml
default_permission:
  read: allowed
  write: forbidden_without_user_authorization
  modify_existing_content: forbidden_without_user_authorization
  delete_content: forbidden
  weaken_rules: forbidden
```

### 2.2 允许写入的条件

只有当用户明确说出类似指令时，才允许修改本文件：

```text
允许修改结构化文件
授权写入 PROJECT_STRUCTURE_LOCK.md
更新项目结构锁定文件
把这次阶段结果写入结构化文件
```

### 2.3 每次写入必须包含版本说明

每次授权写入时，必须更新本文件的“版本日志”，至少包含：

```yaml
version:
date:
operator:
authorization_source:
change_scope:
reason:
files_or_modules_affected:
verification:
next_expected_stage:
```

### 2.4 推荐写入流程

```text
1. 确认用户授权。
2. 取消本文件只读属性。
3. 只追加或小范围更新必要字段。
4. 新增版本日志。
5. 保存后重新设置只读属性。
6. 告知用户本次写入内容和版本号。
```

Windows PowerShell 参考命令：

```powershell
attrib -R PROJECT_STRUCTURE_LOCK.md
# 修改文件
attrib +R PROJECT_STRUCTURE_LOCK.md
```

---

## 3. 项目一句话定义

MetaCode 是一个围绕“可复用能力单元 metacode + workflow 组合 + 失败诊断 + 自动修复/规划 + 能力图谱 + 监控观察台”的实验性软件生产系统。

它不是一次性让 AI 写代码，而是让项目逐步积累：

```text
能力资产
工作流路径
失败样本
修复经验
图谱结构
阶段报告
监控数据
可视化观察入口
```

---

## 4. 当前工程状态

```yaml
current_stage: 10
stage_range: Stage 2 - Stage 10
metacode_count: 15
stable_workflow_count: 10
workflow_file_count: 13
generated_workflow_count: 1
intentional_failure_workflow_count: 2
capability_graph_edges: 26
field_count: 16
unresolved_field_count: 0
latest_test_count: 45
latest_test_status: OK
dashboard_mode:
  static_dashboard: http://127.0.0.1:8765/dashboard/
  api_dashboard: http://127.0.0.1:8770/dashboard/
  api_status: http://127.0.0.1:8770/api/status
```

当前最重要的判断：

```text
MetaCode 已经从“能跑的原型”进入“有本地 API 的可观察工程原型”。
下一阶段应优先做失败钻取与诊断工作台，而不是重构底层目录。
```

---

## 5. 目录职责

```yaml
core:
  role: 核心运行时与分析逻辑
  contains:
    - Context 协议
    - Workflow 执行器
    - Registry 构建
    - Recommender 推荐
    - Workflow fixer
    - Path planner
    - Capability graph
    - Monitoring export
    - Local API
  rule: 新核心能力优先放入 core 下的独立模块，不要塞进已有模块。

metacodes:
  role: 可复用能力单元库
  structure: metacodes/<category>/<metacode_id>/
  required_files:
    - identity.yaml
    - runner.py
  rule: 新能力必须先定义身份、输入字段、输出字段，再实现 runner。

workflows:
  role: 工作流定义
  file_type: YAML
  categories:
    stable: 可正常执行的基线 workflow
    broken: 故意失败样例，用于诊断测试
    generated: 修复或规划生成的 workflow
  rule: 不要随意改动稳定 workflow 的语义，新增实验路径优先新建文件。

dashboard:
  role: Web 可视化观察台
  files:
    - index.html
    - styles.css
    - app.js
  rule: 前端必须保留 API 优先 + 静态 JSON 回退。

monitoring:
  role: 监控数据层
  contains:
    - exports/*.json
    - stages/stage_*.json
    - schema.sql
    - metacode_monitor.db 本地生成，不进 Git
  rule: 新监控字段必须同步 JSON 导出、SQLite schema、Dashboard、测试。

docs:
  role: 阶段报告、设计文档、项目记录
  rule: 每个新阶段必须新增 docs/Stage N 验证报告.md。

tests:
  role: 自动化验证
  naming: test_stageN_unittest.py
  rule: 新阶段必须有对应测试，风险越大测试越具体。

logs:
  role: 运行日志与失败日志
  files:
    - run_log.jsonl
    - failure_log.jsonl
  rule: 日志是阶段跟踪资产，不要清空历史日志。
```

---

## 6. 当前关键模块索引

```yaml
runtime:
  context: core/context.py
  workflow_executor: core/combiner.py
  schema: core/schema.py

registry_and_reuse:
  registry_builder: core/registry.py
  reuse_analysis: analyze_reuse.py
  registry_output: registry/metacodes.json

diagnosis_and_repair:
  recommender: core/recommender.py
  workflow_fixer: core/workflow_fixer.py
  path_planner: core/path_planner.py
  fix_cli: fix_workflow.py
  plan_cli: plan_workflow_fix.py

capability_graph:
  graph_builder: core/capability_graph.py
  graph_cli: analyze_capability_graph.py

monitoring:
  export_logic: core/monitoring_store.py
  export_cli: export_monitoring_data.py
  sqlite_schema: monitoring/schema.sql

api_and_dashboard:
  api_server: core/monitoring_api.py
  api_cli: serve_observatory.py
  dashboard_html: dashboard/index.html
  dashboard_css: dashboard/styles.css
  dashboard_js: dashboard/app.js
```

---

## 7. 现有 metacode 能力清单

```yaml
io:
  - io.read_markdown_file
  - io.write_markdown
  - io.read_json_file
  - io.save_csv

text:
  - text.clean_text_basic
  - text.simple_summary
  - text.extract_markdown_headings
  - text.extract_keywords_basic

analysis:
  - analysis.count_frequency
  - analysis.count_text_stats

data:
  - data.filter_rows_contains
  - data.pick_fields
  - data.sort_rows

transform:
  - transform.json_items_to_rows
  - transform.headings_to_rows
```

metacode 开发约束：

```text
1. metacode_id 必须稳定，不能随意改名。
2. identity.yaml 是能力契约，runner.py 是能力实现。
3. reads/writes 字段决定 workflow、推荐器、能力图谱能否正确工作。
4. 新增 metacode 后必须新增或更新测试。
5. 不要让 runner.py 直接依赖 Dashboard 或 API。
```

---

## 8. Workflow 开发约束

workflow YAML 代表可执行路径，不是随手脚本。

新增 workflow 时遵守：

```text
1. 稳定 workflow 放 workflows/ 根目录。
2. 故意失败样例用 broken_ 前缀。
3. 自动生成结果放 workflows/generated/。
4. 新 workflow 应尽量复用已有 metacode。
5. 不要为了一个 workflow 改坏已有 metacode 的字段契约。
6. 每条新 workflow 至少跑一次，并进入 run_log。
```

---

## 9. 监控与 API 扩展接口

### 9.1 新增监控字段

修改顺序：

```text
1. core/monitoring_store.py
2. monitoring/schema.sql
3. export_monitoring_data.py 如需展示命令输出
4. dashboard/app.js
5. tests/test_stageN_unittest.py
6. docs/Stage N 验证报告.md
```

必须保持：

```text
monitoring/exports/dashboard_summary.json 可被前端读取
monitoring/exports/runs.json 可被 API 和 Dashboard 读取
monitoring/exports/failures.json 可被 API 和 Dashboard 读取
monitoring/exports/stages.json 按 stage_id 数字排序
```

### 9.2 新增 API 端点

修改位置：

```text
core/monitoring_api.py
```

当前端点：

```text
GET  /api/status
GET  /api/monitoring
GET  /api/runs
GET  /api/failures
GET  /api/workflows
GET  /api/stages
GET  /api/reuse-summary
GET  /api/capability-graph
GET  /api/reports
POST /api/export-monitoring-data
```

新增端点规则：

```text
1. 默认只读 GET。
2. 会改变项目状态的 POST 必须谨慎，并在验证报告中说明。
3. API 返回 JSON，Content-Type 使用 application/json; charset=utf-8。
4. 不要让 API 直接删除历史数据。
5. Dashboard 必须能在 API 不可用时回退到静态 JSON。
```

### 9.3 Dashboard 扩展窗口

新增页面区域时：

```text
1. index.html 增加 section。
2. styles.css 增加响应式样式。
3. app.js 增加 renderXxx 函数。
4. 保持移动端单列可读。
5. 用 Edge 或浏览器截图检查桌面和移动端。
```

---

## 10. 阶段推进规则

每一个新阶段必须完成：

```text
1. 明确阶段目标。
2. 实现最小可验证功能。
3. 新增 tests/test_stageN_unittest.py。
4. 运行全量测试。
5. 新增 docs/Stage N 验证报告.md。
6. 更新 docs/项目进度记录.md。
7. export_monitoring_data.py 重新导出。
8. 检查 Dashboard/API。
9. 提交 Git。
10. 推送 GitHub。
```

验证命令基线：

```powershell
python export_monitoring_data.py
python -m unittest discover -s tests -p "*unittest.py" -v
python serve_observatory.py --port 8770
```

---

## 11. 下一阶段开发入口

建议下一阶段：

```yaml
next_stage: Stage 11
name: 失败钻取与诊断工作台
goal: 把 failure、missing_fields、metacode 推荐、修复路径串成可分析页面
```

优先功能：

```text
1. 新增 /api/diagnostics/summary
2. 新增 /api/diagnostics/by-field
3. 新增 /api/diagnostics/by-workflow
4. Dashboard 新增“诊断工作台” section
5. 按 missing_fields 聚合失败次数
6. 按 workflow 聚合失败次数
7. 显示推荐 metacode 与是否 ready
8. 预留“修复成功率”字段
```

最小开发路径：

```text
1. 不动 metacodes。
2. 不动已有 workflow。
3. 在 core/monitoring_api.py 增加只读诊断端点。
4. 在 dashboard 增加诊断展示。
5. 新增 tests/test_stage11_unittest.py。
6. 新增 docs/Stage 11 验证报告.md。
```

---

## 12. 低成本开发原则

```text
1. 优先新增，不优先重构。
2. 优先沿用现有目录和命名。
3. 优先让数据结构向后兼容。
4. 优先写只读分析接口，再考虑写操作。
5. 优先让 Dashboard 展示已有数据，再新增采集逻辑。
6. 每次开发只改变一个阶段目标相关的最小范围。
7. 不把实验性功能混入稳定 workflow。
8. 不把 UI 逻辑写进 metacode。
9. 不把 metacode 能力写死到 Dashboard。
10. 不为了短期演示破坏长期可复用结构。
```

---

## 13. 新窗口 AI 快速接续提示词

如果在新窗口继续开发，可以直接使用：

```text
请先读取 PROJECT_STRUCTURE_LOCK.md，再读取 README.md、docs/项目进度记录.md 和最新 Stage 验证报告。
然后扫描项目代码，但不要改变原有代码结构。
当前目标是继续 Stage 11：失败钻取与诊断工作台。
请以最小改动实现下一步功能，保留 API 优先和静态 JSON 回退机制，并在完成后新增测试、验证报告、项目记录，最后提交 Git。
未经授权不要修改 PROJECT_STRUCTURE_LOCK.md。
```

---

## 14. 版本日志

### v1.0.0

```yaml
date: 2026-06-11
operator: Codex
authorization_source: 用户要求生成结构化项目文件，并要求未经授权不得修改
change_scope:
  - 创建 PROJECT_STRUCTURE_LOCK.md
  - 记录当前 Stage 10 项目结构
  - 记录开发约束
  - 记录后续扩展接口
  - 记录新窗口 AI 接续协议
reason: 降低后续开发接续成本，避免新窗口 AI 破坏既有结构
files_or_modules_affected:
  - PROJECT_STRUCTURE_LOCK.md
verification:
  - git status 已确认基线为 main...origin/main
  - 当前最新提交为 52d1471
  - 当前监控摘要为 current_stage = 10
next_expected_stage: Stage 11 失败钻取与诊断工作台
```

