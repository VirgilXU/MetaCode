# MetaCode Stage 2 验证报告

> 日期：2026-06-08  
> 目标：将 V0.1 原型从 7 个元代码 / 3 条成功工作流，扩展到 15 个元代码 / 10 条成功工作流，并验证复用是否真实发生。

---

## 1. 阶段目标

本阶段验证的不是智能 Agent，而是 MetaCode 底层组合机制的可扩展性。

核心问题：

```text
新增少量元代码后，是否能组合出更多可执行 Workflow？
```

以及：

```text
同一个元代码是否会在多条 Workflow 中反复复用？
```

---

## 2. 本阶段新增内容

### 2.1 元代码数量

从 7 个扩展到 15 个。

新增 8 个：

```text
io.read_json_file
io.save_csv
transform.json_items_to_rows
data.pick_fields
data.sort_rows
data.filter_rows_contains
analysis.count_frequency
text.extract_keywords_basic
```

### 2.2 Workflow 数量

成功 Workflow 从 3 条扩展到 10 条。

新增 7 条：

```text
note_keywords_report
note_frequency_report
note_full_report
json_to_csv_export
json_pick_fields_csv
json_filter_active_csv
json_sort_by_priority_csv
```

保留 1 条故意失败 Workflow：

```text
broken_missing_clean_text
```

用于验证缺口定位。

---

## 3. 验证结果

运行命令：

```powershell
python analyze_reuse.py
python run_all_workflows.py
python -m unittest discover -s tests -p '*unittest.py' -v
```

结果：

```text
15 个元代码
10 条成功 Workflow
44 个 Workflow Step
11 个元代码被复用 2 次或以上
0 个闲置元代码
9 个 unittest 全部通过
```

---

## 4. 复用统计

```text
io.read_markdown_file              6
io.write_markdown                  6
text.clean_text_basic              5
io.read_json_file                  4
io.save_csv                        4
transform.json_items_to_rows       4
text.extract_markdown_headings     3
analysis.count_frequency           2
analysis.count_text_stats          2
text.extract_keywords_basic        2
text.simple_summary                2
data.filter_rows_contains          1
data.pick_fields                   1
data.sort_rows                     1
transform.headings_to_rows         1
```

---

## 5. 阶段结论

### 5.1 底层组合机制成立

`identity.yaml + run(context) + workflow.yaml + combiner` 的结构可以支撑多条 Workflow。

同一个元代码可以稳定出现在不同 Workflow 中。

### 5.2 复用已经出现

15 个元代码支撑了 10 条成功 Workflow，共 44 个步骤。

其中 11 个元代码被至少复用 2 次。

这说明项目已经从“单条脚本”进入“能力组合”阶段。

### 5.3 当前仍然不是智能系统

目前 Workflow 顺序仍然由人手写。

系统还没有自动完成：

```text
需求解析
差异定位
路径检索
能力推荐
Adapter 推荐
```

但底层数据结构已经为这些能力准备好了接口。

### 5.4 缺口定位雏形成立

故意失败 Workflow：

```text
io.read_markdown_file -> text.simple_summary
```

会失败，因为 `text.simple_summary` 需要：

```text
data.clean_text
```

但前一步只产出：

```text
data.raw_text
```

系统能明确指出缺失字段。

这就是后续“自动推荐缺失步骤”的基础。

---

## 6. 当前项目状态

```text
元代码：15
成功 Workflow：10
故意失败 Workflow：1
测试：9 个 unittest
注册表：registry/metacodes.json
成功日志：logs/run_log.jsonl
失败日志：logs/failure_log.jsonl
```

---

## 7. 下一阶段建议

Stage 3 不应继续盲目增加元代码。

下一步应该实现：

```text
基于 context_read / context_write 的自动步骤推荐
```

最小目标：

当 Workflow 失败时，系统不仅说：

```text
缺失 data.clean_text
```

还应该能扫描 registry 并推荐：

```text
建议插入 text.clean_text_basic
因为它可以写入 data.clean_text
```

这一步将把 MetaCode 从“可执行组合系统”推进到“半自动编排系统”。

---

## 8. 阶段判断

Stage 2 成功。

MetaCode 当前已经证明：

```text
少量能力元代码
可以通过不同 Workflow 配置
组合出多个可执行工程结果。
```

接下来真正值得攻的是：

```text
从缺失字段反推可补能力。
```
