"""dashboard.py - Página web sencilla con las gráficas de DuckDB (la "UI" que pide la guía)."""
import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()
HTML = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "dashboard.html")


@router.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(HTML)
