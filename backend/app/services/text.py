import re


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def token_set(value: str) -> set[str]:
    return set(normalize_text(value).split())
