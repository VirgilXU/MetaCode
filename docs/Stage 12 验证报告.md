# MetaCode Stage 12 验证报告

## 1. 阶段名称

第十二阶段：修复闭环与修复成功率统计。

Stage 12 接在 Stage 11 的失败诊断工作台之后，目标是把“失败 -> 推荐 -> fixed/planned 修复运行 -> 验证结果”整理成可观察的闭环指标。

## 2. 测试日期

2026-06-11

## 3. 阶段目标

Stage 12 的核心目标：

```text
让 MetaCode 不只知道哪里失败，也能统计失败修复之后到底有没有跑通。
```

具体目标包括：

1. 从历史 runs 中识别 fixed/planned 修复验证运行。
2. 回溯修复运行对应的原始失败 workflow。
3. 统计修复尝试次数、成功次数、失败次数和成功率。
4. 按修复策略聚合 fixed 与 planned。
5. 按原始 workflow 聚合修复效果。
6. Dashboard 新增“修复闭环”模块。
7. 本地 API 新增修复指标端点。
8. 新增 Stage 12 自动化测试和验证报告。

## 4. 本阶段改动

### 4.1 监控导出

修改文件：

```text
core/monitoring_store.py
export_monitoring_data.py
```

新增导出文件：

```text
monitoring/exports/repair_metrics.json
```

核心统计维度：

```text
repairs.summary
repairs.by_strategy
repairs.by_workflow
repairs.recent_attempts
```

### 4.2 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/repairs/summary
GET /api/repairs/by-strategy
GET /api/repairs/by-workflow
GET /api/repairs/recent
```

`GET /api/monitoring` 也会返回：

```text
repairs
diagnostics.summary.repair_success_rate
diagnostics.summary.repair_success_rate_status
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
修复闭环
```

显示内容：

```text
修复验证次数
修复成功率
Fixed 成功率
Planned 成功率
策略成功率
Workflow 修复效果
最新修复验证
```

静态 JSON 回退模式下，前端也能从 runs 和 workflows 中本地计算 repair metrics。

### 4.4 自动化测试

新增文件：

```text
tests/test_stage12_unittest.py
```

测试覆盖：

```text
/api/status 是否升级为 stage12
/api/monitoring 是否包含 repairs
/api/repairs/* 是否可读
修复统计是否满足 attempt_count = success_count + failed_count
fixed 和 planned 是否都进入策略统计
修复 workflow 是否按验证次数排序
Dashboard 是否包含修复闭环模块
Stage 12 报告和项目记录是否存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage12_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

浏览器验证：

```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/repairs/summary
```

## 6. 验证结果

本轮验证结果：

```text
监控数据导出：通过
Stage 12 自动化测试：通过，6 tests OK
全量自动化测试：通过，57 tests OK
API 端点检查：通过
Dashboard 可视化检查：通过，桌面与移动端均已检查，移动端无页面级横向溢出
```

关键指标：

```text
current_stage = 12
stage_report_count = 11
run_count = 563
success_run_count = 418
failure_run_count = 145
success_rate = 74.2%
repair_attempt_count = 122
repair_success_count = 122
repair_failed_count = 0
repair_success_rate = 100.0%
fixed_attempt_count = 64
fixed_success_count = 64
fixed_success_rate = 100.0%
planned_attempt_count = 58
planned_success_count = 58
planned_success_rate = 100.0%
repair_source_workflow_count = 2
repair_workflow_count = 2
```

当前两个已验证修复闭环：

```text
broken_missing_clean_text -> broken_missing_clean_text_fixed
broken_missing_summary_chain -> broken_missing_summary_chain_planned
```

## 7. 阶段判断

Stage 12 的阶段判断：

```text
MetaCode 已经具备“失败可诊断、修复可验证、成功率可观测”的最小闭环。
```

这意味着项目已经从“能生成修复方案”推进到“能记录修复方案是否有效”。

## 8. 当前不足

Stage 12 仍是修复闭环 MVP：

1. 修复成功率来自历史运行日志聚合，还没有独立 repair_events 表。
2. Dashboard 还不能直接点击触发 fixed/planned 修复。
3. 当前统计以 workflow_id 后缀和 generated_from 推断修复关系，后续应增加显式 repair_id。
4. 还没有把单次失败、推荐、修复文件、验证运行绑定成完整事件链。
5. 还没有与传统 AI 编程做同任务对比采样。

## 9. 下一阶段建议

建议 Stage 13 做：

```text
修复事件链与一键修复入口
```

优先任务：

1. 新增 repair_events 结构。
2. 给每次失败生成 repair_id。
3. 绑定 failure -> suggestion -> generated workflow -> verification run。
4. Dashboard 增加修复详情页或抽屉。
5. 预留从页面触发 fixed/planned 修复的 API 入口。
