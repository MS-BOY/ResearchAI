from playwright.sync_api import sync_playwright


def youtube_search(keyword):

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page(
            viewport={"width": 1280, "height": 800}
        )

        page.goto(
            "https://www.youtube.com",
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(5000)

        search_box = page.locator(
            "input[name='search_query']"
        )

        search_box.wait_for(
            state="visible",
            timeout=15000
        )

        search_box.fill(keyword)
        search_box.press("Enter")

        page.wait_for_timeout(7000)

        print(f"YouTube search completed: {keyword}")

        input("Enter চাপলে browser বন্ধ হবে...")

        browser.close()