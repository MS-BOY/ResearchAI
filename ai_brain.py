"""
Advanced AI Brain
-----------------

Responsible for:
- Detecting user intent
- Selecting the best tool
- Understanding Bangla + English
- Detecting search/research/video intent
- Cleaning the search query
- Returning confidence score
- Returning structured intent data
"""

from __future__ import annotations

import re
from typing import Dict, Any


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOOL = "research"

DEFAULT_ACTION = "research"

MIN_CONFIDENCE = 0.35


# ============================================================
# TOOL KEYWORDS
# ============================================================

YOUTUBE_KEYWORDS = [

    # English
    "youtube",
    "youtube video",
    "watch video",
    "video",

    # Bangla
    "ইউটিউব",
    "ভিডিও",
    "ভিডিও দেখাও",
    "ভিডিও খুঁজে দাও",
    "ভিডিও সার্চ"

]


GOOGLE_KEYWORDS = [

    # English
    "google",
    "google search",
    "search google",
    "search on google",

    # Bangla
    "গুগল",
    "গুগলে সার্চ",
    "গুগল সার্চ"

]


RESEARCH_KEYWORDS = [

    # English
    "research",
    "research about",
    "research on",
    "explain",
    "explanation",
    "information",
    "details",
    "analyze",
    "analysis",
    "compare",
    "comparison",
    "difference",
    "why",
    "how",
    "what",
    "which",
    "when",
    "where",
    "who",
    "how much",
    "latest",
    "recent",
    "current",
    "facts",
    "study",
    "investigate",

    # Bangla
    "কী",
    "কি",
    "কেন",
    "কিভাবে",
    "কীভাবে",
    "কোন",
    "কোনটা",
    "কত",
    "কখন",
    "কোথায়",
    "কে",
    "কেনো",
    "তথ্য",
    "বিস্তারিত",
    "ব্যাখ্যা",
    "গবেষণা",
    "জানাও",
    "জানাও আমাকে",
    "বুঝিয়ে বল",
    "তুলনা",
    "পার্থক্য",
    "বিশ্লেষণ",
    "বর্তমান",
    "সাম্প্রতিক",
    "সর্বশেষ"

]


# ============================================================
# ACTION KEYWORDS
# ============================================================

ACTION_KEYWORDS = {

    "search": [

        "search",
        "find",
        "খুঁজ",
        "খুঁজে",
        "সার্চ",
        "অনুসন্ধান"

    ],

    "research": [

        "research",
        "গবেষণা",
        "বিশ্লেষণ",
        "analyze",
        "analysis",
        "explain",
        "ব্যাখ্যা"

    ],

    "compare": [

        "compare",
        "comparison",
        "vs",
        "versus",
        "তুলনা",
        "পার্থক্য",
        "difference"

    ],

    "explain": [

        "explain",
        "explanation",
        "বুঝিয়ে",
        "ব্যাখ্যা",
        "মানে কী",
        "মানে কি"

    ]

}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = str(
        text
    ).strip().lower()

    # Multiple spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# KEYWORD MATCHING
# ============================================================

def contains_keyword(
    text: str,
    keyword: str
) -> bool:

    keyword = keyword.lower().strip()

    if not keyword:
        return False

    # Bangla / multi-word keyword
    if any(
        "\u0980" <= char <= "\u09FF"
        for char in keyword
    ):

        return keyword in text

    # English word boundary
    pattern = (
        r"(?<![a-zA-Z])"
        + re.escape(keyword)
        + r"(?![a-zA-Z])"
    )

    return bool(
        re.search(
            pattern,
            text
        )
    )


# ============================================================
# SCORE KEYWORDS
# ============================================================

def score_keywords(
    text: str,
    keywords: list[str]
) -> int:

    score = 0

    for keyword in keywords:

        if contains_keyword(
            text,
            keyword
        ):

            # Longer phrases get more weight
            words = len(
                keyword.split()
            )

            score += max(
                1,
                words
            )

    return score


# ============================================================
# DETECT ACTION
# ============================================================

def detect_action(
    text: str
) -> str:

    scores = {}

    for action, keywords in ACTION_KEYWORDS.items():

        scores[action] = score_keywords(
            text,
            keywords
        )

    best_action = max(
        scores,
        key=scores.get
    )

    if scores[best_action] == 0:

        return DEFAULT_ACTION

    return best_action


# ============================================================
# CLEAN TOOL PREFIX
# ============================================================

def clean_query(
    command: str,
    tool: str
) -> str:

    query = command.strip()


    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if tool == "youtube":

        patterns = [

            r"\byoutube\b",
            r"\byoutube video\b",
            r"\bsearch\b",
            r"\bfind\b",

            "ইউটিউব",
            "ভিডিও",
            "সার্চ",
            "খুঁজে দাও"

        ]

        for pattern in patterns:

            try:

                query = re.sub(
                    pattern,
                    "",
                    query,
                    flags=re.IGNORECASE
                )

            except re.error:

                query = query.replace(
                    pattern,
                    ""
                )


    # --------------------------------------------------------
    # Google
    # --------------------------------------------------------

    elif tool == "google":

        patterns = [

            r"\bgoogle\b",
            r"\bsearch\b",
            r"\bfind\b",

            "গুগল",
            "সার্চ",
            "খুঁজে দাও"

        ]

        for pattern in patterns:

            try:

                query = re.sub(
                    pattern,
                    "",
                    query,
                    flags=re.IGNORECASE
                )

            except re.error:

                query = query.replace(
                    pattern,
                    ""
                )


    # --------------------------------------------------------
    # Clean extra spaces
    # --------------------------------------------------------

    query = re.sub(
        r"\s+",
        " ",
        query
    ).strip()


    # Remove common punctuation
    query = query.strip(
        " :-,?!।"
    )


    return query or command.strip()


