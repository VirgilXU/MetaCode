# MetaCode Stage 13 验证报告

## 1. 阶段名称

第十三阶段：修复事件链与一键修复入口预留。

Stage 13 接在 Stage 12 的修复成功率统计之后，目标是把单次失败、推荐能力、生成 workflow 和验证运行绑定成完整 repair event。

## 2. 测试日期

2026-06-11

## 3. 阶段目标

Stage 13 的核心目标：

```text
把“修复成功率”背后的每一次修复，变成可追踪、可查询、可展示的事件链。
```

具体目标包括：

1. 新增 repair_events 结构。
2. 给每次修复验证生成稳定 repair_id。
3. 绑定 failure run、suggestions、generated workflow、verification run。
4. 统计事件闭环成功率和失败绑定率。
5. 按 source workflow 聚合事件。
6. 按 fixed/planned 策略聚合事件。
7. Dashboard 新增“修复事件链”模块。
8. SQLite 监控库新增 repair_events 表。
9. 预留后续一键修复 API 与详情页入口。

## 4. 本阶段改动

### 4.1 事件链导出

修改文件：

```text
core/monitoring_store.py
export_monitoring_data.py
monitoring/schema.sql
```

新增导出文件：

```text
monitoring/exports/repair_events.json
```

核心结构：

```text
repairEvents.summary
repairEvents.events
repairEvents.recent_events
repairEvents.by_strategy
repairEvents.by_workflow
```

每条 repair event 包含：

```text
repair_id
failure_run_id
source_workflow_id
missing_fields
suggestions
strategy
generated_workflow_id
inserted_steps
verification_run_id
verification_status
event_status
event_latency_ms
```

### 4.2 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/repair-events/summary
GET /api/repair-events
GET /api/repair-events/by-strategy
GET /api/repair-events/by-workflow
GET /api/repair-events/recent
```

`GET /api/monitoring` 也会返回：

```text
repairEvents
```

### 4.3 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

新增区域：

```text
修复事件链
```

显示内容：

```text
事件链数量
失败绑定率
闭环成功率
生成路径数量
最新事件链
Workflow 事件聚合
策略事件聚合
最近事件列表
```

静态 JSON 回退模式下，前端也能从 runs 和 workflows 中本地计算 repair events。

### 4.4 自动化测试

新增文件：

```text
tests/test_stage13_unittest.py
```

测试覆盖：

```text
/api/status 是否升级为 stage13
/api/monitoring 是否包含 repairEvents
/api/repair-events/* 是否可读
repair event 是否绑定 failure 和 verification
事件聚合是否按 event_count 排序
SQLite 是否包含 repair_events 表
Dashboard 是否包含修复事件链模块
Stage 13 报告和项目记录是否存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage13_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

浏览器验证：

```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/repair-events/summary
```

## 6. 验证结果

本轮验证结果：

```text
监控数据导出：通过
Stage 13 自动化测试：通过，8 tests OK
全量自动化测试：通过，65 tests OK
API 端点检查：通过
Dashboard 可视化检查：通过，桌面与移动端均已检查，移动端无页面级横向溢出
```

关键指标：

```text
current_stage = 13
stage_report_count = 12
run_count = 594
success_run_count = 440
failure_run_count = 154
success_rate = 74.1%
repair_attempt_count = 130
repair_event_count = 130
closed_success_count = 130
closed_failed_count = 0
event_success_rate = 100.0%
linked_event_count = 130
unlinked_event_count = 0
failure_link_rate = 100.0%
strategy_count = 2
source_workflow_count = 2
generated_workflow_count = 2
```

当前已验证事件链：

```text
broken_missing_clean_text failure -> text.clean_text_basic -> broken_missing_clean_text_fixed -> success
broken_missing_summary_chain failure -> io.read_markdown_file + text.clean_text_basic -> broken_missing_summary_chain_planned -> success
```

## 7. 阶段判断

Stage 13 的阶段判断：

```text
MetaCode 已经具备可追踪的修复事件链，后续可以在事件级别做复盘、详情页和一键修复入口。
```

这让项目从“知道修复成功率”进一步推进到“知道每一次修复为什么发生、怎么生成、如何验证”。

## 8. 当前不足

Stage 13 仍是事件链 MVP：

1. repair event 来自历史 runs 推断，执行器还没有显式写入 repair_id。
2. Dashboard 仍是只读展示，不能直接触发修复。
3. failure 与 repair 的绑定规则是“同源 workflow 最近失败”，复杂并发场景需要更强关联。
4. repair_events 表已经存在，但还没有独立写入生命周期。
5. 还没有修复详情抽屉和人工审核状态。

## 9. 下一阶段建议

建议 Stage 14 做：

```text
一键修复 API 与修复详情页
```

优先任务：

1. 新增 POST /api/repair/fix-workflow。
2. 新增 POST /api/repair/plan-workflow。
3. 为触发的修复写入显式 repair_id。
4. Dashboard 增加修复详情抽屉。
5. 在详情中展示 failure、suggestion、generated workflow、verification 的完整链路。
