# MetaCode Stage 15 验证报告

## 1. 阶段名称

第十五阶段：测试副作用隔离与验证基线整理。

Stage 15 接在 Stage 14 的一键修复 API 与修复详情页之后，目标不是继续扩展业务功能，而是把测试体系从“都写真实项目状态”推进到“项目状态验证”和“隔离行为验证”分层。

## 2. 测试日期

2026-06-12

## 3. 阶段目标

Stage 15 的核心目标：

```text
减少测试对 logs/ 和 monitoring/exports/ 的副作用，让后续开发能更快、更清楚地判断行为是否正确。
```

具体目标包括：

1. 明确哪些测试会刷新真实项目状态。
2. 明确哪些测试适合高频隔离运行。
3. 建立一个可复用的隔离测试样板。
4. 验证 repair event 显式 repair_id 绑定不需要文件写入。
5. 验证 fixed / planned 修复逻辑可以在临时项目副本中运行。
6. 更新测试策略文档和项目进度记录。

## 4. 本阶段改动

### 4.1 测试策略文档

新增文件：

```text
docs/测试策略草案.md
```

新增内容：

```text
测试总目标
测试分层
测试副作用规则
推荐测试命令
当前测试基线
现有测试分层清单
Stage 15 阶段边界建议
```

### 4.2 隔离测试样板

新增文件：

```text
tests/test_stage15_unittest.py
```

覆盖内容：

```text
显式 repair_id 绑定 failure 和 verification
Stage 13 旧推断逻辑兼容
fix_workflow 在临时项目副本中运行
plan_workflow_fix 在临时项目副本中运行
主项目 logs/run_log.jsonl 和 logs/failure_log.jsonl 不被隔离测试写入
```

隔离方式：

```text
测试临时复制 metacodes/
测试临时复制 workflows/
测试临时复制 examples/
修复生成文件和日志只写入临时目录
测试结束自动删除临时目录
```

### 4.3 项目记录

修改文件：

```text
docs/项目进度记录.md
```

记录内容：

```text
Stage 15 当前进展
测试基线结果
隔离测试样板
现有测试分层清单
下一步测试整理方向
```

## 5. 验证方式

本阶段使用以下命令验证：

```powershell
python -m unittest tests.test_stage15_unittest -v
python -m unittest discover -s tests -p "*unittest.py" -v
node --check dashboard\app.js
```

## 6. 验证结果

本轮验证结果：

```text
Stage 15 隔离测试：通过，4 tests OK
全量自动化测试：通过，75 tests OK
Dashboard JS 语法检查：通过
```

关键判断：

```text
repair event 显式 repair_id 绑定可在内存中测试
fixed / planned 修复副作用可被限制在临时项目副本
现有项目状态验证仍保留，可用于阶段收尾
Dashboard 脚本语法有效
```

## 7. 阶段判断

Stage 15 的阶段判断：

```text
MetaCode 已经具备第一版测试分层基线，后续可以优先新增隔离行为测试，减少高频开发时对项目历史日志和监控导出的污染。
```

## 8. 当前不足

Stage 15 仍是测试基线 MVP：

1. 现有历史测试大多仍会写真实 `logs/` 或刷新 `monitoring/exports/`。
2. 只有 repair event / repair workflow 形成了隔离测试样板。
3. 还没有统一测试 fixture 工具模块。
4. 还没有命令级别区分 quick / full / stateful test suites。
5. Dashboard 仍以语法检查和人工检查为主，没有完整浏览器自动化回归。

## 9. 下一阶段建议

建议 Stage 16 做：

```text
对比实验记录器 MVP
```

优先任务：

1. 设计 MetaCode vs 传统 AI 编程的实验记录结构。
2. 记录同一任务的耗时、失败次数、返工次数和可复用资产增量。
3. 增加最小 JSON 或 Markdown 实验记录。
4. Dashboard 预留对比实验数据读取入口。
5. 用一到两个小任务验证 MetaCode 的复用收益。
