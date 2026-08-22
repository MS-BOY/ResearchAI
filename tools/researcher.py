import requests

from bs4 import BeautifulSoup

from urllib.parse import (
    quote,
    urlparse,
    parse_qs,
    unquote
)


HEADERS = {

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
        "en-US,en;q=0.9"

}


def get_real_url(url):

    if not url:
        return ""

    url = str(url).strip()

    if url.startswith("//"):

        url = "https:" + url

    if "duckduckgo.com/l/?" in url:

        try:

            parsed = urlparse(url)

            params = parse_qs(
                parsed.query
            )

            if "uddg" in params:

                real_url = unquote(
                    params["uddg"][0]
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


def search_web(question):

    print(
        f"\n🔎 SEARCHING: {question}"
    )

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(question)
    )

    try:

        response = requests.get(

            search_url,

            headers=HEADERS,

            timeout=20

        )

        print(
            "🔎 Search HTTP:",
            response.status_code
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "❌ Search request failed:",
            repr(e)
        )

        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    # ======================================
    # DuckDuckGo results
    # ======================================

    for item in soup.select(
        ".result"
    ):

        link = item.select_one(
            ".result__a"
        )

        if not link:

            continue

        title = link.get_text(
            " ",
            strip=True
        )

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

        results.append({

            "title":
                title or "Untitled",

            "url":
                real_url

        })

    # ======================================
    # Fallback selector
    # ======================================

    if not results:

        print(
            "⚠️ .result selector returned 0"
        )

        for link in soup.select(
            "a.result__a"
        ):

            title = link.get_text(
                " ",
                strip=True
            )

            raw_url = link.get(
                "href",
                ""
            )

            real_url = get_real_url(
                raw_url
            )

            if real_url.startswith(
                "http"
            ):

                results.append({

                    "title":
                        title or "Untitled",

                    "url":
                        real_url

                })

    # ======================================
    # Remove duplicates
    # ======================================

    unique = []

    seen = set()

    for result in results:

        url = result["url"]

        if url in seen:

            continue

        seen.add(url)

        unique.append(
            result
        )

    print(
        f"✅ SEARCH RESULTS: {len(unique)}"
    )

    for item in unique[:5]:

        print(
            "→",
            item["title"]
        )

        print(
            " ",
            item["url"]
        )

    return unique[:8]


def read_page(url):

    if not url:

        return ""

    print(
        f"🌐 Opening: {url}"
    )

    try:

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=15,

            allow_redirects=True

        )

        print(
            "🌐 HTTP:",
            response.status_code
        )

        if response.status_code != 200:

            return ""

    except Exception as e:

        print(
            "❌ Page request failed:",
            repr(e)
        )

        return ""

    # ======================================
    # Content type
    # ======================================

    content_type = (
        response.headers
        .get(
            "Content-Type",
            ""
        )
        .lower()
    )

    if (
        "text/html" not in content_type
        and "application/xhtml" not in content_type
    ):

        print(
            "⏭️ Not HTML:",
            content_type
        )

        return ""

    try:

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

    except Exception as e:

        print(
            "❌ BeautifulSoup error:",
            repr(e)
        )

        return ""

    # ======================================
    # Remove unwanted
    # ======================================

    for tag in soup.find_all([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "svg"
    ]):

        tag.decompose()

    # ======================================
    # Article priority
    # ======================================

    article = soup.find(
        "article"
    )

    if article:

        text = article.get_text(
            " ",
            strip=True
        )

    else:

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

    text = " ".join(
        text.split()
    )

    if len(text) < 100:

        print(
            "⚠️ Very little text:",
            len(text)
        )

        return ""

    print(
        "✅ Extracted:",
        len(text),
        "characters"
    )

    return text[:8000]
