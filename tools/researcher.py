"""
Fast Production Research Engine
================================

Compatible with current app.py

Flow:
    Question
       ↓
    DuckDuckGo + Wikipedia (parallel)
       ↓
    Select best web sources
       ↓
    Read 3 sources in parallel
       ↓
    Return article text to app.py

Public API:
    search_web(question)
    read_page(url)
    research(question)

Optimized for:
    - Flask
    - Gunicorn
    - Render
    - No Playwright
    - Low memory
    - Fast requests
    - Parallel source reading
"""

from __future__ import annotations

import re
import threading

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

MAX_QUERY_LENGTH = 500

# Number of search results collected
MAX_SEARCH_RESULTS = 8

# Number of actual articles read
MAX_SOURCES_TO_READ = 3

# Parallel source readers
MAX_WORKERS = 3

# Timeouts
SEARCH_TIMEOUT = 5
WIKI_TIMEOUT = 5
PAGE_TIMEOUT = 6

# Content limits
MAX_TEXT_LENGTH = 8000
MAX_HTML_SIZE = 2 * 1024 * 1024

# Minimum useful article text
MIN_PAGE_TEXT = 150

# User agent
USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/131.0 Safari/537.36 "
    "ResearchAI/1.0"
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
    "linkedin.com",
    "pinterest.com",
    "reddit.com",
}


# ============================================================
# THREAD LOCAL SESSION
# ============================================================

_thread_local = threading.local()


def create_session() -> requests.Session:
    """
    Create optimized reusable HTTP session.
    """

    session = requests.Session()

    retry = Retry(
        total=1,
        connect=1,
        read=1,

        backoff_factor=0.1,

        status_forcelist=(
            429,
            500,
            502,
            503,
            504,
        ),

        allowed_methods=frozenset({
            "GET",
            "HEAD",
        }),

        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=10,
        pool_maxsize=10,
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

        "User-Agent":
            USER_AGENT,

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/json;q=0.9,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.8",

        "Connection":
            "keep-alive",
    })

    return session


def get_session() -> requests.Session:

    session = getattr(
        _thread_local,
        "session",
        None,
    )

    if session is None:

        session = create_session()

        _thread_local.session = session

    return session


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

    return query[:MAX_QUERY_LENGTH]


# ============================================================
# URL HELPERS
# ============================================================

def is_valid_url(url: str) -> bool:

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


def get_domain(url: str) -> str:

    try:

        domain = (
            urlparse(
                str(url)
            )
            .netloc
            .lower()
            .split(":")[0]
        )

        if domain.startswith("www."):

            domain = domain[4:]

        return domain

    except Exception:

        return ""


def is_blocked_domain(url: str) -> bool:

    domain = get_domain(
        url
    )

    if not domain:

        return True

    return any(
        domain == blocked
        or domain.endswith(
            "." + blocked
        )
        for blocked in BLOCKED_DOMAINS
    )


def normalize_url(url: str) -> str:

    if not url:

        return ""

    try:

        url = str(
            url
        ).strip()

        if url.startswith("//"):

            url = "https:" + url

        # DuckDuckGo redirect
        if "duckduckgo.com/l/" in url:

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

        parsed = urlparse(
            url
        )

        # Remove fragment
        url = parsed._replace(
            fragment=""
        ).geturl()

        return url

    except Exception:

        return str(
            url
        )


