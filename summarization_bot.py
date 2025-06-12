import requests
from bs4 import BeautifulSoup
import newsapi
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize NewsAPI
newsapi_client = newsapi.NewsApiClient(api_key=NEWSAPI_KEY)

def fetch_content(topic):
    topic_queries = {
        "airline ticket deals": "airline ticket deals OR flight sales OR cheap flights",
        "car rental deals": "car rental deals OR budget car rentals OR rental car promotions",
        "bbq cooking": "bbq recipes OR barbecue techniques"
    }
    if topic in topic_queries:
        # Fetch articles via NewsAPI
        articles = newsapi_client.get_everything(q=topic_queries[topic], language="en", page_size=5)
        return [article["content"] or article["description"] for article in articles["articles"] if article["content"] or article["description"]]
    else:
        # Fallback to scraping (example for permissive site)
        url = "https://example-deal-site.com"  # Replace with real URL
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        return [" ".join([p.text for p in soup.find_all("p")])]

def summarize_text(text, api_key):
    # Use Grok 3 API for summarization
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "grok-3",
            "messages": [{"role": "user", "content": f"Summarize this in 100 words with a focus on deals or key tips: {text[:4000]}"}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

def store_summary(topic, summary):
    # Store in Supabase
    supabase.table("summaries").insert({"topic": topic, "summary": summary, "created_at": "now()"}).execute()

def main():
    topics = ["airline ticket deals", "car rental deals", "bbq cooking"]
    for topic in topics:
        contents = fetch_content(topic)
        for content in contents:
            if content:
                summary = summarize_text(content, GROK_API_KEY)
                store_summary(topic, summary)
                print(f"Summary for {topic}: {summary}")

if __name__ == "__main__":
    main()