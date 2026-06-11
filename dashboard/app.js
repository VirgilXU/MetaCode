const API_BASE = "/api";
const STATIC_EXPORT_BASE = "../monitoring/exports";
const REFRESH_INTERVAL_MS = 30000;

const files = {
  summary: "dashboard_summary.json",
  runs: "runs.json",
  failures: "failures.json",
  stages: "stages.json",
  workflows: "workflow_graph.json",
  repairs: "repair_metrics.json",
  reuse: "reuse_summary.json",
  graph: "capability_graph.json",
  graphSummary: "capability_graph_summary.json",
};

const state = {
  data: null,
  dataSource: "unknown",
  lastApiError: null,
  lastRefreshAt: null,
  workflowFilter: "all",
  selectedWorkflowId: null,
  refreshTimer: null,
};

const categoryColors = {
  io: "#15847f",
  text: "#6257a6",
  transform: "#b87818",
  data: "#2e74a8",
  analysis: "#b64b45",
  control: "#6d7b44",
  adapter: "#8b5e34",
};

const comparisonItems = [
  {
    title: "可复用资产",
    metacode: "沉淀为 metacode、workflow、报告和图谱。",
    traditional: "更多依赖单次提示词和即时上下文。",
    status: "优势明显",
  },
  {
    title: "失败修复",
    metacode: "能从 missing_fields 追踪缺口并生成修复路径。",
    traditional: "通常靠重新描述问题或手动粘贴错误。",
    status: "已验证",
  },
  {
    title: "阶段记忆",
    metacode: "每阶段有验证报告和监控数据。",
    traditional: "容易散落在聊天记录和临时代码里。",
    status: "持续增强",
  },
  {
    title: "探索速度",
    metacode: "前期需要定义身份、字段和组合规则。",
    traditional: "早期生成速度更快。",
    status: "短板保留",
  },
];

const extensionItems = [
  {
    title: "后端 API",
    body: "已提供本地 API 服务，Dashboard 可以从接口读取监控数据。",
    tag: "Stage 10",
  },
  {
    title: "实时刷新",
    body: "观察台每 30 秒自动刷新一次，也可以手动刷新。",
    tag: "Stage 10",
  },
  {
    title: "对比实验采集器",
    body: "记录同一任务在 MetaCode 与传统 AI 编程中的耗时、失败率和返工次数。",
    tag: "预留",
  },
  {
    title: "智能告警",
    body: "当失败集中在某个 metacode、字段或 workflow 时主动提示。",
    tag: "预留",
  },
];

