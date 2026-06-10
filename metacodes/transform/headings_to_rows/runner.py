from core.context import append_log, read_path, write_path


def run(context):
    headings = read_path(context, "data.headings")
    rows = [
        {"level": item["level"], "title": item["title"], "line": item["line"]}
        for item in headings
    ]
    write_path(context, "data.rows", rows)
    append_log(context, "headings_to_rows", rows=len(rows))
    return context
