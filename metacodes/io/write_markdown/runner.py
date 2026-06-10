from pathlib import Path

from core.context import append_log, has_path, read_path, write_path


def build_report(context):
    parts = []
    if has_path(context, "data.summary"):
        parts.extend(["# Summary", read_path(context, "data.summary")])
    if has_path(context, "data.headings"):
        parts.append("# Headings")
        for item in read_path(context, "data.headings"):
            parts.append(f"- H{item['level']} L{item['line']}: {item['title']}")
    if has_path(context, "data.text_stats"):
        parts.append("# Text Stats")
        for key, value in read_path(context, "data.text_stats").items():
            parts.append(f"- {key}: {value}")
    if has_path(context, "data.keywords"):
        parts.extend(["# Keywords", ", ".join(read_path(context, "data.keywords"))])
    if has_path(context, "data.frequency"):
        parts.append("# Frequency")
        for item in read_path(context, "data.frequency"):
            parts.append(f"- {item['term']}: {item['count']}")
    if has_path(context, "data.rows"):
        parts.append("# Rows")
        for row in read_path(context, "data.rows")[:10]:
            rendered = ", ".join(f"{key}={value}" for key, value in row.items())
            parts.append(f"- {rendered}")
    if not parts:
        parts.append("# Empty Report")
    return "\n\n".join(parts) + "\n"


def run(context):
    output_path = Path(read_path(context, "inputs.output_path"))
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(context), encoding="utf-8")
    write_path(context, "artifacts.output_file", str(output_path))
    append_log(context, "write_markdown", output_file=str(output_path))
    return context
