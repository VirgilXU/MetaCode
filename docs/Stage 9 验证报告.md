# MetaCode Stage 9 验证报告

## 1. 阶段名称

第九阶段：可视化观察台实用化测试。

本阶段不是重新发明核心算法，而是把 Stage 8 的静态 Dashboard 推进为更接近项目监控入口的观察台 MVP。

## 2. 测试日期

2026-06-11

## 3. 阶段目标

Stage 9 的目标是验证：

```text
MetaCode 是否已经具备“可持续观察、可阶段追踪、可扩展”的工程监控雏形。
```

具体目标包括：

1. 让 Dashboard 能直接展示项目当前阶段、运行质量、阶段报告数量和导出时间。
2. 增加阶段门禁，让用户快速判断当前项目是否适合进入下一阶段。
3. 增加报告中心，集中查看每一阶段验证报告。
4. 增加 MetaCode 与传统 AI 编程的对比实验预留区。
5. 增加后续功能扩展窗口，为后端 API、实时刷新、对比实验采集器和智能告警留入口。
6. 新增第九阶段自动化测试，保证观察台 MVP 结构不会被后续改动破坏。
7. 新增项目进度记录，方便后续分析时回看每阶段的判断依据。

## 4. 本阶段改动

### 4.1 监控导出层

修改文件：

```text
core/monitoring_store.py
```

新增摘要字段：

```text
stage_report_count
stage_range
stable_workflow_file_count
generated_workflow_count
intentional_failure_workflow_count
success_rate
last_exported_at
```

这些字段让前端不需要临时推断项目状态，可以直接读取结构化监控数据。

### 4.2 Web 观察台

修改文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

观察台从 Stage 8 的基础展示升级为 8 个核心区域：

```text
总览
阶段
Workflow
失败诊断
能力图谱
对比实验
报告中心
扩展窗口
```

新增能力：

```text
阶段门禁
报告中心
对比实验预留
扩展窗口
导出时间显示
成功率显示
生成型 workflow 统计
失败样例 workflow 统计
```

### 4.3 自动化测试

新增文件：

```text
tests/test_stage9_unittest.py
```

测试覆盖：

```text
Dashboard Stage 9 模块是否存在
前端是否包含阶段门禁、报告、对比、扩展渲染函数
导出摘要是否包含 Stage 9 所需字段
Stage 9 验证报告和项目进度记录是否存在
```

### 4.4 项目记录

新增文件：

```text
docs/项目进度记录.md
```

用途：

```text
记录每一阶段已完成内容、当前判断、下一阶段建议和可追踪资产。
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python export_monitoring_data.py
python -m unittest discover -s tests -p "*unittest.py" -v
python -m http.server 8765 --bind 127.0.0.1
```

Dashboard 访问地址：

```text
http://127.0.0.1:8765/dashboard/
```

## 6. 验证结果

本轮验证结果：

```text
监控数据导出：通过
自动化测试：通过，39 tests OK
Dashboard 可视化检查：通过，Edge 无头截图已检查桌面与移动端
```

需要确认的关键指标：

```text
current_stage = 9
stage_report_count = 8
metacode_count = 15
stable_workflow_count = 10
workflow_file_count = 13
generated_workflow_count = 1
intentional_failure_workflow_count = 2
run_count = 407
success_run_count = 307
failure_run_count = 100
success_rate = 75.4%
unresolved_field_count = 0
```

测试过程中发现：

```text
当前生成型 workflow 实际为 1 条，因此 Stage 9 测试断言采用 generated_workflow_count >= 1。
```

这说明观察台没有夸大当前样本规模，而是按真实导出数据展示项目状态。

## 7. 阶段判断

Stage 9 的核心判断：

```text
MetaCode 已经从“能跑的原型”进入“能观察的工程原型”。
```

这意味着项目具备了继续扩展的基础：

```text
有可复用能力单元
有 workflow 执行和修复链路
有能力图谱
有监控导出
有可视化观察入口
有阶段验证报告
有项目进度记录
```

## 8. 当前不足

当前观察台仍然是静态 Web MVP：

1. 数据刷新依赖手动运行 `export_monitoring_data.py`。
2. Dashboard 通过静态 JSON 文件读取数据，还没有后端 API。
3. 对比实验区只是结构预留，还没有真实对比实验数据。
4. 失败诊断可以展示最近失败，但还不能按字段、metacode、workflow 交互钻取。
5. 多项目、多用户、权限和长期历史趋势还没有实现。

这些不足是合理的，因为 Stage 9 的目标是先把监控结构跑通，而不是一次性做完整平台。

## 9. 下一阶段建议

建议 Stage 10 进入：

```text
后端 API 与实时观察台阶段
```

优先顺序：

1. 增加一个轻量后端服务，统一提供 runs、failures、stages、workflows、graph、reports API。
2. Dashboard 从直接读取 JSON 改为读取 API。
3. 增加自动刷新和运行状态提示。
4. 为传统 AI 编程对比实验设计数据采集表。
5. 增加失败钻取页面：按 workflow、missing_fields、metacode、建议路径查看。

Stage 10 的目标应该是：

```text
让观察台从“展示导出结果”升级为“项目运行中的监控入口”。
```
