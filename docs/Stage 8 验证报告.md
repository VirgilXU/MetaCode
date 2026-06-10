# MetaCode Stage 8 验证报告

> 日期：2026-06-10  
> 目标：实现第一版 Web 可视化观察台，读取 Stage 7 的监控导出数据，展示 MetaCode 当前运行、Workflow、失败诊断、能力图谱和阶段演进。

---

## 1. 阶段目标

Stage 7 已经完成：

```text
monitoring/exports/*.json
SQLite 监控库
统一 runs / failures / stages / workflow graph / capability graph
```

Stage 8 的目标是：

```text
把这些机器可读数据变成可浏览、可理解的 Web Dashboard。
```

本阶段坚持第一版原则：

```text
先做观察台
不急着做控制台
```

也就是：

```text
只读展示
不直接运行 Workflow
不直接修复 Workflow
不编辑元代码
```

---

## 2. 本阶段新增内容

新增目录：

```text
dashboard/
```

新增文件：

```text
dashboard/index.html
dashboard/styles.css
dashboard/app.js
```

新增测试：

```text
tests/test_stage8_unittest.py
```

---

## 3. Dashboard 功能

第一版观察台包含 5 个主要区域：

```text
总览
Workflow 监控
失败诊断
能力图谱
阶段演进
```

---

## 4. 数据来源

页面直接读取：

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

当前没有后端 API。

前端通过 `fetch()` 读取静态 JSON。

---

## 5. 页面设计

### 5.1 总览

显示：

```text
当前阶段
元代码数量
稳定 Workflow 数量
能力图谱边数
运行记录数
成功运行数
失败运行数
未解析字段数
```

同时显示：

```text
成功/失败比例图
最近一次运行
```

---

### 5.2 Workflow 监控

显示所有 Workflow：

```text
stable
intentional_failure
generated_fixed
generated_planned
```

支持筛选：

```text
全部
稳定
生成
失败样例
```

点击 Workflow 后显示步骤链。

---

### 5.3 失败诊断

展示最近 8 条失败记录：

```text
workflow_id
failed_step
missing_fields
suggestion
reason
duration
```

这部分对应 Stage 3-5 的能力：

```text
缺失字段识别
推荐补缺能力
自动修复/规划前置数据
```

---

### 5.4 能力图谱

展示：

```text
核心节点
桥接节点
字段连接图
edge_count
field_count
```

当前图谱为第一版简化可视化：

```text
核心节点 + 桥接节点组成的小型 SVG 连接图
```

后续可升级为完整可交互图。

---

### 5.5 阶段演进

展示 Stage 报告时间线：

```text
Stage 2
Stage 3
Stage 4
Stage 5
Stage 6
Stage 7
Stage 8
```

用于把项目进展从代码隐藏状态变成可见状态。

---

## 6. 设计风格

本阶段采用工程监控风格：

```text
左侧导航
顶部状态条
指标卡
表格
诊断卡片
节点列表
时间线
```

视觉方向：

```text
克制
清晰
偏工程工具
不做营销页
不做花哨动画
```

配色避免单一深蓝/紫色，采用：

```text
暖灰背景
墨色文字
青绿状态色
琥珀/红色辅助色
少量蓝紫区分类别
```

---

## 7. 运行方式

先刷新监控数据：

```powershell
python export_monitoring_data.py
```

启动本地服务：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

访问：

```text
http://127.0.0.1:8765/dashboard/
```

---

## 8. 验证方式

本阶段执行：

```powershell
python export_monitoring_data.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

HTTP 验证：

```text
GET /dashboard/ -> 200
GET /dashboard/app.js -> 200
GET /monitoring/exports/dashboard_summary.json -> 200
```

浏览器渲染验证：

```text
Chrome headless desktop screenshot
Chrome headless mobile screenshot
```

确认：

```text
页面非空
Stage 7/8 指标可显示
元代码数量可显示
Workflow 表格可显示
能力图谱可显示
移动宽度无明显挤压
```

---

## 9. 测试结果

全量测试：

```text
Ran 35 tests
OK
```

新增 Stage 8 测试覆盖：

```text
dashboard/index.html 存在
dashboard/styles.css 存在
dashboard/app.js 存在
关键页面 section 存在
关键 JSON 数据源被引用
响应式 CSS 存在
```

---

## 10. 当前边界

本阶段仍未实现：

```text
后端 API
运行 Workflow 按钮
修复 Workflow 按钮
规划 Workflow 按钮
完整交互式能力图谱
实时刷新
日志分页
多项目监控
```

当前是第一版只读观察台。

---

## 11. 下一阶段建议

Stage 9 建议做：

```text
Dashboard 数据交互增强
```

优先级：

```text
1. runs / failures 分页与筛选
2. Workflow 详情增强
3. 能力图谱节点详情
4. 点击节点查看上下游
5. Generated Workflow diff
```

暂时仍不建议直接做控制按钮。

先把观察体验打磨稳定，再进入控制台。

---

## 12. 阶段结论

Stage 8 成功。

MetaCode 当前已经具备：

```text
可执行系统
可诊断系统
可修复系统
可规划系统
可分析系统
可监控数据层
Web 观察台
```

这意味着 MetaCode 不再只是命令行实验原型。

它已经有了第一版可视化界面。
