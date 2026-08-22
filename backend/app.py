
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback
import time
import importlib


# ============================================================
# PROJECT PATH DETECTION
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Possible project roots
POSSIBLE_ROOTS = [
    CURRENT_DIR,
    os.path.dirname(CURRENT_DIR)
]

PROJECT_ROOT = CURRENT_DIR

for path in POSSIBLE_ROOTS:

    tools_path = os.path.join(
        path,
        "tools"
    )

    frontend_path = os.path.join(
        path,
        "frontend"
    )

    if os.path.isdir(tools_path):

        PROJECT_ROOT = path
        break

    if os.path.isdir(frontend_path):

        PROJECT_ROOT = path


# Add project paths to Python path
for path in [
    CURRENT_DIR,
    PROJECT_ROOT,
    os.path.dirname(PROJECT_ROOT)
]:

    if path and path not in sys.path:

        sys.path.insert(
            0,
            path
        )


# ============================================================
# DIRECTORIES
# ============================================================

TOOLS_DIR = os.path.join(
    PROJECT_ROOT,
    "tools"
)

FRONTEND_DIR = os.path.join(
    PROJECT_ROOT,
    "frontend"
)


# ============================================================
# TOOL VARIABLES
# ============================================================

TOOLS_LOADED = False

RESEARCHER_LOADED = False
ANALYZER_LOADED = False
SUMMARIZER_LOADED = False
TRANSLATOR_LOADED = False

TOOL_IMPORT_ERRORS = {}


search_web = None
read_page = None

analyze_question = None
get_intent_labels = None

build_research_summary = None
build_structured_research = None

translate_to_bangla = None
translate_to_english = None


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

def load_module(module_name):

    try:

        module = importlib.import_module(
            module_name
        )

        print(
            f"✅ Loaded: {module_name}"
        )

        return module

    except Exception as e:

        error_text = (
            f"{type(e).__name__}: {str(e)}"
        )

        TOOL_IMPORT_ERRORS[
            module_name
        ] = error_text

        print(
            f"\n❌ Failed: {module_name}"
        )

        print(
            error_text
        )

        traceback.print_exc()

        return None


# ============================================================
# LOAD RESEARCHER
# ============================================================

print("\n" + "=" * 70)
print("🔧 LOADING RESEARCH AI TOOLS")
print("=" * 70)

print(
    "📁 CURRENT_DIR:",
    CURRENT_DIR
)

print(
    "📁 PROJECT_ROOT:",
    PROJECT_ROOT
)

print(
    "📁 TOOLS_DIR:",
    TOOLS_DIR
)

print(
    "📁 FRONTEND_DIR:",
    FRONTEND_DIR
)


if not os.path.isdir(TOOLS_DIR):

    TOOL_IMPORT_ERRORS["tools"] = (
        f"tools directory not found: {TOOLS_DIR}"
    )

    print(
        "❌ tools directory not found"
    )

else:

    print(
        "✅ tools directory found"
    )


# ============================================================
# RESEARCHER
# ============================================================

researcher_module = load_module(
    "tools.researcher"
)

if researcher_module:

    search_web = getattr(
        researcher_module,
        "search_web",
        None
    )

    read_page = getattr(
        researcher_module,
        "read_page",
        None
    )

    if callable(search_web) and callable(read_page):

        RESEARCHER_LOADED = True

        print(
            "✅ Researcher functions ready"
        )

    else:

        TOOL_IMPORT_ERRORS[
            "tools.researcher.functions"
        ] = (
            "search_web() or read_page() "
            "is missing from tools/researcher.py"
        )


# ============================================================
# QUESTION ANALYZER
# ============================================================

analyzer_module = load_module(
    "tools.question_analyzer"
)

if analyzer_module:

    analyze_question = getattr(
        analyzer_module,
        "analyze_question",
        None
    )

    get_intent_labels = getattr(
        analyzer_module,
        "get_intent_labels",
        None
    )

    if callable(analyze_question):

        ANALYZER_LOADED = True

        print(
            "✅ Question analyzer ready"
        )

    else:

        TOOL_IMPORT_ERRORS[
            "tools.question_analyzer.functions"
        ] = (
            "analyze_question() is missing"
        )


# ============================================================
# SUMMARIZER
# ============================================================

summarizer_module = load_module(
    "tools.summarizer"
)

if summarizer_module:

    build_research_summary = getattr(
        summarizer_module,
        "build_research_summary",
        None
    )

    build_structured_research = getattr(
        summarizer_module,
        "build_structured_research",
        None
    )

    if callable(build_research_summary):

        SUMMARIZER_LOADED = True

        print(
            "✅ Summarizer ready"
        )

    else:

        TOOL_IMPORT_ERRORS[
            "tools.summarizer.functions"
        ] = (
            "build_research_summary() is missing"
        )


# ============================================================
# TRANSLATOR
# ============================================================

translator_module = load_module(
    "tools.translator"
)

