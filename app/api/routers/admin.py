"""
admin.py - ADAPTADOR DE ENTRADA (HTTP): endpoint de prueba para el rol ADMIN.

  GET /api/v1/admin/stats -> resumen interno del sistema. Un USER recibe 403 Forbidden.
"""
from fastapi import APIRouter, Depends

from app.api.dependencies import (get_auth_service, get_opendata_service, get_recommendation_service,
                                  get_song_service)
from app.api.security import require_role
from app.domain.identity.user import ADMIN

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/stats", summary="System summary (ADMIN role test endpoint)",
            description="Internal numbers of the system. Only the ADMIN role can see them; a USER gets 403.",
            responses={401: {"description": "Missing or invalid token"},
                       403: {"description": "The user does not have the ADMIN role"}},
            dependencies=[Depends(require_role(ADMIN))])
def stats(songs=Depends(get_song_service), auth=Depends(get_auth_service),
          recommendations=Depends(get_recommendation_service), opendata=Depends(get_opendata_service)):
    calls = recommendations.calls()
    return {
        "songs": len(songs.list()),
        "users": auth.count_users(),
        "llm_calls": len(calls),
        "llm_failed_calls": sum(1 for c in calls if c.get("status") != 200),
        "circuit_breakers": {s["source"]: s["state"] for s in opendata.status()["sources"]},
    }
