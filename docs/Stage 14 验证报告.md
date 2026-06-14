# MetaCode Stage 14 验证报告

## 1. 阶段名称

第十四阶段：一键修复 API 与修复详情页。

Stage 14 接在 Stage 13 的修复事件链之后，目标是让 Dashboard 不只读取 repair event，还能通过本地 API 触发 fixed / planned 修复，并查看事件级详情。

## 2. 测试日期

2026-06-12

## 3. 阶段目标

Stage 14 的核心目标：

```text
把“只读修复事件链”推进为“可触发、可追踪、可复盘”的本地修复工作台 MVP。
```

具体目标包括：

1. 新增 `POST /api/repair/fix-workflow`。
2. 新增 `POST /api/repair/plan-workflow`。
3. API 触发修复时生成显式 `repair_id`。
4. 失败诊断运行和验证运行写入同一个 `repair_id`。
5. repair event 导出优先按显式 `repair_id` 绑定。
6. Dashboard 增加一键修复入口。
7. Dashboard 增加修复详情面板。
8. 新增 Stage 14 自动化测试。

## 4. 本阶段改动

### 4.1 工作流执行元数据

修改文件：

```text
core/combiner.py
core/workflow_fixer.py
core/path_planner.py
```

`execute_workflow` 增加可选修复元数据：

```text
repair_id
repair_strategy
repair_source_workflow_id
```

普通 workflow 运行不需要传入这些字段；只有 API 触发的修复动作会把同一个 `repair_id` 写入失败诊断运行和验证运行。

### 4.2 事件链导出

修改文件：

```text
core/monitoring_store.py
```

Stage 14 保留 Stage 13 的历史推断逻辑，同时新增优先级：

```text
如果 verification run 带有 repair_id，则优先用 repair_id 找到对应 failure run。
如果没有 repair_id，则继续按 source workflow 最近失败推断。
```

这让旧数据兼容，新触发的修复动作具备更稳定的事件绑定。

### 4.3 API

修改文件：

```text
core/monitoring_api.py
```

新增端点：

```text
POST /api/repair/fix-workflow
POST /api/repair/plan-workflow
```

请求体示例：

```json
{
  "workflow_path": "workflows/broken_missing_clean_text.yaml"
}
```

响应包含：

```text
repair_id
strategy
result
repair_event
summary
```

修复动作完成后 API 会立即重新导出监控数据，让 Dashboard 能在同一轮刷新中看到新事件。

### 4.4 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

新增内容：

```text
一键修复入口
失败样例 workflow 选择器
Fixed / Planned 触发按钮
修复详情面板
最近事件点击查看详情
```

静态 JSON 回退模式只展示数据，不触发修复动作。

### 4.5 自动化测试

新增文件：

```text
tests/test_stage14_unittest.py
```

测试覆盖：

```text
/api/status 是否升级为 stage14
/api/monitoring 是否列出两个 POST 修复端点
POST /api/repair/fix-workflow 是否返回显式 repair_id
POST /api/repair/plan-workflow 是否返回显式 repair_id
显式 repair_id 是否写入 repair_events.json
Dashboard 是否包含一键修复入口和详情面板
Stage 14 报告和项目记录是否存在
```

## 5. 验证方式

本阶段建议使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest tests.test_stage14_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

浏览器验证：

```text
http://127.0.0.1:8770/dashboard/
http://127.0.0.1:8770/api/status
```

## 6. 验证结果

本轮已完成验证。

命令结果：

```text
python -m unittest tests.test_stage14_unittest -v
Ran 6 tests
OK

python -m unittest discover -s tests -p "*unittest.py" -v
Ran 71 tests
OK

node --check dashboard\app.js
通过
```

关键结果：

```text
current_stage >= 14
API version = stage14
POST /api/repair/fix-workflow 可触发 fixed 修复
POST /api/repair/plan-workflow 可触发 planned 修复
repair event 可按 repair_id 绑定 failure 与 verification
Dashboard 可触发修复并查看详情
```

## 7. 阶段判断

Stage 14 的阶段判断：

```text
MetaCode 已经从“只读修复事件链”推进为“可触发、可追踪、可复盘”的本地修复工作台 MVP。
```

## 8. 当前不足

Stage 14 仍是本地原型：

1. 修复动作没有权限模型和队列系统。
2. repair event 仍主要由运行日志和监控导出生成，没有独立事件存储生命周期。
3. Dashboard 只支持从失败样例 workflow 触发修复，还没有从任意失败详情直接触发。
4. 生成 workflow 仍保留在 `workflows/generated/`，不会自动提升为 stable workflow。
5. 还没有人工审核状态和候选路径比较。

## 9. 下一阶段建议

建议 Stage 15 做：

```text
修复审核状态与候选路径比较
```

优先任务：

1. 为 repair event 增加人工审核状态。
2. 对同一失败展示 fixed / planned 候选路径差异。
3. 将修复动作历史独立记录为结构化 action log。
4. 从失败详情直接触发修复。
5. 增加受控的 generated workflow 提升流程。