async function loadJson(url) {
  const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`);
  if (!response.ok) throw new Error(`Failed to load ${url}`);
  return response.json();
}

async function loadFromApi() {
  const payload = await loadJson(`${API_BASE}/monitoring`);
  return {
    summary: payload.summary,
    runs: payload.runs,
    failures: payload.failures,
    stages: payload.stages,
    workflows: payload.workflows,
    repairs: payload.repairs || buildRepairMetrics(payload.runs || [], payload.workflows || []),
    reuse: payload.reuse,
    graph: payload.graph,
    graphSummary: payload.graphSummary,
    diagnostics: payload.diagnostics,
    api: payload.api,
  };
}

async function loadFromStaticExports() {
  const entries = await Promise.all(
    Object.entries(files).map(async ([key, file]) => [key, await loadJson(`${STATIC_EXPORT_BASE}/${file}`)]),
  );
  const data = Object.fromEntries(entries);
  return {
    ...data,
    diagnostics: buildDiagnostics(data.failures || []),
    repairs: data.repairs || buildRepairMetrics(data.runs || [], data.workflows || []),
    api: {
      mode: "static-fallback",
      version: "stage12-compatible",
      endpoints: Object.values(files).map((file) => `${STATIC_EXPORT_BASE}/${file}`),
    },
  };
}

async function loadData() {
  try {
    const apiData = await loadFromApi();
    state.dataSource = "api";
    state.lastApiError = null;
    return apiData;
  } catch (error) {
    state.dataSource = "static";
    state.lastApiError = error.message;
    return loadFromStaticExports();
  }
}

function sortedRows(counter, countKey = "failure_count") {
  return Object.values(counter).sort((left, right) => {
    const countDelta = (right[countKey] || 0) - (left[countKey] || 0);
    if (countDelta !== 0) return countDelta;
    return String(left.id || left.field || "").localeCompare(String(right.id || right.field || ""));
  });
}

function percent(successCount, attemptCount) {
  return attemptCount ? Number(((successCount / attemptCount) * 100).toFixed(1)) : 0;
}

function inferRepairStrategy(workflowId, workflow = {}) {
  if (workflow.status_type === "generated_fixed" || workflowId.endsWith("_fixed")) return "fixed";
  if (workflow.status_type === "generated_planned" || workflowId.endsWith("_planned")) return "planned";
  return null;
}

function inferRepairSource(workflowId, strategy, workflow = {}) {
  if (workflow.generated_from) return workflow.generated_from;
  const suffix = `_${strategy}`;
  return workflowId.endsWith(suffix) ? workflowId.slice(0, -suffix.length) : workflowId;
}

function buildRepairMetrics(runs, workflows) {
  const workflowById = Object.fromEntries((workflows || []).map((workflow) => [workflow.workflow_id, workflow]));
  const byStrategy = {};
  const byWorkflow = {};
  const recentAttempts = [];

  (runs || []).forEach((run) => {
    const workflowId = run.workflow_id || "";
    const workflow = workflowById[workflowId] || {};
    const strategy = inferRepairStrategy(workflowId, workflow);
    if (!strategy) return;

    const sourceWorkflowId = inferRepairSource(workflowId, strategy, workflow);
    const success = run.status === "success";
    const statusKey = success ? "success_count" : "failed_count";

    const strategyRow = byStrategy[strategy] || {
      id: strategy,
      strategy,
      attempt_count: 0,
      success_count: 0,
      failed_count: 0,
      repair_workflows: {},
      source_workflows: {},
      latest_status: "",
    };
    strategyRow.attempt_count += 1;
    strategyRow[statusKey] += 1;
    strategyRow.repair_workflows[workflowId] = (strategyRow.repair_workflows[workflowId] || 0) + 1;
    strategyRow.source_workflows[sourceWorkflowId] = (strategyRow.source_workflows[sourceWorkflowId] || 0) + 1;
    strategyRow.latest_status = run.status || "unknown";
    byStrategy[strategy] = strategyRow;

    const workflowRow = byWorkflow[sourceWorkflowId] || {
      id: sourceWorkflowId,
      source_workflow_id: sourceWorkflowId,
      attempt_count: 0,
      success_count: 0,
      failed_count: 0,
      strategies: {},
      repair_workflows: {},
      latest_repair_workflow_id: "",
      latest_status: "",
    };
    workflowRow.attempt_count += 1;
    workflowRow[statusKey] += 1;
    workflowRow.strategies[strategy] = (workflowRow.strategies[strategy] || 0) + 1;
    workflowRow.repair_workflows[workflowId] = (workflowRow.repair_workflows[workflowId] || 0) + 1;
    workflowRow.latest_repair_workflow_id = workflowId;
    workflowRow.latest_status = run.status || "unknown";
    byWorkflow[sourceWorkflowId] = workflowRow;

    recentAttempts.push({
      run_id: run.run_id,
      workflow_id: workflowId,
      source_workflow_id: sourceWorkflowId,
      strategy,
      status: run.status || "unknown",
      ended_at: run.ended_at,
      duration_ms: run.duration_ms || 0,
    });
  });

  Object.values(byStrategy).forEach((row) => {
    row.success_rate = percent(row.success_count, row.attempt_count);
    row.repair_workflow_count = Object.keys(row.repair_workflows).length;
    row.source_workflow_count = Object.keys(row.source_workflows).length;
  });
  Object.values(byWorkflow).forEach((row) => {
    row.success_rate = percent(row.success_count, row.attempt_count);
    row.repair_workflow_count = Object.keys(row.repair_workflows).length;
  });

  const byStrategyRows = Object.values(byStrategy).sort((left, right) => {
    const countDelta = (right.attempt_count || 0) - (left.attempt_count || 0);
    if (countDelta !== 0) return countDelta;
    return left.strategy.localeCompare(right.strategy);
  });
  const byWorkflowRows = Object.values(byWorkflow).sort((left, right) => {
    const countDelta = (right.attempt_count || 0) - (left.attempt_count || 0);
    if (countDelta !== 0) return countDelta;
    return left.source_workflow_id.localeCompare(right.source_workflow_id);
  });
  const attemptCount = byStrategyRows.reduce((total, row) => total + row.attempt_count, 0);
  const successCount = byStrategyRows.reduce((total, row) => total + row.success_count, 0);
  const fixedRow = byStrategy.fixed || {};
  const plannedRow = byStrategy.planned || {};

  return {
    summary: {
      status: "computed",
      attempt_count: attemptCount,
      success_count: successCount,
      failed_count: attemptCount - successCount,
      repair_success_rate: percent(successCount, attemptCount),
      fixed_attempt_count: fixedRow.attempt_count || 0,
      fixed_success_count: fixedRow.success_count || 0,
      fixed_success_rate: percent(fixedRow.success_count || 0, fixedRow.attempt_count || 0),
      planned_attempt_count: plannedRow.attempt_count || 0,
      planned_success_count: plannedRow.success_count || 0,
      planned_success_rate: percent(plannedRow.success_count || 0, plannedRow.attempt_count || 0),
      source_workflow_count: byWorkflowRows.length,
      repair_workflow_count: new Set(recentAttempts.map((attempt) => attempt.workflow_id)).size,
      latest_attempt: recentAttempts[recentAttempts.length - 1] || null,
    },
    by_strategy: byStrategyRows,
    by_workflow: byWorkflowRows,
    recent_attempts: recentAttempts.slice(-8).reverse(),
  };
}

function buildDiagnostics(failures) {
  const byField = {};
  const byWorkflow = {};
  const byMetacode = {};
  let missingFieldMentions = 0;
  let suggestionCount = 0;
  let readySuggestionCount = 0;

  failures.forEach((failure) => {
    const workflowId = failure.workflow_id || "unknown";
    const failedStep = failure.failed_step || "unknown";
    const reason = failure.reason || "";
    const missingFields = failure.missing_fields || [];
    const suggestions = failure.suggestions || [];

    const workflowRow = byWorkflow[workflowId] || {
      id: workflowId,
      workflow_id: workflowId,
      failure_count: 0,
      failed_steps: {},
      missing_fields: {},
      suggested_metacodes: {},
      ready_suggestion_count: 0,
      latest_reason: "",
    };
    workflowRow.failure_count += 1;
    workflowRow.failed_steps[failedStep] = (workflowRow.failed_steps[failedStep] || 0) + 1;
    workflowRow.latest_reason = reason;
    byWorkflow[workflowId] = workflowRow;

    missingFields.forEach((field) => {
      missingFieldMentions += 1;
      workflowRow.missing_fields[field] = (workflowRow.missing_fields[field] || 0) + 1;
      const fieldRow = byField[field] || {
        field,
        failure_count: 0,
        workflows: {},
        suggested_metacodes: {},
        ready_suggestion_count: 0,
        latest_reason: "",
      };
      fieldRow.failure_count += 1;
      fieldRow.workflows[workflowId] = (fieldRow.workflows[workflowId] || 0) + 1;
      fieldRow.latest_reason = reason;
      byField[field] = fieldRow;
    });

    suggestions.forEach((suggestion) => {
      const metacodeId = suggestion.metacode_id || "unknown";
      const ready = Boolean(suggestion.ready);
      suggestionCount += 1;
      if (ready) {
        readySuggestionCount += 1;
        workflowRow.ready_suggestion_count += 1;
      }
      workflowRow.suggested_metacodes[metacodeId] = (workflowRow.suggested_metacodes[metacodeId] || 0) + 1;
      const metacodeRow = byMetacode[metacodeId] || {
        id: metacodeId,
        metacode_id: metacodeId,
        suggestion_count: 0,
        ready_count: 0,
        workflows: {},
        missing_fields: {},
      };
      metacodeRow.suggestion_count += 1;
      if (ready) metacodeRow.ready_count += 1;
      metacodeRow.workflows[workflowId] = (metacodeRow.workflows[workflowId] || 0) + 1;
      missingFields.forEach((field) => {
        metacodeRow.missing_fields[field] = (metacodeRow.missing_fields[field] || 0) + 1;
        if (byField[field]) {
          byField[field].suggested_metacodes[metacodeId] = (byField[field].suggested_metacodes[metacodeId] || 0) + 1;
          if (ready) byField[field].ready_suggestion_count += 1;
        }
      });
      byMetacode[metacodeId] = metacodeRow;
    });
  });

  const byFieldRows = sortedRows(byField);
  const byWorkflowRows = sortedRows(byWorkflow);
  const byMetacodeRows = Object.values(byMetacode).sort((left, right) => {
    const countDelta = (right.suggestion_count || 0) - (left.suggestion_count || 0);
    if (countDelta !== 0) return countDelta;
    return String(left.metacode_id).localeCompare(String(right.metacode_id));
  });

  return {
    summary: {
      failure_count: failures.length,
      workflow_failure_count: byWorkflowRows.length,
      missing_field_mentions: missingFieldMentions,
      unique_missing_field_count: byFieldRows.length,
      suggestion_count: suggestionCount,
      ready_suggestion_count: readySuggestionCount,
      top_field: byFieldRows[0] || null,
      top_workflow: byWorkflowRows[0] || null,
      top_metacode: byMetacodeRows[0] || null,
      repair_success_rate: null,
      repair_success_rate_status: "reserved",
    },
    by_field: byFieldRows,
    by_workflow: byWorkflowRows,
    by_metacode: byMetacodeRows,
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value ?? 0);
}

function formatMs(value) {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(1)} ms`;
}

function formatTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function shortPath(path) {
  if (!path) return "-";
  return String(path).split(/[\\/]/).slice(-2).join("/");
}

function fileName(path) {
  if (!path) return "";
  return String(path).split(/[\\/]/).pop();
}

function isAutoRefreshEnabled() {
  return document.querySelector("#autoRefreshToggle")?.checked ?? true;
}

function setHealth(summary) {
  const pill = document.querySelector("#healthPill");
  const healthy = summary.unresolved_field_count === 0 && summary.current_stage >= 12;
  const source = state.dataSource === "api" ? "API" : "Static";
  pill.textContent = healthy ? `Stage 12 ${source}` : "Needs Review";
  pill.className = `status-pill ${healthy ? "ok" : "warn"}`;
}

function renderMetrics(summary) {
  const metrics = [
    ["当前阶段", `Stage ${summary.current_stage ?? "-"}`, `${summary.stage_report_count ?? 0} 份阶段报告`],
    ["成功率", `${summary.success_rate ?? 0}%`, `${formatNumber(summary.run_count)} 条运行记录`],
    ["元代码", summary.metacode_count, "可组合能力单元"],
    ["Workflow", summary.workflow_file_count, `${summary.generated_workflow_count ?? 0} 条生成型路径`],
    ["稳定 Workflow", summary.stable_workflow_count, "复用基线"],
    ["能力图谱边", summary.edge_count, `${summary.field_count} 个字段`],
    ["修复成功率", `${summary.repair_success_rate ?? 0}%`, `${formatNumber(summary.repair_attempt_count ?? 0)} 次验证`],
    ["未解析字段", summary.unresolved_field_count, "字段完整性检查"],
  ];

  document.querySelector("#metricGrid").innerHTML = metrics
    .map(
      ([label, value, note]) => `
        <article class="metric-card">
          <div class="metric-label">${escapeHtml(label)}</div>
          <div class="metric-value">${typeof value === "number" ? formatNumber(value) : escapeHtml(value)}</div>
          <div class="metric-note">${escapeHtml(note)}</div>
        </article>
      `,
    )
    .join("");
}

