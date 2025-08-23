import os
import requests
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/")
def root():
    return {"message": "RAOD3R backend is running 🎉"}

@app.get("/story/{work_id}")
def get_story(work_id: int):
    """
    Fetch AO3 story by work ID.
    Example: /story/123456
    """
    url = f"https://archiveofourown.org/works/{work_id}?view_full_work=true"
    headers = {"User-Agent": "Mozilla/5.0"}  # AO3 blocks bots without this
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Story not found")

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract metadata
        title = soup.find("h2", class_="title").get_text(strip=True) if soup.find("h2", class_="title") else "Untitled"
        author = soup.find("a", rel="author").get_text(strip=True) if soup.find("a", rel="author") else "Unknown"
        summary = soup.find("blockquote", class_="userstuff").get_text(strip=True) if soup.find("blockquote", class_="userstuff") else ""
        
        # Extract story text (all chapters if full view)
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
