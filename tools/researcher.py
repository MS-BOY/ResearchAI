"""
Fast Production Research Engine
================================

Compatible with current app.py

Public API:
    search_web(question)
    read_page(url)
    research(question)

Features:
- Fast DuckDuckGo search
- Parallel Wikipedia + DuckDuckGo search
- Fast webpage extraction
- Parallel source reading
- Connection pooling
- Limited retries
- Timeout protection
- HTML size protection
- Duplicate removal
- Domain filtering
- Wikipedia fallback
- Render/Gunicorn friendly
- No Playwright
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
# CONFIGURATION
# ============================================================

MAX_QUERY_LENGTH = 500

# Search
MAX_SEARCH_RESULTS = 6

SEARCH_TIMEOUT = 5
WIKI_TIMEOUT = 5

# Reading
MAX_SOURCES_TO_READ = 2
MAX_WORKERS = 2

PAGE_TIMEOUT = 5

# Content
MAX_TEXT_LENGTH = 8000
MAX_HTML_SIZE = 2 * 1024 * 1024

# Minimum useful text
MIN_PAGE_TEXT = 120

# User agent
USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; ResearchAI/1.0; +https://researchai.example)"
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
}


# ============================================================
# SESSION FACTORY
# ============================================================

def create_session() -> requests.Session:
    """
    Create a reusable HTTP session.

    Connection pooling significantly reduces
    repeated TCP/TLS connection overhead.
    """

    session = requests.Session()

    retry = Retry(
        total=1,
        connect=1,
        read=1,
        backoff_factor=0.15,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],

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
        "https://",
        adapter,
    )

    session.mount(
        "http://",
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
            "keep-alive",
    })

    return session


# Thread-local sessions avoid sharing one Session
# across multiple worker threads.

import threading

_thread_local = threading.local()


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

def clean_query(
    question: str,
) -> str:

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
# URL VALIDATION
# ============================================================

def is_valid_url(
    url: str,
) -> bool:

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

def get_domain(
    url: str,
) -> str:

    try:

        domain = (
            urlparse(
                str(url)
            )
            .netloc
            .lower()
            .split(":")[0]
        )

        if domain.startswith(
            "www."
        ):

            domain = domain[4:]

        return domain

    except Exception:

        return ""


# ============================================================
# BLOCKED DOMAIN
# ============================================================

def is_blocked_domain(
    url: str,
) -> bool:

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


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(
    url: str,
) -> str:

    if not url:

        return ""

    try:

        url = str(
            url
        ).strip()

        if url.startswith(
            "//"
        ):

            url = "https:" + url

        # DuckDuckGo redirect
        if (
            "duckduckgo.com/l/"
            in url
        ):

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

        return str(
            url
        )


# ============================================================
# RESULT KEY
# ============================================================

def result_key(
    url: str,
) -> str:

    try:

        parsed = urlparse(
            url
        )

        return (
            parsed.scheme.lower()
            + "://"
            + parsed.netloc.lower()
            + parsed.path.rstrip("/")
        )

    except Exception:

        return url.lower().strip()


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def duckduckgo_search(
    query: str,
):

    print(
        f"🦆 DDG search: {query}"
    )

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    try:

        session = get_session()

        response = session.get(
            url,
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

            if (
                not title_element
                or not link_element
            ):

                continue

            title = title_element.get_text(
                " ",
                strip=True,
            )

            raw_url = (
                link_element.get(
                    "href",
                    "",
                )
            )

            url = normalize_url(
                raw_url
            )

            if not is_valid_url(
                url
            ):

                continue

            if is_blocked_domain(
                url
            ):

                continue

            key = result_key(
                url
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            results.append({
                "title": title,
                "url": url,
                "source": "DuckDuckGo",
            })

            if len(results) >= MAX_SEARCH_RESULTS:

                break

        print(
            f"✅ DDG: {len(results)} results"
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

def wikipedia_search(
    query: str,
):

    print(
        f"📚 Wikipedia search: {query}"
    )

    url = (
        "https://en.wikipedia.org/"
        "w/rest.php/v1/search/page"
    )

    params = {
        "q": query,
        "limit": min(
            MAX_SEARCH_RESULTS,
            4,
        ),
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

            excerpt_html = page.get(
                "excerpt",
                "",
            )

            excerpt = BeautifulSoup(
                excerpt_html,
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
                "description": page.get(
                    "description",
                    "",
                ),
            })

            if len(results) >= MAX_SEARCH_RESULTS:

                break

        print(
            f"✅ Wikipedia: "
            f"{len(results)} results"
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
# PARALLEL SEARCH
# ============================================================

def parallel_search(
    query: str,
):

    """
    Run DDG and Wikipedia simultaneously.

    This reduces total search latency.
    """

    ddg_results = []
    wiki_results = []

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        ddg_future = executor.submit(
            duckduckgo_search,
            query,
        )

        wiki_future = executor.submit(
            wikipedia_search,
            query,
        )

        try:

            ddg_results = (
                ddg_future.result()
            )

        except Exception as error:

            print(
                "⚠️ DDG worker error:",
                error,
            )

        try:

            wiki_results = (
                wiki_future.result()
            )

        except Exception as error:

            print(
                "⚠️ Wikipedia worker error:",
                error,
            )

    return (
        ddg_results,
        wiki_results,
    )


# ============================================================
# MERGE RESULTS
# ============================================================

def merge_results(
    ddg_results,
    wiki_results,
):

    final = []
    seen = set()

    # Prefer normal web results
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

        if not is_valid_url(
            url
        ):

            continue

        if is_blocked_domain(
            url
        ):

            continue

        key = result_key(
            url
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        item["url"] = url

        final.append(
            item
        )

        if len(final) >= MAX_SEARCH_RESULTS:

            break

    return final


# ============================================================
# MAIN SEARCH API
# ============================================================

def search_web(
    question,
):

    query = clean_query(
        question
    )

    if not query:

        return []

    print(
        "\n" + "=" * 60
    )

    print(
        "🔎 FAST RESEARCH SEARCH"
    )

    print(
        "Query:",
        query,
    )

    print(
        "=" * 60
    )

    # Parallel DDG + Wikipedia
    ddg_results, wiki_results = (
        parallel_search(
            query
        )
    )

    # Prefer DDG but keep Wikipedia
    results = merge_results(
        ddg_results,
        wiki_results,
    )

    # Complete fallback
    if not results:

        print(
            "🔄 Search fallback: Wikipedia"
        )

        results = wikipedia_search(
            query
        )

    print(
        f"✅ Final search results: "
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
# TEXT EXTRACTION
# ============================================================

CONTENT_SELECTORS = (
    "article",
    "main",

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
    # Content containers
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

            return text

    # --------------------------------------------------------
    # Paragraph fallback
    # --------------------------------------------------------

    paragraphs = soup.find_all(
        "p"
    )

    parts = []

    total_length = 0

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

        total_length += len(
            value
        )

        if total_length >= MAX_TEXT_LENGTH:

            break

    return " ".join(
        parts
    )


# ============================================================
# WIKIPEDIA DIRECT READER
# ============================================================

def read_wikipedia_page(
    url: str,
) -> str:

    """
    Wikipedia pages are predictable,
    so extract their main content efficiently.
    """

    try:

        session = get_session()

        response = session.get(
            url,
            timeout=PAGE_TIMEOUT,
            headers={
                "Accept":
                    "text/html",
            },
        )

        if response.status_code != 200:

            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        content = (
            soup.select_one(
                "#mw-content-text"
            )
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
# READ WEBPAGE
# ============================================================

def read_page(
    url,
):

    if not is_valid_url(
        url
    ):

        return ""

    if is_blocked_domain(
        url
    ):

        return ""

    url = normalize_url(
        url
    )

    print(
        f"🌐 Reading: {url}"
    )

    # --------------------------------------------------------
    # Wikipedia optimization
    # --------------------------------------------------------

    if (
        "wikipedia.org" in
        get_domain(url)
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
                f"{response.status_code}: "
                f"{url}"
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
        # Content-Length protection
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
                        "⏭️ HTML too large"
                    )

                    return ""

            except (
                ValueError,
                TypeError,
            ):

                pass

        # ----------------------------------------------------
        # Stream limited body
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
                "⚠️ Not enough readable text"
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
            "⏱️ Page timeout:",
            url,
        )

        return ""

    except requests.exceptions.TooManyRedirects:

        print(
            "🔁 Too many redirects:",
            url,
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
            "❌ Page read error:",
            error,
        )

        return ""


# ============================================================
# READ ONE SOURCE
# ============================================================

def read_source(
    item,
):

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
        "title": str(
            item.get(
                "title",
                "Untitled source",
            )
        ).strip(),

        "url": url,

        "text": text,

        "source": str(
            item.get(
                "source",
                "Web",
            )
        ).strip(),
    }


# ============================================================
# RESEARCH API
# ============================================================

def research(
    question,
):

    """
    Full research API.

    Compatible with:
        from tools.researcher import research
    """

    results = search_web(
        question
    )

    if not results:

        print(
            "❌ No search results"
        )

        return []

    # Only read the first few sources.
    results_to_read = results[
        :MAX_SEARCH_RESULTS
    ]

    print(
        f"📚 Reading up to "
        f"{MAX_SOURCES_TO_READ} sources..."
    )

    sources = []

    # --------------------------------------------------------
    # Parallel source reading
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                read_source,
                item,
            )
            for item in results_to_read
        ]

        for future in as_completed(
            futures
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

                    break

            except Exception as error:

                print(
                    "⚠️ Source worker error:",
                    error,
                )

    # --------------------------------------------------------
    # Stable ordering
    # --------------------------------------------------------

    if sources:

        source_order = {
            item.get(
                "url",
                "",
            ): index

            for index, item
            in enumerate(
                results_to_read
            )
        }

        sources.sort(
            key=lambda item:
                source_order.get(
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
        "✅ FAST RESEARCH COMPLETE"
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
            "❌ Question required"
        )

        raise SystemExit(1)

    data = research(
        question
    )

    print(
        "\nFINAL SOURCES:"
    )

    for index, item in enumerate(
        data,
        1,
    ):

        print(
            f"\n[{index}] "
            f"{item['title']}"
        )

        print(
            "Source:",
            item.get(
                "source",
                "Web",
            )
        )

        print(
            "URL:",
            item["url"]
        )

        print(
            "Text:",
            item["text"][:500],
        )
