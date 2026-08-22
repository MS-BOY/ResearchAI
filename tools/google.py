import requests


def google_search(query):

    print(f"🔎 Searching for: {query}")

    # আপাতত demo search
    url = "https://www.google.com/search"

    params = {
        "q": query
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        print("✅ Search request successful!")
        print("Search URL:", response.url)
    else:
        print("❌ Search failed:", response.status_code)