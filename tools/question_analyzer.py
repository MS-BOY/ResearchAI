import re


# ==========================================
# Question Analyzer
# ==========================================

def analyze_question(question):

    text = question.strip()
    lower = text.lower()

    intents = []

    # ======================================
    # Date of Birth
    # ======================================

    dob_keywords = [
        "date of birth",
        "dob",
        "born",
        "birth",
        "জন্ম",
        "জন্ম তারিখ",
        "জন্মতারিখ",
        "কবে জন্ম",
        "কত সালে জন্ম"
    ]

    if any(keyword in lower for keyword in dob_keywords):

        intents.append("date_of_birth")


    # ======================================
    # Songs / Music
    # ======================================

    song_keywords = [
        "song",
        "songs",
        "music",
        "sing",
        "singer",
        "sang",
        "গান",
        "গেয়েছে",
        "গেয়েছেন",
        "গান গেয়েছে",
        "গান গেয়েছেন",
        "কতগুলো গান",
        "কতটি গান"
    ]

    if any(keyword in lower for keyword in song_keywords):

        intents.append("songs")


    # ======================================
    # Movies / Films
    # ======================================

    movie_keywords = [
        "movie",
        "movies",
        "film",
        "films",
        "cinema",
        "movie-তে",
        "movie তে",
        "সিনেমা",
        "সিনেমায়",
        "সিনেমাতে",
        "কোন সিনেমা",
        "কোন কোন সিনেমা",
        "ছবিতে"
    ]

    if any(keyword in lower for keyword in movie_keywords):

        intents.append("movies")


    # ======================================
    # Career
    # ======================================

    career_keywords = [
        "career",
        "profession",
        "profession",
        "ক্যারিয়ার",
        "পেশা",
        "কাজ",
        "কী করেন",
        "কি করেন"
    ]

    if any(keyword in lower for keyword in career_keywords):

        intents.append("career")


    # ======================================
    # Awards
    # ======================================

    award_keywords = [
        "award",
        "awards",
        "achievement",
        "achievements",
        "পুরস্কার",
        "অর্জন",
        "সম্মাননা"
    ]

    if any(keyword in lower for keyword in award_keywords):

        intents.append("awards")


    # ======================================
    # Family
    # ======================================

    family_keywords = [
        "father",
        "mother",
        "parents",
        "family",
        "বাবা",
        "মা",
        "পরিবার",
        "বাবা মা"
    ]

    if any(keyword in lower for keyword in family_keywords):

        intents.append("family")


    # ======================================
    # Education
    # ======================================

    education_keywords = [
        "education",
        "school",
        "college",
        "university",
        "study",
        "পড়াশোনা",
        "শিক্ষা",
        "স্কুল",
        "কলেজ",
        "বিশ্ববিদ্যালয়"
    ]

    if any(keyword in lower for keyword in education_keywords):

        intents.append("education")


    # ======================================
    # Biography / General Summary
    # ======================================

    biography_keywords = [
        "about",
        "biography",
        "bio",
        "summary",
        "life",
        "সম্পর্কে",
        "জীবনী",
        "জীবন",
        "সারাংশ",
        "সংক্ষেপে",
        "পরিচয়"
    ]

    if any(keyword in lower for keyword in biography_keywords):

        intents.append("biography")


    # ======================================
    # If nothing detected
    # ======================================

    if not intents:

        intents.append("general")


    # ======================================
    # Remove duplicates
    # ======================================

    intents = list(dict.fromkeys(intents))


    # ======================================
    # Build search query
    # ======================================

    search_query = build_search_query(
        text,
        intents
    )


    return {

        "question": text,

        "intents": intents,

        "search_query": search_query,

        "intent_count": len(intents)

    }


# ==========================================
# Build Better Search Query
# ==========================================

def build_search_query(
    question,
    intents
):

    parts = [question]


    if "date_of_birth" in intents:

        parts.append(
            "date of birth born"
        )


    if "songs" in intents:

        parts.append(
            "songs singing discography"
        )


    if "movies" in intents:

        parts.append(
            "films movies soundtrack"
        )


    if "career" in intents:

        parts.append(
            "career biography"
        )


    if "awards" in intents:

        parts.append(
            "awards achievements"
        )


    if "family" in intents:

        parts.append(
            "family parents"
        )


    if "education" in intents:

        parts.append(
            "education school university"
        )


    return " ".join(parts)


# ==========================================
# Human Readable Intent
# ==========================================

def get_intent_labels(intents):

    labels = {

        "date_of_birth":
            "Date of Birth",

        "songs":
            "Songs / Music",

        "movies":
            "Movies / Films",

        "career":
            "Career",

        "awards":
            "Awards",

        "family":
            "Family",

        "education":
            "Education",

        "biography":
            "Biography",

        "general":
            "General Information"

    }


    return [
        labels.get(
            intent,
            intent
        )
        for intent in intents
    ]