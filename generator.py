"""
WorldPulse Static Site Generator
Crawls free sources worldwide → builds thousands of SEO HTML pages
Sources: Google Trends, Reddit, YouTube, Wikipedia, BBC, Reuters,
         HackerNews, GitHub Trending, Al Jazeera, DW, France24,
         NPR, The Guardian, AP News, and many more RSS feeds.
"""

import os, re, json, time, html, hashlib, logging, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, quote
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worldpulse")

# ── CONFIG ────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = Path("output")
TOPICS_JSON = Path("topics_cache.json")
MAX_WORKERS = 8
REQUEST_TIMEOUT = 12
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WorldPulseBot/1.0; +https://worldpulse.site/bot)"
}

# ── ALL FREE SOURCES ──────────────────────────────────────────────────────────
RSS_SOURCES = {
    # Google Trends
    "google_trends_global":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=",
    "google_trends_us":       "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
    "google_trends_uk":       "https://trends.google.com/trends/trendingsearches/daily/rss?geo=GB",
    "google_trends_india":    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
    "google_trends_brazil":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=BR",
    "google_trends_japan":    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=JP",
    "google_trends_germany":  "https://trends.google.com/trends/trendingsearches/daily/rss?geo=DE",
    "google_trends_france":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR",
    "google_trends_nigeria":  "https://trends.google.com/trends/trendingsearches/daily/rss?geo=NG",
    "google_trends_mexico":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=MX",
    "google_trends_korea":    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
    "google_trends_indonesia":"https://trends.google.com/trends/trendingsearches/daily/rss?geo=ID",
    "google_trends_turkey":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=TR",
    "google_trends_argentina":"https://trends.google.com/trends/trendingsearches/daily/rss?geo=AR",
    "google_trends_egypt":    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=EG",
    "google_trends_canada":   "https://trends.google.com/trends/trendingsearches/daily/rss?geo=CA",
    "google_trends_australia":"https://trends.google.com/trends/trendingsearches/daily/rss?geo=AU",
    "google_trends_sa":       "https://trends.google.com/trends/trendingsearches/daily/rss?geo=SA",

    # Major International News
    "bbc_world":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc_tech":         "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "bbc_science":      "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "bbc_health":       "http://feeds.bbci.co.uk/news/health/rss.xml",
    "bbc_business":     "http://feeds.bbci.co.uk/news/business/rss.xml",
    "reuters_world":    "https://feeds.reuters.com/reuters/worldNews",
    "reuters_tech":     "https://feeds.reuters.com/reuters/technologyNews",
    "reuters_business": "https://feeds.reuters.com/reuters/businessNews",
    "reuters_science":  "https://feeds.reuters.com/reuters/scienceNews",
    "ap_news":          "https://feeds.apnews.com/rss/apf-topnews",
    "ap_science":       "https://feeds.apnews.com/rss/apf-Science",
    "ap_tech":          "https://feeds.apnews.com/rss/apf-Technology",
    "aljazeera":        "https://www.aljazeera.com/xml/rss/all.xml",
    "dw_world":         "https://rss.dw.com/rdf/rss-en-world",
    "dw_science":       "https://rss.dw.com/rdf/rss-en-science",
    "france24":         "https://www.france24.com/en/rss",
    "guardian_world":   "https://www.theguardian.com/world/rss",
    "guardian_tech":    "https://www.theguardian.com/technology/rss",
    "guardian_science": "https://www.theguardian.com/science/rss",
    "guardian_env":     "https://www.theguardian.com/environment/rss",
    "npr_news":         "https://feeds.npr.org/1001/rss.xml",
    "npr_science":      "https://feeds.npr.org/1007/rss.xml",
    "npr_health":       "https://feeds.npr.org/1128/rss.xml",
    "euronews":         "https://www.euronews.com/rss?format=mrss&level=theme&name=news",
    "nytimes_world":    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "nytimes_tech":     "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "nytimes_science":  "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    "nytimes_health":   "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    "washpost_world":   "http://feeds.washingtonpost.com/rss/world",
    "washpost_tech":    "http://feeds.washingtonpost.com/rss/business/technology",
    "economist":        "https://www.economist.com/the-world-this-week/rss.xml",

    # Tech & Science
    "hackernews":       "https://hnrss.org/frontpage",
    "hackernews_ask":   "https://hnrss.org/ask",
    "techcrunch":       "https://techcrunch.com/feed/",
    "wired":            "https://www.wired.com/feed/rss",
    "arstechnica":      "https://feeds.arstechnica.com/arstechnica/index",
    "verge":            "https://www.theverge.com/rss/index.xml",
    "mit_tech":         "https://www.technologyreview.com/feed/",
    "nature":           "https://www.nature.com/nature.rss",
    "science_daily":    "https://www.sciencedaily.com/rss/all.xml",
    "phys_org":         "https://phys.org/rss-feed/",
    "space_com":        "https://www.space.com/feeds/all",
    "nasa":             "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "new_scientist":    "https://www.newscientist.com/feed/home/",
    "github_trending":  "https://github.com/trending.atom",

    # Reddit (JSON as RSS equivalent)
    # Handled separately below via Reddit JSON API

    # YouTube (handled separately)

    # Health & Environment
    "who":              "https://www.who.int/rss-feeds/news-releases.xml",
    "cdc":              "https://tools.cdc.gov/api/v2/resources/media/132608.rss",
    "climate_home":     "https://www.climatechangenews.com/feed/",
    "carbon_brief":     "https://www.carbonbrief.org/feed",

    # Business & Economy
    "ft_world":         "https://www.ft.com/world?format=rss",
    "bloomberg_tech":   "https://feeds.bloomberg.com/technology/news.rss",
    "cnbc_world":       "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "cnbc_tech":        "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    "marketwatch":      "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",

    # Culture & Society
    "smithsonian":      "https://www.smithsonianmag.com/rss/latest_articles/",
    "natgeo":           "https://www.nationalgeographic.com/latest-stories/_jcr_content/content/feedbackgrid/grid-cell-layout/content/auto/contentItems.rss",
    "wikipedia_itn":    "https://en.wikipedia.org/w/index.php?title=Template:In_the_news&action=rss",

    # Sports
    "espn":             "https://www.espn.com/espn/rss/news",
    "bbc_sport":        "http://feeds.bbci.co.uk/sport/rss.xml",
}

