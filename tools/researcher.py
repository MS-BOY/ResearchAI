import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    quote,
    urlparse,
    parse_qs,
    unquote,
    urljoin
)

import time


# ============================================================
# CONFIG
# ============================================================

MAX_RESULTS = 8
MAX_TEXT_LENGTH = 8000

SEARCH_TIMEOUT = 20
PAGE_TIMEOUT = 20

MIN_TEXT_LENGTH = 80


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9",

    "Accept-Encoding":
        "gzip, deflate",

    "Connection":
        "keep-alive",

    "Upgrade-Insecure-Requests":
        "1"

})


# ============================================================
# DOMAIN HELPERS
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
# REAL URL
# ============================================================

def get_real_url(url):

    if not url:

        return ""


    url = str(url).strip()


    # DuckDuckGo relative URL

    if url.startswith("//"):

        url = "https:" + url


    # DuckDuckGo redirect

    if "duckduckgo.com/l/?" in url:

        try:

            parsed = urlparse(url)

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
                "⚠️ URL decode error:",
                str(e)
            )


    return url


# ============================================================
# SEARCH DUCKDUCKGO HTML
# ============================================================

def search_duckduckgo_html(question):

    print(
        "\n🔎 DuckDuckGo HTML search:"
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
            "🔎 Search HTTP:",
            response.status_code
        )


        print(
            "🌐 Search URL:",
            response.url
        )


        if response.status_code != 200:

            print(
                "❌ DuckDuckGo search failed"
            )

            return []


        html = response.text


        print(
            "📦 Search HTML:",
            len(html),
            "characters"
        )


        soup = BeautifulSoup(

            html,

            "html.parser"

        )


        results = []


        # Normal DDG results

        for result in soup.select(
            ".result"
        ):

            title_element = result.select_one(
                ".result__title"
            )

            link_element = result.select_one(
                ".result__a"
            )


            if not link_element:

                continue


            raw_url = link_element.get(
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


            title = ""

            if title_element:

                title = title_element.get_text(
                    " ",
                    strip=True
                )

            else:

                title = link_element.get_text(
                    " ",
                    strip=True
                )


            if not title:

                title = "Untitled source"


            if is_blocked_domain(
                real_url
            ):

                print(
                    "⏭️ Blocked/social:",
                    real_url
                )

                continue


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


    except Exception as e:

        print(
            "❌ DuckDuckGo exception:",
            str(e)
        )

        return []


# ============================================================
# SEARCH FALLBACK - DDG LITE
# ============================================================

def search_duckduckgo_lite(question):

    print(
        "\n🔎 Trying DuckDuckGo Lite..."
    )


    search_url = (
        "https://lite.duckduckgo.com/lite/?q="
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
            "🔎 Lite HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            return []


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        results = []


        for link in soup.select(
            "a"
        ):

            href = link.get(
                "href",
                ""
            )


            title = link.get_text(
                " ",
                strip=True
            )


            if not href:

                continue


            real_url = get_real_url(
                href
            )


            if not real_url.startswith(
                "http"
            ):

                continue


            if not title:

                continue


            if is_blocked_domain(
                real_url
            ):

                continue


            # Ignore DDG internal links

            if "duckduckgo.com" in get_domain(
                real_url
            ):

                continue


            results.append({

                "title":
                    title,

                "url":
                    real_url

            })


            print(
                f"✅ Lite result {len(results)}:",
                title
            )


            if len(results) >= MAX_RESULTS:

                break


        return results


    except Exception as e:

        print(
            "❌ DuckDuckGo Lite error:",
            str(e)
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


    print(
        "\n" + "=" * 70
    )

    print(
        "🌐 WEB SEARCH"
    )

    print(
        "🔎 Query:",
        question
    )

    print(
        "=" * 70
    )


    # ========================================================
    # FIRST SEARCH
    # ========================================================

    results = search_duckduckgo_html(
        question
    )


    # ========================================================
    # FALLBACK
    # ========================================================

    if not results:

        print(
            "\n⚠️ HTML search returned 0 results."
        )

        time.sleep(1)


        results = search_duckduckgo_lite(
            question
        )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = []

    seen = set()


    for item in results:

        url = item.get(
            "url",
            ""
        )


        if not url:

            continue


        normalized = url.rstrip(
            "/"
        ).lower()


        if normalized in seen:

            continue


        seen.add(
            normalized
        )


        unique.append(
            item
        )


    print(
        "\n📚 Final search results:",
        len(unique)
    )


    return unique[:MAX_RESULTS]


# ============================================================
# EXTRACT PAGE TEXT
# ============================================================

def extract_page_text(html, url):

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

        tag.decompose()


    # ========================================================
    # REMOVE COMMON ADS / UI
    # ========================================================

    for tag in soup.find_all(

        class_=lambda value:

        value and any(

            word in str(value).lower()

            for word in [

                "advertisement",
                "cookie",
                "popup",
                "modal",
                "sidebar",
                "social-share",
                "newsletter"

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
    # META DESCRIPTION
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
    # PRIORITY CONTENT
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

        found = soup.select_one(
            selector
        )


        if found:

            text_length = len(
                found.get_text(
                    " ",
                    strip=True
                )
            )


            if text_length >= MIN_TEXT_LENGTH:

                content = found

                break


    # ========================================================
    # FALLBACK TO BODY
    # ========================================================

    if content is None:

        content = soup.body


    if content is None:

        return ""


    # ========================================================
    # EXTRACT PARAGRAPHS
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
    # IF PARAGRAPHS EMPTY
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
    # ADD TITLE / DESCRIPTION WHEN USEFUL
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


    return text[:MAX_TEXT_LENGTH]


# ============================================================
# READ PAGE
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


    try:

        response = session.get(

            url,

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


        # ====================================================
        # HTTP ERROR
        # ====================================================

        if response.status_code >= 400:

            print(
                f"⚠️ Page blocked/error: "
                f"HTTP {response.status_code}"
            )

            return ""


        # ====================================================
        # NON HTML
        # ====================================================

        if (

            "text/html"
            not in content_type.lower()

            and

            "application/xhtml+xml"
            not in content_type.lower()

        ):

            print(
                "⚠️ Not an HTML webpage"
            )

            return ""


        # ====================================================
        # EXTRACT
        # ====================================================

        text = extract_page_text(

            response.text,

            response.url

        )


        print(
            "📝 Extracted characters:",
            len(text)
        )


        if len(text) < MIN_TEXT_LENGTH:

            print(
                "⚠️ Page text too short"
            )

            return ""


        print(
            "✅ Page readable"
        )


        return text


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


    except requests.exceptions.ConnectionError as e:

        print(
            "🌐 Connection error:",
            str(e)
        )

        return ""


    except requests.exceptions.RequestException as e:

        print(
            "❌ Request error:",
            str(e)
        )

        return ""


    except Exception as e:

        print(
            "❌ Page read failed:",
            str(e)
        )

        return ""


# ============================================================
# RESEARCH TEST
# ============================================================

def research(question):

    print(
        "\n" + "=" * 70
    )

    print(
        "🧠 RESEARCH TEST"
    )

    print(
        "❓ Question:",
        question
    )

    print(
        "=" * 70
    )


    results = search_web(
        question
    )


    if not results:

        print(
            "❌ No sources found."
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


        if is_blocked_domain(
            result["url"]
        ):

            print(
                "⏭️ Social/video source skipped"
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
        "📚 Readable sources:",
        len(readable_sources)
    )

    print(
        "=" * 70
    )


    return readable_sources
