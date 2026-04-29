import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="MusicBot Admin Panel", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    from utils.database import get_stats
    from assistant import get_active_chats
    from bot import START_TIME
    from utils.formatters import uptime_string
    import psutil

    stats = await get_stats()
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "active_vc": len(get_active_chats()),
        "uptime": uptime_string(START_TIME),
        "cpu": cpu,
        "ram": mem.percent,
        "ram_used": mem.used // 1024 // 1024,
        "ram_total": mem.total // 1024 // 1024,
    })


@app.get("/api/stats")
async def api_stats():
    from utils.database import get_stats
    from assistant import get_active_chats
    from bot import START_TIME
    from utils.formatters import uptime_string
    import psutil

    stats = await get_stats()
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    return JSONResponse({
        "groups": stats["groups"],
        "users": stats["users"],
        "plays": stats["plays"],
        "active_vc": len(get_active_chats()),
        "uptime": uptime_string(START_TIME),
        "cpu": cpu,
        "ram": mem.percent,
    })


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


async def start_web():
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()
