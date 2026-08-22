```python
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback
import time


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# If app.py is inside backend/
PROJECT_ROOT = os.path.dirname(
    CURRENT_DIR
)

# Add both locations to Python path
for path in [PROJECT_ROOT, CURRENT_DIR]:

    if path not in sys.path:
        sys.path.insert(0, path)


# ============================================================
# FRONTEND DIRECTORY
# ============================================================

FRONTEND_DIR = os.path.join(
    PROJECT_ROOT,
    "frontend"
)


# ============================================================
# TOOL STATUS
# ============================================================

TOOLS_LOADED = False

TOOL_IMPORT_ERROR = ""

search_web = None
read_page = None

analyze_question = None
get_intent_labels = None

build_research_summary = None
build_structured_research = None

translate_to_bangla = None
translate_to_english = None


# ============================================================
# LOAD TOOLS
# ============================================================

try:

    print("\n" + "=" * 70)
    print("🔧 LOADING RESEARCH TOOLS")
    print("=" * 70)

    # --------------------------------------------------------
    # Researcher
    # --------------------------------------------------------

    from tools.researcher import (
        search_web,
        read_page
    )

    print("✅ researcher.py loaded")


    # --------------------------------------------------------
    # Question Analyzer
    # --------------------------------------------------------

    from tools.question_analyzer import (
        analyze_question,
        get_intent_labels
    )

    print("✅ question_analyzer.py loaded")


    # --------------------------------------------------------
    # Summarizer
    # --------------------------------------------------------

    from tools.summarizer import (
        build_research_summary,
        build_structured_research
    )

    print("✅ summarizer.py loaded")


    # --------------------------------------------------------
    # Translator
    # --------------------------------------------------------

    from tools.translator import (
        translate_to_bangla,
        translate_to_english
    )

    print("✅ translator.py loaded")


    TOOLS_LOADED = True

    print("=" * 70)
    print("✅ ALL RESEARCH TOOLS LOADED")
    print("=" * 70)


except Exception as e:

    TOOLS_LOADED = False

    TOOL_IMPORT_ERROR = str(e)

    print("\n" + "=" * 70)
    print("❌ TOOL IMPORT ERROR")
    print("=" * 70)

    print("Error:")
    print(str(e))

    print("\nFull traceback:")

    traceback.print_exc()

    print("=" * 70)


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
# BASIC CONFIG
# ============================================================

app.config["JSON_AS_ASCII"] = False


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    text = str(
        text or ""
    )

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

def safe_translate(
    text,
    language
):

    if not text:

        return ""


    if language not in (
        "বাংলা",
        "English"
    ):

        return text


    try:

        if language == "বাংলা":

            if translate_to_bangla:

                translated = translate_to_bangla(
                    text
                )

                if translated:

                    return translated


        elif language == "English":

            if translate_to_english:

                translated = translate_to_english(
                    text
                )

                if translated:

                    return translated


    except Exception as e:

        print(
            "⚠️ Translation failed:"
        )

        print(
            str(e)
        )

        traceback.print_exc()


    # Never fail the whole research
    return text


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    print(
        "🏠 Home request"
    )


    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )


    if not os.path.exists(
        index_file
    ):

        return jsonify({

            "status":
                "online",

            "error":
                "frontend/index.html not found",

            "frontend_directory":
                FRONTEND_DIR,

            "project_root":
                PROJECT_ROOT

        }), 404


    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )


    return jsonify({

        "status":
            "online",

        "message":
            "Research AI Backend is running",

        "tools_loaded":
            TOOLS_LOADED,

        "tool_import_error":
            TOOL_IMPORT_ERROR,

        "frontend_exists":
            os.path.exists(
                index_file
            ),

        "frontend_directory":
            FRONTEND_DIR,

        "project_root":
            PROJECT_ROOT

    })


# ============================================================
# SIMPLE TEST ENDPOINT
# ============================================================

@app.route(
    "/api/test",
    methods=["GET"]
)
def test():

    return jsonify({

        "status":
            "success",

        "message":
            "Research AI API is working",

        "tools_loaded":
            TOOLS_LOADED

    })


# ============================================================
# STATIC FRONTEND FILES
# ============================================================

@app.route(
    "/<path:filename>"
)
def frontend_files(
    filename
):

    # Prevent accidental API routing
    if filename.startswith(
        "research"
    ):

        return jsonify({

            "error":
                "API endpoint not found"

        }), 404


    if filename.startswith(
        "api/"
    ):

        return jsonify({

            "error":
                "API endpoint not found"

        }), 404


    file_path = os.path.join(
        FRONTEND_DIR,
        filename
    )


    if os.path.isfile(
        file_path
    ):

        return send_from_directory(
            FRONTEND_DIR,
            filename
        )


    return jsonify({

        "error":
            "Frontend file not found",

        "file":
            filename

    }), 404


# ============================================================
# RESEARCH API
# ============================================================

@app.route(
    "/research",
    methods=["POST"]
)
def research():

    start_time = time.time()


    print("\n")
    print("=" * 70)
    print("🤖 RESEARCH AI REQUEST")
    print("=" * 70)


    # ========================================================
    # CHECK TOOLS
    # ========================================================

    if not TOOLS_LOADED:

        print(
            "❌ Research tools are not loaded"
        )

        return jsonify({

            "error":
                "Research tools failed to load.",

            "details":
                TOOL_IMPORT_ERROR,

            "tools_loaded":
                False

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
            "❌ JSON parsing error:",
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
        "❓ Question:",
        question
    )

    print(
        "🌐 Requested language:",
        requested_language
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
        "🌐 Detected language:",
        detected_language
    )

    print(
        "🗣️ Answer language:",
        answer_language
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
            "⚠️ Question analyzer failed:"
        )

        print(
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
        "🎯 Intents:",
        intents
    )

    print(
        "🔎 Search query:",
        search_query
    )


    # ========================================================
    # WEB SEARCH
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
        "📚 Search results:",
        len(results)
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


    # Limit sources to prevent Render timeout
    results_to_read = results[:3]


    print(
        f"\n📚 Reading {len(results_to_read)} sources..."
    )


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


        if not url:

            print(
                f"⚠️ Source {index}: URL missing"
            )

            continue


        print(
            "\n" + "-" * 60
        )

        print(
            f"📖 SOURCE {index}/{len(results_to_read)}"
        )

        print(
            "📄 Title:",
            title
        )

        print(
            "🔗 URL:",
            url
        )


        try:

            text = read_page(
                url
            )


        except Exception as e:

            print(
                "❌ Page read failed:"
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
                "⚠️ Text too short"
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
            "📝 Characters:",
            len(text)
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
                "কিন্তু কোনো webpage থেকে "
                "readable text পাওয়া যায়নি।"
            )

        else:

            message = (
                "Search completed, but no "
                "webpage could be read."
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

        print(
            "⚠️ Using summarizer compatibility mode"
        )


        try:

            summary = build_research_summary(
                sources
            )

        except Exception as e:

            print(
                "❌ Summary failed:",
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


    translated_summary = safe_translate(

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
        ] = safe_translate(

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
            "⚠️ Intent labels failed:",
            str(e)
        )

        intent_labels = {}


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    elapsed = round(
        time.time() - start_time,
        2
    )


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

        "processing_time":
            elapsed

    }


    print(
        "\n" + "=" * 70
    )

    print(
        "✅ RESEARCH COMPLETED"
    )

    print(
        "❓ Question:",
        question
    )

    print(
        "🔎 Query:",
        search_query
    )

    print(
        "📚 Sources:",
        source_count
    )

    print(
        "🌐 Language:",
        answer_language
    )

    print(
        "⏱️ Time:",
        elapsed,
        "seconds"
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
        "\n" + "=" * 70
    )

    print(
        "❌ UNHANDLED SERVER ERROR"
    )

    print(
        str(error)
    )

    traceback.print_exc()

    print(
        "=" * 70
    )


    return jsonify({

        "success":
            False,

        "error":
            "Internal server error",

        "details":
            str(error)

    }), 500


# ============================================================
# 404 HANDLER
# ============================================================

@app.errorhandler(404)
def handle_404(error):

    return jsonify({

        "success":
            False,

        "error":
            "404 Not Found",

        "path":
            request.path

    }), 404


# ============================================================
# 500 HANDLER
# ============================================================

@app.errorhandler(500)
def handle_500(error):

    return jsonify({

        "success":
            False,

        "error":
            "500 Internal Server Error",

        "details":
            str(error)

    }), 500


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    print(
        "\n" + "=" * 70
    )

    print(
        "🚀 RESEARCH AI BACKEND"
    )

    print(
        "=" * 70
    )

    print(
        "🌐 Port:",
        port
    )

    print(
        "📁 Current directory:",
        CURRENT_DIR
    )

    print(
        "📁 Project root:",
        PROJECT_ROOT
    )

    print(
        "📁 Frontend:",
        FRONTEND_DIR
    )

    print(
        "📄 index.html:",
        os.path.exists(
            os.path.join(
                FRONTEND_DIR,
                "index.html"
            )
        )
    )

    print(
        "🔧 Tools loaded:",
        TOOLS_LOADED
    )

    if TOOL_IMPORT_ERROR:

        print(
            "❌ Import error:",
            TOOL_IMPORT_ERROR
        )

    print(
        "=" * 70
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
```