function renderRunStatus(summary) {
  const total = Math.max(summary.success_run_count + summary.failure_run_count, 1);
  const successPct = Math.round((summary.success_run_count / total) * 100);
  const donut = document.querySelector("#runDonut");
  donut.style.setProperty("--success", `${successPct}%`);

  document.querySelector("#runBreakdown").innerHTML = `
    <div class="kv-row"><span>成功率</span><span class="value-strong">${successPct}%</span></div>
    <div class="kv-row"><span>成功运行</span><span>${formatNumber(summary.success_run_count)}</span></div>
    <div class="kv-row"><span>失败运行</span><span>${formatNumber(summary.failure_run_count)}</span></div>
    <div class="kv-row"><span>总运行</span><span>${formatNumber(summary.run_count)}</span></div>
  `;
}

function renderLatestRun(summary) {
  const run = summary.latest_run;
  if (!run) {
    document.querySelector("#latestRun").innerHTML = `<div class="empty-state">暂无运行记录</div>`;
    return;
  }
  document.querySelector("#latestRun").innerHTML = `
    <div class="kv-row"><span>Workflow</span><span class="value-strong">${escapeHtml(run.workflow_id)}</span></div>
    <div class="kv-row"><span>状态</span><span>${escapeHtml(run.status)}</span></div>
    <div class="kv-row"><span>耗时</span><span>${formatMs(run.duration_ms)}</span></div>
    <div class="kv-row"><span>步骤</span><span>${run.steps_success}/${run.steps_total}</span></div>
    <div class="kv-row"><span>输出</span><span class="mono">${escapeHtml(shortPath(Object.values(run.outputs || {})[0]))}</span></div>
  `;
}

function renderStageGates(summary) {
  const gates = [
    {
      label: "阶段报告",
      value: `${summary.stage_report_count ?? 0} 份`,
      ok: summary.current_stage >= 12,
      note: "第十二阶段报告进入监控范围",
    },
    {
      label: "字段完整性",
      value: `${summary.unresolved_field_count} 个缺口`,
      ok: summary.unresolved_field_count === 0,
      note: "能力图谱字段全部可解析",
    },
    {
      label: "本地 API",
      value: state.dataSource === "api" ? "已连接" : "静态回退",
      ok: state.dataSource === "api",
      note: state.dataSource === "api" ? "Dashboard 正在读取 API" : "API 未启动时仍可读取 JSON",
    },
    {
      label: "自动刷新",
      value: isAutoRefreshEnabled() ? "30 秒" : "已暂停",
      ok: isAutoRefreshEnabled(),
      note: "观察台可持续刷新当前项目状态",
    },
  ];

  document.querySelector("#stageGateGrid").innerHTML = gates
    .map(
      (gate) => `
        <div class="gate-item ${gate.ok ? "ok" : "warn"}">
          <div class="tag ${gate.ok ? "green" : "amber"}">${gate.ok ? "通过" : "待补"}</div>
          <div class="value-strong">${escapeHtml(gate.label)}</div>
          <div>${escapeHtml(gate.value)}</div>
          <div class="small-label">${escapeHtml(gate.note)}</div>
        </div>
      `,
    )
    .join("");
}

