"""
Production Research Engine
==========================

Features:
- DuckDuckGo HTML search
- Wikipedia API search
- Parallel source reading
- Fast timeouts
- Retry handling
- Render-friendly
- Local-friendly
- HTML extraction
- Wikipedia fallback
- Duplicate removal
- Domain filtering
- Response size protection
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIG
# ============================================================

MAX_SEARCH_RESULTS = 8
MAX_SOURCES_TO_READ = 3
MAX_TEXT_LENGTH = 8000
MAX_QUERY_LENGTH = 500

SEARCH_TIMEOUT = 10
PAGE_TIMEOUT = 8
WIKI_TIMEOUT = 8

MAX_HTML_SIZE = 2 * 1024 * 1024  # 2 MB

MAX_WORKERS = 3

USER_AGENT = (
    "ResearchAI/1.0 "
    "(web research application)"
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
    "x.com",
    "twitter.com",
}


# ============================================================
# SESSION
# ============================================================

def create_session():

    session = requests.Session()

    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.3,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],

        allowed_methods=[
            "GET",
            "HEAD",
        ],

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


session = create_session()


# ============================================================
# QUERY CLEANING
# ============================================================

def clean_query(question):

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

def is_valid_url(url):

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

def get_domain(url):

    try:

        return (
            urlparse(url)
            .netloc
            .lower()
            .split(":")[0]
            .replace("www.", "")
        )

    except Exception:

        return ""


# ============================================================
# BLOCKED CHECK
# ============================================================

def is_blocked_domain(url):

    domain = get_domain(
        url
    )

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
# DUCKDUCKGO URL
# ============================================================

def get_real_url(url):

    if not url:
        return None

    try:

        if url.startswith("//"):

            url = "https:" + url

        if "duckduckgo.com/l/?" in url:

            parsed = urlparse(
                url
            )

            params = parse_qs(
                parsed.query
            )

            if "uddg" in params:

                real_url = params["uddg"][0]

                return unquote(
                    real_url
                )

        return url

    except Exception:

        return url


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def duckduckgo_search(query):

    print(
        f"\n🦆 DuckDuckGo: {query}"
    )

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    try:

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

        for result in soup.select(
            ".result"
        ):

            title_element = (
                result.select_one(
                    ".result__title"
                )
            )

            link_element = (
                result.select_one(
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

            url = get_real_url(
                raw_url
            )

            if not is_valid_url(url):

                continue

            if url in seen:

                continue

            if is_blocked_domain(url):

                continue

            seen.add(url)

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
            "❌ DDG error:",
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
            [],
        )

        results = []

        for page in pages:

            title = page.get(
                "title"
            )

            if not title:

                continue

            key = page.get(
                "key",
                title.replace(
                    " ",
                    "_",
                ),
            )

            page_url = (
                "https://en.wikipedia.org/wiki/"
                + quote(
                    key,
                    safe="",
                )
            )

            excerpt = BeautifulSoup(
                page.get(
                    "excerpt",
                    "",
                ),
                "html.parser",
            ).get_text(
                " ",
                strip=True,
            )

            results.append({

                "title":
                    title,

                "url":
                    page_url,

                "source":
                    "Wikipedia",

                "excerpt":
                    excerpt,

                "description":
                    page.get(
                        "description",
                        "",
                    ),
            })

            if (
                len(results)
                >= MAX_SEARCH_RESULTS
            ):

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

        url = item.get(
            "url"
        )

        if not is_valid_url(url):

            continue

        if url in seen:

            continue

        seen.add(url)

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
# MAIN SEARCH
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
        query,
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # DDG
    # --------------------------------------------------------

    ddg_results = duckduckgo_search(
        query
    )

    # --------------------------------------------------------
    # Wikipedia
    # --------------------------------------------------------

    wiki_results = []

    if len(ddg_results) < 3:

        wiki_results = wikipedia_search(
            query
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    results = merge_results(
        ddg_results,
        wiki_results,
    )

    # --------------------------------------------------------
    # Complete fallback
    # --------------------------------------------------------

    if not results:

        print(
            "🔄 Trying Wikipedia fallback..."
        )

        results = wikipedia_search(
            query
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

    # Article
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

    # Main
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

    # Common content
    selectors = [

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

    # Paragraph fallback
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

    return " ".join(
        parts
    )


# ============================================================
# READ WEBPAGE
# ============================================================

def read_page(url):

    if not is_valid_url(url):

        return ""

    if is_blocked_domain(url):

        return ""

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
        # Content size protection
        # ----------------------------------------------------

        content_length = response.headers.get(
            "Content-Length"
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

            except ValueError:

                pass

        # ----------------------------------------------------
        # Read limited content
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

            if len(data) > MAX_HTML_SIZE:

                print(
                    "⏭️ HTML size limit reached"
                )

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

        if len(text) < 100:

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
            "🔁 Redirect limit"
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
            "❌ Read failed:",
            error,
        )

        return ""


# ============================================================
# RESEARCH ONE SOURCE
# ============================================================

def read_source(item):

    url = item.get(
        "url",
        "",
    )

    if not url:

        return None

    text = read_page(
        url
    )

    if not text:

        return None

    return {

        "title":
            item.get(
                "title",
                "Untitled",
            ),

        "url":
            url,

        "text":
            text,

        "source":
            item.get(
                "source",
                "Web",
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

    print(
        f"\n📚 Reading "
        f"{min(len(results), MAX_SEARCH_RESULTS)} "
        f"sources..."
    )

    results_to_read = results[
        :MAX_SEARCH_RESULTS
    ]

    sources = []

    # ========================================================
    # PARALLEL READING
    # ========================================================

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                read_source,
                item,
            ): item

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

                    print(
                        f"✅ Source accepted "
                        f"({len(sources)})"
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

    print(
        "\n" + "=" * 60
    )

    print(
        f"✅ Research complete"
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
    )

    data = research(
        question
    )

    print(
        "\nFINAL SOURCES:"
    )

    for item in data:

        print(
            "\nTitle:",
            item["title"],
        )

        print(
            "Source:",
            item["source"],
        )

        print(
            "URL:",
            item["url"],
        )

        print(
            "Text:",
            item["text"][:500],
        )
