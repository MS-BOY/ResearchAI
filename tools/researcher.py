```python
import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    quote,
    urlparse,
    parse_qs,
    unquote
)

import re
import time


# ============================================================
# CONFIG
# ============================================================

REQUEST_TIMEOUT = 20

MAX_SEARCH_RESULTS = 5

MAX_PAGE_LENGTH = 8000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent":
        USER_AGENT,

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9",

    "Connection":
        "keep-alive",

})


# ============================================================
# BLOCKED DOMAINS
# ============================================================

BLOCKED_DOMAINS = [

    "youtube.com",
    "youtu.be",

    "facebook.com",
    "fb.com",

    "instagram.com",

    "tiktok.com",

    "twitter.com",
    "x.com",

]


# ============================================================
# DOMAIN CHECK
# ============================================================

def is_blocked_domain(url):

    try:

        domain = urlparse(
            url
        ).netloc.lower()

        domain = domain.split(":")[0]

        for blocked in BLOCKED_DOMAINS:

            if (
                domain == blocked
                or domain.endswith(
                    "." + blocked
                )
            ):

                return True

    except Exception:

        pass


    return False


# ============================================================
# GET REAL DUCKDUCKGO URL
# ============================================================

def get_real_url(url):

    if not url:

        return ""


    url = str(
        url
    ).strip()


    # --------------------------------------------
    # Protocol-relative URL
    # --------------------------------------------

    if url.startswith("//"):

        url = "https:" + url


    # --------------------------------------------
    # DuckDuckGo redirect
    # --------------------------------------------

    if (
        "duckduckgo.com/l/?" in url
        or "duckduckgo.com/l/?" in url.lower()
    ):

        try:

            parsed = urlparse(
                url
            )

            params = parse_qs(
                parsed.query
            )


            if "uddg" in params:

                real_url =
                    params["uddg"][0]


                real_url =
                    unquote(
                        real_url
                    )


                real_url =
                    real_url.replace(
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
# CLEAN URL
# ============================================================

def normalize_url(url):

    if not url:

        return ""


    url = get_real_url(
        url
    )


    url = url.strip()


    if not (
        url.startswith("http://")
        or
        url.startswith("https://")
    ):

        return ""


    return url


# ============================================================
# SEARCH WEB
# ============================================================

def search_web(question):

    print(
        "\n" +
        "=" * 70
    )

    print(
        "🔎 WEB SEARCH"
    )

    print(
        "Query:",
        question
    )

    print(
        "=" * 70
    )


    if not question:

        return []


    question = str(
        question
    ).strip()


    search_url = (
        "https://html.duckduckgo.com/html/?q="
        +
        quote(question)
    )


    try:

        response = session.get(

            search_url,

            timeout=REQUEST_TIMEOUT,

            allow_redirects=True

        )


        print(
            "🔎 Search HTTP:",
            response.status_code
        )


        response.raise_for_status()


    except Exception as e:

        print(
            "❌ Search request failed:"
        )

        print(
            str(e)
        )

        return []


    soup = BeautifulSoup(

        response.text,

        "html.parser"

    )


    results = []


    # ========================================================
    # PRIMARY DDG SELECTOR
    # ========================================================

    result_blocks = soup.select(
        ".result"
    )


    print(
        "📚 Result blocks:",
        len(result_blocks)
    )


    for result in result_blocks:

        try:

            title_element =
                result.select_one(
                    ".result__title"
                )


            link_element =
                result.select_one(
                    ".result__a"
                )


            if not link_element:

                continue


            raw_url =
                link_element.get(
                    "href",
                    ""
                )


            real_url =
                normalize_url(
                    raw_url
                )


            if not real_url:

                continue


            title = ""


            if title_element:

                title =
                    title_element.get_text(
                        " ",
                        strip=True
                    )


            if not title:

                title =
                    link_element.get_text(
                        " ",
                        strip=True
                    )


            if not title:

                title =
                    "Untitled source"


            # ----------------------------------------
            # Skip blocked websites
            # ----------------------------------------

            if is_blocked_domain(
                real_url
            ):

                print(
                    "⏭️ Skipping blocked:",
                    real_url
                )

                continue


            # ----------------------------------------
            # Avoid duplicate URLs
            # ----------------------------------------

            already_exists = any(

                item["url"] ==
                real_url

                for item in results

            )


            if already_exists:

                continue


            results.append({

                "title":
                    title,

                "url":
                    real_url

            })


            print(
                f"✅ {len(results)}.",
                title
            )

            print(
                "   ",
                real_url
            )


            if (
                len(results)
                >= MAX_SEARCH_RESULTS
            ):

                break


        except Exception as e:

            print(
                "⚠️ Result parsing error:",
                e
            )

            continue


    print(
        "\n📚 Final search results:",
        len(results)
    )


    return results


# ============================================================
# CLEAN HTML TEXT
# ============================================================

def clean_html_text(
    html
):

    if not html:

        return ""


    try:

        soup =
            BeautifulSoup(
                html,
                "html.parser"
            )


        # ----------------------------------------------------
        # Remove unwanted elements
        # ----------------------------------------------------

        for tag in soup([

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

        ]):

            tag.decompose()


        # ----------------------------------------------------
        # Prefer article/main
        # ----------------------------------------------------

        container = (

            soup.find("article")

            or

            soup.find("main")

            or

            soup.body

            or

            soup

        )


        # ----------------------------------------------------
        # Paragraph extraction
        # ----------------------------------------------------

        paragraphs =
            container.find_all(
                "p"
            )


        paragraph_text = []


        for paragraph in paragraphs:

            text =
                paragraph.get_text(
                    " ",
                    strip=True
                )


            text =
                re.sub(
                    r"\s+",
                    " ",
                    text
                )


            if len(text) >= 30:

                paragraph_text.append(
                    text
                )


        # ----------------------------------------------------
        # Use paragraphs if available
        # ----------------------------------------------------

        if paragraph_text:

            text =
                " ".join(
                    paragraph_text
                )

        else:

            text =
                container.get_text(
                    " ",
                    strip=True
                )


        # ----------------------------------------------------
        # Normalize whitespace
        # ----------------------------------------------------

        text =
            re.sub(
                r"\s+",
                " ",
                text
            ).strip()


        return text[
            :MAX_PAGE_LENGTH
        ]


    except Exception as e:

        print(
            "⚠️ HTML cleaning failed:",
            e
        )

        return ""


# ============================================================
# READ WITH REQUESTS
# ============================================================

def read_page_requests(
    url
):

    print(
        "🌐 Requests reader:"
    )

    print(
        url
    )


    try:

        response =
            session.get(

                url,

                timeout=REQUEST_TIMEOUT,

                allow_redirects=True

            )


        print(
            "HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            return ""


        content_type =
            response.headers.get(
                "content-type",
                ""
            ).lower()


        # Only process HTML pages

        if (
            "text/html"
            not in content_type
        ):

            print(
                "⚠️ Not an HTML page:",
                content_type
            )

            return ""


        text =
            clean_html_text(
                response.text
            )


        if len(text) < 100:

            return ""


        return text


    except Exception as e:

        print(
            "⚠️ Requests reader failed:"
        )

        print(
            str(e)
        )

        return ""


# ============================================================
# PLAYWRIGHT READER
# ============================================================

def read_page_playwright(
    url
):

    print(
        "🎭 Playwright reader:"
    )

    print(
        url
    )


    try:

        from playwright.sync_api import (
            sync_playwright,
            TimeoutError as PlaywrightTimeoutError
        )


    except Exception as e:

        print(
            "⚠️ Playwright import failed:",
            e
        )

        return ""


    try:

        with sync_playwright() as p:

            browser =
                p.chromium.launch(

                    headless=True,

                    args=[

                        "--no-sandbox",

                        "--disable-setuid-sandbox",

                        "--disable-dev-shm-usage",

                        "--disable-gpu",

                        "--no-zygote",

                        "--single-process",

                    ]

                )


            page =
                browser.new_page(

                    user_agent=
                        USER_AGENT,

                    viewport={
                        "width": 1366,
                        "height": 768
                    }

                )


            page.set_default_timeout(
                20000
            )


            try:

                page.goto(

                    url,

                    wait_until="domcontentloaded",

                    timeout=20000

                )

            except PlaywrightTimeoutError:

                print(
                    "⚠️ Page navigation timeout"
                )

            except Exception as e:

                print(
                    "⚠️ Navigation failed:",
                    e
                )


            # Give JavaScript time to render

            try:

                page.wait_for_timeout(
                    1500
                )

            except Exception:

                pass


            html =
                page.content()


            browser.close()


        text =
            clean_html_text(
                html
            )


        if len(text) < 100:

            return ""


        return text


    except Exception as e:

        print(
            "❌ Playwright reader failed:"
        )

        print(
            str(e)
        )

        return ""


# ============================================================
# READ PAGE
# ============================================================

def read_page(
    url
):

    print(
        "\n" +
        "-" * 60
    )

    print(
        "📖 READING WEBPAGE"
    )

    print(
        url
    )

    print(
        "-" * 60
    )


    url =
        normalize_url(
            url
        )


    if not url:

        print(
            "❌ Invalid URL"
        )

        return ""


    # --------------------------------------------------------
    # Skip social/video sites
    # --------------------------------------------------------

    if is_blocked_domain(
        url
    ):

        print(
            "⏭️ Blocked/social website"
        )

        return ""


    # --------------------------------------------------------
    # Method 1: Requests
    # --------------------------------------------------------

    text =
        read_page_requests(
            url
        )


    if text:

        print(
            "✅ Page read with requests"
        )

        print(
            "📝 Characters:",
            len(text)
        )

        return text[
            :MAX_PAGE_LENGTH
        ]


    # --------------------------------------------------------
    # Method 2: Playwright
    # --------------------------------------------------------

    print(
        "🔄 Requests failed."
    )

    print(
        "🎭 Trying Playwright..."
    )


    text =
        read_page_playwright(
            url
        )


    if text:

        print(
            "✅ Page read with Playwright"
        )

        print(
            "📝 Characters:",
            len(text)
        )

        return text[
            :MAX_PAGE_LENGTH
        ]


    print(
        "❌ Could not read webpage"
    )


    return ""


# ============================================================
# FULL RESEARCH TEST
# ============================================================

def research(
    question
):

    print(
        "\n" +
        "=" * 70
    )

    print(
        "🤖 RESEARCHER TEST"
    )

    print(
        "=" * 70
    )


    results =
        search_web(
            question
        )


    if not results:

        print(
            "❌ No sources found."
        )

        return []


    successful =
        0


    sources = []


    for i, result in enumerate(
        results,
        1
    ):

        print(
            "\n" +
            "=" * 60
        )

        print(
            f"📄 SOURCE {i}"
        )

        print(
            "Title:",
            result["title"]
        )

        print(
            "URL:",
            result["url"]
        )


        text =
            read_page(
                result["url"]
            )


        if text:

            successful += 1


            source = {

                "title":
                    result["title"],

                "url":
                    result["url"],

                "text":
                    text

            }


            sources.append(
                source
            )


            print(
                "\n📝 Extracted text:"
            )

            print(
                text[:2000]
            )


        else:

            print(
                "⚠️ No readable text"
            )


    print(
        "\n" +
        "=" * 60
    )

    print(
        f"✅ Successfully read "
        f"{successful} source(s)."
    )


    return sources


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    research(
        "hello"
    )
```
