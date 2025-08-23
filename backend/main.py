import os
import requests
from fastapi import FastAPI, HTTPException, Query
from bs4 import BeautifulSoup

app = FastAPI()

BASE_URL = "https://archiveofourown.org"

@app.get("/")
def root():
    return {"message": "RAOD3R backend is running 🎉"}

@app.get("/story/{work_id}")
def get_story(work_id: int):
    """
    Fetch AO3 story by work ID.
    Example: /story/123456
    """
    url = f"{BASE_URL}/works/{work_id}?view_full_work=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Story not found")

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract metadata
        title = soup.find("h2", class_="title").get_text(strip=True) if soup.find("h2", class_="title") else "Untitled"
        author = soup.find("a", rel="author").get_text(strip=True) if soup.find("a", rel="author") else "Unknown"
        summary = soup.find("blockquote", class_="userstuff").get_text(strip=True) if soup.find("blockquote", class_="userstuff") else ""
        
        # Extract story text
        content_divs = soup.find_all("div", class_="userstuff")
        chapters = [div.get_text("\n", strip=True) for div in content_divs]

        return {
            "id": work_id,
            "title": title,
            "author": author,
            "summary": summary,
            "chapters": chapters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search_stories(
    tag: str = Query("", description="Search tag or keyword"),
    fandom: str = Query("", description="Fandom filter"),
    rating: str = Query("", description="Rating filter (G, T, M, E)"),
    complete: bool = Query(False, description="Only completed works"),
    sort: str = Query("revised_at", description="Sort method (revised_at, hits, kudos, comments, bookmarks)"),
    page: int = 1
):
    """
    Search AO3 stories with advanced filters.
    Example: /search?tag=romance&fandom=Harry+Potter&rating=T&complete=true&sort=hits&page=1
    """
    params = {
        "work_search[query]": tag,
        "work_search[fandom_names]": fandom,
        "work_search[rating_ids]": rating,
        "work_search[complete]": "T" if complete else "",
        "sort_column": sort,
    }
    url = f"{BASE_URL}/works/search"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params={**params, "page": page}, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Search failed")

        soup = BeautifulSoup(r.text, "html.parser")
        works = []

        results = soup.find_all("li", class_="work")
        for result in results:
            title_tag = result.find("h4", class_="heading").find("a")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            link = BASE_URL + title_tag["href"] if title_tag else None
            work_id = int(link.split("/works/")[1].split("?")[0]) if link else None
            author = result.find("a", rel="author").get_text(strip=True) if result.find("a", rel="author") else "Unknown"

            summary_tag = result.find("blockquote", class_="userstuff summary")
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            works.append({
                "id": work_id,
                "title": title,
                "author": author,
                "summary": summary,
                "url": link
            })

        return {
            "tag": tag,
            "fandom": fandom,
            "rating": rating,
            "complete": complete,
            "sort": sort,
            "page": page,
            "results": works
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
