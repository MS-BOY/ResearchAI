from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
import os


# ==========================================
# Project Directory
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    BASE_DIR
)


# ==========================================
# Researcher
# ==========================================

from tools.researcher import (
    search_web,
    read_page
)


# ==========================================
# Question Analyzer
# ==========================================

from tools.question_analyzer import (
    analyze_question,
    get_intent_labels
)


# ==========================================
# Summarizer
# ==========================================

from tools.summarizer import (
    build_research_summary,
    build_structured_research
)


# ==========================================
# Translator
# ==========================================

from tools.translator import (
    translate_to_bangla,
    translate_to_english
)


# ==========================================
# Flask
# ==========================================

app = Flask(__name__)

CORS(app)


# ==========================================
# Language Detection
# ==========================================

def detect_language(text):

    bangla_count = 0
    english_count = 0


    for char in text:

        if '\u0980' <= char <= '\u09FF':

            bangla_count += 1

        elif char.isalpha():

            english_count += 1


    if bangla_count > english_count:

        return "বাংলা"


    return "English"


# ==========================================
# Answer Language
# ==========================================

def get_answer_language(
    requested_language,
    detected_language
):

    if requested_language == "bangla":

        return "বাংলা"


    if requested_language == "english":

        return "English"


    return detected_language


# ==========================================
# Safe Translation
# ==========================================

def translate_text(
    text,
    language
):

    if not text:

        return ""


    try:

        if language == "বাংলা":

            return translate_to_bangla(
                text
            )


        if language == "English":

            return translate_to_english(
                text
            )


    except Exception as e:

        print(
            "⚠️ Translation error:",
            e
        )


    return text


# ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    return jsonify({

        "status":
            "online",

        "message":
            "Research AI Backend is running"

    })


# ==========================================
# Research API
# ==========================================

@app.route(
    "/research",
    methods=["POST"]
)
def research():

    # ======================================
    # JSON
    # ======================================

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "error":
                "Invalid JSON request"

        }), 400


    # ======================================
    # Question
    # ======================================

    question = data.get(
        "question",
        ""
    ).strip()


    # ======================================
    # Language
    # ======================================

    requested_language = data.get(
        "language",
        "auto"
    )


    # ======================================
    # Validate
    # ======================================

    if not question:

        return jsonify({

            "error":
                "Question is required"

        }), 400


    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 RESEARCH AI"
    )

    print(
        f"❓ Question: {question}"
    )


    # ======================================
    # Language
    # ======================================

    detected_language = detect_language(
        question
    )


    answer_language = get_answer_language(
        requested_language,
        detected_language
    )


    print(
        f"🌐 Detected: "
        f"{detected_language}"
    )

    print(
        f"🗣️ Answer: "
        f"{answer_language}"
    )


    # ======================================
    # Analyze Question
    # ======================================

    print(
        "\n🧠 Analyzing question..."
    )


    analysis = analyze_question(
        question
    )


    intents = analysis["intents"]

    search_query = analysis[
        "search_query"
    ]


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: "
        f"{search_query}"
    )


    # ======================================
    # Search
    # ======================================

    print(
        "\n🔎 Searching internet..."
    )


    try:

        results = search_web(
            search_query
        )


    except Exception as e:

        print(
            "❌ Search error:",
            e
        )


        return jsonify({

            "error":
                "Internet search failed",

            "details":
                str(e)

        }), 500


    print(
        f"📚 Results found: "
        f"{len(results)}"
    )


    # ======================================
    # Read Sources
    # ======================================

    sources = []


    for index, result in enumerate(
        results,
        1
    ):

        print(
            f"\n📖 Reading "
            f"{index}/{len(results)}"
        )


        print(
            result["title"]
        )


        try:

            text = read_page(
                result["url"]
            )


        except Exception as e:

            print(
                "⚠️ Read error:",
                e
            )

            text = ""


        if not text:

            print(
                "⚠️ No readable text"
            )

            continue


        sources.append({

            "title":
                result["title"],

            "url":
                result["url"],

            "text":
                text[:8000]

        })


        print(
            "✅ Source added"
        )


    # ======================================
    # No Sources
    # ======================================

    if not sources:

        return jsonify({

            "question":
                question,

            "answer_language":
                answer_language,

            "source_count":
                0,

            "summary":
                "কোনো readable source পাওয়া যায়নি।"
                if answer_language == "বাংলা"
                else
                "No readable sources were found.",

            "sources":
                []

        })


    # ======================================
    # Create Summary
    # ======================================

    print(
        "\n🧠 Creating intelligent summary..."
    )


    summary = build_research_summary(

        sources,

        intents=intents,

        max_sentences_per_source=5,

        max_total_sentences=20

    )


    # ======================================
    # Structured Research
    # ======================================

    structured = build_structured_research(

        sources,

        intents

    )


    # ======================================
    # Empty Summary
    # ======================================

    if not summary:

        summary = (
            "No relevant information "
            "was found."
        )


    # ======================================
    # Translate Main Summary
    # ======================================

    print(
        "\n🌐 Translating summary..."
    )


    translated_summary = translate_text(

        summary,

        answer_language

    )


    # ======================================
    # Translate Structured Sections
    # ======================================

    translated_sections = {}


    for intent, sentences in structured.items():

        if not sentences:

            translated_sections[
                intent
            ] = []

            continue


        section_text = "\n\n".join(
            sentences
        )


        translated = translate_text(

            section_text,

            answer_language

        )


        translated_sections[
            intent
        ] = translated


    # ======================================
    # Translate Source Text
    # ======================================
    #
    # আমরা পুরো source translate করছি না।
    # এতে translation request অনেক বেড়ে যায়।
    #
    # Frontend-এ মূল source text রাখতে পারো।
    #
    # ======================================

    output_sources = []


    for source in sources:

        output_sources.append({

            "title":
                source["title"],

            "url":
                source["url"],

            "text":
                source["text"]

        })


    # ======================================
    # Intent Labels
    # ======================================

    intent_labels = get_intent_labels(
        intents
    )


    # ======================================
    # Response
    # ======================================

    response = {

        "question":
            question,

        "detected_language":
            detected_language,

        "answer_language":
            answer_language,

        "intents":
            intents,

        "intent_labels":
            intent_labels,

        "search_query":
            search_query,

        "source_count":
            len(output_sources),

        "summary":
            translated_summary,

        "structured":
            translated_sections,

        "sources":
            output_sources

    }


    # ======================================
    # Console
    # ======================================

    print(
        "\n" + "=" * 70
    )

    print(
        "✅ Research completed"
    )

    print(
        f"📚 Sources: "
        f"{len(output_sources)}"
    )

    print(
        f"🎯 Intents: "
        f"{', '.join(intents)}"
    )

    print(
        f"🌐 Final language: "
        f"{answer_language}"
    )

    print(
        "=" * 70
    )


    return jsonify(
        response
    )


# ==========================================
# Start Server
# ==========================================

if __name__ == "__main__":

    print(
        "\n🚀 Research AI Backend"
    )

    print(
        "🌐 http://127.0.0.1:5000"
    )


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )