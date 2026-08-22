
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


# ============================================================
# IMPORT TOOLS
# ============================================================

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

    print("✅ All research tools loaded successfully")


except Exception as e:

    TOOLS_LOADED = False

    print("❌ Tool import error:")
    print(str(e))

    traceback.print_exc()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

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


# ============================================================
# ANSWER LANGUAGE
# ============================================================

def get_answer_language(
    requested_language,
    detected_language
):

    requested_language = str(
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


# ============================================================
# SAFE TRANSLATION
# ============================================================

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
            str(e)
        )

        traceback.print_exc()

    return text


# ============================================================
# HOME / FRONTEND
# ============================================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    print(
        "🏠 Frontend request"
    )

    print(
        "📁 Frontend:",
        FRONTEND_DIR
    )

    if not os.path.exists(index_file):

        print(
            "❌ index.html not found:",
            index_file
        )

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


# ============================================================
# STATIC FILES
# ============================================================

@app.route("/<path:filename>")
def frontend_files(filename):

    # API route-গুলো এখানে যাবে না
    if filename.startswith("research"):
        return jsonify({
            "error": "API endpoint not found"
        }), 404

    if filename.startswith("api/"):
        return jsonify({
            "error": "API endpoint not found"
        }), 404

    file_path = os.path.join(
        FRONTEND_DIR,
        filename
    )

    if os.path.isfile(file_path):

        return send_from_directory(
            FRONTEND_DIR,
            filename
        )

    return jsonify({
        "error": "Frontend file not found",
        "file": filename
    }), 404


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "online",

        "message":
            "Research AI Backend is running",

        "tools_loaded":
            TOOLS_LOADED,

        "frontend_exists":
            os.path.exists(
                os.path.join(
                    FRONTEND_DIR,
                    "index.html"
                )
            )

    })


# ============================================================
# RESEARCH API
# ============================================================

