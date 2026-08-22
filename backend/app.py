from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback


# =========================================================
# PROJECT DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =========================================================
# FRONTEND
# =========================================================

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


# =========================================================
# IMPORT TOOLS
# =========================================================

try:

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

    TOOLS_LOADED = True

    print("✅ All tools imported successfully")


except Exception as e:

    TOOLS_LOADED = False

    print("❌ TOOL IMPORT ERROR")
    print(str(e))

    traceback.print_exc()


# =========================================================
# FLASK
# =========================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(text):

    text = str(text)

    bangla_count = 0
    english_count = 0

    for char in text:

        if "\u0980" <= char <= "\u09FF":

            bangla_count += 1

        elif char.isalpha():

            english_count += 1


    if bangla_count > english_count:

        return "বাংলা"


    return "English"


# =========================================================
# ANSWER LANGUAGE
# =========================================================

def get_answer_language(
    requested_language,
    detected_language
):

    value = str(
        requested_language or "auto"
    ).lower().strip()


    if value in (
        "bangla",
        "bn",
        "বাংলা"
    ):

        return "বাংলা"


    if value in (
        "english",
        "en"
    ):

        return "English"


    return detected_language


# =========================================================
# SAFE TRANSLATION
# =========================================================

def translate_text(
    text,
    language
):

    if not text:

        return ""


    try:

        if language == "বাংলা":

            result = translate_to_bangla(
                text
            )

        elif language == "English":

            result = translate_to_english(
                text
            )

        else:

            result = text


        if result:

            return result


        return text


    except Exception as e:

        print(
            "⚠️ Translation failed:",
            str(e)
        )

        traceback.print_exc()

        # Translation fail করলে original
        # summary return হবে

        return text


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )


    if not os.path.exists(
        index_file
    ):

        return jsonify({

            "error":
                "frontend/index.html not found",

            "frontend_directory":
                FRONTEND_DIR

        }), 404


    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "online",

        "tools_loaded":
            TOOLS_LOADED,

        "message":
            "Research AI Backend is running"

    })


# =========================================================
# DEBUG / TEST SEARCH
# =========================================================

@app.route(
    "/api/test-search",
    methods=["GET"]
)
def test_search():

    if not TOOLS_LOADED:

        return jsonify({

            "success":
                False,

            "error":
                "Tools could not be imported"

        }), 500


    try:

        results = search_web(
            "What is artificial intelligence?"
        )


        if not isinstance(
            results,
            list
        ):

            results = []


        return jsonify({

            "success":
                True,

            "result_count":
                len(results),

            "results":
                results

        })


    except Exception as e:

        print(
            "❌ TEST SEARCH ERROR:"
        )

        traceback.print_exc()


        return jsonify({

            "success":
                False,

            "error":
                str(e),

            "type":
                type(e).__name__

        }), 500


