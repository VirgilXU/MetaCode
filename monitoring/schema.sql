CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  workflow_id TEXT NOT NULL,
  workflow_path TEXT,
  status TEXT NOT NULL,
  started_at TEXT,
  ended_at TEXT,
  duration_ms REAL,
  steps_total INTEGER,
  steps_success INTEGER,
  failed_step TEXT,
  reason TEXT,
  missing_fields_json TEXT,
  suggestions_json TEXT,
  outputs_json TEXT,
  context_keys_json TEXT,
  source_log TEXT
);

CREATE TABLE IF NOT EXISTS workflows (
  workflow_id TEXT PRIMARY KEY,
  name TEXT,
  workflow_path TEXT,
  status_type TEXT,
  steps_json TEXT,
  generated_from TEXT,
  inserted_steps_json TEXT,
  output_path TEXT
);

CREATE TABLE IF NOT EXISTS stages (
  stage_id INTEGER PRIMARY KEY,
  title TEXT,
  status TEXT,
  report_path TEXT,
  report_size INTEGER,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS metacodes (
  metacode_id TEXT PRIMARY KEY,
  category TEXT,
  purpose TEXT,
  reads_json TEXT,
  writes_json TEXT,
  usage_count INTEGER,
  in_degree INTEGER,
  out_degree INTEGER,
  bridge_score INTEGER
);

CREATE TABLE IF NOT EXISTS graph_edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_id TEXT,
  to_id TEXT,
  field TEXT,
  from_category TEXT,
  to_category TEXT
);

CREATE TABLE IF NOT EXISTS summaries (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL
);
