# MetaCode Web 可视化 Dashboard 功能设计

> 日期：2026-06-10  
> 当前工程阶段：Stage 7 已完成  
> 本文目标：完整设计 MetaCode 的 Web 可视化监控系统，并为后续运行控制、智能分析、API、多人协作和多项目扩展预留接口。

---

## 1. 设计定位

MetaCode Web Dashboard 不是普通项目后台，也不是单纯日志查看器。

它的核心定位是：

```text
MetaCode 的工程观察台
```

它要让人清楚看到：

```text
系统现在有哪些能力
能力之间如何连接
Workflow 如何运行
失败发生在哪里
系统如何推荐和修复
每个阶段如何演进
哪些能力是核心节点
哪些路径值得复用
```

一句话：

```text
让 MetaCode 看见自己的成长过程。
```

---

## 2. 当前数据基础

Stage 7 已经完成可视化预处理层。

当前可直接读取的数据文件：

```text
monitoring/exports/dashboard_summary.json
monitoring/exports/runs.json
monitoring/exports/failures.json
monitoring/exports/stages.json
monitoring/exports/workflow_graph.json
monitoring/exports/reuse_summary.json
monitoring/exports/capability_graph.json
monitoring/exports/capability_graph_summary.json
```

当前 SQLite 数据库：

```text
monitoring/metacode_monitor.db
```

当前数据库表：

```text
runs
workflows
stages
metacodes
graph_edges
summaries
```

因此第一版 Web Dashboard 不需要先做复杂后端。

第一版建议：

```text
前端静态读取 monitoring/exports/*.json
```

后续再升级为：

```text
FastAPI / Flask / Node API + SQLite
```

---

## 3. 总体设计原则

## 3.1 先观察，后控制

第一版只做观察：

```text
展示状态
展示图谱
展示日志
展示失败
展示阶段演进
```

暂不直接在 UI 中执行：

```text
运行 Workflow
修复 Workflow
规划 Workflow
删除记录
编辑元代码
```

原因：

```text
先把系统状态看清楚，再开放操作入口。
```

---

## 3.2 先静态，后实时

第一版采用：

```text
读取 JSON export
手动刷新
```

后续再做：

```text
自动刷新
WebSocket
实时运行状态
```

---

## 3.3 先单项目，后多项目

第一版只监控当前项目：

```text
D:\Virgil\Virgil\元代码项目Software DNA\源码
```

后续预留：

```text
project_id
project_name
project_root
```

用于支持多个 MetaCode 项目。

---

## 3.4 先规则图谱，后语义图谱

当前能力图谱基于：

```text
context_read
context_write
```

后续可以扩展：

```text
Embedding 相似度
能力语义聚类
Workflow 相似度
自然语言需求匹配
```

---

## 4. 信息架构

建议 Web Dashboard 顶层导航：

```text
Overview
Workflows
Runs
Failures
Capability Graph
MetaCodes
Stages
Generated
Settings
```

中文界面可对应：

```text
总览
工作流
运行记录
失败诊断
能力图谱
元代码库
阶段演进
生成结果
设置
```

第一版最小页面：

```text
1. 总览页
2. Workflow 监控页
3. 失败诊断页
4. 能力图谱页
5. 阶段演进页
```

第二版再补：

```text
6. 元代码库页
7. 运行日志页
8. Generated 结果页
9. 设置页
```

---

## 5. 页面设计

## 5.1 总览页 Overview

### 目标

让用户一眼看到 MetaCode 当前健康状态。

### 数据源

```text
dashboard_summary.json
reuse_summary.json
capability_graph_summary.json
```

### 核心指标卡

```text
当前阶段 current_stage
元代码数量 metacode_count
稳定 Workflow 数 stable_workflow_count
Workflow 文件数 workflow_file_count
运行总数 run_count
成功运行数 success_run_count
失败运行数 failure_run_count
能力图谱边数 edge_count
字段数量 field_count
未解析字段 unresolved_field_count
```

### 推荐展示

```text
顶部：项目状态摘要
中部：成功/失败运行比例
中部：核心节点 Top 5
中部：桥接节点 Top 5
底部：最近一次运行
```

### 状态判断

可以用简单规则显示健康状态：

```text
unresolved_field_count = 0 -> healthy
failure_run_count > success_run_count -> warning
edge_count = 0 -> graph missing
latest_run.status = failed -> attention
```

### 后续扩展窗口

```text
阶段趋势图
测试通过率趋势
运行耗时趋势
失败率趋势
能力数量增长曲线
```

---

## 5.2 Workflow 监控页

### 目标

展示所有 Workflow 的结构、状态和生成来源。

### 数据源

```text
workflow_graph.json
runs.json
failures.json
```

### 列表字段

```text
workflow_id
name
status_type
steps
generated_from
inserted_steps
output_path
workflow_path
last_run_status
last_duration_ms
```

### Workflow 类型

```text
stable
intentional_failure
generated_fixed
generated_planned
```

### 详情面板

点击某个 Workflow 后展示：

```text
步骤链
每一步 metacode 的 category
每一步 context_read
每一步 context_write
最近运行记录
相关失败记录
相关 generated workflow
输出文件
```

