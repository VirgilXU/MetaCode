# MetaCode Stage 3 验证报告

> 日期：2026-06-08  
> 目标：实现“缺失字段 -> 推荐可补元代码”的最小能力，并将推荐结果接入失败日志和命令行输出。

---

## 1. 阶段目标

Stage 2 已经证明：

```text
15 个元代码可以组合出 10 条成功 Workflow。
```

Stage 3 要验证下一步：

```text
当 Workflow 失败时，系统能不能根据缺失字段反推可补能力。
```

本阶段不做自动修改 Workflow，只做推荐。

---

## 2. 本阶段新增内容

### 2.1 新增推荐器

新增文件：

```text
core/recommender.py
```

核心函数：

```text
suggest_for_missing_fields
```

输入：

```text
registry
context
missing_fields
exclude_ids
```

输出：

```text
候选 metacode
可补字段 provides
所需输入 requires
尚未满足的输入 unmet_inputs
是否可直接插入 ready
简单分数 score
```

---

### 2.2 接入执行器

修改文件：

```text
core/combiner.py
```

当某一步缺少 `context_read` 字段时，执行器现在会：

```text
1. 识别 missing_fields
2. 扫描 registry
3. 找到 context_write 可以补字段的元代码
4. 生成 suggestions
5. 写入 failure_log
6. 返回结构化失败结果
```

---

### 2.3 命令行输出增强

修改文件：

```text
run_workflow.py
```

失败时现在会输出：

```text
missing_fields
suggestions
```

---

### 2.4 新增测试

新增文件：

```text
tests/test_stage3_unittest.py
```

测试覆盖：

```text
推荐器能找到 text.clean_text_basic
完整失败 Workflow 能返回结构化 suggestions
候选能力前置输入缺失时会标记 ready=false
```

---

## 3. 验证命令

本阶段执行：

```powershell
python run_all_workflows.py
python run_workflow.py workflows/broken_missing_clean_text.yaml
python analyze_reuse.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

---

## 4. 验证结果

### 4.1 成功 Workflow

10 条成功 Workflow 全部通过。

```text
json_filter_active_csv
json_pick_fields_csv
json_sort_by_priority_csv
json_to_csv_export
note_frequency_report
note_full_report
note_health_report
note_keywords_report
note_outline_export
note_to_summary
```

---

### 4.2 测试结果

```text
Ran 12 tests in 0.952s
OK
```

---

### 4.3 复用统计保持稳定

```text
metacode_count: 15
workflow_count: 10
total_workflow_steps: 44
reused_metacode_count: 11
unused_metacode_count: 0
```

---

## 5. 关键失败样例

故意失败 Workflow：

```text
broken_missing_clean_text
```

步骤：

```text
io.read_markdown_file
text.simple_summary
```

失败原因：

```text
text.simple_summary missing context field(s): data.clean_text
```

系统推荐：

```text
text.clean_text_basic provides data.clean_text (ready)
```

结构化结果：

```json
{
  "missing_fields": [
    "data.clean_text"
  ],
  "suggestions": [
    {
      "metacode_id": "text.clean_text_basic",
      "provides": [
        "data.clean_text"
      ],
      "requires": [
        "data.raw_text"
      ],
      "unmet_inputs": [],
      "ready": true,
      "score": 10
    }
  ]
}
```

---

## 6. 阶段结论

Stage 3 成功。

MetaCode 当前已经具备：

```text
缺失字段识别
候选元代码检索
候选可用性判断
结构化推荐输出
失败日志记录
```

这意味着系统已经从“只能告诉你哪里坏了”，前进到：

```text
可以告诉你可能用哪个能力补上。
```

---

## 7. 当前边界

本阶段仍未实现：

```text
自动插入步骤
自动生成修复后的 Workflow
多步补全路径搜索
Adapter 推荐
语义相似度推荐
```

当前推荐只基于：

```text
context_write 是否覆盖 missing_fields
```

这是规则级推荐，不是语义级推荐。

---

## 8. 下一阶段建议

Stage 4 建议实现：

```text
根据 suggestions 生成修复后的 Workflow 草案
```

最小目标：

输入失败 Workflow：

```text
io.read_markdown_file
text.simple_summary
```

系统生成：

```text
io.read_markdown_file
text.clean_text_basic
text.simple_summary
```

并保存为：

```text
workflows/generated/broken_missing_clean_text.fixed.yaml
```

这一步会把 MetaCode 从“推荐能力”推进到“半自动修复 Workflow”。

---

## 9. 阶段追踪规则

从 Stage 3 开始，每一阶段测试完成后，都必须新增一份验证报告：

```text
docs/Stage N 验证报告.md
```

报告至少包含：

```text
阶段目标
新增内容
验证命令
验证结果
关键样例
阶段结论
当前边界
下一阶段建议
```

这条规则用于保证 MetaCode 不只积累代码，也持续积累流程数据、实验结果和失败经验。
