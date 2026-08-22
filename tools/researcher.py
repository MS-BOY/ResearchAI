"""
Research AI - Fast Production Research Engine
===============================================

Public API:
    search_web(question)
    read_page(url)
    research(question)

Flow:
    User Question
        ↓
    DuckDuckGo Web Search
        ↓
    Filter / Rank / Deduplicate
        ↓
    Read up to 3 different websites
        ↓
    Clean article text
        ↓
    Return structured sources to app.py

Designed for:
    - Flask
    - Gunicorn
    - Render
    - Low memory
    - Fast response
    - Parallel requests
    - No Playwright
    - No Selenium
    - No Google API required

Important:
    This is a web research/scraping engine.
    Some websites may block bots, require JavaScript,
    login, Cloudflare, or otherwise refuse scraping.
    Those sources are skipped automatically.
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

# Search result count
MAX_SEARCH_RESULTS = 10

# Maximum actual articles to read
MAX_SOURCES_TO_READ = 3

# Parallel search workers
SEARCH_WORKERS = 2

# Parallel page readers
READ_WORKERS = 3

# Timeouts
SEARCH_TIMEOUT = 5
PAGE_TIMEOUT = 6
WIKI_TIMEOUT = 5

# Content limits
MAX_TEXT_LENGTH = 8000
MAX_HTML_SIZE = 2 * 1024 * 1024

# Minimum useful article
MIN_PAGE_TEXT = 180

# Maximum response text per source
MAX_SOURCE_CHARS = 8000

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
# DOMAINS WE DO NOT SCRAPE
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

    "telegram.me",
    "t.me",
}


# ============================================================
# PREFERRED / LOW QUALITY DOMAINS
# ============================================================

LOW_PRIORITY_DOMAINS = {
    "quora.com",
    "medium.com",
}

PREFERRED_DOMAINS = {
    "wikipedia.org",
    "britannica.com",
    "reuters.com",
    "bbc.com",
    "bbc.co.uk",
    "apnews.com",
    "nasa.gov",
    "who.int",
    "un.org",
}


# ============================================================
# THREAD LOCAL SESSION
# ============================================================

_thread_local = threading.local()


def create_session() -> requests.Session:
    """
    Create an optimized reusable HTTP session.

    Each thread gets its own Session instance.
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


def get_session() -> requests.Session:
    """
    Get thread-local HTTP session.
    """

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
    """
    Normalize user question.
    """

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


# ============================================================
# DOMAIN
# ============================================================

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


def base_domain(url: str) -> str:

    """
    Return simplified domain.

    Example:
        news.example.com
        -> example.com

    This is intentionally simple and doesn't try
    to implement the complete public suffix list.
    """

    domain = get_domain(url)

    parts = domain.split(".")

    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return domain


# ============================================================
# DOMAIN FILTER
# ============================================================

def is_blocked_domain(url: str) -> bool:

    domain = get_domain(url)

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

def normalize_url(url: str) -> str:

    if not url:
        return ""

    try:

        url = str(
            url
        ).strip()

        if url.startswith("//"):
            url = "https:" + url

        # ----------------------------------------------------
        # DuckDuckGo redirect
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Remove fragment
        # ----------------------------------------------------

        parsed = urlparse(
            url
        )

        parsed = parsed._replace(
            fragment=""
        )

        url = parsed.geturl()

        return url

    except Exception:

        return str(
            url
        )


# ============================================================
# URL KEY
# ============================================================

def result_key(url: str) -> str:

    try:

        parsed = urlparse(
            normalize_url(url)
        )

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        path = parsed.path.rstrip("/")

        return (
            domain
            + path
        ).lower()

    except Exception:

        return str(
            url
        ).lower().strip()


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def duckduckgo_search(
    query: str,
):

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

            snippet_element = (
                item.select_one(
                    ".result__snippet"
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

            snippet = ""

            if snippet_element:

                snippet = snippet_element.get_text(
                    " ",
                    strip=True,
                )

            results.append({
                "title": title,
                "url": url,
                "source": "DuckDuckGo",
                "snippet": snippet,
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
        "limit": 4,
    }

    try:

        session = get_session()

        response = session.get(
            url,
            params=params,
            timeout=WIKI_TIMEOUT,
        )

        if response.status_code != 200:
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
                "title": title,
                "url": page_url,
                "source": "Wikipedia",
                "snippet": page.get(
                    "excerpt",
                    "",
                ),
            })

        print(
            f"✅ Wikipedia results: {len(results)}"
        )

        return results

    except Exception as error:

        print(
            "⚠️ Wikipedia error:",
            error,
        )

        return []


# ============================================================
# SEARCH IN PARALLEL
# ============================================================

def parallel_search(
    query: str,
):

    ddg_results = []
    wiki_results = []

    with ThreadPoolExecutor(
        max_workers=SEARCH_WORKERS
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
                "⚠️ DDG worker:",
                error,
            )

        try:
            wiki_results = (
                wiki_future.result()
            )
        except Exception as error:
            print(
                "⚠️ Wiki worker:",
                error,
            )

    return (
        ddg_results,
        wiki_results,
    )


# ============================================================
# RESULT SCORING
# ============================================================

def score_result(
    item: dict,
    query: str,
) -> int:

    url = item.get(
        "url",
        "",
    )

    title = item.get(
        "title",
        "",
    ).lower()

    domain = get_domain(
        url
    )

    score = 0

    # --------------------------------------------------------
    # Prefer actual web articles over Wikipedia
    # --------------------------------------------------------

    if domain == "wikipedia.org":
        score -= 10
    else:
        score += 10

    # --------------------------------------------------------
    # Preferred reliable domains
    # --------------------------------------------------------

    if domain in PREFERRED_DOMAINS:
        score += 8

    # --------------------------------------------------------
    # Low priority domains
    # --------------------------------------------------------

    if domain in LOW_PRIORITY_DOMAINS:
        score -= 4

    # --------------------------------------------------------
    # Article-like title
    # --------------------------------------------------------

    article_words = (
        "news",
        "report",
        "guide",
        "explained",
        "analysis",
        "research",
        "study",
        "update",
        "latest",
        "how",
        "what",
        "why",
    )

    for word in article_words:

        if word in title:
            score += 1

    # --------------------------------------------------------
    # Query word matching
    # --------------------------------------------------------

    query_words = set(
        re.findall(
            r"[a-zA-Z0-9]{3,}",
            query.lower(),
        )
    )

    for word in query_words:

        if word in title:
            score += 2

    return score


# ============================================================
# MERGE + DEDUPLICATE + DIVERSIFY
# ============================================================

def merge_results(
    ddg_results,
    wiki_results,
    query="",
):

    candidates = []

    seen_urls = set()

    # DDG first
    for item in (
        ddg_results
        + wiki_results
    ):

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

        if key in seen_urls:
            continue

        seen_urls.add(key)

        item = dict(item)

        item["url"] = url

        item["_score"] = score_result(
            item,
            query,
        )

        candidates.append(
            item
        )

    # --------------------------------------------------------
    # Sort by quality
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: x.get(
            "_score",
            0,
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # Domain diversity
    # --------------------------------------------------------

    final = []

    used_domains = set()

    # First pass:
    # one source per domain
    for item in candidates:

        domain = base_domain(
            item["url"]
        )

        if domain in used_domains:
            continue

        used_domains.add(domain)

        item.pop(
            "_score",
            None,
        )

        final.append(
            item
        )

        if len(final) >= MAX_SEARCH_RESULTS:
            break

    return final


# ============================================================
# PUBLIC SEARCH
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
        query,
    )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not results:

        print(
            "🔄 Wikipedia fallback..."
        )

        results = wikipedia_search(
            query
        )

    print(
        f"✅ Search results: {len(results)}"
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
    "template",
)


def clean_html(
    soup: BeautifulSoup,
):

    for tag in soup(
        UNWANTED_TAGS
    ):

        tag.decompose()


# ============================================================
# CONTENT SELECTORS
# ============================================================

CONTENT_SELECTORS = (

    # Schema.org article
    "[itemprop='articleBody']",

    # Common article containers
    "article",

    "main",

    ".article-body",

    ".article-content",

    ".article__body",

    ".post-content",

    ".entry-content",

    ".post-body",

    ".story-body",

    ".story-content",

    ".content-body",

    ".page-content",

    ".news-content",

    ".article-text",

    ".article__content",

    "#article",

    "#article-content",

    "#main-content",

    "#content",

)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    text: str,
) -> str:

    text = re.sub(
        r"\s+",
        " ",
        text or "",
    )

    return text.strip()


# ============================================================
# ARTICLE TEXT EXTRACTION
# ============================================================

