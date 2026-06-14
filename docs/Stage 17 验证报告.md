# MetaCode Stage 17 验证报告

## 1. 阶段名称

第十七阶段：修复审核与 generated workflow 提升流程。

Stage 17 接在 Stage 16 的对比实验记录器之后，目标是把 generated workflow 从“生成后只展示”推进到“有审核状态、有提升就绪度、有受控提升入口的前置流程”。

## 2. 测试日期

2026-06-14

## 3. 阶段目标

Stage 17 的核心目标：

```text
建立 generated workflow 的最小审核记录，让修复结果进入受控治理流程，而不是直接自动提升为 stable workflow。
```

具体目标包括：

1. 新增 generated workflow 审核记录资产。
2. 对 generated workflow 增加 review_status。
3. 对 generated workflow 增加 promotion_status 和 promotion_ready。
4. 导出审核摘要和审核记录。
5. 提供只读 API 端点。
6. Dashboard 增加最小修复审核视图。
7. 新增 Stage 17 自动化测试。

## 4. 本阶段改动

### 4.1 审核记录资产

新增文件：

```text
reviews/generated_workflow_reviews.json
```

每条审核记录包含：

```text
review_id
generated_workflow_id
source_workflow_id
strategy
review_status
promotion_status
promotion_ready
reviewed_by
reviewed_at
promotion_target
notes
```

当前 Stage 17 不自动复制、重命名或提升 stable workflow，只记录“是否具备人工提升审核条件”。

### 4.2 监控导出

修改文件：

```text
core/monitoring_store.py
export_monitoring_data.py
```

新增导出文件：

```text
monitoring/exports/generated_workflow_reviews.json
```

摘要字段：

```text
generated_workflow_count
review_record_count
reviewed_count
pending_count
accepted_count
rejected_count
promotion_ready_count
review_coverage_rate
promotion_ready_rate
```

### 4.3 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/generated-workflow-reviews/summary
GET /api/generated-workflow-reviews
```

`GET /api/monitoring` 会返回：

```text
generatedReviews
```

### 4.4 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/app.js
```

新增区域：

```text
修复审核
```

展示内容：

```text
生成 Workflow 数量
审核覆盖率
已接受数量
提升就绪数量
generated workflow 审核列表
promotion_status / promotion_ready
```

### 4.5 自动化测试

新增文件：

```text
tests/test_stage17_unittest.py
```

测试覆盖：

```text
审核记录源文件存在
generated_workflow_reviews.json 导出包含 summary 和 records
API 审核端点可读
Dashboard 包含修复审核区块
Stage 17 报告和项目记录存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage17_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

## 6. 验证结果

本轮已完成验证。

命令结果：

```text
python -m unittest tests.test_stage17_unittest -v
Ran 5 tests
OK

python -m unittest discover -s tests -p "*unittest.py" -v
Ran 85 tests
OK

node --check dashboard\app.js
通过
```

关键结果：

```text
current_stage >= 17
API version = stage17
generated_workflow_reviews.json 包含审核摘要和记录
Dashboard 修复审核区展示 generated workflow 审核状态
```

## 7. 阶段判断

Stage 17 的阶段判断：

```text
MetaCode 已经具备 generated workflow 的最小治理入口，后续可以在不破坏稳定 workflow 的前提下推进人工审核和受控提升。
```

## 8. 当前不足

Stage 17 仍是审核流程 MVP：

1. 审核记录是手工维护 JSON，还没有写入型 API。
2. Dashboard 只读展示审核状态，还不能接受或拒绝。
3. promotion_ready 只是流程状态，不会自动生成 stable workflow。
4. 还没有对 promoted workflow 建立独立历史。
5. 还没有把审核记录与具体 repair event 双向链接。

## 9. 下一阶段建议

建议 Stage 18 做：

```text
能力质量评分和复用收益分析
```

优先任务：

1. 统计 metacode 的复用次数、失败关联、修复贡献。
2. 给核心能力和桥接能力增加质量评分。
3. Dashboard 展示能力质量列表。
4. 将能力质量与对比实验收益连接起来。
5. 对评分逻辑增加隔离测试。
