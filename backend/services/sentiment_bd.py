from __future__ import annotations

from dataclasses import dataclass

@dataclass
class SentimentResult:
    label: str  # "positive" | "negative" | "neutral"
    score: float
    matched_positive: list[str]
    matched_negative: list[str]
    notes: list[str]

# Explainable Bangladesh-context lexicon (small, hackathon-safe)
BN_POS = {
    "ভালো", "চমৎকার", "দারুণ", "সুন্দর", "অসাধারণ", "ধন্যবাদ", "প্রশংসা", "সাফল্য",
    "উন্নতি", "সঠিক", "সাহায্য", "খুশি", "আনন্দ"
}
BN_NEG = {
    "খারাপ", "ভয়", "দুঃখ", "দুঃখিত", "রাগ", "ক্ষতি", "ব্যর্থ", "মিথ্যা", "অন্যায়",
    "সমস্যা", "দুর্নীতি", "অসন্তোষ", "কষ্ট"
}

EN_POS = {"good", "great", "excellent", "amazing", "thank", "success", "improve", "happy", "love", "helpful"}
EN_NEG = {"bad", "angry", "sad", "fear", "loss", "fail", "fake", "unfair", "problem", "corrupt", "hurt"}

def tokenize_simple(text: str) -> list[str]:
    # keep Bangla & English letters, split on others
    out = []
    buf = []
    for ch in text.lower():
        if ch.isalnum() or ("\u0980" <= ch <= "\u09FF"):
            buf.append(ch)
        else:
            if buf:
                out.append("".join(buf))
                buf = []
    if buf:
        out.append("".join(buf))
    return out

def sentiment_bd(text: str) -> SentimentResult:
    toks = tokenize_simple(text)
    pos_hit = []
    neg_hit = []

    for t in toks:
        if t in BN_POS or t in EN_POS:
            pos_hit.append(t)
        if t in BN_NEG or t in EN_NEG:
            neg_hit.append(t)

    # Explainable scoring
    pos = len(pos_hit)
    neg = len(neg_hit)
    total = pos + neg

    notes = []
    if total == 0:
        notes.append("No strong sentiment keywords found (Bangladesh-context lexicon + English lexicon).")
        return SentimentResult("neutral", 0.0, pos_hit, neg_hit, notes)

    # score in [-1, +1]
    score = (pos - neg) / max(1, total)

    # label thresholds (simple & documented)
    if score >= 0.25:
        label = "positive"
        notes.append("Positive keywords outweigh negative keywords.")
    elif score <= -0.25:
        label = "negative"
        notes.append("Negative keywords outweigh positive keywords.")
    else:
        label = "neutral"
        notes.append("Mixed keywords; not strong enough to classify as clearly positive/negative.")

    return SentimentResult(label, float(score), pos_hit, neg_hit, notes)
