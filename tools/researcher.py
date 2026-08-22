```python
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
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9"
    })

    return session


# ==========================================
# Get Real URL
# ==========================================

def get_real_url(url):

    if not url:
        return ""

    url = str(url).strip()

    # DuckDuckGo protocol-relative URL
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
                "⚠️ URL parsing error:",
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

    if not question:
        return []

    session = create_session()

    search_urls = [

        (
            "https://html.duckduckgo.com/html/?q="
            + quote(question)
        ),

        (
            "https://lite.duckduckgo.com/lite/?q="
            + quote(question)
        )

    ]

    for search_url in search_urls:

        print(
            f"🌐 Search URL: {search_url}"
        )

        try:

            response = session.get(
                search_url,
                timeout=20
            )

            print(
                f"📡 Search HTTP: "
                f"{response.status_code}"
            )

            response.raise_for_status()

        except Exception as e:

            print(
                "⚠️ Search request failed:",
                e
            )

            continue


        if not response.text:

            print(
                "⚠️ Empty search response"
            )

            continue


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []


        # ==================================
        # Method 1: Normal DDG Results
        # ==================================

        result_blocks = soup.select(
            ".result"
        )


        for block in result_blocks:

            link = block.select_one(
                "a.result__a"
            )

            if not link:

                link = block.find(
                    "a",
                    href=True
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


            title = link.get_text(
                " ",
                strip=True
            )


            if not title:

                title = (
                    "Untitled source"
                )


            results.append({

                "title":
                    title,

                "url":
                    real_url

            })


        # ==================================
        # Method 2: Fallback Links
        # ==================================

        if not results:

            print(
                "⚠️ Normal DDG selector found "
                "no results. Using fallback..."
            )


            for link in soup.find_all(
                "a",
                href=True
            ):

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


                # DDG internal links skip
                if (
                    "duckduckgo.com" in
                    real_url.lower()
                ):

                    continue


                title = link.get_text(
                    " ",
                    strip=True
                )


                if len(title) < 3:
                    continue


                results.append({

                    "title":
                        title[:300],

                    "url":
                        real_url

                })


                if len(results) >= 10:
                    break


        # ==================================
        # Remove Duplicate URLs
        # ==================================

        unique_results = []

        seen_urls = set()


        for result in results:

            url = result["url"]


            if url in seen_urls:
                continue


            seen_urls.add(url)

            unique_results.append(
                result
            )


        print(
            f"📚 Parsed search results: "
            f"{len(unique_results)}"
        )


        if unique_results:

            return unique_results[:8]


    print(
        "❌ No search results found."
    )

    return []


# ==========================================
# Read Web Page
# ==========================================

def read_page(url):

    if not url:
        return ""

    print(
        f"🌐 Opening: {url}"
    )


    session = create_session()


    try:

        response = session.get(
            url,
            timeout=20,
            allow_redirects=True
        )


        print(
            f"📡 Page HTTP: "
            f"{response.status_code}"
        )


        if response.status_code != 200:

            print(
                f"⚠️ HTTP status: "
                f"{response.status_code}"
            )

            return ""


        content_type = (
            response.headers
            .get(
                "content-type",
                ""
            )
            .lower()
        )


        # Only HTML pages
        if (
            "text/html" not in
            content_type
            and
            "application/xhtml" not in
            content_type
        ):

            print(
                f"⚠️ Not an HTML page: "
                f"{content_type}"
            )

            return ""


        html = response.text


        if not html:

            return ""


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # ==================================
        # Remove Unwanted Elements
        # ==================================

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "iframe",
            "canvas",
            "button"
        ]):

            tag.decompose()


        # ==================================
        # Find Main Content
        # ==================================

        containers = []


        article = soup.find(
            "article"
        )

        if article:

            containers.append(
                article
            )


        main = soup.find(
            "main"
        )

        if main:

            containers.append(
                main
            )


        # ==================================
        # Extract Text
        # ==================================

        text = ""


        for container in containers:

            candidate = container.get_text(
                " ",
                strip=True
            )

            if len(candidate) > len(text):

                text = candidate


        # ==================================
        # Paragraph Fallback
        # ==================================

        if len(text) < 200:

            paragraphs = soup.find_all(
                "p"
            )


            paragraph_texts = []


            for p in paragraphs:

                value = p.get_text(
                    " ",
                    strip=True
                )


                if len(value) >= 30:

                    paragraph_texts.append(
                        value
                    )


            text = " ".join(
                paragraph_texts
            )


        # ==================================
        # Body Fallback
        # ==================================

        if len(text) < 200:

            body = soup.find(
                "body"
            )


            if body:

                text = body.get_text(
                    " ",
                    strip=True
                )


        # ==================================
        # Clean Text
        # ==================================

        text = " ".join(
            text.split()
        )


        if len(text) < 100:

            print(
                "⚠️ Page has insufficient "
                "readable text."
            )

            return ""


        print(
            f"✅ Readable text: "
            f"{len(text)} characters"
        )


        return text[:8000]


    except requests.exceptions.Timeout:

        print(
            "⚠️ Page request timed out."
        )

        return ""


    except requests.exceptions.RequestException as e:

        print(
            "⚠️ Page request error:",
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
# Research Test
# ==========================================

def research(question):

    results = search_web(
        question
    )


    if not results:

        print(
            "❌ No sources found."
        )

        return []


    print(
        f"\n📚 Found "
        f"{len(results)} sources:\n"
    )


    successful = []


    for i, result in enumerate(
        results,
        1
    ):

        print(
            "\n" + "=" * 60
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


        domain = urlparse(
            result["url"]
        ).netloc.lower()


        # Social/video sites
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
                "⏭️ Social/video source skipped"
            )

            continue


        print(
            "\n📖 Reading webpage..."
        )


        text = read_page(
            result["url"]
        )


        if text:

            successful.append({

                "title":
                    result["title"],

                "url":
                    result["url"],

                "text":
                    text

            })


            print(
                "✅ Source successfully read."
            )


        else:

            print(
                "⚠️ No readable text found."
            )


    print(
        "\n" + "=" * 60
    )


    print(
        f"✅ Successfully read "
        f"{len(successful)} source(s)."
    )


    return successful
```
