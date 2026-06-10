# MetaCode Stage 5 验证报告

> 日期：2026-06-08  
> 目标：实现多步补全路径搜索，从“单步修复”推进到“递归规划缺失字段的前置能力链”。

---

## 1. 阶段目标

Stage 4 已经实现：

```text
缺失字段 -> 推荐 ready 元代码 -> 插入一步 -> fixed Workflow
```

Stage 5 要验证：

```text
如果推荐元代码本身还缺前置输入，系统能不能继续向前搜索，生成多步补全链。
```

本阶段最小目标：

```text
缺 data.clean_text
-> text.clean_text_basic 能提供 data.clean_text
-> 但 text.clean_text_basic 需要 data.raw_text
-> io.read_markdown_file 能提供 data.raw_text
-> 当前 inputs.file_path 已满足
-> 规划 io.read_markdown_file -> text.clean_text_basic
```

---

## 2. 本阶段新增内容

### 2.1 新增路径规划器

新增文件：

```text
core/path_planner.py
```

核心能力：

```text
根据 missing_fields 反向搜索 provider
递归补齐 provider 的 context_read
生成有序 plan
生成 planned Workflow
执行 planned Workflow 验证
```

---

### 2.2 新增规划命令

新增文件：

```text
plan_workflow_fix.py
```

命令：

```powershell
python plan_workflow_fix.py workflows/broken_missing_summary_chain.yaml
```

---

### 2.3 新增多步失败样例

新增文件：

```text
workflows/broken_missing_summary_chain.yaml
```

原始步骤：

```text
text.simple_summary
io.write_markdown
```

失败原因：

```text
text.simple_summary 需要 data.clean_text
```

但当前 Context 只有：

```text
inputs.file_path
inputs.output_path
```

所以单步修复不够，必须规划：

```text
io.read_markdown_file
text.clean_text_basic
```

---

### 2.4 更新跳过列表

修改文件：

```text
run_all_workflows.py
analyze_reuse.py
tests/test_stage2_unittest.py
```

目的：

```text
故意失败 Workflow 不计入 10 条成功 Workflow 的稳定统计。
```

---

### 2.5 新增测试

新增文件：

```text
tests/test_stage5_unittest.py
```

测试覆盖：

```text
能规划两步补全链
能生成 planned yaml
planned workflow 步骤顺序正确
planned workflow 能成功运行并生成输出
无法解析字段时返回 not_planned
```

---

## 3. 验证命令

本阶段执行：

```powershell
python plan_workflow_fix.py workflows/broken_missing_summary_chain.yaml
python run_workflow.py workflows/generated/broken_missing_summary_chain.planned.yaml
python run_all_workflows.py
python analyze_reuse.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

---

## 4. 验证结果

### 4.1 规划命令结果

```json
{
  "status": "planned",
  "workflow_id": "broken_missing_summary_chain",
  "failed_step": "text.simple_summary",
  "inserted": [
    "io.read_markdown_file",
    "text.clean_text_basic"
  ],
  "verification_status": "success",
  "planned_steps": [
    "io.read_markdown_file",
    "text.clean_text_basic",
    "text.simple_summary",
    "io.write_markdown"
  ]
}
```

---

### 4.2 生成的 planned Workflow

```yaml
id: broken_missing_summary_chain_planned
name: Broken Missing Summary Chain Planned
inputs:
  file_path: examples/sample_note.md
  output_path: examples/outputs/planned_summary.md
steps:
  - io.read_markdown_file
  - text.clean_text_basic
  - text.simple_summary
  - io.write_markdown
planned_from: broken_missing_summary_chain
inserted_steps:
  - io.read_markdown_file
  - text.clean_text_basic
```

生成位置：

```text
workflows/generated/broken_missing_summary_chain.planned.yaml
```

---

### 4.3 planned Workflow 输出

输出文件：

```text
examples/outputs/planned_summary.md
```

内容为摘要报告，说明 planned Workflow 已经完整跑通。

---

### 4.4 全量测试结果

```text
Ran 21 tests in 1.367s
OK
```

---

### 4.5 原有成功 Workflow 统计保持稳定

```text
metacode_count: 15
workflow_count: 10
total_workflow_steps: 44
reused_metacode_count: 11
unused_metacode_count: 0
```

---

## 5. 阶段结论

Stage 5 成功。

MetaCode 当前已经从：

```text
单步补缺
```

推进到：

```text
多步补全路径搜索
```

现在系统可以处理：

```text
目标 step 缺字段
-> 候选 provider 也缺字段
-> 继续寻找 provider 的 provider
-> 生成有序补全链
-> 生成 planned Workflow
-> 自动验证 planned Workflow
```

这说明 MetaCode 的能力图谱雏形已经出现。

---

## 6. 当前边界

本阶段仍是规则级路径搜索，不是完整智能规划。

当前限制：

```text
只基于 context_read/context_write
搜索深度默认最多 4
没有候选质量评分
没有路径成本模型
没有语义相似度
没有 Adapter 自动插入
没有分支 Workflow
没有多目标最优规划
```

另外，当前规划器只解决“字段可达性”问题，不判断业务意图是否真的合理。

例如它能判断：

```text
data.clean_text 可以由 text.clean_text_basic 生成
```

但还不能判断：

```text
这个摘要是否符合用户真正想要的报告风格
```

---

## 7. 下一阶段建议

Stage 6 建议不要马上接自然语言，也不要急着上 Embedding。

下一阶段更应该做：

```text
能力图谱与路径评分
```

最小目标：

```text
扫描所有 metacode 的 context_read/context_write
构建 Capability Graph
统计 provider / consumer / bridge 节点
给每条规划路径计算成本
优先选择更短、更稳定、更常用的路径
```

建议新增：

```text
core/capability_graph.py
analyze_capability_graph.py
docs/Stage 6 验证报告.md
```

这样 MetaCode 会从“能找到一条路径”推进到：

```text
能分析路径质量，并开始知道哪些能力是核心节点、桥接节点、薄弱节点。
```

---

## 8. 阶段追踪

当前已有阶段报告：

```text
Stage 2 验证报告.md
Stage 3 验证报告.md
Stage 4 验证报告.md
Stage 5 验证报告.md
```

阶段报告机制继续保留。
