import json

from core.crawler import DataScout


def run_news_recon():
    """Step 1 新聞偵察獨立 runner。"""
    news_agent = DataScout()
    intelligence = news_agent.fetch_all_news()
    source_status = getattr(news_agent, "last_source_status", {})
    source_failures = [
        f"情報來源:{source_key}"
        for source_key, status in source_status.items()
        if not status.get("success")
    ]

    return {
        "intelligence": intelligence,
        "source_status": source_status,
        "source_failures": source_failures
    }


if __name__ == "__main__":
    print(json.dumps(run_news_recon(), ensure_ascii=False))
