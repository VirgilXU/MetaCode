import re

from core.context import append_log, read_path, write_path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def run(context):
    raw_text = read_path(context, "data.raw_text")
    headings = []
    for line_no, line in enumerate(raw_text.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(
                {
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "line": line_no,
                }
            )
    write_path(context, "data.headings", headings)
    append_log(context, "extract_markdown_headings", count=len(headings))
    return context