REDDIT_SUBREDDITS = [
    "worldnews", "science", "technology", "space", "environment",
    "todayilearned", "explainlikeimfive", "futurology", "economics",
    "health", "programming", "artificial", "singularity", "climate",
    "sports", "entertainment", "philosophy", "history", "askscience",
]

WIKIPEDIA_PORTALS = [
    "https://en.wikipedia.org/w/index.php?title=Portal:Current_events&action=raw",
]

# ── CRAWLERS ─────────────────────────────────────────────────────────────────

def fetch(url, timeout=REQUEST_TIMEOUT):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        log.warning(f"Fetch failed {url}: {e}")
        return None

def parse_rss(content, source_name):
    """Parse RSS/Atom XML, return list of topic dicts."""
    topics = []
    try:
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # RSS 2.0
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            link  = (item.findtext("link") or "").strip()
            date  = (item.findtext("pubDate") or "").strip()
            if title and len(title) > 5:
                topics.append({
                    "title": clean_text(title),
                    "description": clean_text(strip_html(desc))[:400],
                    "url": link,
                    "source": source_name,
                    "date": date,
                    "category": guess_category(title + " " + desc),
                })

        # Atom
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href","") if link_el is not None else ""
            if title and len(title) > 5:
                topics.append({
                    "title": clean_text(title),
                    "description": clean_text(strip_html(summary))[:400],
                    "url": link,
                    "source": source_name,
                    "date": "",
                    "category": guess_category(title + " " + summary),
                })
    except ET.ParseError as e:
        log.warning(f"XML parse error ({source_name}): {e}")
    return topics

def crawl_rss_sources():
    topics = []
    def fetch_one(name, url):
        r = fetch(url)
        if r:
            return parse_rss(r.content, name)
        return []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_one, name, url): name for name, url in RSS_SOURCES.items()}
        for fut in as_completed(futures):
            result = fut.result()
            topics.extend(result)
            log.info(f"  ✓ {futures[fut]}: {len(result)} topics")
    return topics

def crawl_reddit():
    topics = []
    for sub in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
        r = fetch(url)
        if not r:
            continue
        try:
            data = r.json()
            for post in data["data"]["children"]:
                p = post["data"]
                if p.get("stickied") or p.get("is_self") is False and not p.get("url"):
                    continue
                title = (p.get("title") or "").strip()
                desc  = (p.get("selftext") or "")[:400].strip()
                if title and len(title) > 8:
                    topics.append({
                        "title": clean_text(title),
                        "description": clean_text(desc),
                        "url": "https://reddit.com" + p.get("permalink",""),
                        "source": f"reddit_r_{sub}",
                        "date": datetime.fromtimestamp(p.get("created_utc",0)).strftime("%Y-%m-%d"),
                        "category": guess_category(title + " " + sub),
                        "score": p.get("score", 0),
                        "comments": p.get("num_comments", 0),
                    })
        except Exception as e:
            log.warning(f"Reddit {sub}: {e}")
        time.sleep(0.5)
    return topics

def crawl_youtube_trending():
    """YouTube trending RSS (no key needed)."""
    topics = []
    # YouTube doesn't expose trending RSS directly but channel feeds work
    youtube_channels = [
        # Science / Education
        "UCVBMKcPDLtbhPrHAd5x62Jg",  # Veritasium
        "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed
        "UCWX3yGbODI3HLCWlCfTkylQ",  # Wendover Productions
        "UCHnyfMqiRRG1u-2MsSQLbXA",  # Veritasium
        "UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt
        # News
        "UCupvZG-5ko_eiXAupbDfxWw",  # CNN
        "UCeY0bbntWzzVIaj2z3QigXg",  # NBC News
        "UCNye-wNBqNL5ZzHSJj3l8Bg",  # Al Jazeera
        "UCF9IOB2TExg3QIBupFtBDxg",  # DW News
    ]
    for channel_id in youtube_channels:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = fetch(url)
        if not r:
            continue
        parsed = parse_rss(r.content, "youtube")
        topics.extend(parsed)
        time.sleep(0.3)
    return topics

