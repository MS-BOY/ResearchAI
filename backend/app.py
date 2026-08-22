from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback


# ==========================================
# Project Directory
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
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

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# ==========================================
# Language Detection
# ==========================================

def detect_language(text):

    bangla_count = 0
    english_count = 0

    for char in str(text):

        if "\u0980" <= char <= "\u09FF":
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
    ).lower().strip()

    if requested_language in (
        "bangla",
        "bn",
        "বাংলা"
    ):
        return "বাংলা"

    if requested_language in (
        "english",
        "en"
    ):
        return "English"

    return detected_language


# ==========================================
# Safe Translation
# ==========================================

def translate_text(text, language):

    if not text:
        return ""

    try:

        if language == "বাংলা":
            return translate_to_bangla(text)

        if language == "English":
            return translate_to_english(text)

    except Exception as e:

        print(
            "⚠️ Translation error:",
            e
        )

    return text


# ==========================================
# Frontend
# ==========================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    if not os.path.exists(index_file):

        return jsonify({
            "error": "Frontend index.html not found"
        }), 404

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ==========================================
# Health
# ==========================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "online",
        "message": "Research AI Backend is running"
    })


# ==========================================
# Research
# ==========================================

@app.route("/research", methods=["POST"])
def research():

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        return jsonify({
            "error": "Invalid JSON request"
        }), 400


    question = str(
        data.get("question", "")
    ).strip()


    requested_language = data.get(
        "language",
        "auto"
    )


    if not question:

        return jsonify({
            "error": "Question is required"
        }), 400


    print("\n" + "=" * 70)
    print("🤖 RESEARCH AI")
    print(f"❓ Question: {question}")


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
        f"🌐 Detected: {detected_language}"
    )

    print(
        f"🗣️ Answer: {answer_language}"
    )


    # ======================================
    # Analyze
    # ======================================

    try:

        analysis = analyze_question(
            question
        )

    except Exception as e:

        print(
            "⚠️ Analyzer error:",
            e
        )

        analysis = {
            "intents": [],
            "search_query": question
        }


    if not isinstance(analysis, dict):
        analysis = {}


    intents = analysis.get(
        "intents",
        []
    )

    search_query = analysis.get(
        "search_query",
        question
    )


    if not search_query:
        search_query = question


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: {search_query}"
    )


    # ======================================
    # Search
    # ======================================

    try:

        results = search_web(
            search_query
        )

    except Exception as e:

        print(
            "❌ Search error:",
            e
        )

        traceback.print_exc()

        return jsonify({
            "error": "Internet search failed",
            "details": str(e)
        }), 500


    if not isinstance(results, list):
        results = []


    print(
        f"📚 Search results: {len(results)}"
    )


    # ======================================
    # Read Sources
    # ======================================

    sources = []


    for index, result in enumerate(
        results,
        1
    ):

        if not isinstance(result, dict):
            continue


        title = str(
            result.get(
                "title",
                "Untitled source"
            )
        )

        url = str(
            result.get(
                "url",
                ""
            )
        ).strip()


        if not url:
            continue


        print(
            f"\n📖 Reading {index}/{len(results)}"
        )

        print(
            f"📄 {title}"
        )

        print(
            f"🔗 {url}"
        )


        try:

            text = read_page(
                url
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

            "title": title,

            "url": url,

            "text": text[:8000]

        })


        print(
            "✅ Source added"
        )


    # ======================================
    # No Sources
    # ======================================

    if not sources:

        if answer_language == "বাংলা":

            message = (
                "কোনো readable source পাওয়া যায়নি। "
                "Search engine ফলাফল দিয়েছে কিনা অথবা "
                "website access করা যাচ্ছে কিনা পরীক্ষা করুন।"
            )

        else:

            message = (
                "No readable sources were found. "
                "The search engine may have returned no results "
                "or the websites may have blocked automated access."
            )


        try:

            labels = get_intent_labels(
                intents
            )

        except Exception:

            labels = {}


        return jsonify({

            "question": question,

            "detected_language":
                detected_language,

            "answer_language":
                answer_language,

            "intents":
                intents,

            "intent_labels":
                labels,

            "search_query":
                search_query,

            "source_count":
                0,

            "summary":
                message,

            "structured":
                {},

            "sources":
                []

        })


    # ======================================
    # Summary
    # ======================================

    print(
        "\n🧠 Creating summary..."
    )


    try:

        summary = build_research_summary(
            sources,
            intents=intents,
            max_sentences_per_source=5,
            max_total_sentences=20
        )

    except TypeError:

        try:

            summary = build_research_summary(
                sources,
                max_sentences_per_source=5,
                max_total_sentences=20
            )

        except Exception as e:

            print(
                "⚠️ Summary fallback error:",
                e
            )

            summary = ""

    except Exception as e:

        print(
            "⚠️ Summary error:",
            e
        )

        summary = ""


    if not summary:

        summary = (
            "No relevant information was found."
        )


    # ======================================
    # Structured Research
    # ======================================

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


    if not isinstance(
        structured,
        dict
    ):
        structured = {}


    # ======================================
    # Translate Summary
    # ======================================

    translated_summary = translate_text(
        summary,
        answer_language
    )


    # ======================================
    # Translate Sections
    # ======================================

    translated_sections = {}


    for intent, sentences in structured.items():

        if not sentences:

            translated_sections[
                intent
            ] = ""

            continue


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
            len(sources),

        "summary":
            translated_summary,

        "structured":
            translated_sections,

        "sources":
            sources

    }


    print("\n" + "=" * 70)

    print(
        "✅ Research completed"
    )

    print(
        f"📚 Readable sources: {len(sources)}"
    )

    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🌐 Language: {answer_language}"
    )

    print("=" * 70)


    return jsonify(response)


# ==========================================
# Error Handler
# ==========================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):

    print(
        "❌ Internal server error:",
        error
    )

    return jsonify({
        "error": "Internal server error"
    }), 500


# ==========================================
# Local Development
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
        debug=False
    )
