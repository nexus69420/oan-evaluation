"""
Rule-based language mixing detection for LanguageMixingMetric.
Ported from inf_bh_dev/language_analysis/ -- no LLM calls, no external dependencies.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

ALL_SCRIPTS: List[Tuple[str, int, int]] = [
    ("Devanagari",             0x0900, 0x097F),
    ("Bengali",                0x0980, 0x09FF),
    ("Gurmukhi",               0x0A00, 0x0A7F),
    ("Gujarati",               0x0A80, 0x0AFF),
    ("Oriya",                  0x0B00, 0x0B7F),
    ("Tamil",                  0x0B80, 0x0BFF),
    ("Telugu",                 0x0C00, 0x0C7F),
    ("Kannada",                0x0C80, 0x0CFF),
    ("Malayalam",              0x0D00, 0x0D7F),
    ("Chinese/Japanese (CJK)", 0x4E00, 0x9FFF),
    ("Japanese (Kana)",        0x3040, 0x30FF),
    ("Korean",                 0xAC00, 0xD7AF),
]

SHARED_INDIC_PUNCTUATION = frozenset([0x0964, 0x0965])

LANGUAGE_CONFIGS: Dict[str, dict] = {
    "assamese": {
        "display_name":         "Assamese",
        "target_script":        "Bengali",
        "target_range":         (0x0980, 0x09FF),
        "check_english_mixing": True,
    },
    "bengali": {
        "display_name":         "Bengali",
        "target_script":        "Bengali",
        "target_range":         (0x0980, 0x09FF),
        "check_english_mixing": True,
    },
    "english": {
        "display_name":         "English",
        "target_script":        "Latin/ASCII",
        "target_range":         None,
        "check_english_mixing": False,
    },
    "gujarati": {
        "display_name":         "Gujarati",
        "target_script":        "Gujarati",
        "target_range":         (0x0A80, 0x0AFF),
        "check_english_mixing": True,
    },
    "hindi": {
        "display_name":         "Hindi",
        "target_script":        "Devanagari",
        "target_range":         (0x0900, 0x097F),
        "check_english_mixing": True,
    },
    "kannada": {
        "display_name":         "Kannada",
        "target_script":        "Kannada",
        "target_range":         (0x0C80, 0x0CFF),
        "check_english_mixing": True,
    },
    "malayalam": {
        "display_name":         "Malayalam",
        "target_script":        "Malayalam",
        "target_range":         (0x0D00, 0x0D7F),
        "check_english_mixing": True,
    },
    "marathi": {
        "display_name":         "Marathi",
        "target_script":        "Devanagari",
        "target_range":         (0x0900, 0x097F),
        "check_english_mixing": True,
    },
    "tamil": {
        "display_name":         "Tamil",
        "target_script":        "Tamil",
        "target_range":         (0x0B80, 0x0BFF),
        "check_english_mixing": True,
    },
    "telugu": {
        "display_name":         "Telugu",
        "target_script":        "Telugu",
        "target_range":         (0x0C00, 0x0C7F),
        "check_english_mixing": True,
    },
}

OUTPUT_LANGUAGE_MAP: Dict[str, str] = {
    "assamese":  "assamese",
    "bengali":   "bengali",
    "english":   "english",
    "gujarati":  "gujarati",
    "gu":        "gujarati",
    "hindi":     "hindi",
    "hi":        "hindi",
    "kannada":   "kannada",
    "malayalam": "malayalam",
    "marathi":   "marathi",
    "mr":        "marathi",
    "tamil":     "tamil",
    "telugu":    "telugu",
}

KNOWN_TECHNICAL = re.compile(
    r'^(ICAR|NPSS|PMFBY|PMKSY|KCC|SHC|IMD|APMC|FYM|SSP|MOP|AIF|SMAM|'
    r'PDMC|PKVY|NFSM|RAD|IFS|SATHI|OTP|KVK|DAO|DHO|eKYC|PM-KISAN|CSC|'
    r'BIOGROW|NAA|WP|GR|CG|NPK|FMD|WSP|EC|SC|ST|URL|ID|OTP|SMS|PDF|'
    r'SG|SP|DHN|ICAR|DNA|RNA)$', re.IGNORECASE,
)


def detect_foreign_scripts(text: str, config: dict) -> Dict[str, List[Tuple[str, str]]]:
    target_range = config["target_range"]
    found: Dict[str, List[Tuple[str, str]]] = {}
    for i, ch in enumerate(text):
        cp = ord(ch)
        if cp < 0x0080:
            continue
        if cp in SHARED_INDIC_PUNCTUATION:
            continue
        if target_range and target_range[0] <= cp <= target_range[1]:
            continue
        for name, lo, hi in ALL_SCRIPTS:
            if lo <= cp <= hi:
                if target_range and lo == target_range[0] and hi == target_range[1]:
                    break
                ctx = text[max(0, i - 30): i + 30].replace("\n", " ")
                found.setdefault(name, []).append((ch, ctx))
                break
    return found


def detect_english_mixing(text: str) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {
        "technical_abbrevs": [],
        "parens_english":    [],
        "inline_english":    [],
    }
    for m in re.finditer(r'\(([A-Za-z][^)]{1,60})\)', text):
        result["parens_english"].append(m.group(1).strip())
    paren_spans = [(m.start(), m.end()) for m in re.finditer(r'\([^)]*\)', text)]

    def in_parens(pos: int) -> bool:
        return any(s <= pos <= e for s, e in paren_spans)

    for m in re.finditer(r'[A-Za-z][A-Za-z\-\.]{1,}', text):
        if in_parens(m.start()):
            continue
        word = m.group()
        if KNOWN_TECHNICAL.match(word):
            result["technical_abbrevs"].append(word)
        elif len(word) >= 4:
            result["inline_english"].append(word)
    return result


def detect_target_from_question(question: str) -> Optional[str]:
    script_counts: Counter = Counter()
    for ch in question:
        cp = ord(ch)
        if cp < 0x0080:
            continue
        if cp in SHARED_INDIC_PUNCTUATION:
            continue
        for name, lo, hi in ALL_SCRIPTS:
            if lo <= cp <= hi:
                script_counts[name] += 1
                break
    if not script_counts:
        return None
    dominant = script_counts.most_common(1)[0][0]
    return {
        "Devanagari": "hindi",
        "Bengali":    "bengali",
        "Gujarati":   "gujarati",
        "Tamil":      "tamil",
        "Telugu":     "telugu",
        "Kannada":    "kannada",
        "Malayalam":  "malayalam",
    }.get(dominant)


def compute_score(config: dict, foreign_detail: dict, english_detail: dict) -> int:
    if foreign_detail:
        return 1
    if not config["check_english_mixing"]:
        return 4
    if english_detail.get("inline_english"):
        return 2
    if english_detail.get("parens_english") or english_detail.get("technical_abbrevs"):
        return 3
    return 4


def build_reason(config: dict, foreign_detail: dict, english_detail: dict) -> str:
    name = config["display_name"]
    if foreign_detail:
        scripts_str = ", ".join(sorted(foreign_detail.keys()))
        inline = english_detail.get("inline_english", [])
        suffix = f" Also unnecessary English: {', '.join(inline[:3])}." if inline else ""
        return f"CRITICAL -- {scripts_str} script mixed into {name} text." + suffix
    if not config["check_english_mixing"]:
        return "Pure English text -- no script mixing expected."
    inline = english_detail.get("inline_english", [])
    parens = english_detail.get("parens_english", [])
    techni = english_detail.get("technical_abbrevs", [])
    if inline:
        sample = ", ".join(inline[:5])
        return f"Unnecessary inline English code-switching: {sample}" + (" ..." if len(inline) > 5 else ".")
    if parens:
        return "English used inside parentheses only -- borderline acceptable."
    if techni:
        sample = ", ".join(sorted(set(techni))[:6])
        return f"Technical abbreviations only ({sample}) -- standard in agricultural content."
    return f"Pure {name} script. No foreign script or English mixing detected."
