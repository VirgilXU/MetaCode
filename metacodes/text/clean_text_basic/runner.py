import re

from core.context import append_log, read_path, write_path


def run(context):
    raw_text = read_path(context, "data.raw_text")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw_text.splitlines()]
    clean_text = "\n".join(line for line in lines if line)
    write_path(context, "data.clean_text", clean_text)
    append_log(context, "clean_text_basic", chars=len(clean_text))
    return context
