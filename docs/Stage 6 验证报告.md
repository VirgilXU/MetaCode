# MetaCode Stage 6 验证报告

> 日期：2026-06-08  
> 目标：构建能力图谱，识别核心节点与桥接节点，并为补全路径提供基础评分。

---

## 1. 阶段目标

Stage 5 已经证明：

```text
系统可以从缺失字段反向搜索多步补全链。
```

Stage 6 要进一步回答：

```text
这些能力之间到底形成了怎样的图？
哪些能力是核心节点？
哪些能力是桥接节点？
一条补全路径的成本和质量能不能被初步评分？
```

本阶段仍然不做自然语言和 Embedding，继续夯实规则层能力图谱。

---

## 2. 本阶段新增内容

### 2.1 新增能力图谱模块

新增文件：

```text
core/capability_graph.py
```

核心能力：

```text
扫描 registry
读取每个 metacode 的 context_read/context_write
构建字段生产者 field_producers
构建字段消费者 field_consumers
构建 metacode -> metacode 的连接边
统计核心节点 core_nodes
统计桥接节点 bridge_nodes
统计 input_only_fields / unresolved_fields / orphan_outputs
计算路径评分 score_path
```

---

### 2.2 新增分析命令

新增文件：

```text
analyze_capability_graph.py
```

命令：

```powershell
python analyze_capability_graph.py
```

---

### 2.3 新增测试

新增文件：

```text
tests/test_stage6_unittest.py
```

测试覆盖：

```text
能力图谱能构建成功
图谱节点数量符合当前 registry
图谱存在连接边
没有未解析内部字段
核心节点包含高复用元代码
桥接节点包含 text.clean_text_basic
路径评分可用
未知节点会被拒绝评分
```

---

## 3. 验证命令

本阶段执行：

```powershell
python analyze_capability_graph.py
python run_all_workflows.py
python analyze_reuse.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

---

## 4. 验证结果

### 4.1 能力图谱统计

```text
metacode_count: 15
workflow_count: 10
field_count: 16
edge_count: 26
unresolved_fields: []
```

说明：

```text
当前 15 个元代码之间已经形成 26 条可连接关系。
所有内部字段都有可解释来源。
```

---

### 4.2 输入字段

当前 input-only 字段：

```text
inputs.fields
inputs.file_path
inputs.filter_field
inputs.filter_value
inputs.output_path
inputs.sort_field
```

这些字段不需要元代码生产，而是外部输入。

---

### 4.3 孤立输出字段

当前 orphan outputs：

```text
artifacts.output_file
data.frequency
data.keywords
data.summary
data.text_stats
```

说明：

这些字段目前主要作为终点输出，后续没有其他元代码继续消费它们。

这不是错误，但提示了一个方向：

```text
后续如果要做报告组装、质量评分或二次分析，可以围绕这些终点字段增加消费者。
```

---

## 5. 核心节点

当前 core nodes：

```text
io.read_markdown_file
io.write_markdown
text.clean_text_basic
io.save_csv
transform.json_items_to_rows
```

判断依据：

```text
Workflow 使用次数高
图谱连接度高
```

解释：

```text
io.read_markdown_file 是 Markdown 工作流入口。
io.write_markdown 是 Markdown 报告输出终点。
text.clean_text_basic 是 raw_text 到 clean_text 的关键桥。
transform.json_items_to_rows 是 JSON 到 rows 的关键桥。
io.save_csv 是 rows 到 CSV 输出的终点。
```

---

## 6. 桥接节点

当前 bridge nodes：

```text
text.clean_text_basic
transform.json_items_to_rows
io.save_csv
data.filter_rows_contains
data.pick_fields
```

其中最关键的是：

```text
text.clean_text_basic
```

原因：

```text
它读取 data.raw_text
写入 data.clean_text
下游被 summary / keyword / frequency / stats 等多个能力依赖
```

它是当前 Markdown 能力族群里的关键桥。

---

## 7. 路径评分

本阶段新增基础路径评分：

```text
score = reuse_score * 2 + bridge_score - length * 3
```

这不是最终评分模型，只是一个透明、可解释的起点。

### 7.1 Stage 5 planned chain

路径：

```text
io.read_markdown_file
text.clean_text_basic
```

评分：

```text
length: 2
reuse_score: 11
bridge_score: 18
score: 34
```

说明：

```text
这条路径虽然有两步，但两个节点都是高复用、高连接能力，所以评分较高。
```

### 7.2 Stage 4 fixed chain

路径：

```text
text.clean_text_basic
```

评分：

```text
length: 1
reuse_score: 5
bridge_score: 10
score: 17
```

说明：

```text
单步成本低，但覆盖的是较小补缺场景。
```

---

## 8. 全量测试结果

```text
Ran 26 tests in 1.944s
OK
```

原有成功 Workflow 仍然稳定：

```text
10 条成功 Workflow 全部通过
15 个元代码
44 个 Workflow step
11 个元代码被复用
0 个闲置元代码
```

---

## 9. 阶段结论

Stage 6 成功。

MetaCode 当前已经从：

```text
能找到一条补全路径
```

推进到：

```text
能分析能力图谱，并初步判断路径质量。
```

这一步非常关键，因为它让系统开始知道：

```text
哪些能力是入口
哪些能力是出口
哪些能力是桥
哪些字段是终点
哪些路径成本更低
```

MetaCode 的“能力空间分析”开始从文档概念进入可执行统计。

---

## 10. 当前边界

当前能力图谱仍是规则图谱，不是语义图谱。

限制：

```text
只基于 context_read/context_write 建边
没有字段类型系统
没有 Schema 兼容度评分
没有历史失败率评分
没有执行耗时评分
没有语义相似度
没有自动 Adapter 生成
```

当前评分也只是启发式：

```text
复用次数
连接度
路径长度
```

还不能代表真实工程质量。

---

## 11. 下一阶段建议

Stage 7 建议实现：

```text
Workflow 自动生成草案
```

原因：

Stage 5 和 Stage 6 已经具备：

```text
字段可达性搜索
能力图谱
路径评分
```

下一步可以尝试：

```text
给定目标输出字段
从 inputs 出发自动规划 Workflow
```

最小测试：

```text
已有 inputs.file_path 和 inputs.output_path
目标字段 artifacts.output_file
目标中间意图 data.summary
系统生成：
io.read_markdown_file
text.clean_text_basic
text.simple_summary
io.write_markdown
```

建议新增：

```text
core/workflow_generator.py
generate_workflow.py
tests/test_stage7_unittest.py
docs/Stage 7 验证报告.md
```

这会让 MetaCode 从“修复已有 Workflow”推进到：

```text
根据目标生成 Workflow 草案
```

---

## 12. 阶段追踪

当前已有阶段报告：

```text
Stage 2 验证报告.md
Stage 3 验证报告.md
Stage 4 验证报告.md
Stage 5 验证报告.md
Stage 6 验证报告.md
```

阶段报告机制继续保留。
