from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Allow frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/story/{work_id}")
def get_story(work_id: int):
    url = f"https://archiveofourown.org/works/{work_id}?view_full_work=true"
    res = requests.get(url)

    if res.status_code != 200:
        raise HTTPException(status_code=404, detail="Story not found")

    soup = BeautifulSoup(res.text, "html.parser")

    # Extract fields
    title = soup.select_one("h2.title").get_text(strip=True)
    author = soup.select_one("a[rel='author']").get_text(strip=True)
    summary_el = soup.select_one("blockquote.summary")
    summary = summary_el.get_text(strip=True) if summary_el else "No summary"
    content = str(soup.select_one("div#chapters"))

    return {
        "title": title,
        "author": author,
        "summary": summary,
        "content": content,
    }
