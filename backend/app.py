```python
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys
import traceback
import time


# ============================================================
# PROJECT PATH
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# app.py যদি backend/ এর ভিতরে থাকে
PROJECT_ROOT = os.path.dirname(
    CURRENT_DIR
)

# app.py যদি project root-এ থাকে
if not os.path.exists(
    os.path.join(PROJECT_ROOT, "tools")
):
    PROJECT_ROOT = CURRENT_DIR


# Add paths
for path in [
    PROJECT_ROOT,
    CURRENT_DIR
]:

    if path not in sys.path:

        sys.path.insert(
            0,
            path
        )


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = os.path.join(
    PROJECT_ROOT,
    "frontend"
)


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
        }
    }
)

app.config["JSON_AS_ASCII"] = False


# ============================================================
# MODULE STATUS
# ============================================================

MODULES = {

    "researcher": False,

    "question_analyzer": False,

    "summarizer": False,

    "translator": False

}


IMPORT_ERRORS = {}


# ============================================================
# DEFAULT FUNCTIONS
# ============================================================

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

def load_module(
    module_name
):

    global search_web
    global read_page

    global analyze_question
    global get_intent_labels

    global build_research_summary
    global build_structured_research

    global translate_to_bangla
    global translate_to_english


    try:

        print(
            f"🔧 Loading {module_name}..."
        )


        # ====================================================
        # RESEARCHER
        # ====================================================

        if module_name == "researcher":

            from tools.researcher import (
                search_web as _search_web,
                read_page as _read_page
            )

            search_web = _search_web
            read_page = _read_page


        # ====================================================
        # QUESTION ANALYZER
        # ====================================================

        elif module_name == "question_analyzer":

            from tools.question_analyzer import (
                analyze_question as _analyze_question,
                get_intent_labels as _get_intent_labels
            )

            analyze_question = _analyze_question
            get_intent_labels = _get_intent_labels


        # ====================================================
        # SUMMARIZER
        # ====================================================

        elif module_name == "summarizer":

            from tools.summarizer import (
                build_research_summary as _build_research_summary,
                build_structured_research as _build_structured_research
            )

            build_research_summary = (
                _build_research_summary
            )

            build_structured_research = (
                _build_structured_research
            )


        # ====================================================
        # TRANSLATOR
        # ====================================================

        elif module_name == "translator":

            from tools.translator import (
                translate_to_bangla as _translate_to_bangla,
                translate_to_english as _translate_to_english
            )

            translate_to_bangla = (
                _translate_to_bangla
            )

            translate_to_english = (
                _translate_to_english
            )


        MODULES[
            module_name
        ] = True

        IMPORT_ERRORS.pop(
            module_name,
            None
        )

        print(
            f"✅ {module_name} loaded"
        )

        return True


    except Exception as e:

        MODULES[
            module_name
        ] = False

        IMPORT_ERRORS[
            module_name
        ] = str(e)


        print(
            f"❌ {module_name} failed"
        )

        print(
            str(e)
        )

        traceback.print_exc()

        return False


# ============================================================
# LOAD MODULES
# ============================================================

print("\n" + "=" * 70)
print("🔧 RESEARCH AI - MODULE LOADING")
print("=" * 70)

load_module(
    "researcher"
)

load_module(
    "question_analyzer"
)

load_module(
    "summarizer"
)

load_module(
    "translator"
)

print("=" * 70)

print(
    "MODULE STATUS:",
    MODULES
)

print("=" * 70)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(
    text
):

    text = str(
        text or ""
    )

    bangla = 0
    english = 0


    for char in text:

        if "\u0980" <= char <= "\u09FF":

            bangla += 1

        elif char.isalpha():

            english += 1


    if bangla > english:

        return "বাংলা"


    return "English"


# ============================================================
# ANSWER LANGUAGE
# ============================================================

def get_answer_language(
    requested,
    detected
):

    requested = str(
        requested or "auto"
    ).lower().strip()


    if requested in (
        "bn",
        "bangla",
        "বাংলা"
    ):

        return "বাংলা"


    if requested in (
        "en",
        "english"
    ):

        return "English"


    return detected


# ============================================================
# SAFE TRANSLATION
# ============================================================

def safe_translate(
    text,
    language
):

    if not text:

        return ""


    # Translator optional
    if not MODULES.get(
        "translator"
    ):

        print(
            "⚠️ Translator unavailable. "
            "Returning original text."
        )

        return text


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

            return text


        if result:

            return result


    except Exception as e:

        print(
            "⚠️ Translation failed:",
            str(e)
        )


    return text


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )


    if not os.path.isfile(
        index_file
    ):

        return jsonify({

            "success": False,

            "error":
                "frontend/index.html not found",

            "project_root":
                PROJECT_ROOT,

            "frontend":
                FRONTEND_DIR

        }), 404


    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success": True,

        "status": "online",

        "message":
            "Research AI Backend is running",

        "modules":
            MODULES,

        "import_errors":
            IMPORT_ERRORS,

        "frontend_exists":
            os.path.isfile(
                os.path.join(
                    FRONTEND_DIR,
                    "index.html"
                )
            ),

        "project_root":
            PROJECT_ROOT

    })


# ============================================================
# TEST
# ============================================================

@app.route(
    "/api/test",
    methods=["GET"]
)
def api_test():

    return jsonify({

        "success": True,

        "message":
            "API is working",

        "modules":
            MODULES

    })


# ============================================================
# STATIC FILES
# ============================================================

@app.route(
    "/<path:filename>"
)
def static_files(
    filename
):

    if filename == "research":

        return jsonify({

            "success": False,

            "error":
                "Use POST /research"

        }), 405


    if filename.startswith(
        "api/"
    ):

        return jsonify({

            "success": False,

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

        "success": False,

        "error":
            "Frontend file not found",

        "file":
            filename

    }), 404


# ============================================================
# RESEARCH
# ============================================================

@app.route(
    "/research",
    methods=[
        "POST",
        "OPTIONS"
    ]
)
def research():

    start_time = time.time()


    # ========================================================
    # OPTIONS / CORS
    # ========================================================

    if request.method == "OPTIONS":

        return jsonify({
            "success": True
        })


    print("\n" + "=" * 70)
    print("🤖 NEW RESEARCH REQUEST")
    print("=" * 70)


    # ========================================================
    # RESEARCHER REQUIRED
    # ========================================================

    if not MODULES.get(
        "researcher"
    ):

        return jsonify({

            "success": False,

            "error":
                "Researcher module failed to load.",

            "details":
                IMPORT_ERRORS.get(
                    "researcher",
                    "Unknown import error"
                ),

            "modules":
                MODULES

        }), 500


    # ========================================================
    # JSON
    # ========================================================

    try:

        data = request.get_json(
            silent=True
        )

    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                "Invalid JSON",

            "details":
                str(e)

        }), 400


    if not isinstance(
        data,
        dict
    ):

        return jsonify({

            "success": False,

            "error":
                "Request body must be JSON"

        }), 400


    # ========================================================
    # INPUT
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


    if MODULES.get(
        "question_analyzer"
    ):

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


        except Exception as e:

            print(
                "⚠️ Analyzer failed:",
                str(e)
            )

            traceback.print_exc()

            # Fallback to original question
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
        "🔎 Search:",
        search_query
    )


    # ========================================================
    # WEB SEARCH
    # ========================================================

    print(
        "\n🔎 Searching web..."
    )


    try:

        results = search_web(
            search_query
        )


    except Exception as e:

        print(
            "❌ Search error:",
            str(e)
        )

        traceback.print_exc()


        return jsonify({

            "success": False,

            "error":
                "Internet search failed",

            "details":
                str(e),

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
                []

        })


    # ========================================================
    # READ SOURCES
    # ========================================================

    sources = []


    # IMPORTANT:
    # Render timeout prevent করার জন্য
    # maximum 3 source read করা হচ্ছে

    results_to_read = results[:3]


    print(
        f"📖 Reading {len(results_to_read)} sources..."
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
            f"\n📄 SOURCE {index}"
        )

        print(
            "Title:",
            title
        )

        print(
            "URL:",
            url
        )


        try:

            text = read_page(
                url
            )


        except Exception as e:

            print(
                "⚠️ Page error:",
                str(e)
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
                text[:6000]

        })


        print(
            "✅ Source readable"
        )


    source_count = len(
        sources
    )


    print(
        "\n📚 Readable:",
        source_count
    )


    # ========================================================
    # NO READABLE SOURCES
    # ========================================================

    if source_count == 0:

        message = (

            "Search result পাওয়া গেছে, "
            "কিন্তু কোনো webpage থেকে "
            "readable text পাওয়া যায়নি।"

            if answer_language == "বাংলা"

            else

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
                []

        })


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = ""


    if MODULES.get(
        "summarizer"
    ):

        print(
            "\n🧠 Creating summary..."
        )


        try:

            summary = build_research_summary(

                sources,

                intents=intents,

                max_sentences_per_source=4,

                max_total_sentences=12

            )


        except TypeError:

            try:

                summary = build_research_summary(
                    sources
                )

            except Exception as e:

                print(
                    "⚠️ Summary fallback failed:",
                    str(e)
                )

                summary = ""


        except Exception as e:

            print(
                "⚠️ Summary failed:",
                str(e)
            )

            traceback.print_exc()

            summary = ""


    # ========================================================
    # SUMMARY FALLBACK
    # ========================================================

    if not summary:

        summary = (
            "Research completed successfully. "
            "Please review the sources below."
        )


    # ========================================================
    # STRUCTURED
    # ========================================================

    structured = {}


    if MODULES.get(
        "summarizer"
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


    for intent, content in structured.items():

        if not content:

            translated_sections[
                intent
            ] = ""

            continue


        if isinstance(
            content,
            list
        ):

            text = "\n\n".join(

                str(x)

                for x in content

            )

        else:

            text = str(
                content
            )


        translated_sections[
            intent
        ] = safe_translate(

            text,

            answer_language

        )


    # ========================================================
    # INTENT LABELS
    # ========================================================

    intent_labels = {}


    if MODULES.get(
        "question_analyzer"
    ):

        try:

            intent_labels = get_intent_labels(
                intents
            )

        except Exception:

            intent_labels = {}


    # ========================================================
    # PROCESSING TIME
    # ========================================================

    processing_time = round(
        time.time() - start_time,
        2
    )


    # ========================================================
    # FINAL JSON
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

        "processing_time":
            processing_time

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
        f"⏱️ Time: {processing_time}s"
    )

    print(
        "=" * 70
    )


    return jsonify(
        response
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(Exception)
def global_error(
    error
):

    print(
        "\n❌ GLOBAL ERROR"
    )

    print(
        str(error)
    )

    traceback.print_exc()


    return jsonify({

        "success": False,

        "error":
            "Internal server error",

        "details":
            str(error)

    }), 500


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(
    error
):

    return jsonify({

        "success": False,

        "error":
            "Endpoint not found",

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
            "5000"
        )
    )


    print("\n" + "=" * 70)
    print("🚀 RESEARCH AI BACKEND")
    print("=" * 70)

    print(
        "PORT:",
        port
    )

    print(
        "CURRENT:",
        CURRENT_DIR
    )

    print(
        "PROJECT:",
        PROJECT_ROOT
    )

    print(
        "FRONTEND:",
        FRONTEND_DIR
    )

    print(
        "TOOLS:",
        MODULES
    )

    print(
        "IMPORT ERRORS:",
        IMPORT_ERRORS
    )

    print("=" * 70)


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False,

        threaded=True

    )
```
