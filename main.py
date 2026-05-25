import os
import time
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@INFOCATweets")
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME", "Plan_INFOCA")
CHECK_INTERVAL = 300

LAST_TWEET_FILE = "last_tweet_id.txt"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    response = requests.post(url, json=payload)
    return response.ok

def get_last_tweet_id():
    if os.path.exists(LAST_TWEET_FILE):
        with open(LAST_TWEET_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_tweet_id(tweet_id):
    with open(LAST_TWEET_FILE, "w") as f:
        f.write(str(tweet_id))

def check_new_tweets():
    nitter_instances = ["https://nitter.privacydev.net", "https://nitter.poast.org", "https://nitter.cz"]
    for instance in nitter_instances:
        try:
            rss_url = f"{instance}/{TWITTER_USERNAME}/rss"
            response = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if response.ok:
                return parse_rss(response.text)
        except Exception:
            continue
    return []

def parse_rss(xml_text):
    import xml.etree.ElementTree as ET
    tweets = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            tweets.append({"id": item.findtext("guid", ""), "title": item.findtext("title", ""), "link": item.findtext("link", "")})
    except Exception:
        pass
    return tweets

def main():
    print(f"Monitorizando @{TWITTER_USERNAME}...")
    send_telegram_message(f"✅ Bot iniciado. Monitorizando <b>@{TWITTER_USERNAME}</b>")
    last_id = get_last_tweet_id()
    while True:
        try:
            tweets = check_new_tweets()
            if not tweets:
                print(f"[{datetime.now()}] Sin tweets obtenidos")
            else:
                if last_id is None:
                    last_id = tweets[0]["id"]
                    save_last_tweet_id(last_id)
                    print(f"[{datetime.now()}] Primer arranque OK")
                else:
                    new_tweets = []
                    for tweet in tweets:
                        if tweet["id"] == last_id:
                            break
                        new_tweets.append(tweet)
                    for tweet in reversed(new_tweets):
                        msg = f"🐦 <b>@{TWITTER_USERNAME}</b>\n\n{tweet['title']}\n\n🔗 {tweet['link']}"
                        if send_telegram_message(msg):
                            print(f"[{datetime.now()}] Enviado: {tweet['title'][:50]}")
                        time.sleep(1)
                    if new_tweets:
                        last_id = new_tweets[0]["id"]
                        save_last_tweet_id(last_id)
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
