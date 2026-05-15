import datetime
import re
from typing import Any


_MULTILINE_KEYS = ("description", "duties", "업무", "내용", "수행", "주요")


def format_value(value: Any, field_key: str = "") -> str:
    if isinstance(value, (datetime.date, datetime.datetime)):
        return _fmt_date(value.strftime("%Y-%m-%d"))

    if isinstance(value, dict):
        if "start" in value and "end" in value:
            return f"{_fmt_date(str(value['start']))} ~ {_fmt_date(str(value['end']))}"
        return ""

    if isinstance(value, list):
        if not value:
            return ""
        items = [str(v) for v in value]
        # Description-like fields → newline; everything else → comma-separated
        key_lower = field_key.lower()
        if any(k in key_lower for k in _MULTILINE_KEYS):
            return "\n".join(items)
        return ", ".join(items)

    return _fmt_date(str(value))


def _fmt_date(s: str) -> str:
    if re.match(r"^\d{4}-\d{2}$", s):
        y, m = s.split("-")
        return f"{y[2:]}.{m}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        y, m, d = s.split("-")
        return f"{y[2:]}.{m}.{d}"
    return s
