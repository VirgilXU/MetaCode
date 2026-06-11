# MetaCode Stage 11 验证报告

## 1. 阶段名称

第十一阶段：失败钻取与诊断工作台。

Stage 11 接在 Stage 10 的本地 API 与实时观察台之后，目标是把失败日志、缺失字段、推荐 metacode 和 workflow 失败情况聚合成可直接观察的诊断页面。

## 2. 测试日期

2026-06-11

## 3. 阶段目标

Stage 11 的核心目标：

```text
把散落在 failure_log 和 recommendations 中的失败信息，变成观察台里的诊断工作台。
```

具体目标包括：

1. 新增只读诊断 API。
2. 按 missing_fields 聚合失败。
3. 按 workflow 聚合失败。
4. 按推荐 metacode 聚合建议次数和 ready 次数。
5. Dashboard 新增诊断工作台。
6. 静态 JSON 回退时，前端也能本地计算诊断聚合。
7. 预留 repair_success_rate 字段，为后续修复成功率统计做准备。
8. 新增 Stage 11 自动化测试。

## 4. 本阶段改动

### 4.1 诊断 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
GET /api/diagnostics/summary
GET /api/diagnostics/by-field
GET /api/diagnostics/by-workflow
GET /api/diagnostics/by-metacode
```

`GET /api/monitoring` 也会返回：

```text
diagnostics.summary
diagnostics.by_field
diagnostics.by_workflow
diagnostics.by_metacode
```

### 4.2 Dashboard 诊断工作台

修改文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

新增区域：

```text
诊断工作台
```

显示内容：

```text
失败记录数量
影响 workflow 数量
缺失字段数量
推荐能力数量
缺失字段排行榜
失败 workflow 排行榜
推荐 metacode 排行榜
```

### 4.3 自动化测试

新增文件：

```text
tests/test_stage11_unittest.py
```

测试覆盖：

```text
/api/status 是否升级为 stage11
/api/monitoring 是否包含 diagnostics
/api/diagnostics/* 是否可读
诊断聚合是否按失败次数排序
Dashboard 是否包含诊断工作台
Stage 11 报告和项目记录是否存在
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest discover -s tests -p "*unittest.py" -v
python serve_observatory.py --port 8770
```

浏览器验证：

```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/diagnostics/summary
```

## 6. 验证结果

本轮验证结果：

```text
监控数据导出：通过
自动化测试：通过，51 tests OK
API 端点检查：通过
Dashboard 可视化检查：通过，Edge 无头截图已检查桌面与移动端
```

关键指标：

```text
current_stage = 11
stage_report_count = 10
run_count = 532
success_run_count = 396
failure_run_count = 136
success_rate = 74.4%
API /api/status 返回 version = stage11
diagnostics.summary.failure_count = 136
diagnostics.summary.workflow_failure_count = 2
diagnostics.summary.unique_missing_field_count = 1
diagnostics.summary.suggestion_count = 132
diagnostics.summary.ready_suggestion_count = 91
top_field = data.clean_text / 132
top_workflow = broken_missing_clean_text / 95
top_metacode = text.clean_text_basic / 132
```

本阶段确认了一个重要现象：

```text
当前失败样本高度集中在 data.clean_text 缺失。
这说明 Stage 11 诊断工作台可以直接指出最值得优先治理的能力缺口。
```

## 7. 阶段判断

Stage 11 的预期判断：

```text
MetaCode 已经开始具备“失败可分析”的工程观察能力。
```

如果验证通过，后续就可以继续做：

```text
失败 -> 推荐 -> 修复/规划 -> 成功率
```

这一条闭环。

## 8. 当前不足

Stage 11 仍是诊断工作台 MVP：

1. 诊断数据来自历史 failure_log，还没有独立诊断数据库表。
2. repair_success_rate 只是预留字段，还没有真实统计。
3. Dashboard 只展示聚合排行，还没有点击钻取详情页。
4. 还不能从页面直接触发修复或规划。
5. 还没有传统 AI 编程对比采集数据。

## 9. 下一阶段建议

建议 Stage 12 做：

```text
修复闭环与修复成功率统计
```

优先任务：

1. 记录每次失败后的推荐结果。
2. 记录是否生成 fixed/planned workflow。
3. 记录修复 workflow 是否运行成功。
4. 在诊断工作台中展示修复成功率。
5. 为 MetaCode vs 传统 AI 编程对比实验准备真实指标。
