import json
from pathlib import Path

from core.context import append_log, read_path, write_path


def run(context):
    file_path = Path(read_path(context, "inputs.file_path"))
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    data = json.loads(file_path.read_text(encoding="utf-8"))
    write_path(context, "data.json", data)
    append_log(context, "read_json_file", file_path=str(file_path))
    return context
