# MetaCode Stage 7 验证报告

> 日期：2026-06-08  
> 目标：为后续可视化监控系统完成预处理数据层，统一导出 JSON 数据，并建立 SQLite 监控库。

---

## 1. 阶段目标

Stage 6 已经实现能力图谱与路径评分。

Stage 7 的目标不是做 UI，而是先完成可视化系统的数据地基：

```text
运行记录可读
失败记录可读
阶段报告可读
Workflow 图谱可读
能力图谱可读
复用统计可读
SQLite 监控库可查询
```

这样后续 Dashboard 不需要直接解析零散的 JSONL、YAML 和 Markdown。

---

## 2. 本阶段新增内容

### 2.1 新增 monitoring 目录

新增目录：

```text
monitoring/
├── metacode_monitor.db
├── schema.sql
├── exports/
└── stages/
```

用途：

```text
metacode_monitor.db：SQLite 监控库
schema.sql：数据库结构
exports/：给前端读取的 JSON 文件
stages/：每个阶段的机器可读 JSON
```

---

### 2.2 新增监控存储模块

新增文件：

```text
core/monitoring_store.py
```

核心能力：

```text
读取 run_log.jsonl
读取 failure_log.jsonl
兼容旧日志并补 synthetic run_id
读取 Stage 验证报告
读取 workflows/*.yaml
读取 generated workflow
读取 registry / reuse / capability graph
导出 JSON
写入 SQLite
```

---

### 2.3 新增导出命令

新增文件：

```text
export_monitoring_data.py
```

命令：

```powershell
python export_monitoring_data.py
```

输出：

```text
status: exported
database_path: monitoring/metacode_monitor.db
run_count
stage_count
workflow_count
```

---

### 2.4 执行器新增 run_id

修改文件：

```text
core/combiner.py
```

新增字段：

```text
run_id
started_at
ended_at
workflow_path
steps_total
steps_success
failed_step
```

说明：

旧日志没有 `run_id`，导出器会自动生成兼容 ID。

新日志从 Stage 7 开始会直接写入真实 `run_id`。

---

### 2.5 新增测试

新增文件：

```text
tests/test_stage7_unittest.py
```

测试覆盖：

```text
execute_workflow 会返回 run_id
JSON exports 能生成
dashboard_summary.json 前端可读
SQLite 表能写入数据
stage_N.json 能生成
```

---

## 3. 当前导出的 JSON 文件

导出目录：

```text
monitoring/exports/
```

当前文件：

```text
dashboard_summary.json
runs.json
failures.json
stages.json
workflow_graph.json
reuse_summary.json
capability_graph.json
capability_graph_summary.json
```

这些文件可以直接作为未来前端 Dashboard 的第一批数据源。

---

## 4. SQLite 数据库

数据库位置：

```text
monitoring/metacode_monitor.db
```

当前表：

```text
runs
workflows
stages
metacodes
graph_edges
summaries
```

这些表覆盖：

```text
运行记录
Workflow 配置
阶段记录
元代码节点
能力图谱边
摘要数据
```

---

## 5. 验证命令

本阶段执行：

```powershell
python export_monitoring_data.py
python run_all_workflows.py
python analyze_capability_graph.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

---

## 6. 验证结果

导出结果：

```text
status: exported
database_path: monitoring/metacode_monitor.db
run_count: 221
stage_count: 5
workflow_count: 13
```

说明：

```text
run_count 会随着测试和 workflow 执行继续增长。
stage_count 在 Stage 7 报告写入前为 5，报告写入并重新导出后会包含 Stage 7。
workflow_count 包含 stable / broken / generated workflow。
```

全量测试：

```text
Ran 31 tests
OK
```

---

## 7. 当前 Dashboard 可展示的数据

现在前端已经可以读取：

```text
当前阶段
元代码数量
稳定 Workflow 数量
Workflow 文件数量
运行次数
成功次数
失败次数
能力图谱边数
字段数量
未解析字段数量
最近一次运行
```

也可以展示：

```text
所有 runs
所有 failures
所有 stages
所有 workflows
所有 metacode nodes
所有 graph edges
核心节点
桥接节点
复用统计
```

---

## 8. 阶段结论

Stage 7 成功。

MetaCode 当前已经具备可视化监控系统的预处理层：

```text
分散日志 -> 统一 runs
Markdown 阶段报告 -> stages JSON
YAML workflows -> workflow_graph JSON
能力图谱 -> capability_graph JSON
统计结果 -> dashboard_summary JSON
全部数据 -> SQLite 监控库
```

这意味着后续做 Dashboard 时，不需要再直接解析项目内部零散文件。

---

## 9. 当前边界

本阶段仍未实现：

```text
Web UI
HTTP API
实时刷新
运行日志去重
阶段报告内容深度结构化
step-level 时间线表
图谱布局数据
```

当前 `runs.json` 会包含历史测试产生的大量记录。

这是可接受的，因为它展示了系统运行历史。

如果后续需要更干净的 Dashboard，可以增加：

```text
run source 分类
测试运行过滤
最近 N 条运行
按 workflow 聚合
```

---

## 10. 下一阶段建议

Stage 8 建议正式开始做可视化 Dashboard。

建议最小 Dashboard 页面：

```text
总览页
Workflow 列表
失败诊断页
能力图谱页
阶段演进页
```

第一版可以不做复杂后端。

直接读取：

```text
monitoring/exports/*.json
```

这样可以快速验证页面是否有价值。

---

## 11. 阶段追踪

当前已有阶段报告：

```text
Stage 2 验证报告.md
Stage 3 验证报告.md
Stage 4 验证报告.md
Stage 5 验证报告.md
Stage 6 验证报告.md
Stage 7 验证报告.md
```
