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

MAX_SEARCH_RESULTS = 8

MAX_READABLE_SOURCES = 5

MAX_TEXT_LENGTH = 8000

MIN_TEXT_LENGTH = 80

SEARCH_TIMEOUT = 15

PAGE_TIMEOUT = 15

RETRY_COUNT = 2


# ============================================================
# SESSION
# ============================================================

session = requests.Session()


session.headers.update({

    "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,image/webp,"
        "*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9",

    "Cache-Control":
        "no-cache",

    "Pragma":
        "no-cache",

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
# BLOCKED DOMAINS
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
        domain == site
        or domain.endswith("." + site)
        for site in blocked
    )


# ============================================================
# REAL DUCKDUCKGO URL
# ============================================================

def get_real_url(url):

    if not url:

        return ""


    url = str(
        url
    ).strip()


    # ----------------------------------------
    # Relative URL
    # ----------------------------------------

    if url.startswith("//"):

        url = "https:" + url


    # ----------------------------------------
    # DDG redirect
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
                "⚠️ URL decode error:",
                e
            )


    return url


# ============================================================
# SEARCH DUCKDUCKGO
# ============================================================

def search_duckduckgo(question):

    print(
        "\n🔎 Searching DuckDuckGo..."
    )

    print(
        "❓ Query:",
        question
    )


    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(question)
    )


    try:

        response = session.get(

            search_url,

            timeout=SEARCH_TIMEOUT,

            allow_redirects=True

        )


        print(
            "📡 DDG HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "❌ DDG search failed"
            )

            return []


        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )


        results = []


        for item in soup.select(
            ".result"
        ):

            link = item.select_one(
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

                continue


            title_element = item.select_one(
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


            # ------------------------------------
            # DDG RESULT SNIPPET
            # ------------------------------------

            snippet_element = (
                item.select_one(
                    ".result__snippet"
                )
            )


            if snippet_element:

                snippet = snippet_element.get_text(
                    " ",
                    strip=True
                )

            else:

                snippet = ""


            results.append({

                "title":
                    title,

                "url":
                    real_url,

                "snippet":
                    snippet

            })


            print(
                f"✅ Search result {len(results)}:"
            )

            print(
                "   Title:",
                title
            )

            print(
                "   URL:",
                real_url
            )


            if len(results) >= MAX_SEARCH_RESULTS:

                break


        return results


    except requests.exceptions.Timeout:

        print(
            "⏱️ DuckDuckGo timeout"
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
            "❌ DuckDuckGo search error:",
            e
        )

        return []


# ============================================================
# SEARCH WEB
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
        "🌐 RENDER WEB SEARCH"
    )

    print(
        "=" * 70
    )


    results = search_duckduckgo(
        question
    )


    # ----------------------------------------
    # Remove duplicates
    # ----------------------------------------

    unique = []

    seen = set()


    for result in results:

        url = result.get(
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
            result
        )


    print(
        "\n📚 Search results:",
        len(unique)
    )


    return unique


# ============================================================
# REMOVE BAD HTML
# ============================================================

def clean_soup(soup):

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

        "select",

        "option"

    ]


    for tag in soup.find_all(
        remove_tags
    ):

        try:

            tag.decompose()

        except Exception:

            pass


    # ----------------------------------------
    # Remove common UI
    # ----------------------------------------

    bad_words = [

        "advertisement",
        "cookie",
        "cookie-banner",
        "popup",
        "modal",
        "newsletter",
        "social-share",
        "sidebar"

    ]


    for tag in soup.find_all(

        class_=lambda value:

        value and any(

            word in str(
                value
            ).lower()

            for word in bad_words

        )

    ):

        try:

            tag.decompose()

        except Exception:

            pass


    return soup


# ============================================================
# EXTRACT PAGE TEXT
# ============================================================

def extract_page_text(
    html,
    url=""
):

    try:

        soup = BeautifulSoup(

            html,

            "html.parser"

        )


        soup = clean_soup(
            soup
        )


        # ====================================================
        # TITLE
        # ====================================================

        title = ""


        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True
            )


        # ====================================================
        # META DESCRIPTION
        # ====================================================

        description = ""


        meta = soup.find(

            "meta",

            attrs={
                "name":
                    "description"
            }

        )


        if not meta:

            meta = soup.find(

                "meta",

                attrs={
                    "property":
                        "og:description"
                }

            )


        if meta:

            description = meta.get(
                "content",
                ""
            )


        # ====================================================
        # FIND MAIN CONTENT
        # ====================================================

        content = None


        selectors = [

            "article",

            "main",

            "[role='main']",

            ".article-content",

            ".article",

            ".post-content",

            ".entry-content",

            ".story-body",

            ".content",

            "#content"

        ]


        for selector in selectors:

            found = soup.select_one(
                selector
            )


            if not found:

                continue


            candidate_text = found.get_text(
                " ",
                strip=True
            )


            if len(candidate_text) >= MIN_TEXT_LENGTH:

                content = found

                break


        # ====================================================
        # BODY FALLBACK
        # ====================================================

        if content is None:

            content = soup.body


        if content is None:

            return ""


        # ====================================================
        # PARAGRAPHS
        # ====================================================

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


        # ====================================================
        # TEXT
        # ====================================================

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


        # ====================================================
        # SHORT PAGE FALLBACK
        # ====================================================

        if len(text) < MIN_TEXT_LENGTH:

            pieces = []


            if title:

                pieces.append(
                    title
                )


            if description:

                pieces.append(
                    description
                )


            if pieces:

                text = " ".join(
                    pieces
                )


        return text[
            :MAX_TEXT_LENGTH
        ]


    except Exception as e:

        print(
            "❌ Text extraction error:",
            e
        )

        return ""


