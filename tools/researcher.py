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


# ============================================================
# CONFIG
# ============================================================

MAX_RESULTS = 5

MAX_TEXT_LENGTH = 8000

SEARCH_TIMEOUT = 20

PAGE_TIMEOUT = 20

MIN_TEXT_LENGTH = 80


# ============================================================
# WEB SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xhtml+xml;q=0.9,"
        "application/xml;q=0.8,"
        "*/*;q=0.7",

    "Accept-Language":
        "en-US,en;q=0.9",

    "Connection":
        "keep-alive"

})


# ============================================================
# DOMAIN
# ============================================================

def get_domain(url):

    try:

        return urlparse(
            str(url)
        ).netloc.lower()

    except Exception:

        return ""


# ============================================================
# BLOCK SOCIAL / VIDEO
# ============================================================

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
# GET REAL URL
# ============================================================

def get_real_url(url):

    if not url:

        return ""


    url = str(
        url
    ).strip()


    # ----------------------------------------
    # Protocol-relative URL
    # ----------------------------------------

    if url.startswith("//"):

        url = "https:" + url


    # ----------------------------------------
    # DuckDuckGo redirect
    # ----------------------------------------

    if "duckduckgo.com/l/?" in url:

        try:

            parsed = urlparse(
                url
            )

            params = parse_qs(
                parsed.query
            )


            if "uddg" in params:

                real_url = params["uddg"][0]

                real_url = unquote(
                    real_url
                )

                real_url = real_url.replace(
                    "\\/",
                    "/"
                )

                return real_url

        except Exception as e:

            print(
                "⚠️ URL decode failed:",
                e
            )


    return url


# ============================================================
# DUCKDUCKGO HTML SEARCH
# ============================================================

def search_duckduckgo(question):

    print(
        "\n🔎 WEB SEARCH"
    )

    print(
        "❓ Query:",
        question
    )


    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(
            question
        )
    )


    try:

        response = session.get(

            search_url,

            timeout=SEARCH_TIMEOUT,

            allow_redirects=True

        )


        print(
            "📡 Search status:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "❌ Search server returned:",
                response.status_code
            )

            return []


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        results = []


        for result in soup.select(
            ".result"
        ):

            link = result.select_one(
                ".result__a"
            )


            if not link:

                continue


            raw_url = link.get(
                "href",
                ""
            )


            real_url = get_real_url(
                raw_url
            )


            if not real_url.startswith(
                "http"
            ):

                continue


            if is_blocked_domain(
                real_url
            ):

                print(
                    "⏭️ Social/video skipped:",
                    real_url
                )

                continue


            title_element = result.select_one(
                ".result__title"
            )


            if title_element:

                title = title_element.get_text(
                    " ",
                    strip=True
                )

            else:

                title = link.get_text(
                    " ",
                    strip=True
                )


            if not title:

                title = "Untitled source"


            results.append({

                "title":
                    title,

                "url":
                    real_url

            })


            print(
                f"✅ Result {len(results)}:",
                title
            )

            print(
                "   ",
                real_url
            )


            if len(results) >= MAX_RESULTS:

                break


        return results


    except requests.exceptions.Timeout:

        print(
            "⏱️ DuckDuckGo search timeout"
        )

        return []


    except requests.exceptions.RequestException as e:

        print(
            "❌ DuckDuckGo request error:",
            e
        )

        return []


    except Exception as e:

        print(
            "❌ Search error:",
            e
        )

        return []


# ============================================================
# WEB SEARCH
# ============================================================

def search_web(question):

    question = str(
        question or ""
    ).strip()


    if not question:

        return []


    print(
        "\n" + "=" * 70
    )

    print(
        "🌐 WEB SERVER SEARCH"
    )

    print(
        "=" * 70
    )


    results = search_duckduckgo(
        question
    )


    # ----------------------------------------
    # Remove duplicate URLs
    # ----------------------------------------

    unique = []

    seen = set()


    for item in results:

        url = item.get(
            "url",
            ""
        )


        normalized = url.rstrip(
            "/"
        ).lower()


        if not normalized:

            continue


        if normalized in seen:

            continue


        seen.add(
            normalized
        )


        unique.append(
            item
        )


    print(
        "\n📚 Final results:",
        len(unique)
    )


    return unique[:MAX_RESULTS]


# ============================================================
# EXTRACT PAGE TEXT
# ============================================================

