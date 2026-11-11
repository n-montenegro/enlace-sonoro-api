"""fakes.py - Dobles de prueba compartidos (reemplazan a Gemini y a las APIs reales)."""
from app.domain.opendata.ports import OpenDataSource, OpenDataUnavailableError
from app.domain.recommendation.ports import LLMPort

DIVIPOLA_SAMPLE = [
    {"cod_dpto": "05", "dpto": "ANTIOQUIA", "cod_mpio": "05001", "nom_mpio": "MEDELLÍN", "tipo_municipio": "Municipio", "longitud": "-75,581775", "latitud": "6,246631"},
    {"cod_dpto": "05", "dpto": "ANTIOQUIA", "cod_mpio": "05002", "nom_mpio": "ABEJORRAL", "tipo_municipio": "Municipio", "longitud": "-75,428739", "latitud": "5,789315"},
    {"cod_dpto": "05", "dpto": "ANTIOQUIA", "cod_mpio": "05004", "nom_mpio": "ABRIAQUÍ", "tipo_municipio": "Municipio", "longitud": "-76,064304", "latitud": "6,632282"},
    {"cod_dpto": "11", "dpto": "BOGOTÁ, D.C.", "cod_mpio": "11001", "nom_mpio": "BOGOTÁ, D.C.", "tipo_municipio": "Municipio", "longitud": "-74,107807", "latitud": "4,64829"},
    {"cod_dpto": "25", "dpto": "CUNDINAMARCA", "cod_mpio": "25754", "nom_mpio": "SOACHA", "tipo_municipio": "Municipio", "longitud": "-74,214", "latitud": "4,579"},
    {"cod_dpto": "25", "dpto": "CUNDINAMARCA", "cod_mpio": "25175", "nom_mpio": "CHÍA", "tipo_municipio": "Municipio", "longitud": "-74,052", "latitud": "4,858"},
]

# Misma forma que devuelve el DANE: los números vienen como texto
DANE_SAMPLE = [
    {"id": "173", "title": "Encuesta Consumo  Cultural - ECC - 2009", "year_start": "2009", "repo_title": "Metadatos - DANE", "total_views": "591600", "total_downloads": "21399"},
    {"id": "242", "title": "Encuesta de Consumo Cultural - ECC - 2010.", "year_start": "2010", "repo_title": "Cultura.", "total_views": "237975", "total_downloads": "14615"},
    {"id": "248", "title": "Encuesta de Consumo Cultural - ECC - 2012", "year_start": "2012", "repo_title": "Cultura.", "total_views": "999063", "total_downloads": "12146"},
    {"id": "584", "title": "Encuesta de Desarrollo e Innovación Tecnológica de Servicios - EDIT", "year_start": "2018", "repo_title": "Tecnología e innovación.", "total_views": "223217", "total_downloads": "5972"},
]


class FakeLLM(LLMPort):
    def __init__(self, answer="Te recomiendo Lofi Study Session.", error=None):
        self.answer = answer
        self.error = error
        self.last_prompt = None

    def model_name(self):
        return "fake-model"

    def ask(self, prompt, system_instruction):
        self.last_prompt = prompt
        if self.error:
            raise self.error
        return {"text": self.answer, "input_tokens": 120, "output_tokens": 15,
                "thinking_tokens": 0, "latency_ms": 5, "model": "fake-model"}


class FakeSource(OpenDataSource):
    """Fuente falsa: devuelve registros fijos o simula que la API está caída."""

    def __init__(self, name, records, down=False):
        self.name = name
        self.records = records
        self.down = down

    def fetch(self):
        if self.down:
            raise OpenDataUnavailableError(f"{self.name} is down")
        return self.records

    def status(self):
        return {"source": self.name, "state": "OPEN" if self.down else "CLOSED",
                "consecutive_failures": 3 if self.down else 0, "failure_threshold": 3, "history": []}