@app.route(
    "/research",
    methods=["POST"]
)
def research():

    print("\n")
    print("=" * 70)
    print("🤖 RESEARCH AI REQUEST")
    print("=" * 70)


    # ========================================================
    # CHECK TOOLS
    # ========================================================

    if not TOOLS_LOADED:

        return jsonify({

            "error":
                "Research tools failed to load.",

            "details":
                "Check Render logs for import errors."

        }), 500


    # ========================================================
    # READ JSON
    # ========================================================

    try:

        data = request.get_json(
            silent=True
        )

    except Exception as e:

        print(
            "❌ JSON error:",
            str(e)
        )

        return jsonify({

            "error":
                "Invalid JSON request",

            "details":
                str(e)

        }), 400


    if not isinstance(
        data,
        dict
    ):

        return jsonify({

            "error":
                "Invalid JSON request"

        }), 400


    # ========================================================
    # QUESTION
    # ========================================================

    question = str(
        data.get(
            "question",
            ""
        )
    ).strip()


    requested_language = str(
        data.get(
            "language",
            "auto"
        )
    ).strip()


    if not question:

        return jsonify({

            "error":
                "Question is required"

        }), 400


    print(
        f"❓ Question: {question}"
    )

    print(
        f"🌐 Requested language: "
        f"{requested_language}"
    )


    # ========================================================
    # LANGUAGE
    # ========================================================

    detected_language = detect_language(
        question
    )

    answer_language = get_answer_language(
        requested_language,
        detected_language
    )


    print(
        f"🌐 Detected language: "
        f"{detected_language}"
    )

    print(
        f"🗣️ Answer language: "
        f"{answer_language}"
    )


    # ========================================================
    # QUESTION ANALYSIS
    # ========================================================

    print(
        "\n🧠 Analyzing question..."
    )


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
            "⚠️ Question analyzer failed:",
            str(e)
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


    search_query = str(
        search_query
    ).strip()


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: {search_query}"
    )


    # ========================================================
    # SEARCH WEB
    # ========================================================

    print(
        "\n🔎 Searching internet..."
    )

    try:

        results = search_web(
            search_query
        )

    except Exception as e:

        print(
            "❌ Search failed:"
        )

        print(
            str(e)
        )

        traceback.print_exc()

        return jsonify({

            "error":
                "Internet search failed",

            "details":
                str(e),

            "question":
                question,

            "search_query":
                search_query

        }), 500


    if not isinstance(
        results,
        list
    ):

        results = []


    print(
        f"📚 Search results found: "
        f"{len(results)}"
    )


    # ========================================================
    # NO SEARCH RESULTS
    # ========================================================

    if not results:

        message = (

            "কোনো search result পাওয়া যায়নি।"

            if answer_language == "বাংলা"

            else

            "No search results were found."

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


    # ========================================================
    # READ WEB SOURCES
    # ========================================================

    sources = []


    for index, result_item in enumerate(
        results,
        1
    ):

        if not isinstance(
            result_item,
            dict
        ):

            continue


        title = str(
            result_item.get(
                "title",
                "Untitled source"
            )
        ).strip()


        url = str(
            result_item.get(
                "url",
                ""
            )
        ).strip()


        if not url:

            print(
                f"⚠️ Source {index}: URL missing"
            )

            continue


        print(
            "\n" + "-" * 60
        )

        print(
            f"📖 Reading source "
            f"{index}/{len(results)}"
        )

        print(
            f"📄 Title: {title}"
        )

        print(
            f"🔗 URL: {url}"
        )


        # ====================================================
        # READ PAGE
        # ====================================================

        try:

            text = read_page(
                url
            )

        except Exception as e:

            print(
                "❌ Page read exception:"
            )

            print(
                str(e)
            )

            traceback.print_exc()

            text = ""


        if not text:

            print(
                "⚠️ No readable text"
            )

            continue


        text = str(
            text
        ).strip()


        if len(text) < 50:

            print(
                "⚠️ Page text too short"
            )

            continue


        sources.append({

            "title":
                title,

            "url":
                url,

            "text":
                text[:8000]

        })


        print(
            "✅ Source added"
        )

        print(
            f"📝 Characters: "
            f"{len(text)}"
        )


    # ========================================================
    # SOURCE COUNT
    # ========================================================

    source_count = len(
        sources
    )


    print(
        "\n📚 Readable sources:",
        source_count
    )


    # ========================================================
    # NO READABLE SOURCES
    # ========================================================

    if source_count == 0:

        if answer_language == "বাংলা":

            message = (
                "Search result পাওয়া গেছে, "
                "কিন্তু কোনো webpage থেকে readable text "
                "পাওয়া যায়নি।"
            )

        else:

            message = (
                "Search completed, but no webpage "
                "could be read."
            )


        try:

            intent_labels = get_intent_labels(
                intents
            )

        except Exception:

            intent_labels = {}


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
                intent_labels,

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


    # ========================================================
    # CREATE SUMMARY
    # ========================================================

    print(
        "\n🧠 Creating intelligent summary..."
    )


    try:

        summary = build_research_summary(

            sources,

            intents=intents,

            max_sentences_per_source=5,

            max_total_sentences=20

        )

    except TypeError:

        print(
            "⚠️ Summarizer does not support intents parameter."
        )

        try:

            summary = build_research_summary(

                sources,

                max_sentences_per_source=5,

                max_total_sentences=20

            )

        except Exception as e:

            print(
                "❌ Summary fallback failed:",
                str(e)
            )

            traceback.print_exc()

            summary = ""


    except Exception as e:

        print(
            "❌ Summary failed:",
            str(e)
        )

        traceback.print_exc()

        summary = ""


    if not summary:

        summary = (
            "No relevant information was found."
        )


    # ========================================================
    # STRUCTURED RESEARCH
    # ========================================================

    print(
        "\n📊 Creating structured research..."
    )


    try:

        structured = build_structured_research(

            sources,

            intents

        )

    except Exception as e:

        print(
            "⚠️ Structured research failed:",
            str(e)
        )

        traceback.print_exc()

        structured = {}


    if not isinstance(
        structured,
        dict
    ):

        structured = {}


    # ========================================================
    # TRANSLATE SUMMARY
    # ========================================================

    print(
        "\n🌐 Translating summary..."
    )


    translated_summary = translate_text(

        summary,

        answer_language

    )


    # ========================================================
    # TRANSLATE STRUCTURED SECTIONS
    # ========================================================

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


    # ========================================================
    # INTENT LABELS
    # ========================================================

    try:

        intent_labels = get_intent_labels(
            intents
        )

    except Exception as e:

        print(
            "⚠️ Intent label error:",
            str(e)
        )

        intent_labels = {}


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

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
            source_count,

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
        f"❓ Question: {question}"
    )

    print(
        f"🔎 Query: {search_query}"
    )

    print(
        f"📚 Sources: {source_count}"
    )

    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🌐 Language: {answer_language}"
    )

    print(
        "=" * 70
    )


    return jsonify(
        response
    )


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.errorhandler(Exception)
def handle_exception(error):

    print(
        "\n❌ UNHANDLED SERVER ERROR"
    )

    print(
        str(error)
    )

    traceback.print_exc()


    return jsonify({

        "error":
            "Internal server error",

        "details":
            str(error)

    }), 500


# ============================================================
# START SERVER
# ============================================================

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

    print(
        f"📁 Base directory: {BASE_DIR}"
    )

    print(
        f"📁 Frontend directory: "
        f"{FRONTEND_DIR}"
    )

    print(
        f"📄 index.html exists: "
        f"{os.path.exists(
            os.path.join(
                FRONTEND_DIR,
                "index.html"
            )
        )}"
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
