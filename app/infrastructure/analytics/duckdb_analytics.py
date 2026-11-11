"""
duckdb_analytics.py - ADAPTADOR de AnalyticsPort con DuckDB.

DuckDB es una base de datos analítica que lee archivos JSON directamente con read_json_auto,
sin tener que crear tablas a mano. Aquí están las consultas SQL analíticas del proyecto.
"""
from typing import List

import duckdb

from app.domain.opendata.ports import AnalyticsPort


class DuckDBAnalytics(AnalyticsPort):

    @staticmethod
    def _rows(sql: str, json_path: str) -> List[dict]:
        con = duckdb.connect()  # base de datos en memoria
        try:
            cursor = con.execute(sql, [json_path])
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            con.close()

    # ---------- datos.gov.co: DIVIPOLA ----------

    def municipalities_by_department(self, json_path: str) -> List[dict]:
        sql = """
            SELECT dpto AS departamento,
                   COUNT(*) AS municipios
            FROM read_json_auto(?)
            GROUP BY dpto
            ORDER BY municipios DESC, departamento
        """
        return self._rows(sql, json_path)

    def municipalities_summary(self, json_path: str) -> dict:
        sql = """
            WITH por_dpto AS (
                SELECT dpto, COUNT(*) AS municipios
                FROM read_json_auto(?)
                GROUP BY dpto
            )
            SELECT COUNT(*)                                AS departamentos,
                   SUM(municipios)                         AS total_municipios,
                   ROUND(AVG(municipios), 2)               AS promedio,
                   MEDIAN(municipios)                      AS mediana,
                   ROUND(STDDEV_SAMP(municipios), 2)       AS desviacion_estandar,
                   MIN(municipios)                         AS minimo,
                   MAX(municipios)                         AS maximo
            FROM por_dpto
        """
        return self._rows(sql, json_path)[0]

    # ---------- DANE: Encuesta de Consumo Cultural ----------

    def culture_studies(self, json_path: str) -> List[dict]:
        sql = """
            SELECT CAST(year_start AS INTEGER)       AS anio,
                   title                             AS estudio,
                   CAST(total_views AS BIGINT)       AS vistas,
                   CAST(total_downloads AS BIGINT)   AS descargas
            FROM read_json_auto(?)
            WHERE title ILIKE '%consumo%cultural%'
            ORDER BY anio
        """
        return self._rows(sql, json_path)

    def culture_studies_summary(self, json_path: str) -> dict:
        sql = """
            WITH ecc AS (
                SELECT CAST(total_downloads AS BIGINT) AS descargas,
                       CAST(total_views AS BIGINT)     AS vistas
                FROM read_json_auto(?)
                WHERE title ILIKE '%consumo%cultural%'
            )
            SELECT COUNT(*)                              AS encuestas,
                   SUM(descargas)                        AS total_descargas,
                   ROUND(AVG(descargas), 2)              AS promedio_descargas,
                   MEDIAN(descargas)                     AS mediana_descargas,
                   ROUND(STDDEV_SAMP(descargas), 2)      AS desviacion_descargas,
                   MIN(descargas)                        AS minimo_descargas,
                   MAX(descargas)                        AS maximo_descargas,
                   ROUND(AVG(vistas), 2)                 AS promedio_vistas
            FROM ecc
        """
        return self._rows(sql, json_path)[0]