# ============================================================
# DETECT TOOL
# ============================================================

def detect_tool(
    text: str
) -> tuple[str, float, Dict[str, int]]:

    scores = {

        "youtube": 0,

        "google": 0,

        "research": 0

    }


    # --------------------------------------------------------
    # YouTube score
    # --------------------------------------------------------

    youtube_score = score_keywords(
        text,
        YOUTUBE_KEYWORDS
    )

    scores[
        "youtube"
    ] = youtube_score * 3


    # --------------------------------------------------------
    # Google score
    # --------------------------------------------------------

    google_score = score_keywords(
        text,
        GOOGLE_KEYWORDS
    )

    scores[
        "google"
    ] = google_score * 3


    # --------------------------------------------------------
    # Research score
    # --------------------------------------------------------

    research_score = score_keywords(
        text,
        RESEARCH_KEYWORDS
    )

    scores[
        "research"
    ] = research_score


    # --------------------------------------------------------
    # Special research patterns
    # --------------------------------------------------------

    comparison_patterns = [

        r"\b(.+)\s+vs\s+(.+)\b",

        r"\b(.+)\s+versus\s+(.+)\b",

        "তুলনা",

        "পার্থক্য",

        "কোনটা ভালো",

        "which is better"

    ]


    for pattern in comparison_patterns:

        if contains_keyword(
            text,
            pattern
        ):

            scores[
                "research"
            ] += 3

            break


    # --------------------------------------------------------
    # Pick highest
    # --------------------------------------------------------

    best_tool = max(
        scores,
        key=scores.get
    )


    best_score = scores[
        best_tool
    ]


    total_score = sum(
        scores.values()
    )


    if total_score <= 0:

        return (
            DEFAULT_TOOL,
            0.40,
            scores
        )


    confidence = (
        best_score /
        total_score
    )


    # Prevent very low confidence
    confidence = max(
        confidence,
        MIN_CONFIDENCE
    )


    return (
        best_tool,
        round(
            confidence,
            2
        ),
        scores
    )


# ============================================================
# MAIN UNDERSTANDING FUNCTION
# ============================================================

def understand(
    command: str
) -> Dict[str, Any]:

    original_command = str(
        command or ""
    ).strip()


    # --------------------------------------------------------
    # Empty command
    # --------------------------------------------------------

    if not original_command:

        return {

            "tool":
                DEFAULT_TOOL,

            "action":
                DEFAULT_ACTION,

            "query":
                "",

            "confidence":
                0.0,

            "language":
                "unknown",

            "original_command":
                ""

        }


    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    text = normalize_text(
        original_command
    )


    # --------------------------------------------------------
    # Detect tool
    # --------------------------------------------------------

    tool, confidence, scores = detect_tool(
        text
    )


    # --------------------------------------------------------
    # Detect action
    # --------------------------------------------------------

    action = detect_action(
        text
    )


    # --------------------------------------------------------
    # Tool-specific action
    # --------------------------------------------------------

    if tool in (
        "youtube",
        "google"
    ):

        action = "search"


    # --------------------------------------------------------
    # Research action
    # --------------------------------------------------------

    if tool == "research":

        if action == "search":

            action = "research"


    # --------------------------------------------------------
    # Clean query
    # --------------------------------------------------------

    query = clean_query(
        original_command,
        tool
    )


    # --------------------------------------------------------
    # Detect language
    # --------------------------------------------------------

    bangla_chars = sum(

        1

        for char in original_command

        if "\u0980" <= char <= "\u09FF"

    )


    english_chars = sum(

        1

        for char in original_command

        if char.isascii()
        and char.isalpha()

    )


    if bangla_chars > english_chars:

        language = "বাংলা"

    elif english_chars > 0:

        language = "English"

    else:

        language = "unknown"


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {

        "tool":
            tool,

        "action":
            action,

        "query":
            query,

        "confidence":
            confidence,

        "language":
            language,

        "scores":
            scores,

        "original_command":
            original_command

    }


    # --------------------------------------------------------
    # Debug
    # --------------------------------------------------------

    print(
        "\n🧠 AI Brain"
    )

    print(
        f"   Tool       : {tool}"
    )

    print(
        f"   Action     : {action}"
    )

    print(
        f"   Query      : {query}"
    )

    print(
        f"   Language   : {language}"
    )

    print(
        f"   Confidence : {confidence}"
    )

    print(
        f"   Scores     : {scores}"
    )


    return result
