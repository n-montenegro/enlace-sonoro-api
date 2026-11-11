"""
demo_circuit_breaker.py - Demostración en vivo de los 3 estados del circuit breaker (evidencia).

Usa el cliente REAL de datos.gov.co. Para provocar fallos, se cambia la URL por una
dirección que no existe (.invalid nunca existe en internet), y luego se restaura la buena.

Ejecutar desde la carpeta del proyecto:
    py -3.14 scripts/demo_circuit_breaker.py
"""
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.domain.opendata.ports import OpenDataUnavailableError  # noqa: E402
from app.infrastructure.opendata.datos_gov_client import DIVIPOLA_URL, DatosGovDivipolaClient  # noqa: E402
from app.infrastructure.resilience.circuit_breaker import CircuitBreaker  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="    %(message)s")

URL_CAIDA = "https://datos-gov-caido.invalid/resource/gdxc-w37w.json"
breaker = CircuitBreaker("datos.gov.co", failure_threshold=3, recovery_timeout=5)
client = DatosGovDivipolaClient(DIVIPOLA_URL, breaker, retries=2, base_delay=0.5)


def intentar(descripcion):
    print(f"\n>> {descripcion}")
    inicio = time.perf_counter()
    try:
        registros = client.fetch()
        print(f"   OK: {len(registros)} municipios recibidos")
    except OpenDataUnavailableError as exc:
        print(f"   FALLÓ: {exc}")
    print(f"   Estado del circuito: {breaker.state}  "
          f"(fallos seguidos: {breaker.failures}, {time.perf_counter() - inicio:.1f} s)")


print("=== Demostración del circuit breaker (umbral: 3 fallos, espera: 5 s) ===")
intentar("1. API funcionando")

client.url = URL_CAIDA
for i in range(2, 5):
    intentar(f"{i}. API caída (fallo {i - 1} de 3)")

intentar("5. Con el circuito OPEN se rechaza al instante, sin llamar a la API")

print("\n... esperando 6 segundos (tiempo de recuperación) ...")
time.sleep(6)
client.url = DIVIPOLA_URL
intentar("6. Llamada de prueba en HALF_OPEN con la API recuperada")

print("\nHistorial de cambios de estado:")
for cambio in breaker.history:
    print(f"   {cambio['time']}  {cambio['from']} -> {cambio['to']}")
