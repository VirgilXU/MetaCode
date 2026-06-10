# MetaCode Stage 4 验证报告

> 日期：2026-06-08  
> 目标：根据 Stage 3 的推荐结果，自动生成修复后的 Workflow 草案，并验证修复版能成功运行。

---

## 1. 阶段目标

Stage 3 已经实现：

```text
缺失字段 -> 推荐可补元代码
```

Stage 4 验证下一步：

```text
缺失字段 -> 推荐可补元代码 -> 自动插入步骤 -> 生成 fixed Workflow -> 运行验证
```

本阶段只处理最小场景：

```text
单个失败 step
单个 ready 推荐
把推荐 step 插入到失败 step 前
```

---

## 2. 本阶段新增内容

### 2.1 新增 Workflow 修复器

新增文件：

```text
core/workflow_fixer.py
```

核心能力：

```text
执行原始 Workflow
读取失败结果中的 suggestions
选择第一个 ready 推荐
推断失败 step
把推荐元代码插入失败 step 前
保存 fixed Workflow
执行 fixed Workflow 验证
```

---

### 2.2 新增修复命令

新增文件：

```text
fix_workflow.py
```

命令：

```powershell
python fix_workflow.py workflows/broken_missing_clean_text.yaml
```

---

### 2.3 新增生成目录

新增目录：

```text
workflows/generated/
```

生成文件：

```text
workflows/generated/broken_missing_clean_text.fixed.yaml
```

---

### 2.4 新增测试

新增文件：

```text
tests/test_stage4_unittest.py
```

测试覆盖：

```text
能生成 fixed yaml
插入步骤正确
fixed workflow 能成功运行
成功 workflow 不需要修复
```

---

## 3. 验证命令

本阶段执行：

```powershell
python fix_workflow.py workflows/broken_missing_clean_text.yaml
python run_workflow.py workflows/generated/broken_missing_clean_text.fixed.yaml
python run_all_workflows.py
python analyze_reuse.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

---

## 4. 验证结果

### 4.1 修复命令结果

```json
{
  "status": "fixed",
  "workflow_id": "broken_missing_clean_text",
  "failed_step": "text.simple_summary",
  "inserted": "text.clean_text_basic",
  "verification_status": "success",
  "fixed_steps": [
    "io.read_markdown_file",
    "text.clean_text_basic",
    "text.simple_summary"
  ]
}
```

---

### 4.2 生成的 fixed Workflow

```yaml
id: broken_missing_clean_text_fixed
name: Broken Missing Clean Text Fixed
inputs:
  file_path: examples/sample_note.md
  output_path: examples/outputs/broken.md
steps:
  - io.read_markdown_file
  - text.clean_text_basic
  - text.simple_summary
fixed_from: broken_missing_clean_text
inserted_steps:
  - text.clean_text_basic
```

---

### 4.3 fixed Workflow 运行结果

```text
workflow_id: broken_missing_clean_text_fixed
status: success
steps:
  - io.read_markdown_file
  - text.clean_text_basic
  - text.simple_summary
```

---

### 4.4 全量测试结果

```text
Ran 16 tests in 1.289s
OK
```

---

### 4.5 原有成功 Workflow 仍然稳定

```text
10 条成功 Workflow 全部通过
15 个元代码
44 个 Workflow step
11 个元代码被复用
0 个闲置元代码
```

---

## 5. 阶段结论

Stage 4 成功。

MetaCode 当前已经从：

```text
发现缺口
```

推进到：

```text
发现缺口 -> 推荐能力 -> 生成修复草案 -> 验证修复草案
```

这说明 MetaCode 已经具备了“半自动 Workflow 修复”的最小闭环。

---

## 6. 当前边界

本阶段仍然非常克制，只支持：

```text
一个缺失点
一个 ready 推荐
插入到失败 step 前
```

暂不支持：

```text
多步路径搜索
多个候选比较
Adapter 自动插入
语义相似度推荐
自动补输出步骤
复杂分支 Workflow
```

另外，本阶段生成的 fixed Workflow 只修复原始失败点。

例如 `broken_missing_clean_text` 原本没有 `io.write_markdown`，所以 fixed Workflow 也不会额外添加输出步骤。它只保证：

```text
text.simple_summary 所需的 data.clean_text 被补齐
```

---

## 7. 下一阶段建议

Stage 5 建议实现：

```text
多步补全路径搜索
```

当前 Stage 4 只能处理“推荐元代码已经 ready”的情况。

下一阶段可以测试更难一点的场景：

```text
目标 step 缺 data.summary
候选 A 能提供 data.summary
但候选 A 又需要 data.clean_text
候选 B 能提供 data.clean_text
候选 B 需要 data.raw_text
当前已有 data.raw_text
```

系统应该生成：

```text
候选 B -> 候选 A -> 目标 step
```

也就是从单步修复进入两步或多步修复。

---

## 8. 阶段追踪

本阶段继续遵守规则：

```text
每一阶段完成后，必须新增 docs/Stage N 验证报告.md
```

当前已有：

```text
Stage 2 验证报告.md
Stage 3 验证报告.md
Stage 4 验证报告.md
```