function renderApiStatus() {
  const api = state.data?.api || {};
  const endpoints = api.endpoints || [];
  const cards = [
    {
      label: "数据模式",
      value: state.dataSource === "api" ? "API 服务" : "静态 JSON",
      note: state.dataSource === "api" ? "实时读取 /api/monitoring" : state.lastApiError || "读取 monitoring/exports",
      tag: state.dataSource === "api" ? "green" : "amber",
    },
    {
      label: "API 版本",
      value: api.version || "-",
      note: "Stage 11 本地服务",
      tag: "blue",
    },
    {
      label: "刷新策略",
      value: isAutoRefreshEnabled() ? "30 秒自动" : "手动刷新",
      note: `最近刷新 ${formatTime(state.lastRefreshAt)}`,
      tag: isAutoRefreshEnabled() ? "green" : "amber",
    },
    {
      label: "可用端点",
      value: `${endpoints.length} 个`,
      note: endpoints.slice(0, 3).join("  "),
      tag: "teal",
    },
  ];

  document.querySelector("#apiGrid").innerHTML = cards
    .map(
      (card) => `
        <article class="api-card">
          <div class="tag ${card.tag}">${escapeHtml(card.label)}</div>
          <div class="value-strong">${escapeHtml(card.value)}</div>
          <code>${escapeHtml(card.note)}</code>
        </article>
      `,
    )
    .join("");
}

function topKeys(record, limit = 3) {
  return Object.entries(record || {})
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, limit)
    .map(([key, count]) => `${key} (${count})`)
    .join(", ");
}

function renderDiagnosticMetrics() {
  const diagnostics = state.data.diagnostics || buildDiagnostics(state.data.failures || []);
  const summary = diagnostics.summary || {};
  const metrics = [
    ["失败记录", summary.failure_count, "进入诊断聚合的失败样本"],
    ["影响 Workflow", summary.workflow_failure_count, "出现过失败的 workflow"],
    ["缺失字段", summary.unique_missing_field_count, `${summary.missing_field_mentions || 0} 次字段缺口`],
    ["推荐能力", summary.suggestion_count, `${summary.ready_suggestion_count || 0} 次 ready`],
  ];

  document.querySelector("#diagnosticMetricGrid").innerHTML = metrics
    .map(
      ([label, value, note]) => `
        <article class="metric-card">
          <div class="metric-label">${escapeHtml(label)}</div>
          <div class="metric-value">${formatNumber(value)}</div>
          <div class="metric-note">${escapeHtml(note)}</div>
        </article>
      `,
    )
    .join("");
}

function renderDiagnosticList(selector, rows, renderer) {
  const target = document.querySelector(selector);
  if (!rows?.length) {
    target.innerHTML = `<div class="empty-state">暂无诊断数据</div>`;
    return;
  }
  target.innerHTML = rows.slice(0, 6).map(renderer).join("");
}

function renderDiagnostics() {
  const diagnostics = state.data.diagnostics || buildDiagnostics(state.data.failures || []);
  renderDiagnosticMetrics();

  renderDiagnosticList("#fieldDiagnostics", diagnostics.by_field, (row) => `
    <div class="diagnostic-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(row.field)}</div>
        <span class="tag red">${formatNumber(row.failure_count)}</span>
      </div>
      <div class="diagnostic-row-meta">Workflows: ${escapeHtml(topKeys(row.workflows) || "-")}</div>
      <div class="diagnostic-row-meta">Suggested: ${escapeHtml(topKeys(row.suggested_metacodes) || "-")}</div>
    </div>
  `);

  renderDiagnosticList("#workflowDiagnostics", diagnostics.by_workflow, (row) => `
    <div class="diagnostic-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(row.workflow_id)}</div>
        <span class="tag red">${formatNumber(row.failure_count)}</span>
      </div>
      <div class="diagnostic-row-meta">Missing: ${escapeHtml(topKeys(row.missing_fields) || "-")}</div>
      <div class="diagnostic-row-meta">Steps: ${escapeHtml(topKeys(row.failed_steps) || "-")}</div>
    </div>
  `);

  renderDiagnosticList("#metacodeDiagnostics", diagnostics.by_metacode, (row) => `
    <div class="diagnostic-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(row.metacode_id)}</div>
        <span class="tag green">${formatNumber(row.ready_count)} ready</span>
      </div>
      <div class="diagnostic-row-meta">Suggestions: ${formatNumber(row.suggestion_count)}</div>
      <div class="diagnostic-row-meta">Fields: ${escapeHtml(topKeys(row.missing_fields) || "-")}</div>
    </div>
  `);
}

