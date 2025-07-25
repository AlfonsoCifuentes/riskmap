"""Social media ingestion (Twitter/X Academic API & Reddit RSS).
Stores geolocated social signals in `events` table as `social_signal`.
Requires TWITTER_BEARER and optional REDDIT_CLIENT_ID/SECRET for full API; fallback RSS for subreddits.
"""

import os
import requests
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from utils.config import config, logger
from utils.geo import extract_event_location
from data_ingestion.real_sources import store_events

TW_BEARER=os.getenv("TWITTER_BEARER")

SEARCH_QUERY="(war OR conflict OR explosion OR protest OR disaster) lang:en -is:retweet"
TW_URL="https://api.twitter.com/2/tweets/search/recent?tweet.fields=created_at,text,lang&max_results=100&query="+requests.utils.quote(SEARCH_QUERY)

HEADERS={"Authorization":f"Bearer {TW_BEARER}"} if TW_BEARER else {}

SUBREDDITS=["worldnews","geopolitics","Disaster","UkraineWarVideoReport"]


def fetch_twitter() -> List[Dict]:
    if not TW_BEARER:
        return []
    try:
        r=requests.get(TW_URL,headers=HEADERS,timeout=20)
        r.raise_for_status()
        data=r.json().get("data",[])
        events=[]
        for t in data:
            loc=extract_event_location(t.get("text",""))
            if not loc:
                continue
            events.append({
                "title": t["text"][:80],
                "content": t["text"],
                "url": f"https://twitter.com/i/web/status/{t['id']}",
                "published_at": t["created_at"],
                "source": "Twitter",
                "location": loc,
                "type": "social_signal"
            })
        return events
    except Exception as exc:
        logger.error(f"[Twitter] error: {exc}")
        return []


def fetch_reddit() -> List[Dict]:
    events=[]
    for sr in SUBREDDITS:
        url=f"https://www.reddit.com/r/{sr}/new.json?limit=50"
        try:
            r=requests.get(url,headers={"User-agent":"riskmap"},timeout=20)
            r.raise_for_status()
            data=r.json()["data"]["children"]
            for post in data:
                p=post["data"]
                loc=extract_event_location(p.get("title",""))
                if not loc:
                    continue
                events.append({
                    "title": p["title"][:80],
                    "content": p.get("selftext",""),
                    "url": f"https://reddit.com{p['permalink']}",
                    "published_at": datetime.utcfromtimestamp(p['created_utc']).isoformat()+"Z",
                    "source": "Reddit",
                    "location": loc,
                    "type": "social_signal"
                })
        except Exception as exc:
            logger.warning(f"[Reddit] {sr} error: {exc}")
    return events


def ingest_social():
    events=fetch_twitter()+fetch_reddit()
    if events:
        store_events(events,table="events")
        logger.info(f"[Social] Stored {len(events)} social signals")

if __name__=="__main__":
    ingest_social()