if translator_module:

    translate_to_bangla = getattr(
        translator_module,
        "translate_to_bangla",
        None
    )

    translate_to_english = getattr(
        translator_module,
        "translate_to_english",
        None
    )

    if (
        callable(translate_to_bangla)
        or
        callable(translate_to_english)
    ):

        TRANSLATOR_LOADED = True

        print(
            "✅ Translator ready"
        )

    else:

        TOOL_IMPORT_ERRORS[
            "tools.translator.functions"
        ] = (
            "Translation functions are missing"
        )


# ============================================================
# FINAL TOOL STATUS
# ============================================================

TOOLS_LOADED = RESEARCHER_LOADED


print("\n" + "=" * 70)

print(
    "🔧 TOOL STATUS"
)

print(
    "Researcher:",
    RESEARCHER_LOADED
)

print(
    "Analyzer:",
    ANALYZER_LOADED
)

print(
    "Summarizer:",
    SUMMARIZER_LOADED
)

print(
    "Translator:",
    TRANSLATOR_LOADED
)

print(
    "Research system:",
    TOOLS_LOADED
)

print("=" * 70)


if TOOL_IMPORT_ERRORS:

    print(
        "\n⚠️ TOOL IMPORT ERRORS:"
    )

    for name, error in TOOL_IMPORT_ERRORS.items():

        print(
            f"❌ {name}: {error}"
        )

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