def extract_page_text(
    html
):

    soup = BeautifulSoup(

        html,

        "html.parser"

    )


    # ========================================================
    # REMOVE UNWANTED ELEMENTS
    # ========================================================

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

        "textarea"

    ]


    for tag in soup.find_all(
        remove_tags
    ):

        try:

            tag.decompose()

        except Exception:

            pass


    # ========================================================
    # REMOVE COMMON UI / ADS
    # ========================================================

    for tag in soup.find_all(

        class_=lambda value:

        value and any(

            word in str(
                value
            ).lower()

            for word in [

                "advertisement",
                "cookie",
                "popup",
                "modal",
                "sidebar",
                "newsletter",
                "social-share"

            ]

        )

    ):

        try:

            tag.decompose()

        except Exception:

            pass


    # ========================================================
    # TITLE
    # ========================================================

    title = ""

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

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


    # ========================================================
    # FIND MAIN CONTENT
    # ========================================================

    content = None


    selectors = [

        "article",

        "main",

        "[role='main']",

        ".article",

        ".article-content",

        ".post-content",

        ".entry-content",

        ".content",

        "#content"

    ]


    for selector in selectors:

        element = soup.select_one(
            selector
        )


        if element:

            element_text = element.get_text(
                " ",
                strip=True
            )


            if len(element_text) >= MIN_TEXT_LENGTH:

                content = element

                break


    # ========================================================
    # BODY FALLBACK
    # ========================================================

    if content is None:

        content = soup.body


    if content is None:

        return ""


    # ========================================================
    # PARAGRAPHS
    # ========================================================

    paragraphs = []


    for p in content.find_all(
        "p"
    ):

        text = p.get_text(
            " ",
            strip=True
        )


        text = " ".join(
            text.split()
        )


        if len(text) >= 30:

            paragraphs.append(
                text
            )


    # ========================================================
    # CREATE TEXT
    # ========================================================

    if paragraphs:

        text = " ".join(
            paragraphs
        )

    else:

        text = content.get_text(
            " ",
            strip=True
        )


    text = " ".join(
        text.split()
    )


    # ========================================================
    # TITLE / DESCRIPTION
    # ========================================================

    if title and len(text) < 300:

        text = (
            title
            + ". "
            + text
        )


    if description and len(text) < 300:

        text = (
            text
            + " "
            + description
        )


    return text[
        :MAX_TEXT_LENGTH
    ]


# ============================================================
# READ WEB PAGE
# ============================================================

def read_page(url):

    if not url:

        return ""


    url = str(
        url
    ).strip()


    if is_blocked_domain(
        url
    ):

        print(
            "⏭️ Blocked domain:",
            url
        )

        return ""


    print(
        "\n🌐 WEB SERVER OPENING:"
    )

    print(
        url
    )


    try:

        response = session.get(

            url,

            timeout=PAGE_TIMEOUT,

            allow_redirects=True

        )


        print(
            "📡 HTTP:",
            response.status_code
        )

        print(
            "🔗 Final URL:",
            response.url
        )


        if response.status_code >= 400:

            print(
                "⚠️ HTTP error"
            )

            return ""


        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()


        print(
            "📦 Content-Type:",
            content_type
        )


        # Only HTML
        if (

            "text/html" not in content_type

            and

            "application/xhtml+xml"
            not in content_type

        ):

            print(
                "⚠️ Not an HTML page"
            )

            return ""


        text = extract_page_text(

            response.text

        )


        print(
            "📝 Extracted:",
            len(text),
            "characters"
        )


        if len(text) < MIN_TEXT_LENGTH:

            print(
                "⚠️ Text too short"
            )

            return ""


        print(
            "✅ Page readable"
        )


        return text


    except requests.exceptions.Timeout:

        print(
            "⏱️ Page timeout:",
            url
        )

        return ""


    except requests.exceptions.TooManyRedirects:

        print(
            "🔁 Too many redirects:",
            url
        )

        return ""


    except requests.exceptions.ConnectionError as e:

        print(
            "🌐 Connection error:",
            e
        )

        return ""


    except requests.exceptions.RequestException as e:

        print(
            "❌ Request error:",
            e
        )

        return ""


    except Exception as e:

        print(
            "❌ Page reading error:",
            e
        )

        return ""


# ============================================================
# RESEARCH TEST
# ============================================================

def research(question):

    results = search_web(
        question
    )


    if not results:

        print(
            "❌ No web results"
        )

        return []


    sources = []


    for index, result in enumerate(

        results,

        1

    ):

        print(
            "\n" + "=" * 60
        )

        print(
            f"📄 SOURCE {index}"
        )

        print(
            "Title:",
            result["title"]
        )

        print(
            "URL:",
            result["url"]
        )


        text = read_page(
            result["url"]
        )


        if not text:

            print(
                "⚠️ Could not read"
            )

            continue


        sources.append({

            "title":
                result["title"],

            "url":
                result["url"],

            "text":
                text

        })


    print(
        "\n" + "=" * 70
    )

    print(
        "✅ READABLE SOURCES:",
        len(sources)
    )

    print(
        "=" * 70
    )


    return sources
```
