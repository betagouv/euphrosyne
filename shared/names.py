import re

_SEPARATOR_RE = re.compile(r"([-\u2019'])")


def _capitalize_segment(segment: str) -> str:
    if not segment:
        return segment
    return segment[0].upper() + segment[1:].lower()


def _normalize_token(token: str) -> str:
    parts = _SEPARATOR_RE.split(token)
    normalized_parts = []
    for part in parts:
        if part == "":
            continue
        if _SEPARATOR_RE.fullmatch(part):
            normalized_parts.append(part)
        else:
            normalized_parts.append(_capitalize_segment(part))
    return "".join(normalized_parts)


def normalize_person_name(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return raw
    if not (raw.islower() or raw.isupper()):
        return raw
    tokens = raw.split()
    return " ".join(_normalize_token(token) for token in tokens)