### 可视化方式

第一版：

```text
垂直步骤链
```

后续：

```text
DAG 图
步骤耗时条
成功/失败标记
```

### 后续扩展窗口

```text
从 UI 运行 Workflow
从 UI 修复 Workflow
从 UI 规划 Workflow
比较原始 Workflow 与 generated Workflow
导出 Workflow 图片
```

---

## 5.3 运行记录页 Runs

### 目标

查看所有运行历史。

### 数据源

```text
runs.json
```

### 列表字段

```text
run_id
workflow_id
status
started_at
ended_at
duration_ms
steps_total
steps_success
failed_step
source_log
```

### 筛选条件

```text
status
workflow_id
failed_step
source_log
时间范围
```

### 详情内容

```text
完整 steps
outputs
reason
missing_fields
suggestions
context_keys
```

### 后续扩展窗口

```text
运行耗时趋势
慢 Workflow 排名
最近 N 次运行对比
按 Workflow 聚合成功率
```

---

## 5.4 失败诊断页 Failures

### 目标

集中展示失败、缺失字段、推荐和修复路径。

### 数据源

```text
failures.json
workflow_graph.json
```

### 列表字段

```text
workflow_id
failed_step
missing_fields
suggestions
ready / not ready
reason
duration_ms
```

### 详情内容

```text
失败原因
缺失字段
当前已有 context_keys
推荐元代码
推荐元代码 requires
推荐元代码 provides
是否 ready
score
```

### 重点交互

第一版只展示：

```text
建议插入什么
为什么推荐它
它还缺什么
```

后续可操作：

```text
一键生成 fixed workflow
一键生成 planned workflow
运行验证
保存修复记录
```

### 后续扩展窗口

```text
失败聚类
高频 missing_fields 排名
高频 failed_step 排名
自动修复成功率
失败到修复的路径回放
```

---

## 5.5 能力图谱页 Capability Graph

### 目标

展示元代码之间的连接关系，帮助理解系统能力结构。

### 数据源

```text
capability_graph.json
capability_graph_summary.json
reuse_summary.json
```

### 图节点

每个节点代表一个元代码：

```text
id
category
usage
in_degree
out_degree
bridge_score
reads
writes
```

### 图边

每条边代表一个字段连接：

```text
from
to
field
from_category
to_category
```

### 视觉编码

```text
节点大小：usage 或 degree
节点颜色：category
边标签：field
高亮：core_nodes
高亮：bridge_nodes
淡化：低使用节点
```

### 侧边信息面板

点击节点后展示：

```text
元代码 ID
类别
用途
读取字段
写入字段
使用次数
入度
出度
桥接分数
相关 Workflow
```

### 关键列表

```text
核心节点 Top 5
桥接节点 Top 5
孤立输出字段
未解析字段
输入字段
```

### 后续扩展窗口

```text
图布局保存
路径高亮
从字段反查 producer / consumer
显示路径评分
语义相似边
跨项目能力图谱
```

---

## 5.6 元代码库页 MetaCodes

### 目标

查看所有元代码身份证。

### 数据源

```text
registry/metacodes.json
capability_graph.json
reuse_summary.json
```

### 列表字段

```text
id
name
category
purpose
context_read
context_write
usage
bridge_score
tests
```

### 详情内容

```text
identity.yaml 内容
runner 路径
适用场景
不适用场景
constraints
failure_modes
相关 Workflow
上下游节点
```

### 后续扩展窗口

```text
在线编辑 identity
运行单个 metacode 测试
新增元代码向导
元代码质量评分
元代码版本历史
```

---

## 5.7 阶段演进页 Stages

### 目标

展示 MetaCode 从 Stage 2 到当前阶段的演进。

### 数据源

```text
stages.json
monitoring/stages/stage_N.json
docs/Stage N 验证报告.md
```

### 展示内容

```text
stage_id
title
status
report_path
report_size
updated_at
```

### 推荐布局

```text
左侧阶段时间线
右侧阶段报告摘要
底部关键指标变化
```

### 后续扩展窗口

```text
阶段目标结构化
阶段新增文件列表
阶段测试数量
阶段指标变化
阶段间 diff
阶段回滚点
```

---

## 5.8 Generated 结果页

### 目标

集中展示系统自动生成的 Workflow。

### 数据源

```text
workflow_graph.json
workflows/generated/*.yaml
runs.json
```

### 类型

```text
fixed workflow
planned workflow
```

### 展示内容

```text
generated workflow id
generated_from
inserted_steps
steps
verification_status
output_path
```

### 后续扩展窗口

```text
原始与生成 Workflow diff
接受/拒绝 generated Workflow
沉淀为 stable Workflow
生成原因解释
```

---

## 6. 第一版 MVP 范围

第一版 Web Dashboard 建议只做只读展示。

必须有：

```text
总览页
Workflow 监控页
失败诊断页
能力图谱页
阶段演进页
```

可以暂缓：

```text
运行 Workflow
修复 Workflow
规划 Workflow
编辑元代码
后端 API
用户系统
实时刷新
```

第一版目标：

