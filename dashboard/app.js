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
  io: "#167c78",
  text: "#6255a4",
  transform: "#b87a19",
  data: "#356c9c",
  analysis: "#b34b42",
  control: "#6d7b44",
  adapter: "#8b5e34",
};

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

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value ?? 0);
}

function formatMs(value) {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(1)} ms`;
}

function shortPath(path) {
  if (!path) return "-";
  return String(path).split(/[\\/]/).slice(-2).join("/");
}

function setHealth(summary) {
  const pill = document.querySelector("#healthPill");
  const healthy = summary.unresolved_field_count === 0;
  pill.textContent = healthy ? "Healthy" : "Attention";
  pill.className = `status-pill ${healthy ? "ok" : "warn"}`;
}

function renderMetrics(summary) {
  const metrics = [
    ["当前阶段", `Stage ${summary.current_stage}`, "阶段报告已纳入监控"],
    ["元代码", summary.metacode_count, "可组合能力单元"],
    ["稳定 Workflow", summary.stable_workflow_count, "成功路径基线"],
    ["能力图谱边", summary.edge_count, `${summary.field_count} 个字段`],
    ["运行记录", summary.run_count, "历史执行样本"],
    ["成功运行", summary.success_run_count, "来自 run_log"],
    ["失败运行", summary.failure_run_count, "来自 failure_log"],
    ["未解析字段", summary.unresolved_field_count, "内部字段完整"],
  ];

  document.querySelector("#metricGrid").innerHTML = metrics
    .map(
      ([label, value, note]) => `
        <article class="metric-card">
          <div class="metric-label">${label}</div>
          <div class="metric-value">${typeof value === "number" ? formatNumber(value) : value}</div>
          <div class="metric-note">${note}</div>
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
    <div class="kv-row"><span>Workflow</span><span class="value-strong">${run.workflow_id}</span></div>
    <div class="kv-row"><span>状态</span><span>${run.status}</span></div>
    <div class="kv-row"><span>耗时</span><span>${formatMs(run.duration_ms)}</span></div>
    <div class="kv-row"><span>步骤</span><span>${run.steps_success}/${run.steps_total}</span></div>
    <div class="kv-row"><span>输出</span><span class="mono">${shortPath(Object.values(run.outputs || {})[0])}</span></div>
  `;
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

function renderWorkflows() {
  const workflows = state.data.workflows.filter(workflowMatchesFilter);
  if (!state.selectedWorkflowId && workflows.length) {
    state.selectedWorkflowId = workflows[0].workflow_id;
  }

  document.querySelector("#workflowTable").innerHTML = workflows
    .map(
      (workflow) => `
        <tr data-workflow="${workflow.workflow_id}" class="${workflow.workflow_id === state.selectedWorkflowId ? "selected" : ""}">
          <td>
            <div class="value-strong">${workflow.workflow_id}</div>
            <div class="small-label">${workflow.name}</div>
          </td>
          <td><span class="tag teal">${workflowTypeLabel(workflow.status_type)}</span></td>
          <td>${workflow.steps.length}</td>
          <td class="mono">${workflow.output_path || "-"}</td>
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
          ${String(index + 1).padStart(2, "0")} · ${step}
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
            <div class="failure-title">${failure.workflow_id}</div>
            <div class="small-label">${failure.failed_step || "unknown step"} · ${formatMs(failure.duration_ms)}</div>
          </div>
          <div class="tag-row">
            <span class="tag red">${missing}</span>
            ${
              suggestion
                ? `<span class="tag ${suggestion.ready ? "green" : "teal"}">${suggestion.metacode_id}</span>`
                : `<span class="tag">no suggestion</span>`
            }
          </div>
          <div class="reason">${failure.reason || "-"}</div>
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
            <div class="value-strong">${node.id}</div>
            <div class="small-label">${node.category} · in ${node.in_degree} / out ${node.out_degree}</div>
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
      return `<line x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" stroke="#c9beb0" stroke-width="1.4" />`;
    })
    .join("");

  const nodeMarkup = nodes
    .map((node) => {
      const pos = positions.get(node.id);
      const color = categoryColors[node.category] || "#746b5e";
      const size = 10 + Math.min(node.bridge_score, 12);
      return `
        <g>
          <circle class="node-dot" cx="${pos.x}" cy="${pos.y}" r="${size}" fill="${color}" />
          <text x="${pos.x}" y="${pos.y + size + 16}" text-anchor="middle" font-size="11" fill="#23201b">${node.id.split(".").slice(-1)[0]}</text>
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
  document.querySelector("#stageTimeline").innerHTML = state.data.stages
    .map(
      (stage) => `
        <article class="stage-card">
          <div class="stage-number">${stage.stage_id}</div>
          <div class="value-strong">${stage.title}</div>
          <div class="small-label">${stage.status}</div>
          <div class="metric-note mono">${shortPath(stage.report_path)}</div>
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
  renderWorkflows();
  renderFailures();
  renderMiniGraph();
  renderStages();
  document.querySelector("#lastUpdated").textContent = `current stage ${summary.current_stage}`;
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