# =========================================================
# RESEARCH API
# =========================================================
@app.route("/research", methods=["POST"])
def research():

    try:

        print("\n" + "=" * 70)
        print("🤖 RESEARCH REQUEST STARTED")

        # ======================================
        # JSON
        # ======================================

        data = request.get_json(silent=True)

        print("📦 Request data:", data)

        if not isinstance(data, dict):

            return jsonify({
                "success": False,
                "error": "Invalid JSON request"
            }), 400

        # ======================================
        # Question
        # ======================================

        question = str(
            data.get("question", "")
        ).strip()

        requested_language = str(
            data.get("language", "auto")
        ).strip()

        if not question:

            return jsonify({
                "success": False,
                "error": "Question is required"
            }), 400

        print("❓ Question:", question)
        print("🌐 Requested language:", requested_language)

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
            "🌐 Detected:",
            detected_language
        )

        print(
            "🗣️ Answer:",
            answer_language
        )

        # ======================================
        # Question Analyzer
        # ======================================

        print("\n🧠 Analyzing question...")

        try:

            analysis = analyze_question(
                question
            )

            if not isinstance(
                analysis,
                dict
            ):
                analysis = {}

        except Exception as e:

            print(
                "⚠️ Analyzer failed:",
                repr(e)
            )

            traceback.print_exc()

            analysis = {}

        intents = analysis.get(
            "intents",
            []
        )

        if not isinstance(
            intents,
            list
        ):
            intents = []

        search_query = analysis.get(
            "search_query",
            question
        )

        if not search_query:

            search_query = question

        print(
            "🎯 Intents:",
            intents
        )

        print(
            "🔎 Search query:",
            search_query
        )

        # ======================================
        # WEB SEARCH
        # ======================================

        print("\n🔎 Searching web...")

        try:

            results = search_web(
                search_query
            )

        except Exception as e:

            print(
                "❌ SEARCH ERROR:",
                repr(e)
            )

            traceback.print_exc()

            return jsonify({

                "success": False,

                "error":
                    "Internet search failed",

                "details":
                    str(e),

                "question":
                    question

            }), 500

        if not isinstance(
            results,
            list
        ):
            results = []

        print(
            f"📚 Search results: {len(results)}"
        )

        # ======================================
        # READ WEB PAGES
        # ======================================

        sources = []

        for index, item in enumerate(
            results,
            1
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            title = str(
                item.get(
                    "title",
                    "Untitled source"
                )
            )

            url = str(
                item.get(
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
                "📄",
                title
            )

            print(
                "🔗",
                url
            )

            try:

                text = read_page(
                    url
                )

            except Exception as e:

                print(
                    "⚠️ READ ERROR:",
                    repr(e)
                )

                traceback.print_exc()

                text = ""

            if not text:

                print(
                    "⏭️ Skipping unreadable source"
                )

                continue

            sources.append({

                "title":
                    title,

                "url":
                    url,

                "text":
                    str(text)[:8000]

            })

            print(
                "✅ Source added"
            )

        print(
            f"\n📚 Readable sources: {len(sources)}"
        )

        # ======================================
        # NO SOURCES
        # ======================================

        if len(sources) == 0:

            if answer_language == "বাংলা":

                message = (
                    "Search result পাওয়া গেলেও "
                    "কোনো webpage থেকে readable text "
                    "পাওয়া যায়নি।"
                )

            else:

                message = (
                    "Search results were found, "
                    "but no webpage returned readable text."
                )

            try:

                labels = get_intent_labels(
                    intents
                )

            except Exception:

                labels = {}

            return jsonify({

                "success": True,

                "question":
                    question,

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
        # SUMMARY
        # ======================================

        print(
            "\n🧠 Creating summary..."
        )

        try:

            try:

                summary = build_research_summary(

                    sources,

                    intents=intents,

                    max_sentences_per_source=5,

                    max_total_sentences=20

                )

            except TypeError:

                summary = build_research_summary(

                    sources,

                    max_sentences_per_source=5,

                    max_total_sentences=20

                )

        except Exception as e:

            print(
                "⚠️ SUMMARY ERROR:",
                repr(e)
            )

            traceback.print_exc()

            summary = ""

        if not summary:

            summary = (
                "Relevant information was found "
                "but a summary could not be generated."
            )

        # ======================================
        # STRUCTURED
        # ======================================

        print(
            "\n🧩 Building structured research..."
        )

        try:

            structured = build_structured_research(
                sources,
                intents
            )

        except Exception as e:

            print(
                "⚠️ STRUCTURED ERROR:",
                repr(e)
            )

            traceback.print_exc()

            structured = {}

        if not isinstance(
            structured,
            dict
        ):

            structured = {}

        # ======================================
        # TRANSLATION
        # ======================================

        print(
            "\n🌐 Translating..."
        )

        try:

            translated_summary = translate_text(
                summary,
                answer_language
            )

        except Exception as e:

            print(
                "⚠️ TRANSLATION ERROR:",
                repr(e)
            )

            translated_summary = summary

        # ======================================
        # STRUCTURED TRANSLATION
        # ======================================

        translated_sections = {}

        for intent, sentences in structured.items():

            try:

                if isinstance(
                    sentences,
                    list
                ):

                    section_text = "\n\n".join(
                        str(x)
                        for x in sentences
                    )

                else:

                    section_text = str(
                        sentences
                    )

                translated_sections[
                    str(intent)
                ] = translate_text(
                    section_text,
                    answer_language
                )

            except Exception as e:

                print(
                    "⚠️ Section translation error:",
                    repr(e)
                )

                translated_sections[
                    str(intent)
                ] = str(sentences)

        # ======================================
        # INTENT LABELS
        # ======================================

        try:

            intent_labels = get_intent_labels(
                intents
            )

        except Exception as e:

            print(
                "⚠️ Intent label error:",
                repr(e)
            )

            intent_labels = {}

        # ======================================
        # FINAL RESPONSE
        # ======================================

        response = {

            "success":
                True,

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

        print(
            "\n" + "=" * 70
        )

        print(
            "✅ RESEARCH COMPLETED"
        )

        print(
            "📚 Sources:",
            len(sources)
        )

        print(
            "=" * 70
        )

        return jsonify(response), 200

    # ======================================
    # GLOBAL ERROR
    # ======================================

    except Exception as e:

        print(
            "\n❌❌❌ RESEARCH CRASHED ❌❌❌"
        )

        print(
            "ERROR:",
            repr(e)
        )

        traceback.print_exc()

        return jsonify({

            "success":
                False,

            "error":
                "Research process crashed",

            "details":
                str(e),

            "type":
                type(e).__name__

        }), 500


# =========================================================
# RUN LOCAL
# =========================================================

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
        f"🌐 Port: {port}"
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
