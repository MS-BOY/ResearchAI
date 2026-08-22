def understand(command):

    text = command.strip().lower()

    # Research / question
    question_words = [
        "কী",
        "কি",
        "কেন",
        "কিভাবে",
        "কীভাবে",
        "কোন",
        "কোনটা",
        "কত",
        "কখন",
        "বল",
        "জানাও",
        "তথ্য",
        "ব্যাখ্যা",
        "research",
        "explain",
        "what",
        "why",
        "how",
        "which",
        "information"
    ]

    # YouTube
    if "youtube" in text:

        query = (
            text
            .replace("youtube", "")
            .replace("search", "")
            .strip()
        )

        return {
            "tool": "youtube",
            "action": "search",
            "query": query
        }

    # Google explicitly requested
    if "google" in text:

        query = (
            text
            .replace("google", "")
            .replace("search", "")
            .strip()
        )

        return {
            "tool": "google",
            "action": "search",
            "query": query
        }

    # General question → Research
    for word in question_words:

        if word in text:

            return {
                "tool": "research",
                "action": "research",
                "query": command
            }

    # Default → Research
    return {
        "tool": "research",
        "action": "research",
        "query": command
    }