app.config[
    "JSON_AS_ASCII"
] = False


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

    value = str(
        requested_language or "auto"
    ).lower().strip()

    if value in (
        "bn",
        "bangla",
        "বাংলা"
    ):

        return "বাংলা"

    if value in (
        "en",
        "english"
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

    try:

        if language == "বাংলা":

            if callable(
                translate_to_bangla
            ):

                result = translate_to_bangla(
                    text
                )

                if result:

                    return str(result)


        elif language == "English":

            if callable(
                translate_to_english
            ):

                result = translate_to_english(
                    text
                )

                if result:

                    return str(result)

    except Exception as e:

        print(
            "⚠️ Translation failed:",
            str(e)
        )

        traceback.print_exc()

    # Translation failure must
    # never break research
    return text


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    print(
        "🏠 Home request"
    )

    if not os.path.isfile(index_file):

        return jsonify({

            "success": False,

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

        "success": True,

        "status":
            "online",

        "message":
            "Research AI Backend is running",

        "tools_loaded":
            TOOLS_LOADED,

        "researcher_loaded":
            RESEARCHER_LOADED,

        "analyzer_loaded":
            ANALYZER_LOADED,

        "summarizer_loaded":
            SUMMARIZER_LOADED,

        "translator_loaded":
            TRANSLATOR_LOADED,

        "tool_import_errors":
            TOOL_IMPORT_ERRORS,

        "frontend_exists":
            os.path.isfile(index_file),

        "project_root":
            PROJECT_ROOT,

        "tools_directory":
            TOOLS_DIR,

        "frontend_directory":
            FRONTEND_DIR

    })


# ============================================================
# TEST ENDPOINT
# ============================================================

@app.route(
    "/api/test",
    methods=["GET"]
)
def test():

    return jsonify({

        "success": True,

        "message":
            "Research AI API is working",

        "researcher_loaded":
            RESEARCHER_LOADED,

        "tools_loaded":
            TOOLS_LOADED

    })


# ============================================================
# STATIC FRONTEND
# ============================================================

@app.route(
    "/<path:filename>"
)
def frontend_files(filename):

    if filename == "research":

        return jsonify({

            "success": False,

            "error":
                "Use POST /research"

        }), 405

    if filename.startswith("api/"):

        return jsonify({

            "success": False,

            "error":
                "API endpoint not found"

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

        "success": False,

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
def research_api():

    start_time = time.time()

    print("\n" + "=" * 70)
    print("🤖 RESEARCH REQUEST")
    print("=" * 70)


    # ========================================================
    # RESEARCHER CHECK
    # ========================================================

    if not RESEARCHER_LOADED:

        print(
            "❌ Researcher is not loaded"
        )

        return jsonify({

            "success": False,

            "error":
                "Researcher failed to load",

            "details":
                TOOL_IMPORT_ERRORS,

            "hint":
                "Open /api/health and check tool_import_errors"

        }), 500


    # ========================================================
    # JSON
    # ========================================================

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        return jsonify({

            "success": False,

            "error":
                "Request body must be JSON",

            "example": {
                "question": "What is Python?",
                "language": "English"
            }

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


    print(
        "❓ Question:",
        question
    )

    print(
        "🌐 Language:",
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


    # ========================================================
    # QUESTION ANALYSIS
    # ========================================================

    intents = []

    search_query = question


    if ANALYZER_LOADED:

        try:

            analysis = analyze_question(
                question
            )

            if isinstance(
                analysis,
                dict
            ):

                intents = analysis.get(
                    "intents",
                    []
                )

                search_query = analysis.get(
                    "search_query",
                    question
                )

                if not isinstance(
                    intents,
                    list
                ):

                    intents = []

                if not search_query:

                    search_query = question

        except Exception as e:

            print(
                "⚠️ Analyzer failed:",
                str(e)
            )

            traceback.print_exc()

            # Continue with original question

            intents = []

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

    try:

        results = search_web(
            search_query
        )

    except Exception as e:

        print(
            "\n❌ SEARCH FAILED"
        )

        print(
            str(e)
        )

        traceback.print_exc()

        return jsonify({

            "success": False,

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
        f"🔎 Search results: {len(results)}"
    )


    # ========================================================
    # NO SEARCH RESULT
    # ========================================================

    if not results:

        message = (

            "কোনো search result পাওয়া যায়নি।"

            if answer_language == "বাংলা"

            else

            "No search results were found."

        )

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

            "search_query":
                search_query,

            "source_count":
                0,

            "summary":
                message,

            "structured":
                {},

            "sources":
                [],

            "processing_time":
                round(
                    time.time()
                    - start_time,
                    2
                )

        })


    # ========================================================
    # READ SOURCES
    # ========================================================

    sources = []

    # Render timeout avoid
    results_to_read = results[:5]


    print(
        f"📚 Reading {len(results_to_read)} sources..."
    )


    for index, item in enumerate(
        results_to_read,
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
        ).strip()


        url = str(
            item.get(
                "url",
                ""
            )
        ).strip()


        if not url:

            continue


        print(
            "\n" + "-" * 60
        )

        print(
            f"📖 SOURCE {index}/{len(results_to_read)}"
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
                "⚠️ read_page failed:",
                str(e)
            )

            traceback.print_exc()

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
                text[:8000]

        })


        print(
            f"✅ Source {index} readable"
        )


    source_count = len(
        sources
    )


    print(
        "📚 Readable sources:",
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
                "Search completed, but no webpage "
                "could be read."
            )


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

            "search_query":
                search_query,

            "source_count":
                0,

            "summary":
                message,

            "structured":
                {},

            "sources":
                [],

            "processing_time":
                round(
                    time.time()
                    - start_time,
                    2
                )

        })


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = ""


    if SUMMARIZER_LOADED:

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
                    sources
                )

            except Exception as e:

                print(
                    "⚠️ Summary failed:",
                    str(e)
                )

        except Exception as e:

            print(
                "⚠️ Summary failed:",
                str(e)
            )

            traceback.print_exc()


    # ========================================================
    # FALLBACK SUMMARY
    # ========================================================

    if not summary:

        first_source = sources[0]

        summary = (
            first_source.get(
                "text",
                ""
            )[:2500]
        )


    # ========================================================
    # STRUCTURED
    # ========================================================

    structured = {}


    if SUMMARIZER_LOADED:

        if callable(
            build_structured_research
        ):

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

    translated_summary = safe_translate(

        summary,

        answer_language

    )


    # ========================================================
    # TRANSLATE STRUCTURED
    # ========================================================

    translated_sections = {}


    for key, value in structured.items():

        if isinstance(
            value,
            list
        ):

            section_text = "\n\n".join(

                str(x)

                for x in value

            )

        else:

            section_text = str(
                value
            )


        translated_sections[
            key
        ] = safe_translate(

            section_text,

            answer_language

        )


    # ========================================================
    # INTENT LABELS
    # ========================================================

    intent_labels = {}


    if ANALYZER_LOADED:

        if callable(
            get_intent_labels
        ):

            try:

                intent_labels = get_intent_labels(
                    intents
                )

            except Exception as e:

                print(
                    "⚠️ Intent labels failed:",
                    str(e)
                )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    elapsed = round(
        time.time()
        - start_time,
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


    print("\n" + "=" * 70)

    print(
        "✅ RESEARCH COMPLETED"
    )

    print(
        "📚 Sources:",
        source_count
    )

    print(
        "⏱️ Time:",
        elapsed
    )

    print("=" * 70)


    return jsonify(
        response
    )


# ============================================================
# ERROR HANDLER
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
# START
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    print("\n" + "=" * 70)

    print(
        "🚀 RESEARCH AI BACKEND"
    )

    print(
        "🌐 Port:",
        port
    )

    print(
        "📁 Project root:",
        PROJECT_ROOT
    )

    print(
        "📁 Tools:",
        TOOLS_DIR
    )

    print(
        "📁 Frontend:",
        FRONTEND_DIR
    )

    print(
        "🔧 Researcher:",
        RESEARCHER_LOADED
    )

    print(
        "🔧 Analyzer:",
        ANALYZER_LOADED
    )

    print(
        "🔧 Summarizer:",
        SUMMARIZER_LOADED
    )

    print(
        "🔧 Translator:",
        TRANSLATOR_LOADED
    )

    print("=" * 70)


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
