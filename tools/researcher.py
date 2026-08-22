import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs, unquote


def get_real_url(url):

    # DuckDuckGo relative URL
    if url.startswith("//"):
        url = "https:" + url

    # DuckDuckGo redirect URL থেকে আসল URL বের করা
    if "duckduckgo.com/l/?" in url:

        parsed = urlparse(url)

        params = parse_qs(parsed.query)

        if "uddg" in params:

            real_url = params["uddg"][0]

            real_url = unquote(real_url)

            # ভুল escaped slash থাকলে ঠিক করা
            real_url = real_url.replace("\\/", "/")

            return real_url

    return url


def search_web(question):

    print(f"\n🔎 Searching internet for: {question}")

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(question)
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

    except Exception as e:

        print("❌ Search failed:", e)

        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    for result in soup.select(".result"):

        title = result.select_one(
            ".result__title"
        )

        link = result.select_one(
            ".result__a"
        )

        if title and link:

            raw_url = link.get("href")

            real_url = get_real_url(
                raw_url
            )

            if real_url.startswith("http"):

                results.append({
                    "title": title.get_text(
                        " ",
                        strip=True
                    ),
                    "url": real_url
                })

    return results[:5]


def read_page(url):

    try:

        print(
            f"🌐 Opening: {url}"
        )

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:

            print(
                "⚠️ HTTP:",
                response.status_code
            )

            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Unwanted elements remove
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):

            tag.decompose()

        # Article থাকলে সেটাকে priority
        article = soup.find("article")

        if article:

            text = article.get_text(
                " ",
                strip=True
            )

        else:

            # paragraph থেকে text নেওয়া
            paragraphs = soup.find_all("p")

            text = " ".join(
                p.get_text(
                    " ",
                    strip=True
                )
                for p in paragraphs
            )

        text = " ".join(
            text.split()
        )

        return text[:8000]

    except Exception as e:

        print(
            "⚠️ Page read failed:",
            e
        )

        return ""


def research(question):

    results = search_web(question)

    if not results:

        print("❌ No sources found.")

        return

    print(
        f"\n📚 Found {len(results)} sources:\n"
    )

    successful = 0

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

        # প্রথম version-এ এগুলো বাদ
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
                "⏭️ Video/social source skipped"
            )

            continue

        print(
            "\n📖 Reading webpage..."
        )

        text = read_page(
            result["url"]
        )

        if text:

            successful += 1

            print(
                "\n📝 Extracted text:\n"
            )

            print(
                text[:3000]
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
        f"{successful} source(s)."
    )