import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI()


# Allow frontend (GitHub Pages) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can replace "*" with ["https://rosarioespadera.github.io"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
    rating: str = Query("", description="Rating filter (G, T, M, E, NR)"),
    complete: bool = Query(False, description="Only completed works"),
    sort: str = Query("revised_at", description="Sort method"),
    page: int = 1
):
    # AO3 rating map
    rating_map = {"NR": "9", "G": "10", "T": "11", "M": "12", "E": "13"}
    rating_id = rating_map.get(rating.upper(), "")

    params = {
        "work_search[query]": tag,
        "work_search[fandom_names]": fandom,
        "work_search[rating_ids]": rating_id,
        "work_search[complete]": "T" if complete else "",
        "sort_column": sort,
        "page": page
    }
    url = f"{BASE_URL}/works/search"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params=params, headers=headers)
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
            "query": tag,
            "count": len(works),
            "results": works
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