function strategyLabel(strategy) {
  return {
    fixed: "Fixed",
    planned: "Planned",
  }[strategy] || strategy;
}

function renderRepairMetrics() {
  const repairs = state.data.repairs || buildRepairMetrics(state.data.runs || [], state.data.workflows || []);
  const summary = repairs.summary || {};
  const latest = summary.latest_attempt;
  const metrics = [
    ["修复验证", summary.attempt_count, "fixed / planned 运行"],
    ["修复成功率", `${summary.repair_success_rate ?? 0}%`, `${formatNumber(summary.success_count || 0)} 次成功`],
    ["Fixed 成功率", `${summary.fixed_success_rate ?? 0}%`, `${formatNumber(summary.fixed_attempt_count || 0)} 次验证`],
    ["Planned 成功率", `${summary.planned_success_rate ?? 0}%`, `${formatNumber(summary.planned_attempt_count || 0)} 次验证`],
  ];

  document.querySelector("#repairMetricGrid").innerHTML = metrics
    .map(
      ([label, value, note]) => `
        <article class="metric-card">
          <div class="metric-label">${escapeHtml(label)}</div>
          <div class="metric-value">${typeof value === "number" ? formatNumber(value) : escapeHtml(value)}</div>
          <div class="metric-note">${escapeHtml(note)}</div>
        </article>
      `,
    )
    .join("");

  document.querySelector("#repairLatest").innerHTML = latest
    ? `
      <div class="kv-row"><span>Workflow</span><span class="value-strong">${escapeHtml(latest.workflow_id)}</span></div>
      <div class="kv-row"><span>Source</span><span>${escapeHtml(latest.source_workflow_id)}</span></div>
      <div class="kv-row"><span>Strategy</span><span>${escapeHtml(strategyLabel(latest.strategy))}</span></div>
      <div class="kv-row"><span>Status</span><span>${escapeHtml(latest.status)}</span></div>
    `
    : `<div class="empty-state">暂无修复验证记录</div>`;
}

function renderRepairList(selector, rows, renderer) {
  const target = document.querySelector(selector);
  if (!rows?.length) {
    target.innerHTML = `<div class="empty-state">暂无修复数据</div>`;
    return;
  }
  target.innerHTML = rows.slice(0, 6).map(renderer).join("");
}

function renderRepairs() {
  const repairs = state.data.repairs || buildRepairMetrics(state.data.runs || [], state.data.workflows || []);
  renderRepairMetrics();

  renderRepairList("#repairStrategyList", repairs.by_strategy, (row) => `
    <div class="repair-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(strategyLabel(row.strategy))}</div>
        <span class="tag green">${row.success_rate}%</span>
      </div>
      <div class="diagnostic-row-meta">Attempts: ${formatNumber(row.attempt_count)} / Success: ${formatNumber(row.success_count)}</div>
      <div class="diagnostic-row-meta">Sources: ${escapeHtml(topKeys(row.source_workflows) || "-")}</div>
    </div>
  `);

  renderRepairList("#repairWorkflowList", repairs.by_workflow, (row) => `
    <div class="repair-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(row.source_workflow_id)}</div>
        <span class="tag green">${row.success_rate}%</span>
      </div>
      <div class="diagnostic-row-meta">Strategies: ${escapeHtml(topKeys(row.strategies) || "-")}</div>
      <div class="diagnostic-row-meta">Latest: ${escapeHtml(row.latest_repair_workflow_id || "-")} / ${escapeHtml(row.latest_status || "-")}</div>
    </div>
  `);

  renderRepairList("#repairRecentList", repairs.recent_attempts, (attempt) => `
    <div class="repair-row">
      <div class="diagnostic-row-head">
        <div class="diagnostic-row-title">${escapeHtml(attempt.workflow_id)}</div>
        <span class="tag ${attempt.status === "success" ? "green" : "red"}">${escapeHtml(attempt.status)}</span>
      </div>
      <div class="diagnostic-row-meta">Source: ${escapeHtml(attempt.source_workflow_id)} / ${escapeHtml(strategyLabel(attempt.strategy))}</div>
      <div class="diagnostic-row-meta">${escapeHtml(formatTime(attempt.ended_at))} / ${escapeHtml(formatMs(attempt.duration_ms))}</div>
    </div>
  `);
}

function workflowTypeLabel(type) {
  return {
    stable: "稳定",
    intentional_failure: "失败样例",
    generated_fixed: "Fixed",
    generated_planned: "Planned",
  }[type] || type;
}

function workflowMatchesFilter(workflow) {
  if (state.workflowFilter === "all") return true;
  if (state.workflowFilter === "generated") return workflow.status_type.startsWith("generated");
  return workflow.status_type === state.workflowFilter;
}

function workflowTagClass(type) {
  if (type === "stable") return "green";
  if (type === "intentional_failure") return "red";
  if (String(type).startsWith("generated")) return "blue";
  return "teal";
}

