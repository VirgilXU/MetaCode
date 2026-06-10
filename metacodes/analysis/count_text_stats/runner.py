from core.context import append_log, read_path, write_path


def run(context):
    clean_text = read_path(context, "data.clean_text")
    headings = read_path(context, "data.headings")
    paragraphs = [p for p in clean_text.split("\n") if p.strip() and not p.startswith("#")]
    stats = {
        "chars": len(clean_text),
        "lines": len(clean_text.splitlines()),
        "paragraphs": len(paragraphs),
        "headings": len(headings),
    }
    write_path(context, "data.text_stats", stats)
    append_log(context, "count_text_stats", **stats)
    return context