def crawl_wikipedia():
    """Wikipedia current events portal."""
    topics = []
    r = fetch("https://en.wikipedia.org/wiki/Portal:Current_events?action=raw")
    if not r:
        return topics
    # Extract bolded links which are the actual events
    matches = re.findall(r"\*+\s*(.+)", r.text)
    for m in matches[:80]:
        clean = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", m)
        clean = re.sub(r"\{\{[^}]+\}\}", "", clean)
        clean = re.sub(r"'{2,}", "", clean).strip()
        if len(clean) > 15:
            topics.append({
                "title": clean_text(clean[:120]),
                "description": "",
                "url": "https://en.wikipedia.org/wiki/Portal:Current_events",
                "source": "wikipedia_current_events",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "category": guess_category(clean),
            })
    return topics

# ── HELPERS ──────────────────────────────────────────────────────────────────

def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "")

def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

CATEGORY_KEYWORDS = {
    "technology":   ["tech","ai","software","app","robot","cyber","hack","digital","computer","code","internet","5g","chip","gpu","semiconductor","machine learning","neural","quantum"],
    "science":      ["science","research","study","discover","physics","chemistry","biology","genome","dna","cell","brain","neuron","climate","nasa","space","planet","star","universe"],
    "health":       ["health","covid","virus","vaccine","medicine","hospital","cancer","heart","mental","disease","drug","therapy","doctor","patient","who","epidemic","pandemic"],
    "environment":  ["environment","climate","carbon","emission","forest","ocean","species","extinction","pollution","green","solar","wind","renewable","sustainability"],
    "economy":      ["economy","market","stock","trade","inflation","gdp","bank","finance","invest","crypto","bitcoin","dollar","recession","job","employment","wage"],
    "culture":      ["culture","art","music","film","movie","book","fashion","sport","celebrity","award","festival","entertainment","game","esport"],
    "space":        ["space","nasa","rocket","mars","moon","satellite","asteroid","telescope","orbit","iss","spacex","launch","galaxy"],
    "sports":       ["sport","football","soccer","basketball","tennis","cricket","olympic","world cup","championship","league","match","player","team","tournament"],
}

def guess_category(text):
    text = text.lower()
    scores = defaultdict(int)
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[cat] += 1
    if scores:
        return max(scores, key=scores.get)
    return "world"

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]

def dedup_topics(topics):
    """Remove near-duplicate titles using simple hashing of normalized title."""
    seen = {}
    result = []
    for t in topics:
        key = re.sub(r"[^a-z0-9]", "", t["title"].lower())[:40]
        if key not in seen:
            seen[key] = True
            result.append(t)
    return result

def group_by_topic(topics):
    """Group articles under canonical topic slugs."""
    groups = defaultdict(list)
    for t in topics:
        slug = slugify(t["title"])
        if slug:
            groups[slug].append(t)
    return groups

# ── HTML TEMPLATES ────────────────────────────────────────────────────────────

