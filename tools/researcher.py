import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs, unquote
import re


# ============================================================
# CONFIG
# ============================================================

SEARCH_URL = "https://html.duckduckgo.com/html/"

TIMEOUT = 20

MAX_RESULTS = 8

MAX_TEXT_LENGTH = 8000


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
})


# ============================================================
# REAL URL
# ============================================================

def get_real_url(url):

    if not url:
        return ""

    url = str(url).strip()

    # //example.com
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
                e
            )

    return url


# ============================================================
# VALID URL
# ============================================================

def is_valid_url(url):

    if not url:
        return False

    try:

        parsed = urlparse(url)

        return (
            parsed.scheme in (
                "http",
                "https"
            )
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# ============================================================
# SEARCH WEB
# ============================================================

def search_web(question):

    question = str(
        question or ""
    ).strip()

    print("\n" + "=" * 60)
    print("🔎 WEB SEARCH")
    print("=" * 60)

    print(
        "Query:",
        question
    )

    if not question:

        print(
            "❌ Empty search query"
        )

        return []

    search_url = (
        SEARCH_URL
        + "?q="
        + quote(question)
    )

    print(
        "🌐 URL:",
        search_url
    )

    try:

        response = session.get(
            search_url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        print(
            "📡 HTTP:",
            response.status_code
        )

        response.raise_for_status()

    except requests.RequestException as e:

        print(
            "❌ DuckDuckGo request failed:",
            e
        )

        return []

    except Exception as e:

        print(
            "❌ Search error:",
            e
        )

        return []

    html = response.text

    print(
        "📄 HTML length:",
        len(html)
    )

    if not html:

        print(
            "❌ Empty HTML response"
        )

        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []

    # ========================================================
    # METHOD 1
    # DuckDuckGo normal result blocks
    # ========================================================

    result_blocks = soup.select(
        ".result"
    )

    print(
        "🔍 .result blocks:",
        len(result_blocks)
    )

    for block in result_blocks:

        try:

            link = block.select_one(
                "a.result__a"
            )

            if not link:

                link = block.select_one(
                    "a"
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

            if not is_valid_url(
                real_url
            ):

                continue

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:

                title = (
                    "Untitled source"
                )

            results.append({

                "title": title,

                "url": real_url

            })

        except Exception as e:

            print(
                "⚠️ Result parsing error:",
                e
            )

    # ========================================================
    # METHOD 2
    # Fallback: result__a directly
    # ========================================================

    if not results:

        print(
            "🔄 Trying fallback parser..."
        )

        links = soup.select(
            "a.result__a"
        )

        print(
            "🔗 result__a links:",
            len(links)
        )

        for link in links:

            try:

                raw_url = link.get(
                    "href",
                    ""
                )

                real_url = get_real_url(
                    raw_url
                )

                if not is_valid_url(
                    real_url
                ):

                    continue

                title = link.get_text(
                    " ",
                    strip=True
                )

                if not title:

                    title = (
                        "Untitled source"
                    )

                results.append({

                    "title": title,

                    "url": real_url

                })

            except Exception:

                continue

    # ========================================================
    # METHOD 3
    # Generic external links
    # ========================================================

    if not results:

        print(
            "🔄 Trying generic link parser..."
        )

        for link in soup.find_all(
            "a",
            href=True
        ):

            try:

                raw_url = link.get(
                    "href"
                )

                real_url = get_real_url(
                    raw_url
                )

                if not is_valid_url(
                    real_url
                ):

                    continue

                domain = urlparse(
                    real_url
                ).netloc.lower()

                # Skip DuckDuckGo itself
                if (
                    "duckduckgo.com"
                    in domain
                ):

                    continue

                title = link.get_text(
                    " ",
                    strip=True
                )

                if len(title) < 3:

                    continue

                results.append({

                    "title": title,

                    "url": real_url

                })

            except Exception:

                continue

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

        if url in seen:
            continue

        seen.add(url)

        unique.append(
            item
        )

    results = unique[
        :MAX_RESULTS
    ]

    print(
        "✅ Final search results:",
        len(results)
    )

    for index, item in enumerate(
        results,
        1
    ):

        print(
            f"{index}.",
            item["title"]
        )

        print(
            "   ",
            item["url"]
        )

    print("=" * 60)

    return results


# ============================================================
# READ WEB PAGE
# ============================================================

def read_page(url):

    print("\n" + "-" * 60)

    print(
        "🌐 Reading webpage:"
    )

    print(
        url
    )

    if not is_valid_url(url):

        print(
            "❌ Invalid URL"
        )

        return ""

    try:

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        print(
            "📡 HTTP:",
            response.status_code
        )

        if response.status_code != 200:

            return ""

    except requests.RequestException as e:

        print(
            "⚠️ Page request failed:",
            e
        )

        return ""

    except Exception as e:

        print(
            "⚠️ Page error:",
            e
        )

        return ""

    try:

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unwanted tags
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
            "svg"
        ]):

            tag.decompose()

        # ====================================================
        # ARTICLE
        # ====================================================

        article = soup.find(
            "article"
        )

        if article:

            text = article.get_text(
                " ",
                strip=True
            )

        else:

            # =================================================
            # MAIN
            # =================================================

            main = soup.find(
                "main"
            )

            if main:

                text = main.get_text(
                    " ",
                    strip=True
                )

            else:

                # =============================================
                # PARAGRAPHS
                # =============================================

                paragraphs = soup.find_all(
                    "p"
                )

                text = " ".join(

                    p.get_text(
                        " ",
                        strip=True
                    )

                    for p in paragraphs

                    if p.get_text(
                        strip=True
                    )

                )

        # Normalize spaces
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        if len(text) < 50:

            print(
                "⚠️ Text too short:",
                len(text)
            )

            return ""

        print(
            "✅ Read:",
            len(text),
            "characters"
        )

        return text[
            :MAX_TEXT_LENGTH
        ]

    except Exception as e:

        print(
            "⚠️ BeautifulSoup error:",
            e
        )

        return ""


# ============================================================
# RESEARCH
# ============================================================

def research(question):

    results = search_web(
        question
    )

    if not results:

        print(
            "❌ No search results."
        )

        return []

    sources = []

    for index, result in enumerate(
        results,
        1
    ):

        title = result.get(
            "title",
            "Untitled source"
        )

        url = result.get(
            "url",
            ""
        )

        print(
            f"\n📖 SOURCE {index}/{len(results)}"
        )

        print(
            "📄",
            title
        )

        print(
            "🔗",
            url
        )

        # Skip social/video
        domain = urlparse(
            url
        ).netloc.lower()

        blocked = [
            "youtube.com",
            "youtu.be",
            "facebook.com",
            "instagram.com",
            "tiktok.com"
        ]

        if any(
            site in domain
            for site in blocked
        ):

            print(
                "⏭️ Skipped social/video"
            )

            continue

        text = read_page(
            url
        )

        if not text:

            print(
                "⚠️ No readable text"
            )

            continue

        sources.append({

            "title": title,

            "url": url,

            "text": text

        })

    print("\n" + "=" * 60)

    print(
        "✅ READABLE SOURCES:",
        len(sources)
    )

    print("=" * 60)

    return sources
