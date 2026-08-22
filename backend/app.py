from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import sys


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
# IMPORT TOOLS
# =========================================================

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


# =========================================================
# FLASK APP
# =========================================================

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

app = Flask(__name__)

CORS(app)


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(text):

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

    requested_language = (
        str(requested_language or "auto")
        .strip()
        .lower()
    )

    if requested_language == "bangla":

        return "বাংলা"

    if requested_language == "english":

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

    text = str(text).strip()

    if not text:

        return ""

    try:

        if language == "বাংলা":

            return translate_to_bangla(text)

        if language == "English":

            return translate_to_english(text)

    except Exception as e:

        print(
            f"⚠️ Translation error: {e}"
        )

    # Translation fail হলে original text
    return text


# =========================================================
# FRONTEND
# =========================================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    if not os.path.exists(index_file):

        return jsonify({

            "status": "online",

            "message":
                "Research AI Backend is running",

            "warning":
                "frontend/index.html was not found"

        })

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# =========================================================
# FRONTEND STATIC FILES
# =========================================================

@app.route(
    "/<path:filename>"
)
def frontend_files(filename):

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

        "error":
            "File not found"

    }), 404


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "online",

        "message":
            "Research AI Backend is running"

    })


# =========================================================
# RESEARCH API
# =========================================================

@app.route(
    "/research",
    methods=["POST"]
)
def research():

    # -----------------------------------------------------
    # GET JSON
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "error":
                "Invalid JSON request"

        }), 400


    # -----------------------------------------------------
    # QUESTION
    # -----------------------------------------------------

    question = str(
        data.get(
            "question",
            ""
        )
    ).strip()


    if not question:

        return jsonify({

            "error":
                "Question is required"

        }), 400


    # -----------------------------------------------------
    # REQUESTED LANGUAGE
    # -----------------------------------------------------

    requested_language = data.get(
        "language",
        "auto"
    )


    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    detected_language = detect_language(
        question
    )

    answer_language = get_answer_language(
        requested_language,
        detected_language
    )


    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 RESEARCH AI"
    )

    print(
        f"❓ Question: {question}"
    )

    print(
        f"🌐 Detected language: "
        f"{detected_language}"
    )

    print(
        f"🗣️ Answer language: "
        f"{answer_language}"
    )


    # -----------------------------------------------------
    # QUESTION ANALYSIS
    # -----------------------------------------------------

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
            f"⚠️ Question analyzer error: {e}"
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

    if not search_query:

        search_query = question


    print(
        f"🎯 Intents: {intents}"
    )

    print(
        f"🔎 Search query: "
        f"{search_query}"
    )


    # -----------------------------------------------------
    # SEARCH WEB
    # -----------------------------------------------------

    print(
        "\n🔎 Searching internet..."
    )

    try:

        results = search_web(
            search_query
        )

        if not results:

            results = []

    except Exception as e:

        print(
            f"❌ Search error: {e}"
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


    # -----------------------------------------------------
    # READ SOURCES
    # -----------------------------------------------------

    sources = []


    for index, result in enumerate(
        results,
        1
    ):

        if not isinstance(
            result,
            dict
        ):

            continue


        title = result.get(
            "title",
            "Untitled source"
        )

        url = result.get(
            "url",
            ""
        )


        print(
            f"\n📖 Reading "
            f"{index}/{len(results)}: "
            f"{title}"
        )


        if not url:

            print(
                "⚠️ URL missing"
            )

            continue


        try:

            text = read_page(
                url
            )

        except Exception as e:

            print(
                f"⚠️ Page read error: {e}"
            )

            text = ""


        if not text:

            print(
                "⚠️ No readable text"
            )

            continue


        sources.append({

            "title":
                str(title),

            "url":
                str(url),

            "text":
                str(text)[:8000]

        })


        print(
            "✅ Source added"
        )


    # -----------------------------------------------------
    # NO SOURCES
    # -----------------------------------------------------

    if not sources:

        if answer_language == "বাংলা":

            message = (
                "কোনো readable source "
                "পাওয়া যায়নি।"
            )

        else:

            message = (
                "No readable sources "
                "were found."
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


    # -----------------------------------------------------
    # CREATE SUMMARY
    # -----------------------------------------------------

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

        # Older summarizer compatibility

        try:

            summary = build_research_summary(

                sources,

                max_sentences_per_source=5,

                max_total_sentences=20

            )

        except Exception as e:

            print(
                f"⚠️ Summary error: {e}"
            )

            summary = ""


    except Exception as e:

        print(
            f"⚠️ Summary error: {e}"
        )

        summary = ""


    if not summary:

        summary = (
            "No relevant information "
            "was found."
        )


    # -----------------------------------------------------
    # STRUCTURED RESEARCH
    # -----------------------------------------------------

    print(
        "\n📑 Creating structured research..."
    )


    structured = {}


    try:

        structured = build_structured_research(

            sources,

            intents

        )

        if not isinstance(
            structured,
            dict
        ):

            structured = {}

    except Exception as e:

        print(
            f"⚠️ Structured research error: {e}"
        )

        structured = {}


    # -----------------------------------------------------
    # TRANSLATE SUMMARY
    # -----------------------------------------------------

    print(
        "\n🌐 Translating summary..."
    )


    translated_summary = translate_text(

        summary,

        answer_language

    )


    # -----------------------------------------------------
    # TRANSLATE STRUCTURED DATA
    # -----------------------------------------------------

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

                if item

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


    # -----------------------------------------------------
    # INTENT LABELS
    # -----------------------------------------------------

    try:

        intent_labels = get_intent_labels(
            intents
        )

    except Exception as e:

        print(
            f"⚠️ Intent label error: {e}"
        )

        intent_labels = {}


    # -----------------------------------------------------
    # OUTPUT SOURCES
    # -----------------------------------------------------

    output_sources = []


    for source in sources:

        output_sources.append({

            "title":
                source.get(
                    "title",
                    "Untitled source"
                ),

            "url":
                source.get(
                    "url",
                    ""
                ),

            "text":
                source.get(
                    "text",
                    ""
                )

        })


    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

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
        f"{', '.join(intents) if intents else 'None'}"
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


# =========================================================
# ERROR HANDLER
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "error":
            "Route not found"

    }), 404


@app.errorhandler(500)
def internal_error(error):

    print(
        f"❌ Internal server error: {error}"
    )

    return jsonify({

        "error":
            "Internal server error"

    }), 500


# =========================================================
# LOCAL DEVELOPMENT
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
