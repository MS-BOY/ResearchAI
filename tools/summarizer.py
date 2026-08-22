import re
from collections import Counter


# ==========================================
# Clean Text
# ==========================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================
# Split Sentences
# ==========================================

def split_sentences(text):

    text = clean_text(text)

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?।])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 20
    ]


# ==========================================
# English Stopwords
# ==========================================

STOPWORDS = {

    "the",
    "is",
    "are",
    "was",
    "were",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "that",
    "this",
    "from",
    "as",
    "by",
    "it",
    "an",
    "a",
    "be",
    "has",
    "have",
    "had",
    "which",
    "also",
    "its",
    "their",
    "they",
    "he",
    "she",
    "his",
    "her",
    "at",
    "but",
    "not",
    "about",
    "into",
    "than",
    "after",
    "before",
    "during",
    "over",
    "under",
    "more",
    "most",
    "such",
    "can",
    "will",
    "would",
    "could",
    "been",
    "being",
    "who",
    "whom",
    "what",
    "when",
    "where",
    "how",
    "which"
}


# ==========================================
# Intent Keywords
# ==========================================

INTENT_KEYWORDS = {

    "date_of_birth": [

        "born",
        "birth",
        "date of birth",
        "dob",
        "birthplace",
        "জন্ম",
        "জন্ম তারিখ",
        "জন্মতারিখ"

    ],

    "songs": [

        "song",
        "songs",
        "singer",
        "sing",
        "sang",
        "music",
        "vocal",
        "vocals",
        "discography",
        "গান",
        "গেয়েছেন",
        "গেয়েছে"

    ],

    "movies": [

        "movie",
        "movies",
        "film",
        "films",
        "cinema",
        "soundtrack",
        "soundtracks",
        "সিনেমা",
        "সিনেমায়",
        "সিনেমাতে"

    ],

    "career": [

        "career",
        "profession",
        "works",
        "work",
        "career",
        "ক্যারিয়ার",
        "পেশা",
        "কাজ"

    ],

    "awards": [

        "award",
        "awards",
        "won",
        "winner",
        "achievement",
        "পুরস্কার",
        "অর্জন",
        "সম্মাননা"

    ],

    "family": [

        "father",
        "mother",
        "parents",
        "family",
        "বাবা",
        "মা",
        "পরিবার"

    ],

    "education": [

        "education",
        "school",
        "college",
        "university",
        "study",
        "শিক্ষা",
        "পড়াশোনা",
        "স্কুল",
        "কলেজ",
        "বিশ্ববিদ্যালয়"

    ],

    "biography": [

        "biography",
        "about",
        "life",
        "career",
        "personal",
        "জীবনী",
        "সম্পর্কে",
        "জীবন",
        "পরিচয়"

    ]
}


# ==========================================
# Find Keywords
# ==========================================

def sentence_matches_intent(
    sentence,
    intent
):

    lower = sentence.lower()

    keywords = INTENT_KEYWORDS.get(
        intent,
        []
    )

    return any(
        keyword in lower
        for keyword in keywords
    )


# ==========================================
# Score Sentence
# ==========================================

def sentence_score(
    sentence,
    word_frequency
):

    words = re.findall(
        r"\b[a-zA-Z]{2,}\b",
        sentence.lower()
    )

    if not words:

        return 0


    score = 0


    for word in words:

        if word not in STOPWORDS:

            score += word_frequency.get(
                word,
                0
            )


    length_penalty = max(
        len(words) / 40,
        1
    )


    return score / length_penalty


# ==========================================
# Summarize Source
# ==========================================

def summarize_text(
    text,
    max_sentences=5,
    intents=None
):

    text = clean_text(text)

    if not text:

        return ""


    sentences = split_sentences(
        text
    )


    if not sentences:

        return ""


    if intents is None:

        intents = []


    # ======================================
    # First: Intent matching
    # ======================================

    relevant = []


    for sentence in sentences:

        matched = False


        for intent in intents:

            if sentence_matches_intent(
                sentence,
                intent
            ):

                matched = True

                break


        if matched:

            relevant.append(
                sentence
            )


    # ======================================
    # If enough relevant sentences
    # ======================================

    if len(relevant) >= max_sentences:

        return " ".join(
            relevant[:max_sentences]
        )


    # ======================================
    # General frequency ranking
    # ======================================

    words = re.findall(
        r"\b[a-zA-Z]{2,}\b",
        text.lower()
    )


    frequency = Counter(

        word
        for word in words

        if word not in STOPWORDS

    )


    scored = []


    for index, sentence in enumerate(
        sentences
    ):

        score = sentence_score(
            sentence,
            frequency
        )


        # Give bonus to intent sentences
        for intent in intents:

            if sentence_matches_intent(
                sentence,
                intent
            ):

                score += 10


        scored.append(
            (
                score,
                index,
                sentence
            )
        )


    # ======================================
    # Pick best sentences
    # ======================================

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )


    selected = scored[
        :max_sentences
    ]


    # Original order
    selected.sort(
        key=lambda x: x[1]
    )


    return " ".join(
        item[2]
        for item in selected
    )


# ==========================================
# Build Research Summary
# ==========================================

def build_research_summary(
    sources,
    intents=None,
    max_sentences_per_source=5,
    max_total_sentences=20
):

    if not sources:

        return ""


    if intents is None:

        intents = []


    all_sentences = []


    # ======================================
    # Read every source
    # ======================================

    for source in sources:

        text = source.get(
            "text",
            ""
        )


        sentences = split_sentences(
            text
        )


        if not sentences:

            continue


        # ==================================
        # Relevant sentences first
        # ==================================

        relevant = []


        for sentence in sentences:

            for intent in intents:

                if sentence_matches_intent(
                    sentence,
                    intent
                ):

                    relevant.append(
                        sentence
                    )

                    break


        # ==================================
        # Add relevant
        # ==================================

        for sentence in relevant[
            :max_sentences_per_source
        ]:

            all_sentences.append(
                sentence
            )


        # ==================================
        # Fill remaining
        # ==================================

        if len(relevant) < max_sentences_per_source:

            remaining = [
                s
                for s in sentences
                if s not in relevant
            ]


            for sentence in remaining[
                :max_sentences_per_source
                - len(relevant)
            ]:

                all_sentences.append(
                    sentence
                )


    # ======================================
    # Remove duplicates
    # ======================================

    unique = []

    seen = set()


    for sentence in all_sentences:

        normalized = re.sub(
            r"\W+",
            " ",
            sentence.lower()
        ).strip()


        if not normalized:

            continue


        if normalized in seen:

            continue


        seen.add(
            normalized
        )


        unique.append(
            sentence
        )


    # ======================================
    # Limit
    # ======================================

    unique = unique[
        :max_total_sentences
    ]


    return "\n\n".join(
        unique
    )


# ==========================================
# Build Structured Research
# ==========================================

def build_structured_research(
    sources,
    intents
):

    sections = {}


    for intent in intents:

        matching = []


        for source in sources:

            text = source.get(
                "text",
                ""
            )


            sentences = split_sentences(
                text
            )


            for sentence in sentences:

                if sentence_matches_intent(
                    sentence,
                    intent
                ):

                    matching.append(
                        sentence
                    )


        # Remove duplicates

        unique = []

        seen = set()


        for sentence in matching:

            key = re.sub(
                r"\W+",
                " ",
                sentence.lower()
            ).strip()


            if key in seen:

                continue


            seen.add(key)

            unique.append(
                sentence
            )


        sections[intent] = unique[:8]


    return sections