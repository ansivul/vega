# parser.py
import feedparser
import yaml
import re
from datetime import datetime, date
from time import mktime

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_all_keywords(text, keywords, soft_filter=False):
    text = text.lower()
    matches = []
    for phrase in keywords:
        words = phrase.lower().split()
        if soft_filter:
            if any(w in text for w in words):
                matches.append(phrase)
        else:
            if all(w in text for w in words):
                matches.append(phrase)
    return matches

def fetch_articles(debug=False, soft_filter=False, since_date: date = None, min_matches: int = 1, limit: int = 10):
    config = load_config()
    keywords = [k.lower() for k in config.get('keywords', [])]
    rss_feeds = config.get('rss', [])
    results = []
    log = []

    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if since_date and 'published_parsed' in entry:
                pub_date = datetime.fromtimestamp(mktime(entry.published_parsed)).date()
                if pub_date < since_date:
                    continue

            text = f"{entry.title} {entry.get('summary', '')}".lower()
            if 'tags' in entry:
                categories = " ".join(tag['term'] for tag in entry.tags)
                text += " " + categories.lower()

            matches = find_all_keywords(text, keywords, soft_filter=soft_filter)
            if len(matches) >= min_matches:
                log.append(f"✅ [MATCH: {', '.join(matches)}] {entry.title}")
                results.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'reason': f"ключевые слова: {', '.join(matches)}"
                })
            elif debug:
                log.append(f"🔍 [SKIPPED] {entry.title}")
                results.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'reason': "DEBUG: без совпадений — показано вручную"
                })

    return results[:limit], log