# MetaCode Stage 10 验证报告

## 1. 阶段名称

第十阶段：后端 API 与实时观察台。

Stage 10 接在 Stage 9 的观察台 MVP 之后，目标是让 Dashboard 不再只依赖静态 JSON 文件，而是具备本地 API 服务和自动刷新能力。

## 2. 测试日期

2026-06-11

## 3. 阶段目标

Stage 10 的核心目标：

```text
让观察台从“展示导出结果”升级为“项目运行中的监控入口”。
```

具体目标包括：

1. 新增本地 HTTP API 服务。
2. 保留静态 JSON 读取作为回退路径。
3. Dashboard 优先读取 `/api/monitoring`。
4. 增加 API 状态区，显示当前数据来源、API 版本、刷新策略和可用端点。
5. 增加自动刷新开关，每 30 秒刷新一次观察台数据。
6. 提供 runs、failures、workflows、stages、reports 等基础接口。
7. 新增 Stage 10 自动化测试。
8. 更新项目进度记录，为下一阶段失败钻取和对比实验采集做准备。

## 4. 本阶段改动

### 4.1 后端 API

新增文件：

```text
core/monitoring_api.py
serve_observatory.py
```

主要接口：

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

启动方式：

```powershell
python serve_observatory.py --port 8770
```

访问地址：

```text
http://127.0.0.1:8770/dashboard/
```

### 4.2 Dashboard

修改文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

新增能力：

```text
实时 API 页面区块
自动刷新开关
API 优先读取
静态 JSON 回退
API 状态卡片
Stage 10 健康状态
```

### 4.3 自动化测试

新增文件：

```text
tests/test_stage10_unittest.py
```

测试覆盖：

```text
/api/status 是否可读
/api/monitoring 是否返回完整数据包
/api/runs 是否支持 limit/status 过滤
/api/failures 和 /api/reports 是否可读
Dashboard 是否包含 API 优先与静态回退逻辑
Stage 10 报告和项目记录是否存在
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
http://127.0.0.1:8770/api/status
```

## 6. 验证结果

本轮验证结果：

```text
监控数据导出：通过
自动化测试：通过，45 tests OK
API 端点检查：通过
Dashboard 可视化检查：通过，Edge 无头截图已检查桌面与移动端
```

关键指标：

```text
current_stage = 10
stage_report_count = 9
run_count = 470
success_run_count = 352
failure_run_count = 118
success_rate = 74.9%
metacode_count = 15
workflow_file_count = 13
unresolved_field_count = 0
API /api/status 返回 status = ok
Dashboard 支持 API 优先读取与静态 JSON 回退
```

可视化检查中发现并修正了一个排序问题：

```text
Stage 10 曾因文件名字符串排序显示在 Stage 2 前面。
已改为按 stage_id 数字排序，阶段演进现在按 Stage 2 -> Stage 10 展示。
```

## 7. 阶段判断

Stage 10 的预期判断：

```text
MetaCode 观察台开始从静态结果页进入本地服务化阶段。
```

如果验证通过，项目将具备：

```text
静态导出层
本地 API 层
前端观察台
自动刷新机制
接口测试
阶段报告跟踪
```

## 8. 当前不足

Stage 10 仍然是本地 API MVP：

1. API 只服务本地项目，还没有多项目管理。
2. 自动刷新只是轮询，不是事件流或 WebSocket。
3. POST 导出接口只做监控数据导出，还没有完整操作审计。
4. 失败钻取还没有做成独立页面。
5. 对比实验采集器仍然只是预留。

## 9. 下一阶段建议

建议 Stage 11 做：

```text
失败钻取与诊断工作台
```

优先任务：

1. 增加 workflow 详情页。
2. 按 missing_fields 聚合失败。
3. 按 metacode 聚合失败和建议。
4. 展示失败 -> 推荐 -> 修复/规划路径。
5. 记录每次修复是否成功，为后续对比实验提供数据。
