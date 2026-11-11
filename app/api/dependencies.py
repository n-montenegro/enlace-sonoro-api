"""
dependencies.py - Entrega a cada endpoint el servicio que necesita.

Los servicios se crean UNA vez en main.py (composition root) y se guardan en app.state.
Los routers los piden con Depends(...) en lugar de crearlos ellos mismos.
"""
from fastapi import Request

from app.application.opendata_service import OpenDataService
from app.application.recommendation_service import RecommendationService
from app.application.song_service import SongService


def get_song_service(request: Request) -> SongService:
    return request.app.state.song_service


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service


def get_opendata_service(request: Request) -> OpenDataService:
    return request.app.state.opendata_service
