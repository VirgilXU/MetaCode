# MetaCode Stage 18 验证报告

## 1. 阶段名称

第十八阶段：能力质量评分和复用收益分析。

Stage 18 接在 Stage 17 的 generated workflow 审核流程之后，目标是把已有的复用、能力图谱、失败诊断、修复事件和对比实验数据综合起来，形成第一版 metacode 能力质量评分。

## 2. 测试日期

2026-06-14

## 3. 阶段目标

Stage 18 的核心目标：

```text
让 MetaCode 不只知道“有哪些能力”，还知道“哪些能力更重要、更稳定、更能带来修复和复用收益”。
```

具体目标包括：

1. 新增能力质量评分导出。
2. 将复用次数、桥接得分、失败关联、修复贡献和实验资产增量纳入评分。
3. 提供能力质量 API。
4. Dashboard 增加能力质量区。
5. 新增 Stage 18 自动化测试。

## 4. 本阶段改动

### 4.1 能力质量导出

修改文件：

```text
core/monitoring_store.py
export_monitoring_data.py
```

新增导出文件：

```text
monitoring/exports/capability_quality.json
```

每条能力质量记录包含：

```text
metacode_id
category
purpose
quality_score
quality_tier
usage_count
bridge_score
degree
failure_count
suggestion_count
ready_suggestion_count
repair_contribution_count
comparison_asset_delta
reads
writes
```

评分公式当前是透明的启发式 MVP：

```text
quality_score =
  usage_count * 12
  + bridge_score * 6
  + repair_contribution_count * 10
  + ready_suggestion_count * 4
  - failure_count * 3
```

分层：

```text
core >= 120
strong >= 80
useful >= 40
emerging < 40
```

### 4.2 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/capability-quality/summary
GET /api/capability-quality
```

`GET /api/monitoring` 会返回：

```text
capabilityQuality
```

### 4.3 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/app.js
```

新增区域：

```text
能力质量
```

显示内容：

```text
已评分能力
核心能力数量
修复贡献能力数量
最高分能力
Top 能力资产列表
```

### 4.4 自动化测试

新增文件：

```text
tests/test_stage18_unittest.py
```

测试覆盖：

```text
capability_quality.json 包含评分和摘要
能力质量 API 端点可读
Dashboard 包含能力质量区块
Stage 18 报告和项目记录存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage18_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

## 6. 验证结果

本轮已完成验证。

命令结果：

```text
python -m unittest tests.test_stage18_unittest -v
Ran 4 tests
OK

python -m unittest discover -s tests -p "*unittest.py" -v
Ran 89 tests
OK

node --check dashboard\app.js
通过
```

关键结果：

```text
current_stage >= 18
API version = stage18
capability_quality.json 包含 15 个 metacode 的评分
Dashboard 能力质量区展示 Top 能力资产
```

## 7. 阶段判断

Stage 18 的阶段判断：

```text
MetaCode 已经具备第一版能力资产评估能力，后续可以围绕高质量 metacode 优化复用、修复和实验收益。
```

## 8. 当前不足

Stage 18 仍是评分 MVP：

1. 评分公式是启发式，不代表长期稳定权重。
2. failure_count 当前按 failed_step 统计，复杂失败归因还不够细。
3. comparison_asset_delta 只做粗粒度关联，没有绑定具体 metacode。
4. Dashboard 只有列表，没有趋势图。
5. 还没有把评分反馈到 workflow 规划和修复策略选择。

## 9. 下一阶段建议

建议 Stage 19 做：

```text
从用户目标反推 workflow 的任务入口
```

优先任务：

1. 设计目标描述到 workflow 候选的最小数据结构。
2. 基于 context_read / context_write 和能力质量评分排序候选路径。
3. Dashboard 增加任务入口原型。
4. 对候选路径选择增加隔离测试。
5. 将任务入口与对比实验记录连接起来。