BASE_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Georgia',serif;background:#F8F7F3;color:#111;line-height:1.7}
a{color:#C0392B;text-decoration:none}a:hover{text-decoration:underline}
.topbar{background:#111;color:#F8F7F3;padding:8px 24px;font-family:monospace;font-size:11px;display:flex;justify-content:space-between;align-items:center}
.topbar a{color:#E74C3C}
header{border-bottom:3px solid #111;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;background:#F8F7F3}
.logo{font-size:28px;font-weight:900;letter-spacing:-1px}
.logo span{color:#E74C3C}
nav{padding:0 40px;border-bottom:1px solid #DDD;display:flex;gap:0;overflow-x:auto;background:#F8F7F3}
nav a{font-family:monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;padding:10px 14px;border-bottom:2px solid transparent;color:#666;white-space:nowrap}
nav a:hover,nav a.active{color:#111;border-bottom-color:#E74C3C;text-decoration:none}
.container{max-width:1100px;margin:0 auto;padding:32px 24px}
.breadcrumb{font-family:monospace;font-size:11px;color:#999;margin-bottom:20px}
.breadcrumb a{color:#999}
h1{font-size:clamp(24px,4vw,40px);font-weight:900;line-height:1.1;margin-bottom:16px;letter-spacing:-0.5px}
h2{font-size:22px;font-weight:700;margin:28px 0 12px;border-left:3px solid #E74C3C;padding-left:12px}
.meta{font-family:monospace;font-size:10px;color:#999;margin-bottom:28px;padding-bottom:16px;border-bottom:2px solid #111;display:flex;gap:20px;flex-wrap:wrap}
.tag{display:inline-block;background:#111;color:#F8F7F3;font-family:monospace;font-size:9px;padding:3px 8px;border-radius:2px;letter-spacing:1px;text-transform:uppercase;margin:2px}
.tag:hover{background:#E74C3C;color:#fff;text-decoration:none}
.card{background:#fff;border:1px solid #E0E0D8;padding:20px;margin-bottom:16px;border-radius:2px;transition:border-color .2s,box-shadow .2s}
.card:hover{border-color:#E74C3C;box-shadow:0 4px 16px rgba(0,0,0,.07)}
.card h3{font-size:17px;margin-bottom:8px;line-height:1.3}
.card p{font-size:14px;color:#555;line-height:1.6;margin-bottom:10px}
.card .source{font-family:monospace;font-size:10px;color:#999}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-bottom:32px}
.sidebar-layout{display:grid;grid-template-columns:1fr 280px;gap:40px}
.sidebar{}
.sidebar-box{background:#fff;border:1px solid #E0E0D8;padding:20px;margin-bottom:24px;border-radius:2px}
.sidebar-box h3{font-family:monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#E74C3C;margin-bottom:14px}
.rank-list{list-style:none}
.rank-list li{padding:8px 0;border-bottom:1px solid #F0F0E8;display:flex;gap:12px;align-items:flex-start}
.rank-num{font-size:20px;font-weight:900;color:#DDD;min-width:24px;font-family:Georgia}
.rank-title{font-size:13px;font-weight:600;line-height:1.3}
.rank-title a{color:#111}
footer{background:#111;color:#999;padding:32px 40px;font-family:monospace;font-size:11px;margin-top:60px}
footer a{color:#E74C3C}
.hero-section{background:#111;color:#F8F7F3;padding:36px 40px;margin-bottom:32px}
.hero-section .eyebrow{font-family:monospace;font-size:10px;letter-spacing:2px;color:#E74C3C;text-transform:uppercase;margin-bottom:10px}
.hero-section h1{color:#F8F7F3;font-size:clamp(28px,5vw,48px)}
.hero-section p{color:#AAA;font-size:16px;max-width:600px;margin-top:12px}
.tabs{display:flex;gap:0;border-bottom:1px solid #DDD;margin-bottom:24px}
.tab{font-family:monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;padding:10px 16px;border-bottom:2px solid transparent;color:#666;cursor:pointer}
.tab.active{color:#111;border-bottom-color:#E74C3C}
.forum-post{border:1px solid #E0E0D8;padding:18px;margin-bottom:14px;border-radius:2px;background:#fff}
.forum-post .fp-title{font-size:16px;font-weight:700;margin-bottom:6px}
.forum-post .fp-meta{font-family:monospace;font-size:10px;color:#999;margin-bottom:8px}
.forum-post .fp-body{font-size:14px;color:#555;line-height:1.6}
.timeline{position:relative;padding-left:28px}
.timeline::before{content:'';position:absolute;left:6px;top:0;bottom:0;width:2px;background:#E0E0D8}
.tl-event{position:relative;margin-bottom:24px}
.tl-dot{position:absolute;left:-25px;top:4px;width:10px;height:10px;border-radius:50%;background:#E74C3C;border:2px solid #fff;box-shadow:0 0 0 2px #E74C3C}
.tl-date{font-family:monospace;font-size:10px;color:#E74C3C;margin-bottom:4px;letter-spacing:1px}
.tl-title{font-weight:700;margin-bottom:4px}
.tl-desc{font-size:13px;color:#666;line-height:1.5}
.subtopic-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.subtopic-card{background:#fff;border:1px solid #E0E0D8;padding:16px;border-radius:2px}
.subtopic-card h4{font-size:14px;font-weight:700;margin-bottom:6px}
.subtopic-card p{font-size:12px;color:#666}
.stat-bar{background:#F0F0E8;height:4px;border-radius:2px;margin-top:6px}
.stat-fill{background:#E74C3C;height:100%;border-radius:2px}
@media(max-width:768px){.sidebar-layout{grid-template-columns:1fr}header{padding:14px 16px}.container{padding:20px 16px}.hero-section{padding:24px 16px}nav{padding:0 16px}}
</style>
"""

COMMON_NAV = """
<div class="topbar">
  <span>🌍 WorldPulse — Every Trend, Every Story</span>
  <span><a href="/sitemap.xml">Sitemap</a></span>
</div>
<header>
  <div class="logo"><a href="/" style="color:inherit;text-decoration:none">World<span>Pulse</span></a></div>
  <div style="font-family:monospace;font-size:11px;color:#999">{date} · Auto-updated daily</div>
</header>
<nav>
  <a href="/" class="active">Home</a>
  <a href="/category/technology/">Technology</a>
  <a href="/category/science/">Science</a>
  <a href="/category/health/">Health</a>
  <a href="/category/environment/">Environment</a>
  <a href="/category/economy/">Economy</a>
  <a href="/category/space/">Space</a>
  <a href="/category/sports/">Sports</a>
  <a href="/category/culture/">Culture</a>
  <a href="/category/world/">World</a>
</nav>
"""

COMMON_FOOTER = """
<footer>
  <div style="max-width:1100px;margin:0 auto;display:flex;justify-content:space-between;flex-wrap:wrap;gap:20px">
    <div>
      <div style="color:#F8F7F3;font-size:16px;font-weight:700;margin-bottom:8px">WorldPulse</div>
      <div>Auto-generated daily from trusted global sources.</div>
      <div>No ads. No bias. Just trends.</div>
    </div>
    <div>
      <div style="color:#F8F7F3;margin-bottom:8px">Sources</div>
      <div>BBC · Reuters · AP · Al Jazeera · The Guardian</div>
      <div>DW · France24 · NPR · HackerNews · Reddit</div>
      <div>NASA · WHO · Wikipedia · YouTube · Google Trends</div>
    </div>
    <div>
      <div style="color:#F8F7F3;margin-bottom:8px">Site</div>
      <a href="/sitemap.xml">Sitemap</a><br>
      <a href="/about/">About</a>
    </div>
  </div>
  <div style="margin-top:24px;padding-top:16px;border-top:1px solid #333;text-align:center">
    © {year} WorldPulse · Content sourced from public RSS feeds and APIs · Updated {date}
  </div>
</footer>
"""

def html_page(title, description, canonical, content, extra_head=""):
    date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    year = datetime.now(timezone.utc).year
    nav  = COMMON_NAV.format(date=date)
    foot = COMMON_FOOTER.format(date=date, year=year)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — WorldPulse</title>
<meta name="description" content="{html.escape(description[:160])}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://worldpulse.site{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description[:160])}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://worldpulse.site{canonical}">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{html.escape(title)}","dateModified":"{datetime.now(timezone.utc).isoformat()}","publisher":{{"@type":"Organization","name":"WorldPulse"}}}}
</script>
{extra_head}
{BASE_CSS}
</head>
<body>
{nav}
{content}
{foot}
</body>
</html>"""

# ── PAGE BUILDERS ─────────────────────────────────────────────────────────────

def build_overview_page(slug, articles):
    """Main topic page: overview + all articles listed."""
    topic_name = slug.replace("-", " ").title()
    cats = list({a["category"] for a in articles})
    sources = list({a["source"].replace("_"," ").title() for a in articles})[:8]
    desc = articles[0]["description"] if articles and articles[0]["description"] else f"Everything trending about {topic_name} — news, analysis, timelines, and discussions."
    
    articles_html = ""
    for a in articles[:30]:
        src_domain = urlparse(a["url"]).netloc if a["url"] else a["source"]
        articles_html += f"""
        <div class="card">
          <h3><a href="{html.escape(a['url'])}" target="_blank" rel="noopener">{html.escape(a['title'])}</a></h3>
          <p>{html.escape(a['description'][:200]) if a['description'] else ''}</p>
          <div class="source">Source: {html.escape(src_domain or a['source'])} · {html.escape(a['date'] or 'Recent')}</div>
        </div>"""

    tags_html = "".join(f'<a class="tag" href="/topic/{slug}/subtopics/">{t}</a>' for t in cats[:6])

    content = f"""
    <div class="hero-section">
      <div class="eyebrow">Trending Topic</div>
      <h1>{html.escape(topic_name)}</h1>
      <p>{html.escape(desc[:300])}</p>
    </div>
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/category/{articles[0]['category']}/">{articles[0]['category'].title()}</a> › {html.escape(topic_name)}</div>
      <div class="tabs">
        <span class="tab active">Overview</span>
        <a href="news/" class="tab">News ({len(articles)})</a>
        <a href="timeline/" class="tab">Timeline</a>
        <a href="subtopics/" class="tab">Subtopics</a>
        <a href="forum/" class="tab">Discussion</a>
      </div>
      <div class="sidebar-layout">
        <div>
          <h2>What's Happening</h2>
          {articles_html}
        </div>
        <aside class="sidebar">
          <div class="sidebar-box">
            <h3>Categories</h3>
            {tags_html}
          </div>
          <div class="sidebar-box">
            <h3>Sources Covering This</h3>
            {''.join(f'<div style="font-size:13px;padding:4px 0;border-bottom:1px solid #F0F0E8">{html.escape(s)}</div>' for s in sources)}
          </div>
          <div class="sidebar-box">
            <h3>Pages on This Topic</h3>
            <div style="font-size:13px;line-height:2">
              <a href="news/">📰 News Articles ({len(articles)})</a><br>
              <a href="timeline/">📅 Timeline of Events</a><br>
              <a href="subtopics/">🔗 Related Subtopics</a><br>
              <a href="forum/">💬 Discussion Threads</a>
            </div>
          </div>
        </aside>
      </div>
    </div>"""

    return html_page(
        title=f"{topic_name} — Trending News & Analysis",
        description=desc[:160],
        canonical=f"/topic/{slug}/",
        content=content
    )

def build_news_page(slug, articles):
    topic_name = slug.replace("-", " ").title()
    items = ""
    for i, a in enumerate(articles[:50]):
        src = urlparse(a["url"]).netloc if a["url"] else a["source"]
        items += f"""
        <div class="card">
          <div style="font-family:monospace;font-size:9px;color:#E74C3C;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">#{i+1} · {html.escape(a['date'] or 'Recent')}</div>
          <h3><a href="{html.escape(a['url'])}" target="_blank" rel="noopener">{html.escape(a['title'])}</a></h3>
          <p>{html.escape(a['description'][:250]) if a['description'] else ''}</p>
          <div class="source">📡 {html.escape(src)}</div>
        </div>"""

    content = f"""
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/topic/{slug}/">{html.escape(topic_name)}</a> › News</div>
      <h1>News: {html.escape(topic_name)}</h1>
      <div class="meta"><span>{len(articles)} articles</span><span>Updated daily</span></div>
      <div class="tabs">
        <a href="../" class="tab">Overview</a>
        <span class="tab active">News ({len(articles)})</span>
        <a href="../timeline/" class="tab">Timeline</a>
        <a href="../subtopics/" class="tab">Subtopics</a>
        <a href="../forum/" class="tab">Discussion</a>
      </div>
      {items}
    </div>"""
    return html_page(
        title=f"{topic_name} News — Latest Articles",
        description=f"Latest news articles about {topic_name}. {len(articles)} stories from trusted global sources.",
        canonical=f"/topic/{slug}/news/",
        content=content
    )

def build_timeline_page(slug, articles):
    topic_name = slug.replace("-", " ").title()
    # Sort by date desc for timeline
    dated = sorted([a for a in articles if a.get("date")], key=lambda x: x["date"], reverse=True)
    undated = [a for a in articles if not a.get("date")]
    ordered = dated + undated

    events_html = ""
    for a in ordered[:40]:
        events_html += f"""
        <div class="tl-event">
          <div class="tl-dot"></div>
          <div class="tl-date">{html.escape(a['date'] or 'Recent')}</div>
          <div class="tl-title"><a href="{html.escape(a['url'])}" target="_blank" rel="noopener">{html.escape(a['title'])}</a></div>
          <div class="tl-desc">{html.escape(a['description'][:180]) if a['description'] else ''}</div>
        </div>"""

    content = f"""
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/topic/{slug}/">{html.escape(topic_name)}</a> › Timeline</div>
      <h1>Timeline: {html.escape(topic_name)}</h1>
      <div class="meta"><span>{len(ordered)} events</span><span>Chronological order</span></div>
      <div class="tabs">
        <a href="../" class="tab">Overview</a>
        <a href="../news/" class="tab">News</a>
        <span class="tab active">Timeline</span>
        <a href="../subtopics/" class="tab">Subtopics</a>
        <a href="../forum/" class="tab">Discussion</a>
      </div>
      <div class="timeline">{events_html}</div>
    </div>"""
    return html_page(
        title=f"{topic_name} Timeline — Events in Order",
        description=f"Complete timeline of {topic_name} — {len(ordered)} events from global sources in chronological order.",
        canonical=f"/topic/{slug}/timeline/",
        content=content
    )

def build_subtopics_page(slug, articles):
    topic_name = slug.replace("-", " ").title()
    # Extract subtopics by looking at unique source categories and keyword clusters
    by_source = defaultdict(list)
    for a in articles:
        by_source[a["source"].replace("_"," ").title()].append(a)

    subtopics_html = ""
    for src, items in list(by_source.items())[:24]:
        subtopics_html += f"""
        <div class="subtopic-card">
          <h4>{html.escape(src)}</h4>
          <p>{len(items)} articles · {html.escape(items[0]['category'].title())}</p>
          <div class="stat-bar"><div class="stat-fill" style="width:{min(100,len(items)*10)}%"></div></div>
        </div>"""

    # Also list related topic links from category
    content = f"""
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/topic/{slug}/">{html.escape(topic_name)}</a> › Subtopics</div>
      <h1>Subtopics: {html.escape(topic_name)}</h1>
      <div class="meta"><span>{len(by_source)} subtopics</span><span>By source and angle</span></div>
      <div class="tabs">
        <a href="../" class="tab">Overview</a>
        <a href="../news/" class="tab">News</a>
        <a href="../timeline/" class="tab">Timeline</a>
        <span class="tab active">Subtopics</span>
        <a href="../forum/" class="tab">Discussion</a>
      </div>
      <h2>Coverage by Source</h2>
      <div class="subtopic-list">{subtopics_html}</div>
    </div>"""
    return html_page(
        title=f"{topic_name} Subtopics — Related Topics & Angles",
        description=f"Explore subtopics, angles, and related discussions about {topic_name} from {len(by_source)} different sources.",
        canonical=f"/topic/{slug}/subtopics/",
        content=content
    )

def build_forum_page(slug, articles):
    topic_name = slug.replace("-", " ").title()
    reddit_posts = [a for a in articles if "reddit" in a["source"]]
    hn_posts     = [a for a in articles if "hackernews" in a["source"]]
    other        = [a for a in articles if "reddit" not in a["source"] and "hackernews" not in a["source"]]

    def post_html(a, label):
        return f"""
        <div class="forum-post">
          <div class="fp-meta">{label} · {html.escape(a['date'] or 'Recent')}</div>
          <div class="fp-title"><a href="{html.escape(a['url'])}" target="_blank" rel="noopener">{html.escape(a['title'])}</a></div>
          <div class="fp-body">{html.escape(a['description'][:240]) if a['description'] else 'View the original discussion thread.'}</div>
          {"<div style='font-family:monospace;font-size:10px;color:#999;margin-top:8px'>⬆ "+str(a.get('score',''))+" · 💬 "+str(a.get('comments',''))+" comments</div>" if a.get('score') else ''}
        </div>"""

    posts_html = ""
    for a in reddit_posts[:15]: posts_html += post_html(a, "🔴 Reddit")
    for a in hn_posts[:10]:     posts_html += post_html(a, "🟠 HackerNews")
    for a in other[:10]:        posts_html += post_html(a, "💬 Discussion")

    if not posts_html:
        posts_html = "<p style='color:#999;font-family:monospace;font-size:13px'>No discussion threads found yet. Check back soon.</p>"

    content = f"""
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/topic/{slug}/">{html.escape(topic_name)}</a> › Discussion</div>
      <h1>Discussion: {html.escape(topic_name)}</h1>
      <div class="meta"><span>{len(reddit_posts)} Reddit · {len(hn_posts)} HN threads</span></div>
      <div class="tabs">
        <a href="../" class="tab">Overview</a>
        <a href="../news/" class="tab">News</a>
        <a href="../timeline/" class="tab">Timeline</a>
        <a href="../subtopics/" class="tab">Subtopics</a>
        <span class="tab active">Discussion</span>
      </div>
      {posts_html}
    </div>"""
    return html_page(
        title=f"{topic_name} Discussion — Reddit, HackerNews & More",
        description=f"Community discussion threads about {topic_name} from Reddit, HackerNews, and other forums.",
        canonical=f"/topic/{slug}/forum/",
        content=content
    )

def build_homepage(groups, all_topics_flat):
    date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    by_cat = defaultdict(list)
    for slug, arts in groups.items():
        cat = arts[0]["category"] if arts else "world"
        by_cat[cat].append((slug, arts))

    featured = list(groups.items())[:6]
    hero_slug, hero_arts = featured[0] if featured else ("", [])
    hero_title = hero_slug.replace("-"," ").title()
    hero_desc  = hero_arts[0]["description"] if hero_arts else ""

    featured_html = ""
    for slug, arts in featured[1:6]:
        t = slug.replace("-"," ").title()
        cat = arts[0]["category"] if arts else "world"
        featured_html += f"""
        <div class="card">
          <div class="tag">{cat}</div>
          <h3 style="margin-top:8px"><a href="/topic/{slug}/">{html.escape(t)}</a></h3>
          <p>{html.escape(arts[0]['description'][:150]) if arts and arts[0]['description'] else ''}</p>
          <div class="source">{len(arts)} articles · <a href="/topic/{slug}/news/">News</a> · <a href="/topic/{slug}/timeline/">Timeline</a> · <a href="/topic/{slug}/forum/">Discussion</a></div>
        </div>"""

    # Category sections
    cat_sections = ""
    for cat, items in sorted(by_cat.items()):
        cat_sections += f"""
        <h2 style="margin-top:40px">{cat.title()} <a href="/category/{cat}/" style="font-size:13px;font-weight:400">See all →</a></h2>
        <div class="grid">"""
        for slug, arts in items[:6]:
            t = slug.replace("-"," ").title()
            cat_sections += f"""
          <div class="card">
            <h3><a href="/topic/{slug}/">{html.escape(t)}</a></h3>
            <p>{html.escape(arts[0]['description'][:120]) if arts and arts[0]['description'] else ''}</p>
            <div class="source">{len(arts)} articles</div>
          </div>"""
        cat_sections += "</div>"

    # Rank sidebar
    rank_html = ""
    for i, (slug, arts) in enumerate(list(groups.items())[:20]):
        t = slug.replace("-"," ").title()
        rank_html += f"""
        <li class="rank-item">
          <div class="rank-num">{str(i+1).zfill(2)}</div>
          <div><div class="rank-title"><a href="/topic/{slug}/">{html.escape(t)}</a></div>
          <div style="font-family:monospace;font-size:10px;color:#999">{len(arts)} sources</div></div>
        </li>"""

    total_pages = sum(5 for _ in groups)  # 5 pages per topic

    content = f"""
    <div class="hero-section">
      <div class="eyebrow">🌍 Live · {date}</div>
      <h1>Every Trending Topic in the World</h1>
      <p>{len(groups):,} topics · {total_pages:,} pages · Updated daily from {len(RSS_SOURCES) + len(REDDIT_SUBREDDITS)} global sources</p>
    </div>
    <div class="container">
      <div style="margin-bottom:12px;font-family:monospace;font-size:11px;color:#999">
        Top story: <a href="/topic/{hero_slug}/"><strong style="color:#111">{html.escape(hero_title)}</strong></a> — {html.escape(hero_desc[:120])}
      </div>
      <div class="sidebar-layout">
        <div>
          <div class="section-label" style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#999;text-transform:uppercase;margin-bottom:16px">Featured Topics</div>
          <div class="grid">{featured_html}</div>
          {cat_sections}
        </div>
        <aside class="sidebar">
          <div class="sidebar-box">
            <h3>📈 Top 20 Trending</h3>
            <ol class="rank-list">{rank_html}</ol>
          </div>
          <div class="sidebar-box">
            <h3>📊 Stats</h3>
            <div style="font-size:13px;line-height:2.2">
              <div><strong>{len(groups):,}</strong> topics tracked</div>
              <div><strong>{total_pages:,}</strong> pages generated</div>
              <div><strong>{len(all_topics_flat):,}</strong> articles indexed</div>
              <div><strong>{len(RSS_SOURCES) + len(REDDIT_SUBREDDITS)}</strong> sources crawled</div>
              <div>Updated: {date}</div>
            </div>
          </div>
        </aside>
      </div>
    </div>"""

    return html_page(
        title="WorldPulse — Every Trending Topic in the World",
        description=f"Auto-generated pages for every trending topic worldwide. {len(groups):,} topics, {total_pages:,} pages, updated daily.",
        canonical="/",
        content=content
    )

def build_category_page(cat, groups):
    cat_groups = [(s,a) for s,a in groups.items() if a and a[0]["category"]==cat]
    cards = ""
    for slug, arts in cat_groups:
        t = slug.replace("-"," ").title()
        cards += f"""
        <div class="card">
          <h3><a href="/topic/{slug}/">{html.escape(t)}</a></h3>
          <p>{html.escape(arts[0]['description'][:150]) if arts and arts[0]['description'] else ''}</p>
          <div class="source">{len(arts)} articles · <a href="/topic/{slug}/news/">News</a> · <a href="/topic/{slug}/timeline/">Timeline</a></div>
        </div>"""

    content = f"""
    <div class="container">
      <div class="breadcrumb"><a href="/">Home</a> › {cat.title()}</div>
      <h1>{cat.title()} Trends</h1>
      <div class="meta"><span>{len(cat_groups)} topics</span></div>
      <div class="grid">{cards}</div>
    </div>"""
    return html_page(
        title=f"{cat.title()} Trending Topics — WorldPulse",
        description=f"All trending {cat} topics. {len(cat_groups)} topics with news, timelines, and discussions.",
        canonical=f"/category/{cat}/",
        content=content
    )

# ── SITEMAP ───────────────────────────────────────────────────────────────────

def build_sitemap(groups):
    urls = ['https://worldpulse.site/']
    for cat in CATEGORY_KEYWORDS:
        urls.append(f'https://worldpulse.site/category/{cat}/')
    for slug in groups:
        for page in ['', 'news/', 'timeline/', 'subtopics/', 'forum/']:
            urls.append(f'https://worldpulse.site/topic/{slug}/{page}')

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for u in urls:
        lines.append(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>')
    lines.append('</urlset>')
    return '\n'.join(lines)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def main():
    log.info("=== WorldPulse Generator Starting ===")
    all_topics = []

    log.info("Crawling RSS sources…")
    all_topics += crawl_rss_sources()
    log.info(f"RSS: {len(all_topics)} topics")

    log.info("Crawling Reddit…")
    reddit = crawl_reddit()
    all_topics += reddit
    log.info(f"Reddit: {len(reddit)} topics")

    log.info("Crawling YouTube…")
    yt = crawl_youtube_trending()
    all_topics += yt
    log.info(f"YouTube: {len(yt)} topics")

    log.info("Crawling Wikipedia…")
    wiki = crawl_wikipedia()
    all_topics += wiki
    log.info(f"Wikipedia: {len(wiki)} topics")

    log.info(f"Total raw: {len(all_topics)} — deduplicating…")
    all_topics = dedup_topics(all_topics)
    log.info(f"After dedup: {len(all_topics)}")

    # Save cache
    TOPICS_JSON.write_text(json.dumps(all_topics, indent=2), encoding="utf-8")

    groups = group_by_topic(all_topics)
    log.info(f"Unique topics: {len(groups)}")

    # Build pages
    total = 0
    for slug, articles in groups.items():
        base = OUTPUT_DIR / "topic" / slug
        write(base / "index.html",      build_overview_page(slug, articles))
        write(base / "news/index.html", build_news_page(slug, articles))
        write(base / "timeline/index.html", build_timeline_page(slug, articles))
        write(base / "subtopics/index.html", build_subtopics_page(slug, articles))
        write(base / "forum/index.html",    build_forum_page(slug, articles))
        total += 5
        if total % 50 == 0:
            log.info(f"  Built {total} pages…")

    # Category pages
    for cat in CATEGORY_KEYWORDS:
        write(OUTPUT_DIR / "category" / cat / "index.html", build_category_page(cat, groups))

    # Homepage
    write(OUTPUT_DIR / "index.html", build_homepage(groups, all_topics))

    # Sitemap
    write(OUTPUT_DIR / "sitemap.xml", build_sitemap(groups))

    log.info(f"=== Done! {total} topic pages + {len(CATEGORY_KEYWORDS)} category pages + homepage ===")
    log.info(f"Output: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
