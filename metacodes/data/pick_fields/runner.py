from core.context import append_log, read_path, write_path


def run(context):
    rows = read_path(context, "data.rows")
    fields = read_path(context, "inputs.fields")
    picked = [{field: row.get(field, "") for field in fields} for row in rows]
    write_path(context, "data.rows", picked)
    append_log(context, "pick_fields", fields=fields, rows=len(picked))
    return context