function renderWorkflows() {
  const workflows = state.data.workflows.filter(workflowMatchesFilter);
  if (!state.selectedWorkflowId && workflows.length) {
    state.selectedWorkflowId = workflows[0].workflow_id;
  }

  document.querySelector("#workflowTable").innerHTML = workflows
    .map(
      (workflow) => `
        <tr data-workflow="${escapeHtml(workflow.workflow_id)}" class="${workflow.workflow_id === state.selectedWorkflowId ? "selected" : ""}">
          <td>
            <div class="value-strong">${escapeHtml(workflow.workflow_id)}</div>
            <div class="small-label">${escapeHtml(workflow.name)}</div>
          </td>
          <td><span class="tag ${workflowTagClass(workflow.status_type)}">${escapeHtml(workflowTypeLabel(workflow.status_type))}</span></td>
          <td>${workflow.steps.length}</td>
          <td class="mono">${escapeHtml(workflow.output_path || "-")}</td>
        </tr>
      `,
    )
    .join("");

  document.querySelectorAll("#workflowTable tr").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedWorkflowId = row.dataset.workflow;
      renderWorkflows();
      renderWorkflowDetail();
    });
  });

  renderWorkflowDetail();
}

function renderWorkflowDetail() {
  const workflow = state.data.workflows.find((item) => item.workflow_id === state.selectedWorkflowId);
  const detail = document.querySelector("#workflowDetail");
  const type = document.querySelector("#workflowDetailType");
  if (!workflow) {
    detail.innerHTML = "选择左侧 Workflow 查看步骤。";
    type.textContent = "select";
    return;
  }
  type.textContent = workflowTypeLabel(workflow.status_type);
  const inserted = new Set(workflow.inserted_steps || []);
  detail.innerHTML = workflow.steps
    .map(
      (step, index) => `
        <div class="step-item ${inserted.has(step) ? "inserted" : ""}">
          ${String(index + 1).padStart(2, "0")} · ${escapeHtml(step)}
        </div>
      `,
    )
    .join("");
}

function renderFailures() {
  const failures = [...state.data.failures].slice(-8).reverse();
  document.querySelector("#failureGrid").innerHTML = failures
    .map((failure) => {
      const suggestion = failure.suggestions?.[0];
      const missing = failure.missing_fields?.join(", ") || "-";
      return `
        <article class="failure-card">
          <div>
            <div class="failure-title">${escapeHtml(failure.workflow_id)}</div>
            <div class="small-label">${escapeHtml(failure.failed_step || "unknown step")} · ${formatMs(failure.duration_ms)}</div>
          </div>
          <div class="tag-row">
            <span class="tag red">${escapeHtml(missing)}</span>
            ${
              suggestion
                ? `<span class="tag ${suggestion.ready ? "green" : "teal"}">${escapeHtml(suggestion.metacode_id)}</span>`
                : `<span class="tag">no suggestion</span>`
            }
          </div>
          <div class="reason">${escapeHtml(failure.reason || "-")}</div>
        </article>
      `;
    })
    .join("");
}

function renderNodeList(selector, nodes, mode) {
  document.querySelector(selector).innerHTML = nodes
    .slice(0, 5)
    .map(
      (node) => `
        <div class="node-row">
          <div>
            <div class="value-strong">${escapeHtml(node.id)}</div>
            <div class="small-label">${escapeHtml(node.category)} · in ${node.in_degree} / out ${node.out_degree}</div>
          </div>
          <div class="value-strong">${mode === "usage" ? node.usage : node.bridge_score}</div>
        </div>
      `,
    )
    .join("");
}

function renderMiniGraph() {
  const summary = state.data.graphSummary;
  const graph = state.data.graph;
  const nodes = [...summary.core_nodes, ...summary.bridge_nodes]
    .filter((node, index, arr) => arr.findIndex((item) => item.id === node.id) === index)
    .slice(0, 8);
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = graph.edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to)).slice(0, 16);
  const width = 760;
  const height = 430;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 154;
  const positions = new Map();
  nodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
    positions.set(node.id, {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    });
  });

  const edgeMarkup = edges
    .map((edge) => {
      const from = positions.get(edge.from);
      const to = positions.get(edge.to);
      if (!from || !to) return "";
      return `<line x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" stroke="#c5cdd3" stroke-width="1.4" />`;
    })
    .join("");

  const nodeMarkup = nodes
    .map((node) => {
      const pos = positions.get(node.id);
      const color = categoryColors[node.category] || "#68727d";
      const size = 10 + Math.min(node.bridge_score, 12);
      const label = escapeHtml(node.id.split(".").slice(-1)[0]);
      return `
        <g>
          <circle class="node-dot" cx="${pos.x}" cy="${pos.y}" r="${size}" fill="${color}" />
          <text x="${pos.x}" y="${pos.y + size + 16}" text-anchor="middle" font-size="11" fill="#202428">${label}</text>
        </g>
      `;
    })
    .join("");

  document.querySelector("#miniGraph").innerHTML = `
    <svg class="graph-svg" viewBox="0 0 ${width} ${height}" role="img">
      ${edgeMarkup}
      ${nodeMarkup}
    </svg>
  `;
  document.querySelector("#graphMeta").textContent = `${summary.edge_count} edges · ${summary.field_count} fields`;
  renderNodeList("#coreNodes", summary.core_nodes, "usage");
  renderNodeList("#bridgeNodes", summary.bridge_nodes, "bridge");
}

