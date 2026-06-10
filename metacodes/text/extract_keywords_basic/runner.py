import re
from collections import Counter

from core.context import append_log, read_path, write_path


def run(context):
    clean_text = read_path(context, "data.clean_text")
    tokens = re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", clean_text.lower())
    ranked = Counter(token for token in tokens if len(token) > 1).most_common(8)
    keywords = [term for term, _count in ranked]
    write_path(context, "data.keywords", keywords)
    append_log(context, "extract_keywords_basic", keywords=keywords)
    return context
