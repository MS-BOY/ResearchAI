from ai_brain import understand

from tools.google import google_search
from tools.youtube import youtube_search
from tools.researcher import research


def run_agent(command):

    intent = understand(command)

    print("\n🤖 Agent decision:")
    print(intent)

    tool = intent["tool"]
    query = intent["query"]

    if tool == "research":

        research(query)
        return

    if tool == "google":

        google_search(query)
        return

    if tool == "youtube":

        youtube_search(query)
        return

    print("❌ Tool পাওয়া যায়নি।")