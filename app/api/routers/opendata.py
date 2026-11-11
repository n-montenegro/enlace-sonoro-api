"""
opendata.py - ADAPTADOR DE ENTRADA (HTTP): estadísticas de datos abiertos colombianos.

  GET /api/v1/opendata/municipalities/stats  -> datos.gov.co (DIVIPOLA) analizado con DuckDB
  GET /api/v1/opendata/culture/stats         -> DANE (Encuesta de Consumo Cultural) analizado con DuckDB
  GET /api/v1/opendata/status                -> estado de los circuit breakers de cada API
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_opendata_service
from app.application.opendata_service import OpenDataService
from app.domain.opendata.ports import OpenDataUnavailableError

router = APIRouter(prefix="/api/v1/opendata", tags=["Colombian Open Data"])

UNAVAILABLE = {503: {"description": "The source is down (or its circuit is OPEN) and there is no saved copy"}}


@router.get("/municipalities/stats", summary="Municipalities per department (datos.gov.co)",
            description="Downloads DIVIPOLA from datos.gov.co, saves it as JSON and runs DuckDB analytical "
                        "queries: municipalities per department and descriptive statistics.",
            responses=UNAVAILABLE)
def municipalities_stats(service: OpenDataService = Depends(get_opendata_service)):
    try:
        return service.municipalities_stats()
    except OpenDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/culture/stats", summary="Cultural Consumption Survey downloads (DANE)",
            description="Searches the DANE microdata catalog (ANDA), saves it as JSON and runs DuckDB analytical "
                        "queries over the Encuesta de Consumo Cultural (ECC) studies.",
            responses=UNAVAILABLE)
def culture_stats(service: OpenDataService = Depends(get_opendata_service)):
    try:
        return service.culture_studies_stats()
    except OpenDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/status", summary="Circuit breaker status",
            description="Current state (CLOSED, OPEN or HALF_OPEN) and state history of each API circuit breaker.")
def status(service: OpenDataService = Depends(get_opendata_service)):
    return service.status()
