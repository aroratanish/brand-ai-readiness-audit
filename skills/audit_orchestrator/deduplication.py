import re
from collections.abc import Iterable
from difflib import SequenceMatcher


Finding = dict
TITLE_SIMILARITY_THRESHOLD = 0.75


def normalize_title(title: str) -> str:
    """Normalize title text for conservative near-duplicate comparison."""
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower())
    return " ".join(normalized.split())


def _title_similarity(first_title: str, second_title: str) -> float:
    first = normalize_title(first_title)
    second = normalize_title(second_title)

    sequence_score = SequenceMatcher(None, first, second).ratio()
    first_tokens = set(first.split())
    second_tokens = set(second.split())
    union = first_tokens | second_tokens
    token_score = (
        len(first_tokens & second_tokens) / len(union)
        if union
        else 1.0
    )
    return max(sequence_score, token_score)


def _same_duplicate_group(first: Finding, second: Finding) -> bool:
    return (
        first.get("url") == second.get("url")
        and first.get("category") == second.get("category")
        and first.get("severity") == second.get("severity")
        and _title_similarity(first["title"], second["title"])
        >= TITLE_SIMILARITY_THRESHOLD
    )


def _merge_duplicate(canonical: Finding, duplicate: Finding) -> Finding:
    merged = dict(canonical)

    if len(duplicate.get("evidence", "")) > len(merged.get("evidence", "")):
        merged["evidence"] = duplicate["evidence"]

    if duplicate.get("source_skill") != canonical.get("source_skill"):
        source_note = (
            "Also reported by source skill "
            f"'{duplicate.get('source_skill')}'."
        )
        if source_note not in merged["evidence"]:
            merged["evidence"] = (
                f"{merged['evidence'].rstrip()} {source_note}"
            )

    return merged


def deduplicate_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Return findings with conservative, deterministic duplicate merging."""
    deduplicated: list[Finding] = []

    for finding in findings:
        duplicate_index = next(
            (
                index
                for index, existing in enumerate(deduplicated)
                if _same_duplicate_group(existing, finding)
            ),
            None,
        )

        if duplicate_index is None:
            deduplicated.append(dict(finding))
        else:
            deduplicated[duplicate_index] = _merge_duplicate(
                deduplicated[duplicate_index],
                finding,
            )

    return deduplicated