```text
把 Stage 7 导出的 JSON 数据变成可浏览、可理解的页面。
```

---

## 7. 数据刷新设计

第一版：

```text
手动运行 python export_monitoring_data.py
前端刷新页面
```

第二版：

```text
Dashboard 提供刷新按钮
按钮调用后端 API 执行 export_monitoring_data.py
```

第三版：

```text
定时刷新
WebSocket 推送
运行中状态实时更新
```

---

## 8. API 预留设计

虽然第一版可以不做 API，但功能设计要预留接口。

建议未来 API：

```text
GET /api/status
GET /api/runs
GET /api/failures
GET /api/workflows
GET /api/metacodes
GET /api/capability-graph
GET /api/stages
GET /api/reuse-summary
POST /api/export-monitoring-data
POST /api/run-workflow
POST /api/fix-workflow
POST /api/plan-workflow
```

第一版前端数据读取方式：

```text
fetch('/monitoring/exports/dashboard_summary.json')
```

未来替换为：

```text
fetch('/api/status')
```

因此前端建议封装 data provider：

```text
dataProvider.getDashboardSummary()
dataProvider.getRuns()
dataProvider.getFailures()
dataProvider.getCapabilityGraph()
```

这样未来从静态 JSON 切换到 API 时，不需要重写页面。

---

## 9. 技术建议

## 9.1 前端

建议：

```text
Vite
React
TypeScript
```

图表建议：

```text
Recharts：指标图、趋势图
React Flow：Workflow 链路图
Sigma.js / Cytoscape.js / React Flow：能力图谱
```

第一版也可以先不用复杂图谱库。

能力图谱最小可用方案：

```text
节点列表 + 边列表 + 点击查看详情
```

等数据确认有价值，再升级为可交互图。

---

## 9.2 后端

第一版可以没有后端。

第二版建议：

```text
FastAPI
SQLite
```

原因：

```text
当前项目是 Python
已有 SQLite
FastAPI 适合快速暴露监控接口
```

---

## 10. 扩展窗口

必须预留这些扩展点：

## 10.1 多项目

预留字段：

```text
project_id
project_name
project_root
```

未来可以监控多个 MetaCode 项目。

---

## 10.2 多阶段指标趋势

预留：

```text
stage_metrics
```

未来记录：

```text
metacode_count
workflow_count
test_count
edge_count
failure_count
repair_success_count
```

---

## 10.3 智能分析

预留：

```text
recommendations
insights
warnings
```

未来用于显示：

```text
哪些能力过度依赖
哪些字段缺消费者
哪些 Workflow 经常失败
哪些元代码应该补测试
```

---

## 10.4 操作审计

未来如果 UI 可以执行操作，需要记录：

```text
operator
operation_type
target
before
after
created_at
```

用于回滚和复盘。

---

## 10.5 语义检索

未来可接入：

```text
Embedding
相似 Workflow 检索
相似元代码检索
自然语言需求解析
```

Dashboard 可以预留搜索框：

```text
Search by id / field / purpose / workflow / natural language
```

---

## 11. 页面实现优先级

建议顺序：

```text
1. 总览页
2. Workflow 监控页
3. 失败诊断页
4. 能力图谱页
5. 阶段演进页
6. 元代码库页
7. Generated 结果页
8. 操作按钮和 API
```

原因：

```text
先看整体
再看流程
再看失败
再看图谱
最后开放操作
```

---

## 12. 验收标准

Stage 8 第一版 Dashboard 完成后，应满足：

```text
能读取 monitoring/exports/*.json
能显示 current_stage = 7
能显示 15 个元代码
能显示 10 条稳定 Workflow
能显示运行成功/失败数量
能显示 Workflow 列表和步骤链
能显示失败记录和 suggestions
能显示能力图谱核心节点和桥接节点
能显示 Stage 2-7 阶段列表
页面刷新后数据不丢
```

不要求第一版完成：

```text
运行 Workflow
修复 Workflow
复杂图交互
实时刷新
编辑能力
多用户
```

---

## 13. 风险与控制

## 13.1 风险：页面做得太复杂

控制：

```text
第一版只读
少交互
少动画
先展示核心数据
```

---

## 13.2 风险：图谱难以阅读

控制：

```text
先做核心节点和桥接节点列表
再做可交互图
```

---

## 13.3 风险：日志太多

控制：

```text
默认显示最近 50 条
支持筛选
支持按 workflow 聚合
```

---

## 13.4 风险：数据源变化导致页面坏

控制：

```text
前端建立 data adapter
不要在组件里直接写死 JSON 字段路径
```

---

## 14. 最终设计结论

MetaCode Web Dashboard 第一版应该是：

```text
一个只读、轻量、面向工程观察的本地监控界面。
```

它的核心价值不是操作，而是让人看见：

```text
MetaCode 有哪些能力
Workflow 怎么组合
失败如何发生
系统如何修复
能力图谱如何连接
项目阶段如何演进
```

后续再逐步扩展为：

```text
可运行
可修复
可规划
可搜索
可分析
可协作
```

一句话：

```text
Stage 8 先做观察台，不急着做控制台。
```
