from __future__ import annotations


def next_version_label(current_label: str | None) -> str:
    if not current_label:
        return 'v1'
    if not current_label.startswith('v'):
        return 'v1'
    try:
        return f"v{int(current_label[1:]) + 1}"
    except ValueError:
        return 'v1'
