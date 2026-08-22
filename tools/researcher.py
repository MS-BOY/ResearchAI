"""
Production Research Engine
==========================

Optimized for:
- Local development
- Render + Gunicorn
- Flask backend
- DuckDuckGo HTML
- Wikipedia API
- Parallel page reading
- Fast failure
- Retry handling
- Duplicate removal
- Domain filtering
- HTML extraction
- Response size protection
- Thread-safe HTTP sessions
"""

from __future__ import annotations

import re
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from urllib.parse import (
    quote,
    urlparse,
    parse_qs,
    unquote,
)

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIG
# ============================================================

MAX_SEARCH_RESULTS = 8
MAX_SOURCES_TO_READ = 3

MAX_QUERY_LENGTH = 500
MAX_TEXT_LENGTH = 8000
MAX_HTML_SIZE = 2 * 1024 * 1024

SEARCH_TIMEOUT = (4, 8)
PAGE_TIMEOUT = (4, 7)
WIKI_TIMEOUT = (4, 7)

MAX_WORKERS = 3

RETRY_TOTAL = 1

USER_AGENT = (
    "ResearchAI/1.0 "
    "(educational web research application)"
)


# ============================================================
# BLOCKED DOMAINS
# ============================================================

BLOCKED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
    "reddit.com",
}


# ============================================================
# LOW VALUE EXTENSIONS
# ============================================================

BLOCKED_EXTENSIONS = {
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".exe",
    ".dmg",
    ".iso",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
}


# ============================================================
# SESSION FACTORY
# ============================================================

def create_session():
    """
    Create an independent requests session.

    Important:
    Each worker gets its own session.
    This avoids sharing one Session
    across multiple threads.
    """

    session = requests.Session()

    retry = Retry(
        total=RETRY_TOTAL,
        connect=RETRY_TOTAL,
        read=RETRY_TOTAL,

        backoff_factor=0.2,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],

        allowed_methods={
            "GET",
            "HEAD",
        },

        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=5,
        pool_maxsize=5,
    )

    session.mount(
        "http://",
        adapter,
    )

    session.mount(
        "https://",
        adapter,
    )

    session.headers.update({
        "User-Agent": USER_AGENT,

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/json;q=0.9,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.8",

        "Connection":
            "close",
    })

    return session


# ============================================================
# THREAD LOCAL SESSION
# ============================================================

import threading

_thread_local = threading.local()


def get_session():
    """
    Return one Session per worker thread.
    """

    if not hasattr(
        _thread_local,
        "session"
    ):

        _thread_local.session = (
            create_session()
        )

    return _thread_local.session


# ============================================================
# QUERY CLEANING
# ============================================================

def clean_query(question: str) -> str:

    query = str(
        question or ""
    ).strip()

    query = re.sub(
        r"\s+",
        " ",
        query,
    )

    # Remove obvious control characters
    query = "".join(
        char
        for char in query
        if char.isprintable()
        or char in "\n\t"
    )

    return query[:MAX_QUERY_LENGTH]


# ============================================================
# URL VALIDATION
# ============================================================

def is_valid_url(url) -> bool:

    try:

        parsed = urlparse(
            str(url)
        )

        return (
            parsed.scheme in {
                "http",
                "https",
            }
            and bool(
                parsed.netloc
            )
        )

    except Exception:

        return False


# ============================================================
# DOMAIN
# ============================================================

def get_domain(url: str) -> str:

    try:

        domain = (
            urlparse(url)
            .netloc
            .lower()
            .split(":")[0]
        )

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:

        return ""


# ============================================================
# BLOCKED DOMAIN
# ============================================================

def is_blocked_domain(url: str) -> bool:

    domain = get_domain(
        url
    )

    if not domain:
        return True

    for blocked in BLOCKED_DOMAINS:

        if (
            domain == blocked
            or domain.endswith(
                "." + blocked
            )
        ):

            return True

    return False


# ============================================================
# BLOCKED FILE
# ============================================================

