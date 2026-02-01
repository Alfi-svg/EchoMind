from __future__ import annotations

from backend.services.sentiment_bd import SentimentResult


def build_sentiment_explanation(text: str, res: SentimentResult) -> str:
    """
    Rule-based sentiment explanation (deterministic).
    Keep this as the primary, judge-friendly explainability layer.
    """
    parts: list[str] = []
    parts.append(f"Sentiment: {res.label.upper()} (score={res.score:.2f})")
    parts.append("")
    parts.append("Reasoning (Bangladesh-context, explainable rules):")

    if res.matched_positive:
        parts.append(f"- Positive cues found: {', '.join(sorted(set(res.matched_positive)))}")
    else:
        parts.append("- Positive cues found: none")

    if res.matched_negative:
        parts.append(f"- Negative cues found: {', '.join(sorted(set(res.matched_negative)))}")
    else:
        parts.append("- Negative cues found: none")

    for n in res.notes:
        parts.append(f"- Note: {n}")

    parts.append("")
    parts.append("Limitations:")
    parts.append("- Rule-based lexicon approach may miss sarcasm, subtle context, or domain-specific phrasing.")
    parts.append("- Context here is approximated by common Bangladesh Bangla words + basic English words.")

    return "\n".join(parts)


def merge_with_social_context(rule_expl: str, llm_expl: str | None) -> str:
    """
    Optional helper if you want ONE combined explanation string.
    You can keep separate sections in UI instead (recommended).
    """
    if not llm_expl:
        return rule_expl

    return (
        rule_expl.strip()
        + "\n\n"
        + "----------------------------------------\n"
        + "Social & Cultural Context (AI, Offline)\n"
        + "----------------------------------------\n"
        + llm_expl.strip()
    )
