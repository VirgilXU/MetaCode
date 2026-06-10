from core.context import append_log, read_path, write_path


def run(context):
    data = read_path(context, "data.json")
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        rows = data["items"]
    else:
        raise ValueError("data.json must be a list or contain an items list")

    normalized = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("each JSON item must be an object")
        normalized.append(dict(item))

    write_path(context, "data.rows", normalized)
    append_log(context, "json_items_to_rows", rows=len(normalized))
    return context
