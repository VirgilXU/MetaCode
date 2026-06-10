import re
from collections import Counter

from core.context import append_log, read_path, write_path


STOPWORDS = {"the", "and", "or", "to", "of", "a", "is", "in", "it", "not"}


def run(context):
    clean_text = read_path(context, "data.clean_text")
    tokens = re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", clean_text.lower())
    tokens = [token for token in tokens if token not in STOPWORDS and len(token) > 1]
    frequency = Counter(tokens).most_common(20)
    write_path(context, "data.frequency", [{"term": term, "count": count} for term, count in frequency])
    append_log(context, "count_frequency", terms=len(frequency))
    return context
