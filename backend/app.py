```python
from flask import Flask, request, jsonify, send_from_directory
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

sys.path.insert(0, BASE_DIR)


# ==========================================
# Tools
# ==========================================

from tools.researcher import (
    search_web,
    read_page
)

from tools.question_analyzer import (
    analyze_question,
    get_intent_labels
)

from tools.summarizer import (
    build_research_summary,
    build_structured_research
)

from tools.translator import (
    translate_to_bangla,
    translate_to_english
)


# ==========================================
# Flask App
# ==========================================

app = Flask(
    __name__,
    static_folder=os.path.join(
        BASE_DIR,
        "frontend"
    ),
    static_url_path=""
)

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

    requested_language = (
        requested_language or "auto"
    ).lower()

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

    # Translation fail হলে original text
    # return করবে
    return text


# ==========================================
# Frontend
# ==========================================

@app.route("/")
def home():

    frontend_path = os.path.join(
        BASE_DIR,
        "frontend"
    )

    return send_from_directory(
        frontend_path,
        "index.html"
    )


# ==========================================
# Health Check
# ==========================================

@app.route("/api/health")
def health():

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
    # Get JSON
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
    # Validation
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
    # Detect Language
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
        f"🗣️ Answer language: "
        f"{answer_language}"
    )


    # ======================================
    # Question Analysis
    # ======================================

    print(
        "\n🧠 Analyzing question..."
    )

    try:

        analysis = analyze_question(
            question
        )

    except Exception as e:

        print(
            "⚠️ Question analyzer error:",
            e
        )

        analysis = {

            "intents": [],

            "search_query":
                question

        }


    intents = analysis.get(
        "intents",
        []
    )

    search_query = analysis.get(
        "search_query",
        question
    )


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: "
        f"{search_query}"
    )


    # ======================================
    # Search Internet
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
        f"📚 Search results: "
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
            result.get(
                "title",
                "Untitled"
            )
        )


        url = result.get(
            "url",
            ""
        )


        if not url:
            continue


        try:

            text = read_page(
                url
            )

        except Exception as e:

            print(
                "⚠️ Page read error:",
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
                result.get(
                    "title",
                    "Untitled source"
                ),

            "url":
                url,

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

        no_source_message = (

            "কোনো readable source "
            "পাওয়া যায়নি।"

            if answer_language == "বাংলা"

            else

            "No readable sources were found."

        )


        return jsonify({

            "question":
                question,

            "detected_language":
                detected_language,

            "answer_language":
                answer_language,

            "intents":
                intents,

            "intent_labels":
                get_intent_labels(intents),

            "search_query":
                search_query,

            "source_count":
                0,

            "summary":
                no_source_message,

            "structured":
                {},

            "sources":
                []

        })


    # ======================================
    # Create Summary
    # ======================================

    print(
        "\n🧠 Creating research summary..."
    )


    try:

        summary = build_research_summary(

            sources,

            intents=intents,

            max_sentences_per_source=5,

            max_total_sentences=20

        )

    except TypeError:

        # যদি summarizer-এ intents parameter
        # না থাকে

        summary = build_research_summary(

            sources,

            max_sentences_per_source=5,

            max_total_sentences=20

        )

    except Exception as e:

        print(
            "⚠️ Summary error:",
            e
        )

        summary = ""


    if not summary:

        summary = (

            "No relevant information "
            "was found."

        )


    # ======================================
    # Structured Research
    # ======================================

    structured = {}


    try:

        structured = build_structured_research(

            sources,

            intents

        )

    except Exception as e:

        print(
            "⚠️ Structured research error:",
            e
        )

        structured = {}


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
            ] = ""

            continue


        # List হলে text বানানো
        if isinstance(
            sentences,
            list
        ):

            section_text = "\n\n".join(
                str(item)
                for item in sentences
            )

        else:

            section_text = str(
                sentences
            )


        translated_sections[
            intent
        ] = translate_text(

            section_text,

            answer_language

        )


    # ======================================
    # Intent Labels
    # ======================================

    try:

        intent_labels = get_intent_labels(
            intents
        )

    except Exception:

        intent_labels = {}


    # ======================================
    # Response Sources
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
    # Final Response
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

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    print(
        "\n🚀 Research AI Backend"
    )

    print(
        f"🌐 http://127.0.0.1:{port}"
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=True

    )
```
