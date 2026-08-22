```python
import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    quote,
    urlparse,
    parse_qs,
    unquote
)

import time
import re


# ============================================================
# CONFIG
# ============================================================

MAX_RESULTS = 8
MAX_TEXT_LENGTH = 8000

SEARCH_TIMEOUT = 20
PAGE_TIMEOUT = 20

MIN_TEXT_LENGTH = 80


# ============================================================
# USER AGENTS
# ============================================================

USER_AGENTS = [

    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),

    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),

    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    )

]


# ============================================================
# SESSION
# ============================================================

session = requests.Session()


def get_headers(user_agent=None):

    return {

        "User-Agent":
            user_agent or USER_AGENTS[0],

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.9",

        "Cache-Control":
            "no-cache",

        "Pragma":
            "no-cache",

        "Upgrade-Insecure-Requests":
            "1"

    }


# ============================================================
# DOMAIN
# ============================================================

def get_domain(url):

    try:

        return urlparse(url).netloc.lower()

    except Exception:

        return ""


def is_blocked_domain(url):

    domain = get_domain(url)

    blocked = [

        "youtube.com",
        "youtu.be",

        "facebook.com",
        "instagram.com",

        "tiktok.com",

        "twitter.com",
        "x.com",

        "pinterest.com"

    ]

    return any(
        site in domain
        for site in blocked
    )


# ============================================================
# URL CLEANER
# ============================================================

def get_real_url(url):

    if not url:
        return ""

    url = str(url).strip()

    if url.startswith("//"):
        url = "https:" + url

    try:

        parsed = urlparse(url)

        # DuckDuckGo redirect
        if "duckduckgo.com" in parsed.netloc:

            params = parse_qs(
                parsed.query
            )

            if "uddg" in params:

                real_url = params["uddg"][0]

                return unquote(
                    real_url
                ).replace(
                    "\\/",
                    "/"
                )

    except Exception as e:

        print(
            "⚠️ URL parsing error:",
            e
        )

    return url


# ============================================================
# SEARCH RESULT VALIDATION
# ============================================================

def add_result(
    results,
    title,
    url
):

    if not url:
        return

    url = get_real_url(url)

    if not url.startswith("http"):
        return

    if is_blocked_domain(url):
        return

    domain = get_domain(url)

    if not domain:
        return

    # Skip DDG internal pages
    if "duckduckgo.com" in domain:
        return

    # Duplicate
    for item in results:

        if item["url"].rstrip("/") == url.rstrip("/"):
            return

    results.append({

        "title":
            title or "Untitled source",

        "url":
            url

    })


# ============================================================
# DUCKDUCKGO HTML
# ============================================================

def search_duckduckgo_html(question):

    print("\n🔎 DuckDuckGo HTML search")
    print("❓ Query:", question)

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(question)
    )

    try:

        response = session.get(

            search_url,

            headers=get_headers(),

            timeout=SEARCH_TIMEOUT,

            allow_redirects=True

        )

        print(
            "🔎 Search HTTP:",
            response.status_code
        )

        print(
            "🌐 Search URL:",
            response.url
        )

        print(
            "📦 Search HTML:",
            len(response.text)
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        # Main DDG result containers
        containers = soup.select(
            ".result, .results_links, .result__body"
        )

        for container in containers:

            link = container.select_one(
                "a.result__a"
            )

            if not link:

                link = container.select_one(
                    "a[href]"
                )

            if not link:
                continue

            href = link.get(
                "href",
                ""
            )

            title = link.get_text(
                " ",
                strip=True
            )

            add_result(
                results,
                title,
                href
            )

            if len(results) >= MAX_RESULTS:
                break

        print(
            "📚 HTML results:",
            len(results)
        )

        return results

    except Exception as e:

        print(
            "❌ DDG HTML error:",
            repr(e)
        )

        return []


# ============================================================
# DUCKDUCKGO LITE
# ============================================================

def search_duckduckgo_lite(question):

    print("\n🔎 DuckDuckGo Lite fallback")

    search_url = (
        "https://lite.duckduckgo.com/lite/?q="
        + quote(question)
    )

    try:

        response = session.get(

            search_url,

            headers=get_headers(),

            timeout=SEARCH_TIMEOUT,

            allow_redirects=True

        )

        print(
            "🔎 Lite HTTP:",
            response.status_code
        )

        print(
            "📦 Lite HTML:",
            len(response.text)
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for link in soup.find_all("a"):

            href = link.get(
                "href",
                ""
            )

            title = link.get_text(
                " ",
                strip=True
            )

            if not href or not title:
                continue

            add_result(
                results,
                title,
                href
            )

            if len(results) >= MAX_RESULTS:
                break

        print(
            "📚 Lite results:",
            len(results)
        )

        return results

    except Exception as e:

        print(
            "❌ DDG Lite error:",
            repr(e)
        )

        return []


# ============================================================
# MAIN SEARCH
# ============================================================

def search_web(question):

    question = str(
        question or ""
    ).strip()

    if not question:
        return []

    print("\n" + "=" * 70)
    print("🌐 WEB SEARCH")
    print("🔎 Query:", question)
    print("=" * 70)

    results = search_duckduckgo_html(
        question
    )

    if not results:

        print(
            "\n⚠️ HTML search returned no results."
        )

        time.sleep(0.5)

        results = search_duckduckgo_lite(
            question
        )

    print(
        "\n📚 FINAL SEARCH RESULTS:",
        len(results)
    )

    for index, item in enumerate(
        results,
        1
    ):

        print(
            f"{index}. {item['title']}"
        )

        print(
            f"   {item['url']}"
        )

    return results[:MAX_RESULTS]


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT PAGE TEXT
# ============================================================

def extract_page_text(
    html,
    url
):

    if not html:
        return ""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # --------------------------------------------------------
    # Remove unwanted
    # --------------------------------------------------------

    remove_tags = [

        "script",
        "style",
        "noscript",

        "nav",
        "footer",
        "header",

        "aside",
        "form",

        "iframe",

        "svg",
        "canvas",

        "button",
        "input",
        "textarea",

        "select"

    ]

    for tag in soup.find_all(
        remove_tags
    ):

        try:
            tag.decompose()
        except Exception:
            pass

    # --------------------------------------------------------
    # Remove common UI
    # --------------------------------------------------------

    bad_words = [

        "advertisement",
        "cookie",
        "popup",
        "modal",
        "newsletter",
        "social-share",
        "share-buttons",
        "sidebar"

    ]

    for tag in soup.find_all(
        True
    ):

        try:

            classes = " ".join(
                tag.get(
                    "class",
                    []
                )
            ).lower()

            tag_id = str(
                tag.get(
                    "id",
                    ""
                )
            ).lower()

            combined = (
                classes
                + " "
                + tag_id
            )

            if any(
                word in combined
                for word in bad_words
            ):

                tag.decompose()

        except Exception:
            pass

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = ""

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

    # --------------------------------------------------------
    # Meta description
    # --------------------------------------------------------

    description = ""

    meta = soup.find(
        "meta",
        attrs={
            "name":
                "description"
        }
    )

    if meta:

        description = meta.get(
            "content",
            ""
        )

    # --------------------------------------------------------
    # Find main content
    # --------------------------------------------------------

    content = None

    selectors = [

        "article",
        "main",
        "[role='main']",

        ".article-content",
        ".article-body",

        ".post-content",
        ".post-body",

        ".entry-content",

        ".story-body",

        ".content-body",

        "#content"

    ]

    best_length = 0

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

            for element in elements:

                length = len(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if length > best_length:

                    best_length = length
                    content = element

        except Exception:
            pass

    # --------------------------------------------------------
    # Body fallback
    # --------------------------------------------------------

    if content is None:

        content = soup.body

    if content is None:

        return ""

    # --------------------------------------------------------
    # Paragraphs
    # --------------------------------------------------------

    paragraphs = []

    for p in content.find_all(
        "p"
    ):

        text = clean_text(
            p.get_text(
                " ",
                strip=True
            )
        )

        if len(text) >= 30:

            paragraphs.append(
                text
            )

    if paragraphs:

        text = " ".join(
            paragraphs
        )

    else:

        text = clean_text(
            content.get_text(
                " ",
                strip=True
            )
        )

    # --------------------------------------------------------
    # Add metadata if content short
    # --------------------------------------------------------

    if len(text) < 300:

        extra = []

        if title:
            extra.append(title)

        if description:
            extra.append(description)

        if extra:

            text = (
                " ".join(extra)
                + " "
                + text
            )

    text = clean_text(
        text
    )

    return text[:MAX_TEXT_LENGTH]


# ============================================================
# READ PAGE WITH RETRY
# ============================================================

def read_page(url):

    if not url:
        return ""

    url = str(
        url
    ).strip()

    print(
        "\n🌐 Opening:",
        url
    )

    for attempt, user_agent in enumerate(
        USER_AGENTS,
        1
    ):

        try:

            print(
                f"🔄 Page attempt {attempt}"
            )

            response = session.get(

                url,

                headers=get_headers(
                    user_agent
                ),

                timeout=PAGE_TIMEOUT,

                allow_redirects=True

            )

            print(
                "📡 Page HTTP:",
                response.status_code
            )

            print(
                "🔗 Final URL:",
                response.url
            )

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            print(
                "📦 Content-Type:",
                content_type
            )

            print(
                "📦 Response size:",
                len(response.content)
            )

            # ------------------------------------------------
            # Success
            # ------------------------------------------------

            if response.status_code == 200:

                if (

                    "text/html"
                    not in content_type.lower()

                    and

                    "application/xhtml+xml"
                    not in content_type.lower()

                ):

                    print(
                        "⚠️ Non-HTML source"
                    )

                    return ""

                text = extract_page_text(

                    response.text,

                    response.url

                )

                print(
                    "📝 Extracted characters:",
                    len(text)
                )

                if len(text) >= MIN_TEXT_LENGTH:

                    print(
                        "✅ PAGE READ SUCCESS"
                    )

                    return text

                print(
                    "⚠️ Text too short"
                )

                continue

            # ------------------------------------------------
            # Blocked
            # ------------------------------------------------

            if response.status_code in (
                401,
                403,
                406,
                429
            ):

                print(
                    "⚠️ Website blocked request:",
                    response.status_code
                )

                time.sleep(0.7)

                continue

            # ------------------------------------------------
            # Other HTTP
            # ------------------------------------------------

            print(
                "⚠️ HTTP error:",
                response.status_code
            )

        except requests.exceptions.Timeout:

            print(
                "⏱️ Timeout"
            )

        except requests.exceptions.TooManyRedirects:

            print(
                "🔁 Too many redirects"
            )

            break

        except requests.exceptions.ConnectionError as e:

            print(
                "🌐 Connection error:",
                repr(e)
            )

        except requests.exceptions.RequestException as e:

            print(
                "❌ Request error:",
                repr(e)
            )

        except Exception as e:

            print(
                "❌ Unexpected read error:",
                repr(e)
            )

    print(
        "❌ Could not read page:",
        url
    )

    return ""


# ============================================================
# RESEARCH TEST
# ============================================================

def research(question):

    print("\n" + "=" * 70)
    print("🧠 RESEARCH TEST")
    print("❓ Question:", question)
    print("=" * 70)

    results = search_web(
        question
    )

    if not results:

        print(
            "❌ NO SEARCH RESULTS"
        )

        return []

    readable_sources = []

    for index, result in enumerate(
        results,
        1
    ):

        print(
            "\n" + "-" * 60
        )

        print(
            f"📄 SOURCE {index}/{len(results)}"
        )

        print(
            "Title:",
            result["title"]
        )

        print(
            "URL:",
            result["url"]
        )

        if is_blocked_domain(
            result["url"]
        ):

            print(
                "⏭️ Social/video skipped"
            )

            continue

        text = read_page(
            result["url"]
        )

        if text:

            readable_sources.append({

                "title":
                    result["title"],

                "url":
                    result["url"],

                "text":
                    text

            })

            print(
                "✅ Source successfully read"
            )

        else:

            print(
                "⚠️ Source could not be read"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "📚 SEARCH RESULTS:",
        len(results)
    )

    print(
        "📖 READABLE SOURCES:",
        len(readable_sources)
    )

    print(
        "=" * 70
    )

    return readable_sources
```
