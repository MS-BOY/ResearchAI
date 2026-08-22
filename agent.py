"""
Advanced Research AI Agent
==========================

Render + Local Production Ready

Features:
- Direct URL/tool detection
- AI-based tool routing
- Safe tool registry
- Result validation
- Controlled fallback
- Execution deadline
- Structured responses
- Lightweight logging
- Tool health check
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("research_ai.agent")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


# ============================================================
# AI BRAIN
# ============================================================

try:
    from ai_brain import understand
except Exception as error:
    logger.exception("AI brain import failed")
    understand = None


# ============================================================
# TOOLS
# ============================================================

try:
    from tools.google import google_search
except Exception as error:
    logger.warning("Google tool unavailable: %s", error)
    google_search = None


try:
    from tools.youtube import youtube_search
except Exception as error:
    logger.warning("YouTube tool unavailable: %s", error)
    youtube_search = None


try:
    from tools.researcher import research
except Exception as error:
    logger.warning("Research tool unavailable: %s", error)
    research = None


# ============================================================
# CONFIGURATION
# ============================================================

AGENT_NAME = "Research AI Agent"

MAX_QUERY_LENGTH = 2000

# Render request-এর মধ্যে agent-এর জন্য maximum budget
MAX_EXECUTION_TIME = 80

# Fallback একবারের বেশি নয়
MAX_FALLBACK_ATTEMPTS = 1

DEFAULT_TOOL = "research"


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = {
    "research": research,
    "google": google_search,
    "youtube": youtube_search,
}


# Remove unavailable tools
TOOLS = {
    name: tool
    for name, tool in TOOLS.items()
    if callable(tool)
}


# ============================================================
# TOOL DESCRIPTIONS
# ============================================================

TOOL_DESCRIPTIONS = {
    "research":
        "Deep web research using multiple webpages and sources.",

    "google":
        "General web search for webpages and information.",

    "youtube":
        "Search YouTube videos and related content."
}


# ============================================================
# TOOL ALIASES
# ============================================================

TOOL_ALIASES = {

    "web": "research",
    "web_search": "research",
    "deep_search": "research",
    "deep_research": "research",
    "researcher": "research",

    "search": "google",
    "google_search": "google",
    "google-search": "google",

    "yt": "youtube",
    "video": "youtube",
    "videos": "youtube",
    "youtube_search": "youtube",
    "youtube-search": "youtube",
}


# ============================================================
# SAFE STRING
# ============================================================

def safe_string(
    value: Any,
    fallback: str = ""
) -> str:

    try:

        if value is None:
            return fallback

        return str(value).strip()

    except Exception:

        return fallback


# ============================================================
# EXECUTION TIMER
# ============================================================

class ExecutionBudget:

    def __init__(
        self,
        maximum_seconds: float = MAX_EXECUTION_TIME
    ):

        self.started = time.monotonic()

        self.maximum = maximum_seconds

    @property
    def elapsed(self) -> float:

        return time.monotonic() - self.started

    def remaining(self) -> float:

        remaining = (
            self.maximum
            - self.elapsed
        )

        return max(
            0.0,
            remaining
        )

    def expired(self) -> bool:

        return self.elapsed >= self.maximum


# ============================================================
# QUERY VALIDATION
# ============================================================

def normalize_query(
    query: Any,
    fallback: str
) -> str:

    query = safe_string(
        query,
        fallback
    )

    if not query:
        query = fallback

    return query[:MAX_QUERY_LENGTH]


# ============================================================
# NORMALIZE INTENT
# ============================================================

def normalize_intent(
    intent: Any,
    command: str
) -> Dict[str, str]:

    if not isinstance(
        intent,
        dict
    ):

        return {
            "tool": DEFAULT_TOOL,
            "query": command
        }

    tool = safe_string(
        intent.get(
            "tool",
            DEFAULT_TOOL
        ),
        DEFAULT_TOOL
    ).lower()

    query = normalize_query(
        intent.get(
            "query",
            command
        ),
        command
    )

    # Alias
    tool = TOOL_ALIASES.get(
        tool,
        tool
    )

    # Invalid / unavailable tool
    if tool not in TOOLS:

        logger.warning(
            "Unknown/unavailable tool '%s'. Using '%s'.",
            tool,
            DEFAULT_TOOL
        )

        tool = (
            DEFAULT_TOOL
            if DEFAULT_TOOL in TOOLS
            else next(
                iter(TOOLS),
                DEFAULT_TOOL
            )
        )

    return {
        "tool": tool,
        "query": query
    }


# ============================================================
# URL DETECTION
# ============================================================

def contains_url(
    text: str
) -> bool:

    try:

        parts = text.split()

        for part in parts:

            candidate = (
                part
                .strip(".,!?()[]{}<>")
            )

            if candidate.startswith(
                (
                    "http://",
                    "https://"
                )
            ):

                parsed = urlparse(
                    candidate
                )

                if parsed.netloc:

                    return True

        return False

    except Exception:

        return False


# ============================================================
# DIRECT TOOL DETECTION
# ============================================================

def detect_direct_tool(
    command: str
) -> Optional[Dict[str, str]]:

    text = command.strip()

    lower = text.lower()

    # --------------------------------------------------------
    # YouTube URL
    # --------------------------------------------------------

    if (
        "youtube.com" in lower
        or
        "youtu.be" in lower
    ):

        if "youtube" in TOOLS:

            return {
                "tool": "youtube",
                "query": text
            }

    # --------------------------------------------------------
    # Explicit YouTube command
    # --------------------------------------------------------

    if (
        lower.startswith("youtube ")
        or
        lower.startswith("yt ")
    ):

        query = text.split(
            " ",
            1
        )[1].strip()

        if "youtube" in TOOLS:

            return {
                "tool": "youtube",
                "query": query or text
            }

    # --------------------------------------------------------
    # Explicit Google
    # --------------------------------------------------------

    if lower.startswith(
        "google search "
    ):

        query = text[
            len("google search "):
        ].strip()

        if "google" in TOOLS:

            return {
                "tool": "google",
                "query": query or text
            }

    if lower.startswith(
        "google "
    ):

        query = text[
            len("google "):
        ].strip()

        if "google" in TOOLS:

            return {
                "tool": "google",
                "query": query or text
            }

    # --------------------------------------------------------
    # Direct URL
    # --------------------------------------------------------

    if contains_url(text):

        # Direct URLs are generally better handled
        # by research.
        if "research" in TOOLS:

            return {
                "tool": "research",
                "query": text
            }

    return None


# ============================================================
# SELECT TOOL
# ============================================================

def select_tool(
    command: str,
    budget: ExecutionBudget
) -> Dict[str, str]:

    # --------------------------------------------------------
    # Direct command first
    # --------------------------------------------------------

    direct = detect_direct_tool(
        command
    )

    if direct:

        logger.info(
            "Direct tool selected: %s",
            direct["tool"]
        )

        return direct

    # --------------------------------------------------------
    # AI routing
    # --------------------------------------------------------

    if (
        understand is not None
        and
        not budget.expired()
    ):

        try:

            intent = understand(
                command
            )

            logger.info(
                "AI tool decision: %s",
                intent
            )

            return normalize_intent(
                intent,
                command
            )

        except Exception as error:

            logger.warning(
                "AI understanding failed: %s",
                error
            )

    # --------------------------------------------------------
    # Research fallback
    # --------------------------------------------------------

    return {
        "tool": (
            DEFAULT_TOOL
            if DEFAULT_TOOL in TOOLS
            else next(
                iter(TOOLS),
                DEFAULT_TOOL
            )
        ),
        "query": command
    }


# ============================================================
# RESULT VALIDATION
# ============================================================

def validate_result(
    result: Any
) -> bool:

    if result is None:
        return False

    if isinstance(
        result,
        str
    ):

        return bool(
            result.strip()
        )

    if isinstance(
        result,
        (list, tuple, dict)
    ):

        return len(result) > 0

    return True


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute_tool(
    tool_name: str,
    query: str,
    budget: ExecutionBudget
) -> Any:

    if budget.expired():

        raise TimeoutError(
            "Agent execution budget exceeded."
        )

    tool = TOOLS.get(
        tool_name
    )

    if not callable(tool):

        raise ValueError(
            f"Tool '{tool_name}' is unavailable."
        )

    logger.info(
        "Executing tool=%s query=%s",
        tool_name,
        query[:200]
    )

    started = time.monotonic()

    try:

        result = tool(
            query
        )

        elapsed = (
            time.monotonic()
            - started
        )

        logger.info(
            "Tool %s completed in %.2fs",
            tool_name,
            elapsed
        )

        if budget.expired():

            logger.warning(
                "Tool completed but total budget expired."
            )

        return result

    except Exception as error:

        elapsed = (
            time.monotonic()
            - started
        )

        logger.error(
            "Tool %s failed after %.2fs: %s",
            tool_name,
            elapsed,
            error
        )

        raise


# ============================================================
# FALLBACK RESEARCH
# ============================================================

def fallback_research(
    query: str,
    budget: ExecutionBudget
) -> Any:

    if (
        "research" not in TOOLS
        or
        budget.expired()
    ):

        return None

    logger.info(
        "Research fallback activated."
    )

    try:

        result = execute_tool(
            "research",
            query,
            budget
        )

        if validate_result(
            result
        ):

            return result

    except Exception as error:

        logger.warning(
            "Research fallback failed: %s",
            error
        )

    return None


# ============================================================
# AGENT HEALTH
# ============================================================

def get_agent_health() -> Dict[str, Any]:

    tool_status = {}

    for name in (
        "research",
        "google",
        "youtube"
    ):

        tool = TOOLS.get(
            name
        )

        tool_status[name] = {

            "available":
                callable(tool),

            "description":
                TOOL_DESCRIPTIONS.get(
                    name,
                    ""
                )
        }

    return {

        "agent":
            AGENT_NAME,

        "status":
            "online",

        "default_tool":
            DEFAULT_TOOL,

        "tools":
            tool_status
    }


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    command: str
) -> Dict[str, Any]:

    budget = ExecutionBudget()

    command = safe_string(
        command
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not command:

        return {
            "success": False,
            "error": "Command is required"
        }

    if len(command) > MAX_QUERY_LENGTH:

        return {
            "success": False,
            "error": "Command is too long",
            "max_length": MAX_QUERY_LENGTH
        }

    if not TOOLS:

        return {
            "success": False,
            "error": "No tools are available."
        }

    logger.info(
        "Agent started: %s",
        command[:200]
    )

    # --------------------------------------------------------
    # Select tool
    # --------------------------------------------------------

    decision = select_tool(
        command,
        budget
    )

    tool_name = decision[
        "tool"
    ]

    query = normalize_query(
        decision.get(
            "query",
            command
        ),
        command
    )

    logger.info(
        "Selected tool=%s",
        tool_name
    )

    # --------------------------------------------------------
    # Primary execution
    # --------------------------------------------------------

    try:

        result = execute_tool(
            tool_name,
            query,
            budget
        )

        # ----------------------------------------------------
        # Primary result valid
        # ----------------------------------------------------

        if validate_result(
            result
        ):

            elapsed = round(
                budget.elapsed,
                2
            )

            return {

                "success":
                    True,

                "tool":
                    tool_name,

                "query":
                    query,

                "fallback":
                    False,

                "execution_time":
                    elapsed,

                "result":
                    result
            }

        # ----------------------------------------------------
        # Empty result
        # ----------------------------------------------------

        logger.warning(
            "Primary tool returned empty result."
        )

        if (
            tool_name != "research"
            and
            not budget.expired()
        ):

            fallback_result = (
                fallback_research(
                    query,
                    budget
                )
            )

            if validate_result(
                fallback_result
            ):

                return {

                    "success":
                        True,

                    "tool":
                        "research",

                    "original_tool":
                        tool_name,

                    "fallback":
                        True,

                    "fallback_reason":
                        "Primary tool returned empty result",

                    "query":
                        query,

                    "execution_time":
                        round(
                            budget.elapsed,
                            2
                        ),

                    "result":
                        fallback_result
                }

        return {

            "success":
                False,

            "tool":
                tool_name,

            "query":
                query,

            "fallback":
                False,

            "error":
                "Tool returned no useful result",

            "execution_time":
                round(
                    budget.elapsed,
                    2
                )
        }

    # --------------------------------------------------------
    # Primary tool exception
    # --------------------------------------------------------

    except Exception as error:

        logger.warning(
            "Primary tool failed: %s",
            error
        )

        # ----------------------------------------------------
        # Fallback only once
        # ----------------------------------------------------

        if (
            tool_name != "research"
            and
            not budget.expired()
        ):

            fallback_result = (
                fallback_research(
                    query,
                    budget
                )
            )

            if validate_result(
                fallback_result
            ):

                return {

                    "success":
                        True,

                    "tool":
                        "research",

                    "original_tool":
                        tool_name,

                    "fallback":
                        True,

                    "fallback_reason":
                        str(error),

                    "query":
                        query,

                    "execution_time":
                        round(
                            budget.elapsed,
                            2
                        ),

                    "result":
                        fallback_result
                }

        # ----------------------------------------------------
        # Final failure
        # ----------------------------------------------------

        return {

            "success":
                False,

            "tool":
                tool_name,

            "query":
                query,

            "fallback":
                False,

            "error":
                str(error),

            "execution_time":
                round(
                    budget.elapsed,
                    2
                )
        }


# ============================================================
# AVAILABLE TOOLS
# ============================================================

def get_available_tools():

    return {

        name:
            TOOL_DESCRIPTIONS.get(
                name,
                ""
            )

        for name in TOOLS
    }


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    print(
        f"\n🚀 {AGENT_NAME}"
    )

    print(
        "\nAgent health:"
    )

    print(
        get_agent_health()
    )

    print(
        "\nAvailable tools:"
    )

    for name, description in (
        get_available_tools().items()
    ):

        print(
            f"  • {name}: {description}"
        )

    print(
        "\nType 'exit' to stop."
    )

    while True:

        try:

            command = input(
                "\n👤 You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\n👋 Agent stopped."
            )

            break

        if not command:
            continue

        if command.lower() in (
            "exit",
            "quit",
            "bye"
        ):

            print(
                "👋 Goodbye!"
            )

            break

        result = run_agent(
            command
        )

        print(
            "\n📦 Agent result:"
        )

        print(
            result
        )