def result_key(url: str) -> str:

    try:

        parsed = urlparse(
            url
        )

        return (
            parsed.netloc.lower()
            + parsed.path.rstrip("/")
        )

    except Exception:

        return str(
            url
        ).lower().strip()


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def duckduckgo_search(query: str):

    print(
        f"🦆 DDG search: {query}"
    )

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    try:

        session = get_session()

        response = session.get(
            search_url,
            timeout=SEARCH_TIMEOUT,
        )

        if response.status_code != 200:

            print(
                "⚠️ DDG status:",
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

            if not (
                title_element
                and link_element
            ):

                continue

            title = title_element.get_text(
                " ",
                strip=True,
            )

            raw_url = link_element.get(
                "href",
                "",
            )

            url = normalize_url(
                raw_url
            )

            if not is_valid_url(url):

                continue

            if is_blocked_domain(url):

                continue

            key = result_key(url)

            if key in seen:

                continue

            seen.add(key)

            results.append({

                "title":
                    title,

                "url":
                    url,

                "source":
                    "DuckDuckGo",

            })

            if (
                len(results)
                >= MAX_SEARCH_RESULTS
            ):

                break

        print(
            f"✅ DDG results: "
            f"{len(results)}"
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

def wikipedia_search(query: str):

    print(
        f"📚 Wikipedia search: {query}"
    )

    url = (
        "https://en.wikipedia.org/"
        "w/rest.php/v1/search/page"
    )

    params = {
        "q":
            query,

        "limit":
            4,
    }

    try:

        session = get_session()

        response = session.get(
            url,
            params=params,
            timeout=WIKI_TIMEOUT,
        )

        if response.status_code != 200:

            print(
                "⚠️ Wikipedia status:",
                response.status_code,
            )

            return []

        data = response.json()

        pages = data.get(
            "pages",
            [],
        )

        results = []

        for page in pages:

            title = str(
                page.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:

                continue

            key = page.get(
                "key"
            )

            if not key:

                key = title.replace(
                    " ",
                    "_",
                )

            page_url = (
                "https://en.wikipedia.org/wiki/"
                + quote(
                    key,
                    safe="",
                )
            )

            results.append({

                "title":
                    title,

                "url":
                    page_url,

                "source":
                    "Wikipedia",

                "excerpt":
                    page.get(
                        "excerpt",
                        "",
                    ),

            })

            if len(results) >= 4:

                break

        print(
            f"✅ Wikipedia results: "
            f"{len(results)}"
        )

        return results

    except Exception as error:

        print(
            "⚠️ Wikipedia error:",
            error,
        )

        return []


# ============================================================
# PARALLEL SEARCH
# ============================================================

def parallel_search(query: str):

    ddg_results = []

    wiki_results = []

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        futures = {

            executor.submit(
                duckduckgo_search,
                query,
            ):
                "ddg",

            executor.submit(
                wikipedia_search,
                query,
            ):
                "wiki",
        }

        for future in as_completed(
            futures
        ):

            source_type = futures[
                future
            ]

            try:

                data = future.result()

                if source_type == "ddg":

                    ddg_results = data

                else:

                    wiki_results = data

            except Exception as error:

                print(
                    f"⚠️ {source_type} search error:",
                    error,
                )

    return (
        ddg_results,
        wiki_results,
    )


# ============================================================
# MERGE SEARCH RESULTS
# ============================================================

def merge_results(
    ddg_results,
    wiki_results,
):

    final = []

    seen = set()

    # Web sources first
    combined = (
        ddg_results
        + wiki_results
    )

    for item in combined:

        if not isinstance(
            item,
            dict,
        ):

            continue

        url = normalize_url(
            item.get(
                "url",
                "",
            )
        )

        if not is_valid_url(url):

            continue

        if is_blocked_domain(url):

            continue

        key = result_key(url)

        if key in seen:

            continue

        seen.add(key)

        item["url"] = url

        final.append(
            item
        )

        if (
            len(final)
            >= MAX_SEARCH_RESULTS
        ):

            break

    return final


# ============================================================
# PUBLIC SEARCH FUNCTION
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
        "🔎 FAST WEB RESEARCH"
    )

    print(
        "Query:",
        query,
    )

    print(
        "=" * 60
    )

    ddg_results, wiki_results = (
        parallel_search(
            query
        )
    )

    results = merge_results(
        ddg_results,
        wiki_results,
    )

    if not results:

        print(
            "🔄 Wikipedia fallback..."
        )

        results = wikipedia_search(
            query
        )

    print(
        f"✅ Search results: "
        f"{len(results)}"
    )

    return results


# ============================================================
# HTML CLEANING
# ============================================================

UNWANTED_TAGS = (
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
)


def clean_html(
    soup: BeautifulSoup,
):

    for tag in soup(
        UNWANTED_TAGS
    ):

        tag.decompose()


# ============================================================
# ARTICLE EXTRACTION
# ============================================================

CONTENT_SELECTORS = (

    "article",

    "main",

    "[itemprop='articleBody']",

    ".article-body",

    ".article-content",

    ".post-content",

    ".entry-content",

    ".post-body",

    ".story-body",

    ".content-body",

    ".page-content",

    "#article",

    "#article-content",

    "#main-content",

    "#content",

)


def extract_text(
    soup: BeautifulSoup,
) -> str:

    clean_html(
        soup
    )

    # --------------------------------------------------------
    # Try article containers
    # --------------------------------------------------------

    for selector in CONTENT_SELECTORS:

        element = soup.select_one(
            selector
        )

        if not element:

            continue

        text = element.get_text(
            " ",
            strip=True,
        )

        text = " ".join(
            text.split()
        )

        if len(text) >= MIN_PAGE_TEXT:

            return text[
                :MAX_TEXT_LENGTH
            ]

    # --------------------------------------------------------
    # Paragraph fallback
    # --------------------------------------------------------

    paragraphs = soup.find_all(
        "p"
    )

    parts = []

    total = 0

    for paragraph in paragraphs:

        value = paragraph.get_text(
            " ",
            strip=True,
        )

        value = " ".join(
            value.split()
        )

        if len(value) < 30:

            continue

        parts.append(
            value
        )

        total += len(
            value
        )

        if total >= MAX_TEXT_LENGTH:

            break

    return " ".join(
        parts
    )[
        :MAX_TEXT_LENGTH
    ]


# ============================================================
# WIKIPEDIA READER
# ============================================================

def read_wikipedia_page(
    url: str,
) -> str:

    try:

        session = get_session()

        response = session.get(
            url,
            timeout=PAGE_TIMEOUT,
        )

        if response.status_code != 200:

            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        content = soup.select_one(
            "#mw-content-text"
        )

        if content:

            clean_html(
                content
            )

            text = content.get_text(
                " ",
                strip=True,
            )

        else:

            text = extract_text(
                soup
            )

        text = " ".join(
            text.split()
        )

        if len(text) < MIN_PAGE_TEXT:

            return ""

        return text[
            :MAX_TEXT_LENGTH
        ]

    except Exception as error:

        print(
            "⚠️ Wikipedia read error:",
            error,
        )

        return ""


# ============================================================
# READ PAGE
# ============================================================

def read_page(url):

    if not url:

        return ""

    url = normalize_url(
        url
    )

    if not is_valid_url(url):

        return ""

    if is_blocked_domain(url):

        return ""

    domain = get_domain(
        url
    )

    print(
        f"🌐 Reading: {url}"
    )

    # Wikipedia
    if (
        domain == "wikipedia.org"
        or domain.endswith(
            ".wikipedia.org"
        )
    ):

        return read_wikipedia_page(
            url
        )

    try:

        session = get_session()

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
        # Content type
        # ----------------------------------------------------

        content_type = (
            response.headers
            .get(
                "Content-Type",
                "",
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

            return ""

        # ----------------------------------------------------
        # Size check
        # ----------------------------------------------------

        content_length = (
            response.headers.get(
                "Content-Length"
            )
        )

        if content_length:

            try:

                if (
                    int(content_length)
                    > MAX_HTML_SIZE
                ):

                    print(
                        "⏭️ Page too large"
                    )

                    return ""

            except (
                ValueError,
                TypeError,
            ):

                pass

        # ----------------------------------------------------
        # Limited streaming
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

                break

        if not data:

            return ""

        # ----------------------------------------------------
        # Parse
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

        if len(text) < MIN_PAGE_TEXT:

            print(
                "⚠️ Insufficient article text"
            )

            return ""

        print(
            f"✅ Extracted "
            f"{len(text)} chars"
        )

        return text[
            :MAX_TEXT_LENGTH
        ]

    except requests.exceptions.Timeout:

        print(
            "⏱️ Page timeout"
        )

        return ""

    except requests.exceptions.TooManyRedirects:

        print(
            "🔁 Too many redirects"
        )

        return ""

    except requests.exceptions.RequestException as error:

        print(
            "🌐 Request error:",
            error,
        )

        return ""

    except Exception as error:

        print(
            "❌ Page error:",
            error,
        )

        return ""


# ============================================================
# READ SOURCE
# ============================================================

def read_source(item):

    if not isinstance(
        item,
        dict,
    ):

        return None

    url = str(
        item.get(
            "url",
            "",
        )
    ).strip()

    if not url:

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
                    "Untitled source",
                )
            ).strip(),

        "url":
            url,

        "text":
            text,

        "source":
            str(
                item.get(
                    "source",
                    "Web",
                )
            ).strip(),

    }


# ============================================================
# FULL RESEARCH
# ============================================================

def research(question):

    results = search_web(
        question
    )

    if not results:

        return []

    # Read only a small number
    # to keep Render response fast.

    results_to_read = results[
        :MAX_SEARCH_RESULTS
    ]

    sources = []

    print(
        f"📚 Reading up to "
        f"{MAX_SOURCES_TO_READ} articles..."
    )

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                read_source,
                item,
            ):
                item

            for item in results_to_read
        }

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result:

                    sources.append(
                        result
                    )

                if (
                    len(sources)
                    >= MAX_SOURCES_TO_READ
                ):

                    break

            except Exception as error:

                print(
                    "⚠️ Source error:",
                    error,
                )

    # Keep original search order
    order = {
        item.get(
            "url",
            "",
        ):
            index

        for index, item
        in enumerate(
            results_to_read
        )
    }

    sources.sort(
        key=lambda item:
            order.get(
                item.get(
                    "url",
                    "",
                ),
                999,
            )
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ RESEARCH COMPLETE"
    )

    print(
        f"📚 Sources read: "
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

        raise SystemExit(
            "Question required"
        )

    sources = research(
        question
    )

    for index, source in enumerate(
        sources,
        1,
    ):

        print(
            f"\n[{index}] "
            f"{source['title']}"
        )

        print(
            source["url"]
        )

        print(
            source["text"][:500]
        )
