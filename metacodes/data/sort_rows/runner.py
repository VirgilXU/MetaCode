from core.context import append_log, read_path, write_path


def run(context):
    rows = read_path(context, "data.rows")
    sort_field = read_path(context, "inputs.sort_field")
    sorted_rows = sorted(rows, key=lambda row: str(row.get(sort_field, "")))
    write_path(context, "data.rows", sorted_rows)
    append_log(context, "sort_rows", sort_field=sort_field, rows=len(sorted_rows))
    return context
