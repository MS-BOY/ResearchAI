"""
Advanced Research AI Backend
============================

Supports:
- Local Flask development
- Render production
- Gunicorn
- CORS
- Health check
- Research API
- Frontend serving
- Safe error handling
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from urllib.parse import urlparse

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "Research AI Backend"

DEFAULT_PORT = 5000

MAX_REQUEST_SIZE = 2 * 1024 * 1024

MAX_SOURCES_TO_READ = 4

MAX_SOURCE_TEXT = 8000

MAX_QUESTION_LENGTH = 5000

MAX_SEARCH_QUERY_LENGTH = 1000


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

INDEX_FILE = os.path.join(
    FRONTEND_DIR,
    "index.html"
)


# ============================================================
# IMPORT RESEARCH TOOLS
# ============================================================

TOOLS_LOADED = False
research_tools_error = None

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

    print(
        "✅ All research tools loaded successfully"
    )

except Exception as error:

    research_tools_error = str(error)

    print(
        "❌ Research tools failed to load:"
    )

    print(
        research_tools_error
    )

    traceback.print_exc()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_SIZE


# ============================================================
# CORS
# ============================================================

CORS(
    app,
    resources={
        r"/research": {
            "origins": "*"
        },
        r"/api/*": {
            "origins": "*"
        }
    }
)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    text = str(text or "")

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
# TRANSLATION
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

    except Exception as error:

        print(
            "⚠️ Translation failed:",
            error
        )

    return text


# ============================================================
# URL VALIDATION
# ============================================================

def is_valid_http_url(url):

    try:

        parsed = urlparse(
            str(url)
        )

        return (
            parsed.scheme in (
                "http",
                "https"
            )
            and
            bool(parsed.netloc)
        )

    except Exception:

        return False


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    if not os.path.isfile(
        INDEX_FILE
    ):

        return jsonify({

            "success": False,

            "error":
                "frontend/index.html not found",

            "frontend_directory":
                FRONTEND_DIR,

            "base_directory":
                BASE_DIR

        }), 404

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

@app.route(
    "/<path:filename>",
    methods=["GET"]
)
def frontend_files(filename):

    # Don't handle API routes here

    if filename.startswith("api/"):

        return jsonify({

            "success": False,

            "error":
                "API endpoint not found"

        }), 404


    if filename == "research":

        return jsonify({

            "success": False,

            "error":
                "Research endpoint requires POST"

        }), 405


    file_path = os.path.join(
        FRONTEND_DIR,
        filename
    )


    # Security check

    try:

        frontend_real = os.path.realpath(
            FRONTEND_DIR
        )

        file_real = os.path.realpath(
            file_path
        )

        if not file_real.startswith(
            frontend_real
        ):

            return jsonify({

                "success": False,

                "error":
                    "Invalid file path"

            }), 403

    except Exception:

        return jsonify({

            "success": False,

            "error":
                "Invalid file path"

        }), 403


    if os.path.isfile(
        file_real
    ):

        return send_from_directory(
            FRONTEND_DIR,
            filename
        )


    return jsonify({

        "success": False,

        "error":
            "Frontend file not found",

        "file":
            filename

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

        "success": True,

        "status":
            "online",

        "service":
            APP_NAME,

        "tools_loaded":
            TOOLS_LOADED,

        "frontend_exists":
            os.path.isfile(
                INDEX_FILE
            ),

        "environment":
            "render"
            if os.environ.get("RENDER")
            else "local",

        "python_version":
            sys.version.split()[0]

    })


# ============================================================
# SIMPLE ROOT API HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def simple_health():

    return jsonify({

        "status":
            "ok",

        "service":
            APP_NAME

    })


# ============================================================
# RESEARCH API
# ============================================================

@app.route(
    "/research",
    methods=["POST"]
)
def research_api():

    started_at = time.time()

    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 RESEARCH AI REQUEST"
    )

    print(
        "=" * 70
    )


    # ========================================================
    # CHECK TOOLS
    # ========================================================

    if not TOOLS_LOADED:

        return jsonify({

            "success": False,

            "error":
                "Research tools failed to load.",

            "details":
                research_tools_error

        }), 500


    # ========================================================
    # JSON
    # ========================================================

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):

        return jsonify({

            "success": False,

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

            "success": False,

            "error":
                "Question is required"

        }), 400


    if len(question) > MAX_QUESTION_LENGTH:

        return jsonify({

            "success": False,

            "error":
                "Question is too long",

            "max_length":
                MAX_QUESTION_LENGTH

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
        f"🌐 Detected: {detected_language}"
    )

    print(
        f"🗣️ Answer: {answer_language}"
    )


    # ========================================================
    # QUESTION ANALYSIS
    # ========================================================

    try:

        analysis = analyze_question(
            question
        )

        if not isinstance(
            analysis,
            dict
        ):
            analysis = {}

    except Exception as error:

        print(
            "⚠️ Question analyzer failed:",
            error
        )

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

    search_query = str(
        search_query or question
    ).strip()


    search_query = search_query[
        :MAX_SEARCH_QUERY_LENGTH
    ]


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: {search_query}"
    )


    # ========================================================
    # SEARCH
    # ========================================================

    print(
        "\n🔎 Searching internet..."
    )

    try:

        results = search_web(
            search_query
        )

    except Exception as error:

        print(
            "❌ Search failed:",
            error
        )

        traceback.print_exc()

        return jsonify({

            "success": False,

            "error":
                "Internet search failed",

            "details":
                str(error),

            "question":
                question,

            "search_query":
                search_query

        }), 502


    if not isinstance(
        results,
        list
    ):
        results = []


    print(
        f"📚 Search results: "
        f"{len(results)}"
    )


    # ========================================================
    # NO RESULTS
    # ========================================================

    if not results:

        message = (

            "কোনো search result পাওয়া যায়নি।"

            if answer_language == "বাংলা"

            else

            "No search results were found."

        )

        return jsonify({

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
    # READ SOURCES
    # ========================================================

    sources = []

    results_to_read = results[
        :MAX_SOURCES_TO_READ
    ]


    for index, result_item in enumerate(
        results_to_read,
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


        if not is_valid_http_url(
            url
        ):

            print(
                f"⚠️ Invalid URL: {url}"
            )

            continue


        print(
            f"\n📖 Reading source "
            f"{index}/{len(results_to_read)}"
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

        except Exception as error:

            print(
                "⚠️ Page read failed:",
                error
            )

            text = ""


        if not text:
            continue


        text = str(
            text
        ).strip()


        if len(text) < 50:
            continue


        sources.append({

            "title":
                title,

            "url":
                url,

            "text":
                text[
                    :MAX_SOURCE_TEXT
                ]

        })


        print(
            "✅ Source accepted"
        )


        # Three good sources enough

        if len(sources) >= 3:
            break


    source_count = len(
        sources
    )


    print(
        f"\n📚 Readable sources: "
        f"{source_count}"
    )


    # ========================================================
    # NO READABLE SOURCE
    # ========================================================

    if source_count == 0:

        if answer_language == "বাংলা":

            message = (
                "Search result পাওয়া গেছে, "
                "কিন্তু কোনো webpage থেকে "
                "readable text পাওয়া যায়নি।"
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
                0,

            "summary":
                message,

            "structured":
                {},

            "sources":
                []

        })


    # ========================================================
    # SUMMARY
    # ========================================================

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

        except Exception as error:

            print(
                "❌ Summary failed:",
                error
            )

            summary = ""

    except Exception as error:

        print(
            "❌ Summary failed:",
            error
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

    try:

        structured = build_structured_research(

            sources,

            intents

        )

    except Exception as error:

        print(
            "⚠️ Structured research failed:",
            error
        )

        structured = {}


    if not isinstance(
        structured,
        dict
    ):

        structured = {}


    # ========================================================
    # TRANSLATE SUMMARY
    # ========================================================

    translated_summary = translate_text(
        summary,
        answer_language
    )


    # ========================================================
    # TRANSLATE STRUCTURED DATA
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

    except Exception:

        intent_labels = {}


    # ========================================================
    # EXECUTION TIME
    # ========================================================

    execution_time = round(
        time.time() - started_at,
        2
    )


    # ========================================================
    # RESPONSE
    # ========================================================

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
            source_count,

        "summary":
            translated_summary,

        "structured":
            translated_sections,

        "sources":
            sources,

        "execution_time":
            execution_time

    }


    print(
        "\n" + "=" * 70
    )

    print(
        "✅ RESEARCH COMPLETED"
    )

    print(
        f"📚 Sources: {source_count}"
    )

    print(
        f"⏱️ Time: {execution_time}s"
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

        "success":
            False,

        "error":
            "Internal server error",

        "details":
            str(error)

    }), 500


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def handle_not_found(error):

    return jsonify({

        "success":
            False,

        "error":
            "Endpoint not found",

        "path":
            request.path

    }), 404


# ============================================================
# 413
# ============================================================

@app.errorhandler(413)
def handle_too_large(error):

    return jsonify({

        "success":
            False,

        "error":
            "Request is too large",

        "max_size":
            "2 MB"

    }), 413


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            DEFAULT_PORT
        )
    )

    print(
        "\n🚀 " + APP_NAME
    )

    print(
        f"🌐 Local port: {port}"
    )

    print(
        f"📁 Base directory: {BASE_DIR}"
    )

    print(
        f"📁 Frontend: {FRONTEND_DIR}"
    )

    print(
        f"📄 index.html: "
        f"{os.path.isfile(INDEX_FILE)}"
    )

    print(
        f"🧰 Tools loaded: "
        f"{TOOLS_LOADED}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True
    )