function renderStages() {
  const stages = state.data.stages;
  document.querySelector("#stageTimeline").innerHTML = stages
    .map(
      (stage) => `
        <article class="stage-card">
          <div class="stage-number">${stage.stage_id}</div>
          <div class="value-strong">${escapeHtml(stage.title)}</div>
          <div class="tag green">${escapeHtml(stage.status)}</div>
          <div class="metric-note mono">${escapeHtml(shortPath(stage.report_path))}</div>
        </article>
      `,
    )
    .join("");

  const range = state.data.summary.stage_range;
  document.querySelector("#stageRange").textContent = `Stage ${range?.first ?? "-"} - Stage ${range?.last ?? "-"}`;
}

function renderComparison() {
  document.querySelector("#comparisonGrid").innerHTML = comparisonItems
    .map(
      (item) => `
        <article class="comparison-card">
          <div class="tag blue">${escapeHtml(item.status)}</div>
          <div class="comparison-title">${escapeHtml(item.title)}</div>
          <div class="comparison-body"><strong>MetaCode：</strong>${escapeHtml(item.metacode)}</div>
          <div class="comparison-body"><strong>传统 AI：</strong>${escapeHtml(item.traditional)}</div>
        </article>
      `,
    )
    .join("");
}

function renderReports() {
  document.querySelector("#reportList").innerHTML = state.data.stages
    .map((stage) => {
      const name = fileName(stage.report_path);
      const href = `../docs/${encodeURIComponent(name)}`;
      return `
        <article class="report-item">
          <a class="report-link" href="${href}" target="_blank" rel="noreferrer">${escapeHtml(name)}</a>
          <div class="small-label">Stage ${stage.stage_id} · ${escapeHtml(stage.status)}</div>
          <div class="mono">${formatNumber(stage.report_size)} bytes</div>
        </article>
      `;
    })
    .join("");
}

function renderExtensions() {
  document.querySelector("#extensionGrid").innerHTML = extensionItems
    .map(
      (item) => `
        <article class="extension-card">
          <div class="tag teal">${escapeHtml(item.tag)}</div>
          <div class="extension-title">${escapeHtml(item.title)}</div>
          <div class="extension-body">${escapeHtml(item.body)}</div>
        </article>
      `,
    )
    .join("");
}

function renderAll() {
  const { summary } = state.data;
  setHealth(summary);
  renderMetrics(summary);
  renderRunStatus(summary);
  renderLatestRun(summary);
  renderStageGates(summary);
  renderApiStatus();
  renderDiagnostics();
  renderRepairs();
  renderStages();
  renderWorkflows();
  renderFailures();
  renderMiniGraph();
  renderComparison();
  renderReports();
  renderExtensions();
  document.querySelector("#lastUpdated").textContent = `最后导出 ${formatTime(summary.last_exported_at)}`;
}

function bindEvents() {
  document.querySelector("#refreshBtn").addEventListener("click", refresh);
  document.querySelector("#autoRefreshToggle").addEventListener("change", () => {
    if (state.data) {
      renderStageGates(state.data.summary);
      renderApiStatus();
    }
  });

  document.querySelectorAll("#workflowFilters button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("#workflowFilters button").forEach((item) => item.classList.remove("selected"));
      button.classList.add("selected");
      state.workflowFilter = button.dataset.filter;
      state.selectedWorkflowId = null;
      renderWorkflows();
    });
  });

  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    });
  });
}

async function refresh() {
  const pill = document.querySelector("#healthPill");
  pill.textContent = "刷新中";
  pill.className = "status-pill";
  try {
    state.data = await loadData();
    state.lastRefreshAt = new Date().toISOString();
    renderAll();
  } catch (error) {
    pill.textContent = "数据加载失败";
    pill.className = "status-pill warn";
    console.error(error);
  }
}

function startAutoRefresh() {
  if (state.refreshTimer) {
    clearInterval(state.refreshTimer);
  }
  state.refreshTimer = setInterval(() => {
    if (isAutoRefreshEnabled()) {
      refresh();
    }
  }, REFRESH_INTERVAL_MS);
}

bindEvents();
refresh();
startAutoRefresh();