def extract_text(
    soup: BeautifulSoup,
) -> str:

    clean_html(
        soup
    )

    # --------------------------------------------------------
    # Best content containers
    # --------------------------------------------------------

    best_text = ""

    for selector in CONTENT_SELECTORS:

        try:

            elements = soup.select(
                selector
            )

        except Exception:

            continue

        for element in elements:

            text = normalize_text(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) > len(
                best_text
            ):

                best_text = text

    if len(best_text) >= MIN_PAGE_TEXT:

        return best_text[
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

        value = normalize_text(
            paragraph.get_text(
                " ",
                strip=True,
            )
        )

        if len(value) < 35:
            continue

        parts.append(
            value
        )

        total += len(value)

        if total >= MAX_TEXT_LENGTH:
            break

    return normalize_text(
        " ".join(parts)
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

            text = normalize_text(
                content.get_text(
                    " ",
                    strip=True,
                )
            )

        else:

            text = extract_text(
                soup
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
# READ WEB PAGE
# ============================================================

def read_page(
    url: str,
) -> str:

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

    # --------------------------------------------------------
    # Wikipedia
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # HTTP status
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                f"⚠️ HTTP {response.status_code}"
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
            "text/html" not in content_type
            and
            "application/xhtml+xml"
            not in content_type
        ):

            print(
                "⏭️ Not HTML"
            )

            return ""

        # ----------------------------------------------------
        # Content size
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
        # Parse HTML
        # ----------------------------------------------------

        soup = BeautifulSoup(
            bytes(data),
            "html.parser",
        )

        text = extract_text(
            soup
        )

        text = normalize_text(
            text
        )

        if len(text) < MIN_PAGE_TEXT:

            print(
                "⚠️ Insufficient article text"
            )

            return ""

        print(
            f"✅ Extracted {len(text)} chars"
        )

        return text[
            :MAX_SOURCE_CHARS
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
# READ ONE SOURCE
# ============================================================

def read_source(
    item: dict,
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

        "snippet": str(
            item.get(
                "snippet",
                "",
            )
        ).strip(),
    }


# ============================================================
# SOURCE QUALITY CHECK
# ============================================================

def is_useful_source(
    source: dict,
) -> bool:

    if not source:
        return False

    text = source.get(
        "text",
        "",
    )

    url = source.get(
        "url",
        "",
    )

    if not is_valid_url(url):
        return False

    if len(text) < MIN_PAGE_TEXT:
        return False

    return True


# ============================================================
# FULL RESEARCH API
# ============================================================

def research(
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
        "🚀 RESEARCH START"
    )

    print(
        "Question:",
        query,
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    results = search_web(
        query
    )

    if not results:

        print(
            "❌ No search results"
        )

        return []

    # --------------------------------------------------------
    # Try more candidates than needed.
    #
    # If one site blocks scraping,
    # another site can replace it.
    # --------------------------------------------------------

    candidates = results[
        :MAX_SEARCH_RESULTS
    ]

    print(
        f"📚 Candidate sources: "
        f"{len(candidates)}"
    )

    # --------------------------------------------------------
    # PARALLEL READING
    # --------------------------------------------------------

    sources = []

    with ThreadPoolExecutor(
        max_workers=READ_WORKERS
    ) as executor:

        future_map = {
            executor.submit(
                read_source,
                item,
            ): item

            for item in candidates
        }

        for future in as_completed(
            future_map
        ):

            try:

                source = future.result()

                if not source:
                    continue

                if not is_useful_source(
                    source
                ):
                    continue

                sources.append(
                    source
                )

                print(
                    f"✅ Source accepted "
                    f"{len(sources)}/"
                    f"{MAX_SOURCES_TO_READ}"
                )

                # ------------------------------------------------
                # Stop after enough usable sources
                # ------------------------------------------------

                if (
                    len(sources)
                    >= MAX_SOURCES_TO_READ
                ):

                    break

            except Exception as error:

                print(
                    "⚠️ Reader worker error:",
                    error,
                )

    # --------------------------------------------------------
    # Preserve original search order
    # --------------------------------------------------------

    source_order = {
        result.get(
            "url",
            "",
        ): index

        for index, result
        in enumerate(
            candidates
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

    # --------------------------------------------------------
    # Final domain deduplication
    # --------------------------------------------------------

    final_sources = []

    used_domains = set()

    for source in sources:

        domain = base_domain(
            source.get(
                "url",
                "",
            )
        )

        if domain in used_domains:
            continue

        used_domains.add(
            domain
        )

        final_sources.append(
            source
        )

        if (
            len(final_sources)
            >= MAX_SOURCES_TO_READ
        ):
            break

    # --------------------------------------------------------
    # Log
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ RESEARCH COMPLETE"
    )

    print(
        f"📚 Sources returned: "
        f"{len(final_sources)}"
    )

    for index, source in enumerate(
        final_sources,
        1,
    ):

        print(
            f"{index}. "
            f"{source.get('title', 'Untitled')}"
        )

        print(
            f"   {source.get('url', '')}"
        )

    print(
        "=" * 60
    )

    return final_sources


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

    print(
        "\nFINAL SOURCES"
    )

    print(
        "=" * 60
    )

    for index, source in enumerate(
        sources,
        1,
    ):

        print(
            f"\n[{index}] "
            f"{source.get('title', 'Untitled')}"
        )

        print(
            "Source:",
            source.get(
                "source",
                "Web",
            )
        )

        print(
            "URL:",
            source.get(
                "url",
                "",
            )
        )

        print(
            "Text:"
        )

        print(
            source.get(
                "text",
                "",
            )[:1000]
        )
