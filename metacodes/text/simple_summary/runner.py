from core.context import append_log, read_path, write_path


def run(context):
    clean_text = read_path(context, "data.clean_text")
    paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip() and not p.startswith("#")]
    summary = "\n".join(f"- {p[:140]}" for p in paragraphs[:3])
    if not summary:
        summary = "- No summary content found."
    write_path(context, "data.summary", summary)
    append_log(context, "simple_summary", items=summary.count("\n") + 1)
    return context