def is_blocked_extension(url: str) -> bool:

    try:

        path = (
            urlparse(url)
            .path
            .lower()
        )

        return any(
            path.endswith(ext)
            for ext in BLOCKED_EXTENSIONS
        )

    except Exception:

        return True


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(url):

    if not url:
        return None

    try:

        url = str(
            url
        ).strip()

        if url.startswith("//"):

            url = (
                "https:"
                + url
            )

        # DuckDuckGo redirect
        if "duckduckgo.com/l/?" in url:

            parsed = urlparse(
                url
            )

            params = parse_qs(
                parsed.query
            )

            if "uddg" in params:

                url = unquote(
                    params["uddg"][0]
                )

        # Remove fragment
        parsed = urlparse(
            url
        )

        url = parsed._replace(
            fragment=""
        ).geturl()

        return url

    except Exception:

        return None


# ============================================================
# URL ACCEPTANCE
# ============================================================

def is_acceptable_url(url) -> bool:

    if not is_valid_url(url):
        return False

    if is_blocked_domain(url):
        return False

    if is_blocked_extension(url):
        return False

    return True


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def duckduckgo_search(query):

    print(
        f"\n🦆 DuckDuckGo: {query}"
    )

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    session = get_session()

    try:

        response = session.get(
            url,
            timeout=SEARCH_TIMEOUT,
        )

        if response.status_code != 200:

            print(
                "⚠️ DDG HTTP:",
                response.status_code,
            )

            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = []
        seen = set()

        for item in soup.select(
            ".result"
        ):

            title_element = (
                item.select_one(
                    ".result__title"
                )
            )

            link_element = (
                item.select_one(
                    ".result__a"
                )
            )

            if (
                not title_element
                or not link_element
            ):
                continue

            title = title_element.get_text(
                " ",
                strip=True,
            )

            raw_url = link_element.get(
                "href"
            )

            url = normalize_url(
                raw_url
            )

            if not is_acceptable_url(
                url
            ):
                continue

            if url in seen:
                continue

            seen.add(url)

            results.append({
                "title": title,
                "url": url,
                "source": "DuckDuckGo",
            })

            if len(results) >= MAX_SEARCH_RESULTS:
                break

        print(
            f"✅ DDG results: {len(results)}"
        )

        return results

    except requests.exceptions.Timeout:

        print(
            "⏱️ DDG timeout"
        )

        return []

    except requests.exceptions.RequestException as error:

        print(
            "❌ DDG request error:",
            error,
        )

        return []

    except Exception as error:

        print(
            "❌ DDG parser error:",
            error,
        )

        return []


# ============================================================
# WIKIPEDIA SEARCH
# ============================================================

def wikipedia_search(query):

    print(
        "\n📚 Wikipedia search..."
    )

    url = (
        "https://en.wikipedia.org/"
        "w/rest.php/v1/search/page"
    )

    params = {
        "q": query,
        "limit": MAX_SEARCH_RESULTS,
    }

    session = get_session()

    try:

        response = session.get(
            url,
            params=params,
            timeout=WIKI_TIMEOUT,
        )

        if response.status_code != 200:

            print(
                "⚠️ Wikipedia HTTP:",
                response.status_code,
            )

            return []

        data = response.json()

        pages = data.get(
            "pages",
            []
        )

        results = []

        for page in pages:

            title = str(
                page.get(
                    "title",
                    ""
                )
            ).strip()

            if not title:
                continue

            key = page.get(
                "key",
                title.replace(
                    " ",
                    "_"
                ),
            )

            page_url = (
                "https://en.wikipedia.org/wiki/"
                + quote(
                    str(key),
                    safe="",
                )
            )

            excerpt = BeautifulSoup(
                str(
                    page.get(
                        "excerpt",
                        ""
                    )
                ),
                "html.parser",
            ).get_text(
                " ",
                strip=True,
            )

            results.append({

                "title": title,

                "url": page_url,

                "source": "Wikipedia",

                "excerpt": excerpt,

                "description":
                    page.get(
                        "description",
                        "",
                    ),
            })

            if len(results) >= MAX_SEARCH_RESULTS:
                break

        print(
            f"✅ Wikipedia results: "
            f"{len(results)}"
        )

        return results

    except requests.exceptions.Timeout:

        print(
            "⏱️ Wikipedia timeout"
        )

        return []

    except Exception as error:

        print(
            "❌ Wikipedia error:",
            error,
        )

        return []


# ============================================================
# MERGE RESULTS
# ============================================================

