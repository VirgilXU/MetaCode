# MetaCode

MetaCode is an experimental software-production system built around reusable capability units, workflow composition, failure diagnosis, automatic workflow repair, capability graph analysis, and a local observability dashboard.

MetaCode 是一个实验性软件生产系统。它不把代码片段当作核心资产，而是把“能力单元、工作流路径、失败诊断、自动修复、能力图谱和项目演进记录”作为可积累的工程资产。

---

## 中文说明

### 项目目标

MetaCode 的目标不是让 AI 每次从零写代码，而是让系统逐步沉淀可复用能力，并通过 Workflow 组合这些能力。

当前项目已经验证到 Stage 13：

```text
Stage 2：15 个元代码 + 10 条成功 Workflow，验证复用成立
Stage 3：失败时根据 missing_fields 推荐可补元代码
Stage 4：自动生成 fixed Workflow
Stage 5：多步补全路径搜索，生成 planned Workflow
Stage 6：能力图谱与路径评分
Stage 7：监控数据预处理层，导出 JSON + SQLite
Stage 8：Web 可视化观察台
Stage 9：观察台实用化，增加阶段门禁、报告中心、对比实验预留和扩展窗口
Stage 10：本地 API 服务与自动刷新观察台
Stage 11：失败钻取与诊断工作台
Stage 12：修复闭环与修复成功率统计
Stage 13：修复事件链与一键修复入口预留
```

### 当前能力

当前系统具备：

```text
元代码身份证 identity.yaml
统一 Context 数据协议
Workflow 执行器
运行日志与失败日志
缺失字段诊断
可补能力推荐
单步自动修复
多步路径规划
能力图谱分析
路径评分
监控数据导出
Web Dashboard 观察台
修复闭环成功率统计
修复事件链追踪
```

### 项目结构

```text
core/                 核心执行、推荐、规划、图谱、监控导出和 API 逻辑
metacodes/            元代码能力库，每个能力包含 identity.yaml 和 runner.py
workflows/            稳定、失败样例和生成后的 Workflow
examples/             示例输入与输出
logs/                 运行日志和失败日志
registry/             元代码注册表
monitoring/           Dashboard 数据导出和 SQLite 监控库结构
dashboard/            Web 可视化观察台
tests/                Stage 2-13 自动测试
docs/                 阶段验证报告和功能设计文档
```

### 运行方式

安装依赖：

```powershell
pip install -r requirements.txt
```

运行一条 Workflow：

```powershell
python run_workflow.py workflows/note_to_summary.yaml
```

运行全部稳定 Workflow：

```powershell
python run_all_workflows.py
```

分析复用情况：

```powershell
python analyze_reuse.py
```

分析能力图谱：

```powershell
python analyze_capability_graph.py
```

导出监控数据：

```powershell
python export_monitoring_data.py
```

启动 Dashboard：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

然后访问：

```text
http://127.0.0.1:8765/dashboard/
```

启动带 API 的观察台：
```powershell
python serve_observatory.py --port 8770
```

然后访问：
```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/status
```

运行测试：

```powershell
python -m unittest discover -s tests -p "*unittest.py" -v
```

### 当前状态

当前监控数据摘要：

```text
current_stage: 13
metacode_count: 15
stable_workflow_count: 10
workflow_file_count: 13
edge_count: 26
field_count: 16
unresolved_field_count: 0
```

### 项目价值

传统 AI 编程更强在单次生成。

MetaCode 更强调：

```text
长期复用
失败修复
能力图谱
工程记忆
阶段演进
可观察性
```

---

## English

### Goal

MetaCode is not a prompt-to-code toy. It is an experiment in organizing software production around reusable capability units and validated workflow paths.

Instead of asking an AI to rewrite everything from scratch, MetaCode stores small executable capabilities, describes them with machine-readable identities, composes them into workflows, diagnoses failures, and generates repair or planning candidates.

The project has reached Stage 13:

```text
Stage 2: 15 metacodes and 10 stable workflows prove reuse
Stage 3: missing fields produce structured recommendations
Stage 4: single-step workflow repair generates fixed workflows
Stage 5: multi-step path planning generates planned workflows
Stage 6: capability graph and path scoring
Stage 7: monitoring exports and SQLite observability data
Stage 8: read-only Web observatory dashboard
Stage 9: practical observatory MVP with stage gates, report hub, comparison slots, and extension slots
Stage 10: local API service and auto-refresh observatory
Stage 11: failure drill-down and diagnostics workbench
Stage 12: repair loop and repair success-rate metrics
Stage 13: repair event chains and repair-entry preparation
```

### Features

Current features include:

```text
metacode identity files
shared Context protocol
workflow execution engine
success and failure logs
missing-field diagnosis
candidate capability recommendation
single-step workflow fixing
multi-step workflow planning
capability graph analysis
basic path scoring
monitoring data exports
local Web dashboard
repair-loop success-rate metrics
repair event-chain tracking
```

### Directory Layout

```text
core/                 Runtime, registry, recommendation, planning, graph, monitoring, and API logic
metacodes/            Capability units with identity.yaml and runner.py
workflows/            Stable, intentionally broken, fixed, and planned workflows
examples/             Sample inputs and generated outputs
logs/                 Run and failure logs
registry/             Generated metacode registry
monitoring/           JSON exports and SQLite monitoring schema
dashboard/            Local Web observatory
tests/                Stage 2-13 automated tests
docs/                 Stage reports and design documents
```

### Quick Start

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run a workflow:

```powershell
python run_workflow.py workflows/note_to_summary.yaml
```

Run all stable workflows:

```powershell
python run_all_workflows.py
```

Export monitoring data:

```powershell
python export_monitoring_data.py
```

Start the local dashboard:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/dashboard/
```

Start the dashboard with the local API:

```powershell
python serve_observatory.py --port 8770
```

Open:

```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/status
```

Run tests:

```powershell
python -m unittest discover -s tests -p "*unittest.py" -v
```

### Why MetaCode

Traditional AI coding is strong at one-off code generation.

MetaCode explores a different direction:

```text
reuse over regeneration
workflow paths over isolated snippets
structured failure diagnosis over raw error text
capability graphs over scattered scripts
engineering memory over one-off chats
```

The current implementation is still a prototype, but it already demonstrates a complete loop from capability reuse to workflow repair, graph analysis, monitoring exports, and Web observability.
