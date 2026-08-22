import requests


# ============================================================
# REMOTE WEB SERVER
# ============================================================

BACKEND_URL = (
    "https://researchai-v0f0.onrender.com"
)

RESEARCH_API = (
    BACKEND_URL + "/research"
)


# ============================================================
# REMOTE RESEARCH
# ============================================================

def remote_research(query, language="auto"):

    print("\n" + "=" * 60)
    print("🌐 REMOTE WEB RESEARCH")
    print("=" * 60)

    print("🔎 Query:", query)
    print("🔗 Server:", RESEARCH_API)

    try:

        response = requests.post(

            RESEARCH_API,

            json={
                "question": query,
                "language": language
            },

            headers={
                "Content-Type":
                    "application/json"
            },

            timeout=120

        )


        print(
            "📡 HTTP:",
            response.status_code
        )


        # ----------------------------------------------------
        # JSON CHECK
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            print(
                "❌ Server returned non-JSON response"
            )

            print(
                response.text[:1000]
            )

            return None


        # ----------------------------------------------------
        # SERVER ERROR
        # ----------------------------------------------------

        if response.status_code >= 400:

            print(
                "❌ Research server error:"
            )

            print(
                data
            )

            return None


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print(
            "✅ Remote research completed"
        )

        print(
            "📚 Sources:",
            data.get(
                "source_count",
                0
            )
        )


        return data


    except requests.exceptions.Timeout:

        print(
            "⏱️ Research server timeout"
        )

        return None


    except requests.exceptions.ConnectionError as e:

        print(
            "🌐 Cannot connect to Render server"
        )

        print(
            str(e)
        )

        return None


    except requests.exceptions.RequestException as e:

        print(
            "❌ HTTP request failed:"
        )

        print(
            str(e)
        )

        return None


    except Exception as e:

        print(
            "❌ Remote research error:"
        )

        print(
            str(e)
        )

        return None


# ============================================================
# DISPLAY RESEARCH RESULT
# ============================================================

def display_research(data):

    if not data:

        print(
            "\n❌ Research failed."
        )

        return


    print("\n" + "=" * 60)
    print("🧠 RESEARCH RESULT")
    print("=" * 60)


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = data.get(
        "summary",
        ""
    )


    if summary:

        print(
            "\n🧠 SUMMARY\n"
        )

        print(
            summary
        )


    # --------------------------------------------------------
    # STRUCTURED DATA
    # --------------------------------------------------------

    structured = data.get(
        "structured",
        {}
    )


    if isinstance(
        structured,
        dict
    ) and structured:

        print(
            "\n📊 STRUCTURED RESEARCH\n"
        )


        for key, value in structured.items():

            print(
                f"\n▶ {key}"
            )

            if isinstance(
                value,
                list
            ):

                for item in value:

                    print(
                        "•",
                        item
                    )

            else:

                print(
                    value
                )


    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    sources = data.get(
        "sources",
        []
    )


    print(
        "\n🔗 SOURCES:",
        len(sources)
    )


    for index, source in enumerate(
        sources,
        1
    ):

        print(
            f"\n{index}. "
            f"{source.get('title', 'Untitled')}"
        )

        print(
            source.get(
                "url",
                ""
            )
        )


    print(
        "\n" + "=" * 60
    )


# ============================================================
# AGENT
# ============================================================

def run_agent(
    command,
    language="auto"
):

    command = str(
        command or ""
    ).strip()


    if not command:

        print(
            "❌ Empty command."
        )

        return None


    print("\n" + "=" * 60)
    print("🤖 AI AGENT")
    print("=" * 60)

    print(
        "💬 Command:",
        command
    )


    # ========================================================
    # IMPORT AI BRAIN
    # ========================================================

    try:

        from ai_brain import understand

        intent = understand(
            command
        )

    except Exception as e:

        print(
            "❌ AI brain failed:"
        )

        print(
            str(e)
        )

        return None


    print(
        "\n🤖 Agent decision:"
    )

    print(
        intent
    )


    # ========================================================
    # VALIDATE INTENT
    # ========================================================

    if not isinstance(
        intent,
        dict
    ):

        print(
            "❌ Invalid agent decision."
        )

        return None


    tool = str(
        intent.get(
            "tool",
            ""
        )
    ).lower().strip()


    query = str(
        intent.get(
            "query",
            command
        )
    ).strip()


    if not query:

        query = command


    print(
        "\n🛠️ Tool:",
        tool
    )

    print(
        "🔎 Query:",
        query
    )


    # ========================================================
    # RESEARCH → REMOTE WEB SERVER
    # ========================================================

    if tool == "research":

        data = remote_research(
            query,
            language
        )


        if data:

            display_research(
                data
            )


        return data


    # ========================================================
    # GOOGLE
    # ========================================================

    if tool == "google":

        try:

            from tools.google import google_search

            return google_search(
                query
            )

        except Exception as e:

            print(
                "❌ Google tool failed:",
                str(e)
            )

            return None


    # ========================================================
    # YOUTUBE
    # ========================================================

    if tool == "youtube":

        try:

            from tools.youtube import youtube_search

            return youtube_search(
                query
            )

        except Exception as e:

            print(
                "❌ YouTube tool failed:",
                str(e)
            )

            return None


    # ========================================================
    # UNKNOWN TOOL
    # ========================================================

    print(
        "❌ Tool পাওয়া যায়নি:",
        tool
    )

    return None
