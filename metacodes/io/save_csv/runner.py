import csv
from pathlib import Path

from core.context import append_log, read_path, write_path


def run(context):
    rows = read_path(context, "data.rows")
    output_path = Path(read_path(context, "inputs.output_path"))
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else []
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    write_path(context, "artifacts.output_file", str(output_path))
    append_log(context, "save_csv", output_file=str(output_path), rows=len(rows))
    return context