def merge_results(
    ddg_results,
    wiki_results,
):

    final = []
    seen = set()

    for item in (
        ddg_results
        + wiki_results
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        url = normalize_url(
            item.get(
                "url"
            )
        )

        if not is_acceptable_url(
            url
        ):
            continue

        # Normalize URL in result
        item["url"] = url

        if url in seen:
            continue

        seen.add(url)

        final.append(
            item
        )

        if len(final) >= MAX_SEARCH_RESULTS:
            break

    return final


# ============================================================
# SEARCH WEB
# ============================================================

def search_web(question):

    query = clean_query(
        question
    )

    if not query:
        return []

    print(
        "\n" + "=" * 60
    )

    print(
        "🔎 RESEARCH SEARCH"
    )

    print(
        "Query:",
        query
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Primary DDG
    # --------------------------------------------------------

    ddg_results = (
        duckduckgo_search(
            query
        )
    )

    # --------------------------------------------------------
    # Wikipedia only when needed
    # --------------------------------------------------------

    wiki_results = []

    if len(ddg_results) < 3:

        wiki_results = (
            wikipedia_search(
                query
            )
        )

    results = merge_results(
        ddg_results,
        wiki_results,
    )

    # --------------------------------------------------------
    # Full fallback
    # --------------------------------------------------------

    if not results:

        print(
            "🔄 Search fallback: Wikipedia"
        )

        results = wikipedia_search(
            query
        )

        results = merge_results(
            [],
            results,
        )

    print(
        f"✅ Final results: "
        f"{len(results)}"
    )

    return results


# ============================================================
# HTML CLEANING
# ============================================================

def clean_html(soup):

    unwanted = [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
        "svg",
        "iframe",
        "canvas",
        "button",
        "input",
        "select",
        "textarea",
        "template",
    ]

    for tag in soup(
        unwanted
    ):

        tag.decompose()


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text(soup):

    clean_html(
        soup
    )

    # --------------------------------------------------------
    # Article
    # --------------------------------------------------------

    article = soup.find(
        "article"
    )

    if article:

        text = article.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 200:
            return text

    # --------------------------------------------------------
    # Main
    # --------------------------------------------------------

    main = soup.find(
        "main"
    )

    if main:

        text = main.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 200:
            return text

    # --------------------------------------------------------
    # Content selectors
    # --------------------------------------------------------

    selectors = [
        ".article-body",
        ".article-content",
        ".post-content",
        ".entry-content",
        ".post-body",
        ".story-body",
        ".content-body",
        ".page-content",
        ".main-content",
        ".post",
        "#article",
        "#article-content",
        "#main-content",
        "#content",
    ]

    for selector in selectors:

        element = soup.select_one(
            selector
        )

        if not element:
            continue

        text = element.get_text(
            " ",
            strip=True,
        )

        if len(text) >= 200:
            return text

    # --------------------------------------------------------
    # Paragraph fallback
    # --------------------------------------------------------

    paragraphs = soup.find_all(
        "p"
    )

    parts = []

    for paragraph in paragraphs:

        value = paragraph.get_text(
            " ",
            strip=True,
        )

        if len(value) >= 30:

            parts.append(
                value
            )

        # Avoid massive pages
        if sum(
            len(x)
            for x in parts
        ) >= MAX_TEXT_LENGTH:

            break

    return " ".join(
        parts
    )


# ============================================================
# READ PAGE
# ============================================================

def read_page(url):

    if not is_acceptable_url(
        url
    ):
        return ""

    session = get_session()

    try:

        print(
            f"🌐 Reading: {url}"
        )

        response = session.get(

            url,

            timeout=PAGE_TIMEOUT,

            allow_redirects=True,

            stream=True,
        )

        if response.status_code != 200:

            print(
                f"⚠️ HTTP "
                f"{response.status_code}"
            )

            return ""

        # ----------------------------------------------------
        # Validate final URL
        # ----------------------------------------------------

        final_url = normalize_url(
            response.url
        )

        if not is_acceptable_url(
            final_url
        ):

            print(
                "⏭️ Redirected to blocked URL"
            )

            return ""

        # ----------------------------------------------------
        # Content type
        # ----------------------------------------------------

        content_type = (
            response.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )

        if (
            "text/html"
            not in content_type
            and
            "application/xhtml+xml"
            not in content_type
        ):

            print(
                "⏭️ Not HTML"
            )

            return ""

        # ----------------------------------------------------
        # Content length
        # ----------------------------------------------------

        content_length = (
            response.headers.get(
                "Content-Length"
            )
        )

        if content_length:

            try:

                if int(
                    content_length
                ) > MAX_HTML_SIZE:

                    print(
                        "⏭️ Page too large"
                    )

                    return ""

            except (
                ValueError,
                TypeError
            ):

                pass

        # ----------------------------------------------------
        # Read limited body
        # ----------------------------------------------------

        data = bytearray()

        for chunk in response.iter_content(
            chunk_size=65536
        ):

            if not chunk:
                continue

            data.extend(
                chunk
            )

            if len(data) >= MAX_HTML_SIZE:

                print(
                    "⏭️ HTML limit reached"
                )

                break

        if not data:
            return ""

        # ----------------------------------------------------
        # Parse HTML
        # ----------------------------------------------------

        soup = BeautifulSoup(
            bytes(data),
            "html.parser",
        )

        text = extract_text(
            soup
        )

        text = " ".join(
            text.split()
        )

        if len(text) < 100:

            print(
                "⚠️ Not enough text"
            )

            return ""

        text = text[
            :MAX_TEXT_LENGTH
        ]

        print(
            f"✅ Extracted "
            f"{len(text)} chars"
        )

        return text

    except requests.exceptions.Timeout:

        print(
            "⏱️ Page timeout"
        )

        return ""

    except requests.exceptions.TooManyRedirects:

        print(
            "🔁 Redirect limit"
        )

        return ""

    except requests.exceptions.RequestException as error:

        print(
            "🌐 Request error:",
            error
        )

        return ""

    except Exception as error:

        print(
            "❌ Read failed:",
            error
        )

        return ""


# ============================================================
# READ SOURCE
# ============================================================

def read_source(item):

    if not isinstance(
        item,
        dict
    ):
        return None

    url = normalize_url(
        item.get(
            "url",
            ""
        )
    )

    if not is_acceptable_url(
        url
    ):
        return None

    text = read_page(
        url
    )

    if not text:
        return None

    return {

        "title":
            str(
                item.get(
                    "title",
                    "Untitled"
                )
            ),

        "url":
            url,

        "text":
            text,

        "source":
            str(
                item.get(
                    "source",
                    "Web"
                )
            ),
    }


# ============================================================
# RESEARCH
# ============================================================

def research(question):

    results = search_web(
        question
    )

    if not results:

        print(
            "❌ No search results"
        )

        return []

    results_to_read = results[
        :MAX_SEARCH_RESULTS
    ]

    print(
        f"\n📚 Candidate pages: "
        f"{len(results_to_read)}"
    )

    sources = []

    # --------------------------------------------------------
    # Parallel source reading
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_map = {

            executor.submit(
                read_source,
                item
            ): item

            for item in results_to_read
        }

        for future in as_completed(
            future_map
        ):

            try:

                result = future.result()

                if result:

                    sources.append(
                        result
                    )

                    print(
                        f"✅ Source accepted "
                        f"{len(sources)}/"
                        f"{MAX_SOURCES_TO_READ}"
                    )

                    if (
                        len(sources)
                        >= MAX_SOURCES_TO_READ
                    ):

                        # We stop collecting.
                        # Running requests may finish
                        # in background, but no more
                        # results are needed.
                        break

            except Exception as error:

                print(
                    "⚠️ Worker error:",
                    error
                )

    # --------------------------------------------------------
    # Stable output order
    # --------------------------------------------------------

    sources.sort(
        key=lambda item:
            item.get(
                "title",
                ""
            ).lower()
    )

    # --------------------------------------------------------
    # Final limit
    # --------------------------------------------------------

    sources = sources[
        :MAX_SOURCES_TO_READ
    ]

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ RESEARCH COMPLETE"
    )

    print(
        f"📚 Readable sources: "
        f"{len(sources)}"
    )

    print(
        "=" * 60
    )

    return sources


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    question = input(
        "\n🔍 Research question: "
    ).strip()

    if not question:

        print(
            "❌ Question required."
        )

    else:

        data = research(
            question
        )

        print(
            "\nFINAL SOURCES:"
        )

        for index, item in enumerate(
            data,
            1
        ):

            print(
                f"\n[{index}] "
                f"{item['title']}"
            )

            print(
                item["source"]
            )

            print(
                item["url"]
            )

            print(
                item["text"][:500]
            )
