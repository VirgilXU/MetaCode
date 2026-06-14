# MetaCode Stage 16 验证报告

## 1. 阶段名称

第十六阶段：对比实验记录器 MVP。

Stage 16 接在 Stage 15 的测试副作用隔离之后，目标是开始回答 MetaCode 的核心价值问题：

```text
MetaCode 相比传统 AI 编程，到底在哪些场景减少耗时、失败、返工，并增加可复用资产？
```

## 2. 测试日期

2026-06-12

## 3. 阶段目标

Stage 16 的核心目标：

```text
建立最小对比实验记录结构，并让监控导出、API 和 Dashboard 都能读取它。
```

具体目标包括：

1. 新增对比实验记录数据源。
2. 记录 MetaCode 与传统 AI 编程的耗时、失败、返工、资产增量。
3. 导出对比实验摘要。
4. 提供只读 API 端点。
5. Dashboard 对比实验区展示真实记录。
6. 新增 Stage 16 自动化测试。

## 4. 本阶段改动

### 4.1 实验记录资产

新增文件：

```text
experiments/comparison_records.json
```

当前包含两条最小实验记录：

```text
Note summary workflow reuse
Repair chain traceability
```

每条记录包含：

```text
experiment_id
title
task
date
status
metacode
traditional_ai
result
```

### 4.2 监控导出

修改文件：

```text
core/monitoring_store.py
```

新增导出：

```text
monitoring/exports/comparison_experiments.json
```

摘要字段：

```text
experiment_count
recorded_count
metacode_win_count
metacode_win_rate
total_time_saved_minutes
reusable_asset_delta
latest_experiment
```

### 4.3 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/comparison-experiments/summary
GET /api/comparison-experiments
```

`GET /api/monitoring` 会返回：

```text
comparison
```

### 4.4 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/app.js
```

对比实验区从“预留”升级为读取真实实验记录：

```text
实验摘要
实验记录卡片
MetaCode 耗时与资产增量
传统 AI 耗时与资产增量
阶段结论 takeaway
```

### 4.5 自动化测试

新增文件：

```text
tests/test_stage16_unittest.py
```

测试覆盖：

```text
实验记录源文件存在
comparison_experiments.json 导出包含 summary 和 records
API 对比实验端点可读
Dashboard 引用对比实验导出和真实记录渲染逻辑
Stage 16 报告和项目记录存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage16_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

## 6. 验证结果

本轮已完成验证。

命令结果：

```text
python -m unittest tests.test_stage16_unittest -v
Ran 5 tests
OK

python -m unittest discover -s tests -p "*unittest.py" -v
Ran 80 tests
OK

node --check dashboard\app.js
通过
```

关键结果：

```text
current_stage >= 16
API version = stage16
comparison_experiments.json 包含实验摘要和记录
Dashboard 对比实验区展示真实记录
```

## 7. 阶段判断

Stage 16 的阶段判断：

```text
MetaCode 开始具备“价值可证明”的最小记录结构，后续可以用真实任务持续比较 MetaCode 与传统 AI 编程的差异。
```

## 8. 当前不足

Stage 16 仍是对比实验 MVP：

1. 当前实验数据是手工记录，不是自动采集。
2. 样本数很小，不能证明统计意义。
3. 还没有任务级实验模板和录入命令。
4. Dashboard 只展示摘要和卡片，没有趋势图。
5. 还没有把实验结果和具体 workflow / repair event 双向链接。

## 9. 下一阶段建议

建议 Stage 17 做：

```text
修复审核与 generated workflow 提升流程
```

优先任务：

1. 为 repair event 增加审核状态。
2. 对 generated workflow 增加 accepted / rejected / promoted 标记。
3. 设计从 generated workflow 提升到 stable workflow 的受控流程。
4. Dashboard 增加最小审核入口。
5. 对提升流程增加隔离测试。
