"""
프론트엔드 라우터 모듈
HTML 페이지 및 정적 파일 서빙
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# 라우터 생성
frontend_router = APIRouter()

# 템플릿 설정
templates_dir = os.path.join(os.path.dirname(__file__), "../../frontend/templates")
static_dir = os.path.join(os.path.dirname(__file__), "../../frontend/static")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None

# 정적 파일 마운트
if os.path.exists(static_dir):
    frontend_router.mount("/static", StaticFiles(directory=static_dir), name="static")


@frontend_router.get("/", response_class=HTMLResponse)
@frontend_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드 페이지"""
    if templates:
        return templates.TemplateResponse("dashboard_simple.html", {"request": request})
    return HTMLResponse("<h1>Dashboard - Templates not found</h1>")


@frontend_router.get("/markets", response_class=HTMLResponse)
async def markets_page(request: Request):
    """마켓 페이지"""
    if templates:
        return templates.TemplateResponse("markets.html", {"request": request})
    return HTMLResponse("<h1>Markets - Templates not found</h1>")


@frontend_router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(request: Request):
    """추천 페이지"""
    if templates:
        return templates.TemplateResponse("recommendations.html", {"request": request})
    return HTMLResponse("<h1>Recommendations - Templates not found</h1>")


@frontend_router.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    """디버그 페이지"""
    if templates:
        return templates.TemplateResponse("debug.html", {"request": request})
    return HTMLResponse("<h1>Debug - Templates not found</h1>")