# ============================================================
# FETCH WEBPAGE
# ============================================================

def fetch_page(
    url
):

    headers = {

        "User-Agent":
            session.headers.get(
                "User-Agent"
            ),

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.9",

        "Referer":
            "https://www.google.com/"

    }


    response = session.get(

        url,

        headers=headers,

        timeout=PAGE_TIMEOUT,

        allow_redirects=True

    )


    return response


# ============================================================
# READ PAGE
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
        "\n🌐 Reading webpage:"
    )

    print(
        url
    )


    for attempt in range(
        RETRY_COUNT + 1
    ):

        try:

            print(
                f"🔄 Attempt {attempt + 1}/"
                f"{RETRY_COUNT + 1}"
            )


            response = fetch_page(
                url
            )


            print(
                "📡 HTTP:",
                response.status_code
            )


            print(
                "🔗 Final URL:",
                response.url
            )


            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()


            print(
                "📦 Content-Type:",
                content_type
            )


            # --------------------------------------------
            # SUCCESS
            # --------------------------------------------

            if response.status_code == 200:

                if (

                    "text/html"
                    in content_type

                    or

                    "application/xhtml+xml"
                    in content_type

                ):

                    text = extract_page_text(

                        response.text,

                        response.url

                    )


                    print(
                        "📝 Extracted:",
                        len(text),
                        "characters"
                    )


                    if len(text) >= MIN_TEXT_LENGTH:

                        print(
                            "✅ WEBPAGE READ SUCCESS"
                        )

                        return text


                    print(
                        "⚠️ Page text too short"
                    )


                else:

                    print(
                        "⚠️ Content is not HTML"
                    )


            # --------------------------------------------
            # BLOCKED
            # --------------------------------------------

            elif response.status_code in (
                403,
                429,
                503
            ):

                print(
                    "⚠️ Website blocked request:",
                    response.status_code
                )


            else:

                print(
                    "⚠️ HTTP error:",
                    response.status_code
                )


        except requests.exceptions.Timeout:

            print(
                "⏱️ Page timeout"
            )


        except requests.exceptions.TooManyRedirects:

            print(
                "🔁 Too many redirects"
            )

            break


        except requests.exceptions.ConnectionError as e:

            print(
                "🌐 Connection error:",
                e
            )


        except requests.exceptions.RequestException as e:

            print(
                "❌ Request error:",
                e
            )


        except Exception as e:

            print(
                "❌ Unexpected page error:",
                e
            )


        if attempt < RETRY_COUNT:

            time.sleep(
                1
            )


    print(
        "❌ Could not read webpage"
    )


    return ""


# ============================================================
# SNIPPET FALLBACK
# ============================================================

def create_snippet_source(
    result
):

    title = str(
        result.get(
            "title",
            "Search result"
        )
    ).strip()


    url = str(
        result.get(
            "url",
            ""
        )
    ).strip()


    snippet = str(
        result.get(
            "snippet",
            ""
        )
    ).strip()


    if len(snippet) < MIN_TEXT_LENGTH:

        return None


    return {

        "title":
            title,

        "url":
            url,

        "text":
            snippet[:MAX_TEXT_LENGTH],

        "fallback":
            True

    }


# ============================================================
# FULL RESEARCH
# ============================================================

def research(question):

    print(
        "\n" + "=" * 70
    )

    print(
        "🧠 RESEARCH"
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
            "❌ No search results"
        )

        return []


    sources = []


    # ========================================================
    # TRY EVERY SEARCH RESULT
    # ========================================================

    for index, result in enumerate(

        results,

        1

    ):

        if len(sources) >= MAX_READABLE_SOURCES:

            break


        print(
            "\n" + "-" * 60
        )

        print(
            f"📄 SOURCE {index}/{len(results)}"
        )


        title = result.get(
            "title",
            "Untitled source"
        )


        url = result.get(
            "url",
            ""
        )


        print(
            "📄 Title:",
            title
        )

        print(
            "🔗 URL:",
            url
        )


        # ====================================================
        # TRY REAL WEBPAGE
        # ====================================================

        text = read_page(
            url
        )


        if text:

            sources.append({

                "title":
                    title,

                "url":
                    url,

                "text":
                    text

            })


            print(
                "✅ Real webpage source added"
            )


            continue


        # ====================================================
        # SNIPPET FALLBACK
        # ====================================================

        print(
            "⚠️ Webpage unavailable"
        )

        print(
            "🔄 Trying search snippet..."
        )


        fallback = create_snippet_source(
            result
        )


        if fallback:

            sources.append(
                fallback
            )


            print(
                "✅ Search snippet fallback added"
            )

        else:

            print(
                "❌ No usable content"
            )


    # ========================================================
    # FINAL
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "📚 TOTAL SOURCES:",
        len(sources)
    )

    print(
        "=" * 70
    )


    return sources
```
