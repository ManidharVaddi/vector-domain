# main.py
import sys
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Vector Domain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create database tables
from app.database import Base, engine
Base.metadata.create_all(bind=engine)

from app.routers import auth, documents
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Serve Frontend as plain HTML
@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Template Error: {str(e)}</h1><p>Make sure templates/index.html exists</p>")

@app.get("/")
async def root():
    return {"frontend": "/app", "status": "running"}

# ... (keep all the code above)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
else:
    # For Render / production servers
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))