import os
import time
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI()

# Allow frontend (GitHub Pages) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For security, replace "*" with ["https://rosarioespadera.github.io"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://archiveofourown.org"

# Fake browser headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0 Safari/537.36"
}
CACHE = {}
CACHE_TTL = 60 * 5  # 5 min

def fetch_with_cache(url, params=None):
    """Fetch AO3 page with headers + caching"""
    key = f"{url}|{params}"
    now = time.time()

    # Return cached if still valid
    if key in CACHE:
        ts, data = CACHE[key]
        if now - ts < CACHE_TTL:
            return data

    # Make request (with polite scraping)
    time.sleep(1)  # be nice to AO3
    response = requests.get(url, params=params, headers=HEADERS)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="AO3 request failed")

    CACHE[key] = (now, response.text)
    return response.text


@app.get("/")
def root():
    return {"message": "RAOD3R backend is running 🚀"}


@app.get("/story/{story_id}")
def get_story(story_id: str):
    """Fetch full story content (all chapters) from AO3"""
    url = f"{BASE_URL}/works/{story_id}?view_full_work=true"
    html = fetch_with_cache(url)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h2.title")
    author = soup.select_one("a[rel='author']")
    summary = soup.select_one("blockquote.userstuff")
    chapters = [c.get_text("\n", strip=True) for c in soup.select("div.userstuff")]

    return {
        "id": story_id,
        "title": title.get_text(strip=True) if title else "Untitled",
        "author": author.get_text(strip=True) if author else "Unknown",
        "summary": summary.get_text(strip=True) if summary else "",
        "chapters": chapters
    }


@app.get("/trending")
def trending(page: int = Query(1, ge=1)):
    """Fetch trending (recently popular) works from AO3"""
    url = f"{BASE_URL}/works?page={page}"
    html = fetch_with_cache(url)
    soup = BeautifulSoup(html, "html.parser")

    works = []
    for li in soup.select("li.work.blurb"):
        work_id = li.get("id", "").replace("work_", "")
        title_el = li.select_one("h4.heading a")
        author_el = li.select_one("h4.heading a[rel='author']")
        fandom_el = li.select_one("h5.fandoms a")
        rating_el = li.select_one("span.rating")
        summary_el = li.select_one("blockquote.userstuff")
        completed_el = li.select_one("span.iswip")

        works.append({
            "id": work_id,
            "title": title_el.text.strip() if title_el else "Untitled",
            "author": author_el.text.strip() if author_el else "Unknown",
            "fandom": fandom_el.text.strip() if fandom_el else "Unknown",
            "rating": rating_el["title"] if rating_el else "Not Rated",
            "completed": False if completed_el else True,
            "summary": summary_el.text.strip() if summary_el else "",
            "url": BASE_URL + title_el["href"] if title_el else ""
        })

    return {"results": works, "page": page}


@app.get("/search")
def search(
    tag: str = Query(..., description="Tag to search (e.g. romance)"),
    page: int = Query(1, ge=1),
    fandom: str = Query(None, description="Filter by fandom"),
    rating: str = Query(None, description="Filter by rating (General, Teen, Mature, Explicit)"),
    completed: bool = Query(False, description="Completed works only"),
):
    """Scrape AO3 search results with filters"""

    params = {"tag_id": tag, "page": page}

    # AO3 ratings mapping
    rating_map = {"General": "10", "Teen": "11", "Mature": "12", "Explicit": "13"}
    if rating and rating in rating_map:
        params["work_search[rating_ids]"] = rating_map[rating]
    if completed:
        params["work_search[complete]"] = "T"
    if fandom:
        params["work_search[fandom_names]"] = fandom

    url = f"{BASE_URL}/works/search"
    html = fetch_with_cache(url, params=params)
    soup = BeautifulSoup(html, "html.parser")

    works = []
    for li in soup.select("li.work.blurb"):
        work_id = li.get("id", "").replace("work_", "")
        title_el = li.select_one("h4.heading a")
        author_el = li.select_one("h4.heading a[rel='author']")
        fandom_el = li.select_one("h5.fandoms a")
        rating_el = li.select_one("span.rating")
        summary_el = li.select_one("blockquote.userstuff")
        completed_el = li.select_one("span.iswip")

        works.append({
            "id": work_id,
            "title": title_el.text.strip() if title_el else "Untitled",
            "author": author_el.text.strip() if author_el else "Unknown",
            "fandom": fandom_el.text.strip() if fandom_el else "Unknown",
            "rating": rating_el["title"] if rating_el else "Not Rated",
            "completed": False if completed_el else True,
            "summary": summary_el.text.strip() if summary_el else "",
            "url": BASE_URL + title_el["href"] if title_el else ""
        })

    return {"results": works, "page": page}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
