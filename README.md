# 🌍 WorldPulse — Auto-Generated Trending Topics Site

A fully automated static site generator that crawls **50+ free global sources** and builds **thousands of SEO-optimized HTML pages** daily — zero cost, zero AI APIs, zero paid services.

---

## How It Works

```
Run generator.py
      │
      ├── Crawls 50+ sources simultaneously
      │     ├── Google Trends (18 countries)
      │     ├── Reddit (20 subreddits)
      │     ├── BBC, Reuters, AP, Al Jazeera, Guardian...
      │     ├── HackerNews, TechCrunch, Wired, Ars Technica
      │     ├── NASA, WHO, Wikipedia Current Events
      │     ├── YouTube channel feeds
      │     └── + 30 more RSS feeds
      │
      ├── Deduplicates & groups into topics
      │
      └── Builds HTML pages per topic
            ├── /topic/{slug}/              ← Overview
            ├── /topic/{slug}/news/         ← All articles
            ├── /topic/{slug}/timeline/     ← Chronological
            ├── /topic/{slug}/subtopics/    ← Related angles
            └── /topic/{slug}/forum/        ← Discussions
```

**Result:** 500–2000+ topics × 5 pages = **2,500–10,000+ pages per run.**

---

## Quick Start (Local)

```bash
# 1. Clone your repo
git clone https://github.com/YOUR_USERNAME/worldpulse.git
cd worldpulse

# 2. Install dependencies (only 1 package!)
pip install -r requirements.txt

# 3. Run the generator
python generator.py

# 4. Preview locally
cd output
python -m http.server 8000
# Open http://localhost:8000
```

---

## Deploy Free on GitHub Pages (Recommended)

### Step 1 — Create GitHub repo
1. Go to github.com → New Repository
2. Name it `worldpulse` (or any name)
3. Make it **Public**
4. Upload all files from this folder

### Step 2 — Enable GitHub Pages
1. Go to your repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `gh-pages` / `/ (root)`
4. Save

### Step 3 — Enable Actions
1. Go to **Actions** tab → Enable workflows
2. Click **"Generate WorldPulse Site"** → **Run workflow**
3. Wait ~5 minutes → your site is live!

After that, it runs **automatically twice a day** (6 AM + 2 PM UTC) via the GitHub Actions cron job.

**Your site will be at:** `https://YOUR_USERNAME.github.io/worldpulse/`

---

## Deploy on Netlify (Custom Domain)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --dir=output --prod
```

Or connect your GitHub repo to Netlify and set build command to `python generator.py` and publish directory to `output`.

---

## Custom Domain (SEO)

1. Buy a domain (e.g. `worldpulse.site`) — ~$10/year
2. In GitHub Pages settings → add your custom domain
3. Add a CNAME record in your domain DNS pointing to `YOUR_USERNAME.github.io`
4. Enable "Enforce HTTPS"

---

## SEO Features Built In

Every page includes:
- ✅ Unique `<title>` and `<meta description>`
- ✅ `<link rel="canonical">` 
- ✅ Open Graph tags
- ✅ JSON-LD structured data (Article schema)
- ✅ Auto-generated `sitemap.xml` with all pages
- ✅ Google Sitemap ping after each build
- ✅ Mobile-responsive design
- ✅ Fast-loading (pure HTML, no JS frameworks)
- ✅ Daily freshness signal for Google crawlers

---

## Adding More Sources

In `generator.py`, find `RSS_SOURCES` dict and add any RSS feed URL:

```python
RSS_SOURCES = {
    # Add your new source:
    "my_source": "https://example.com/rss.xml",
    ...
}
```

For more Reddit subreddits, add to `REDDIT_SUBREDDITS` list:
```python
REDDIT_SUBREDDITS = [
    "worldnews", "science", "your_new_subreddit", ...
]
```

---

## File Structure

```
worldpulse/
├── generator.py          ← Main script (run this)
├── requirements.txt      ← Only needs: requests
├── topics_cache.json     ← Cache of last crawl (auto-created)
├── .github/
│   └── workflows/
│       └── generate.yml  ← GitHub Actions auto-runner
└── output/               ← Generated site (auto-created)
    ├── index.html
    ├── sitemap.xml
    ├── category/
    │   ├── technology/index.html
    │   ├── science/index.html
    │   └── ...
    └── topic/
        ├── artificial-intelligence/
        │   ├── index.html
        │   ├── news/index.html
        │   ├── timeline/index.html
        │   ├── subtopics/index.html
        │   └── forum/index.html
        ├── climate-change/
        │   └── ...
        └── (thousands more)
```

---

## Sources Crawled

| Category | Sources |
|----------|---------|
| **Trends** | Google Trends (18 countries: US, UK, India, Brazil, Japan, Germany, France, Nigeria, Mexico, Korea, Indonesia, Turkey, Argentina, Egypt, Canada, Australia, Saudi Arabia, Global) |
| **News** | BBC World/Tech/Science/Health, Reuters World/Tech/Science, AP News, Al Jazeera, DW, France24, The Guardian, NPR, Euronews, NY Times, Washington Post, The Economist |
| **Tech** | HackerNews, TechCrunch, Wired, Ars Technica, The Verge, MIT Tech Review, GitHub Trending |
| **Science** | Nature, ScienceDaily, Phys.org, New Scientist, NASA |
| **Health** | WHO, CDC, NPR Health, BBC Health |
| **Space** | Space.com, NASA Breaking News |
| **Environment** | Climate Home News, Carbon Brief, Guardian Environment |
| **Business** | Financial Times, Bloomberg Tech, CNBC, MarketWatch |
| **Culture** | Smithsonian, National Geographic |
| **Community** | Reddit (20 subreddits), HackerNews |
| **Video** | YouTube (science, news, education channels) |
| **Reference** | Wikipedia Current Events |

**Total: 50+ sources, 18 countries, updated daily.**

---

## Scaling Up

The generator uses `ThreadPoolExecutor` (8 threads) for parallel crawling. To go even bigger:

- Increase `MAX_WORKERS = 16` for faster crawling
- Add more RSS feeds to `RSS_SOURCES`
- Add more countries to Google Trends
- Run the generator 3-4x daily via the cron schedule

At full scale, you can realistically generate **10,000–50,000 pages** per day.
