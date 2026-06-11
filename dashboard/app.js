const EXPORT_BASE = "../monitoring/exports";

const files = {
  summary: "dashboard_summary.json",
  runs: "runs.json",
  failures: "failures.json",
  stages: "stages.json",
  workflows: "workflow_graph.json",
  reuse: "reuse_summary.json",
  graph: "capability_graph.json",
  graphSummary: "capability_graph_summary.json",
};

const state = {
  data: null,
  workflowFilter: "all",
  selectedWorkflowId: null,
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
    body: "把 JSON 读取升级为服务接口，支持筛选、分页、权限和多项目。",
    tag: "Stage 10",
  },
  {
    title: "实时刷新",
    body: "监听测试运行和导出时间，自动刷新观察台状态。",
    tag: "Stage 10+",
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

async function loadJson(name) {
  const response = await fetch(`${EXPORT_BASE}/${name}?t=${Date.now()}`);
  if (!response.ok) throw new Error(`Failed to load ${name}`);
  return response.json();
}

async function loadData() {
  const entries = await Promise.all(
    Object.entries(files).map(async ([key, file]) => [key, await loadJson(file)]),
  );
  return Object.fromEntries(entries);
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

function setHealth(summary) {
  const pill = document.querySelector("#healthPill");
  const healthy = summary.unresolved_field_count === 0 && summary.current_stage >= 9;
  pill.textContent = healthy ? "Stage 9 Ready" : "Needs Review";
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
    ["失败样本", summary.failure_run_count, "用于诊断与修复"],
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
      ok: summary.current_stage >= 9,
      note: "第九阶段报告进入监控范围",
    },
    {
      label: "字段完整性",
      value: `${summary.unresolved_field_count} 个缺口`,
      ok: summary.unresolved_field_count === 0,
      note: "能力图谱字段全部可解析",
    },
    {
      label: "运行样本",
      value: `${formatNumber(summary.run_count)} 条`,
      ok: summary.run_count >= 100,
      note: "有足够样本观察趋势",
    },
    {
      label: "扩展窗口",
      value: "已预留",
      ok: true,
      note: "对比实验、实时刷新、API 可接入",
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
    renderAll();
  } catch (error) {
    pill.textContent = "数据加载失败";
    pill.className = "status-pill warn";
    console.error(error);
  }
}

bindEvents();
refresh();
