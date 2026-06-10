from core.context import append_log, read_path, write_path


def run(context):
    rows = read_path(context, "data.rows")
    field = read_path(context, "inputs.filter_field")
    value = str(read_path(context, "inputs.filter_value")).lower()
    filtered = [row for row in rows if value in str(row.get(field, "")).lower()]
    write_path(context, "data.rows", filtered)
    append_log(context, "filter_rows_contains", field=field, value=value, rows=len(filtered))
    return context
