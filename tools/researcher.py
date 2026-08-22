# tools/researcher.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs, unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==========================================
# Session
# ==========================================

def create_session():

    session = requests.Session()

    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "http://",
        adapter
    )

    session.mount(
        "https://",
        adapter
    )

    session.headers.update({

        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36",

        "Accept":
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8",

        "Accept-Language":
            "en-US,en;q=0.9"

    })

    return session


session = create_session()


# ==========================================
# Get Real URL
# ==========================================

def get_real_url(url):

    if not url:
        return ""

    url = url.strip()

    # //example.com
    if url.startswith("//"):
        return "https:" + url

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

                return real_url.replace(
                    "\\/",
                    "/"
                )

        except Exception as e:

            print(
                "⚠️ URL parse error:",
                e
            )

    return url


# ==========================================
# Search Web
# ==========================================

def search_web(question):

    print(
        f"\n🔎 Searching internet for: {question}"
    )

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(question)
    )

    try:

        response = session.get(
            search_url,
            timeout=20
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "❌ Search request failed:",
            e
        )

        return []


    print(
        "✅ Search page received:",
        response.status_code
    )


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    results = []


    # ======================================
    # Primary selector
    # ======================================

    items = soup.select(
        ".result"
    )


    # ======================================
    # Fallback selectors
    # ======================================

    if not items:

        items = soup.select(
            "div.result"
        )


    print(
        f"📚 Search blocks found: {len(items)}"
    )


    for item in items:

        link = item.select_one(
            "a.result__a"
        )

        if not link:

            link = item.select_one(
                ".result__title a"
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
            ("http://", "https://")
        ):

            continue


        title = link.get_text(
            " ",
            strip=True
        )


        if not title:

            title = "Untitled source"


        # Avoid duplicate URLs

        if any(
            r["url"] == real_url
            for r in results
        ):

            continue


        results.append({

            "title":
                title,

            "url":
                real_url

        })


        if len(results) >= 10:
            break


    print(
        f"✅ Usable search results: {len(results)}"
    )


    # ======================================
    # Debug fallback
    # ======================================

    if not results:

        print(
            "⚠️ DuckDuckGo returned no parsed results."
        )

        # Try generic anchors

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link.get(
                "href",
                ""
            )

            text = link.get_text(
                " ",
                strip=True
            )


            real_url = get_real_url(
                href
            )


            if (
                real_url.startswith(
                    ("http://", "https://")
                )
                and text
            ):

                # Skip DuckDuckGo itself

                if "duckduckgo.com" in real_url:
                    continue


                if any(
                    r["url"] == real_url
                    for r in results
                ):
                    continue


                results.append({

                    "title":
                        text[:200],

                    "url":
                        real_url

                })


                if len(results) >= 5:
                    break


    return results[:10]


# ==========================================
# Read Web Page
# ==========================================

def read_page(url):

    if not url:

        return ""


    print(
        f"🌐 Opening: {url}"
    )


    try:

        response = session.get(
            url,
            timeout=20,
            allow_redirects=True
        )


        print(
            f"   HTTP: {response.status_code}"
        )


        if response.status_code != 200:

            return ""


        content_type = response.headers.get(
            "content-type",
            ""
        ).lower()


        # Only process HTML

        if (
            "text/html" not in content_type
            and
            "application/xhtml" not in content_type
        ):

            print(
                "⚠️ Not an HTML page:",
                content_type
            )

            return ""


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==================================
        # Remove useless elements
        # ==================================

        for tag in soup([
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "svg",
            "iframe"
        ]):

            tag.decompose()


        # ==================================
        # Article priority
        # ==================================

        article = soup.find(
            "article"
        )


        if article:

            text = article.get_text(
                " ",
                strip=True
            )

        else:

            # ==================================
            # Main/content priority
            # ==================================

            main = (
                soup.find("main")
                or
                soup.find(
                    "div",
                    attrs={
                        "role": "main"
                    }
                )
            )


            if main:

                text = main.get_text(
                    " ",
                    strip=True
                )

            else:

                # ==================================
                # Paragraph fallback
                # ==================================

                paragraphs = soup.find_all(
                    "p"
                )


                texts = []


                for p in paragraphs:

                    value = p.get_text(
                        " ",
                        strip=True
                    )


                    if len(value) >= 30:

                        texts.append(
                            value
                        )


                text = " ".join(
                    texts
                )


        # ==================================
        # Clean text
        # ==================================

        text = " ".join(
            text.split()
        )


        # ==================================
        # Minimum content check
        # ==================================

        if len(text) < 100:

            print(
                "⚠️ Page has too little readable text:",
                len(text)
            )

            return ""


        print(
            f"✅ Extracted {len(text)} characters"
        )


        return text[:12000]


    except requests.exceptions.Timeout:

        print(
            "⚠️ Page timeout"
        )

        return ""


    except requests.exceptions.RequestException as e:

        print(
            "⚠️ Request error:",
            e
        )

        return ""


    except Exception as e:

        print(
            "⚠️ Page read failed:",
            e
        )

        return ""


# ==========================================
# Standalone Research Test
# ==========================================

def research(question):

    results = search_web(
        question
    )


    if not results:

        print(
            "❌ No search results found."
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


        if text:

            sources.append({

                "title":
                    result["title"],

                "url":
                    result["url"],

                "text":
                    text

            })


    print(
        "\n" + "=" * 60
    )

    print(
        f"✅ Successfully readable sources: "
        f"{len(sources)}"
    )


    return sources
