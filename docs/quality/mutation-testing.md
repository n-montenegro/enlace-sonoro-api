# Mutation testing (mutmut)

**Herramienta:** mutmut 3.8.1 (Python). Muta el código de `app/domain` y `app/application`
(la lógica de negocio) y ejecuta todas las pruebas contra cada mutante.
Se ejecuta en GitHub Actions (Linux), porque mutmut necesita `fork` y no funciona en Windows.

**Mutation Score** = mutantes detectados (killed + timeout) / mutantes evaluados × 100.
El pipeline falla si el score es menor a **50 %** (`scripts/mutation_score.py --min 50`).

## Evolución del score

| Ronda | Mutantes | Eliminados | Sobrevivientes | Sin pruebas | Score | Cambio realizado |
|---|---|---|---|---|---|---|
| 1 (línea base) | 422 | 282 | 138 | 2 | 66,8 % | — |
| 2 | 422 | 403 | 18 | 1 | 95,5 % | Pruebas exactas de prompts, RAG, playlist, errores y registro de llamadas |
| 3 | 421 | 416 | 5 | 0 | 98,8 % | Se usó `User.is_admin()` (era código muerto) y se añadieron pruebas de mensajes y del límite del RAG |
| 4 (final) | 416 | 415 | 1 | 0 | **99,8 %** | Se eliminó un valor por defecto que nunca se usaba en `AuthService.current_user` |

## Mutantes analizados

| Archivo / función | Mutación (ejemplo) | Por qué sobrevivía | Prueba añadida | Estado |
|---|---|---|---|---|
| `prompts.build_prompt` | Cambiar `"Now your turn"` por `"XXNow your turnXX"` o a mayúsculas (27 mutantes) | Las pruebas solo revisaban que el prompt *contuviera* algunas palabras | `test_zero_shot_prompt_is_exact`, `test_few_shot_prompt_is_exact`, `test_chain_of_thought_prompt_is_exact` | Eliminados |
| `RecommendationService.ask` | Cambiar la clave `"question"` del registro por `"XXquestionXX"` (36 mutantes) | Ninguna prueba revisaba el contenido completo del registro | `test_successful_call_is_logged_with_every_field`, `test_failed_calls_are_logged_with_their_status` | Eliminados |
| `rag.retrieve_songs` | `sorted(..., key=lambda x: +x[0])` (orden invertido) | No había prueba con canciones de distinto puntaje | `test_retrieve_orders_by_number_of_matches` | Eliminado |
| `rag.retrieve_songs` | `limit: int = 9` en vez de 8 | Ninguna prueba usaba el límite por defecto | `test_retrieve_default_limit_is_eight` | Eliminado |
| `rag.extract_keywords` | `len(w) >= 2` en vez de `> 2` | No se probaban palabras cortas | `test_extract_keywords_filters_stopwords_and_short_words` | Eliminado |
| `rag.build_context` | `divmod(..., 61)` en vez de 60 | No se revisaba el formato exacto de la duración | `test_build_context_exact_format` | Eliminado |
| `Playlist.eliminar` | `self.cola = None` al borrar la última canción | Las pruebas recorrían la lista solo hacia adelante | `test_delete_last_song_updates_tail`, `test_links_work_in_both_directions` | Eliminado |
| `User.is_admin` | `!=` en vez de `==` (sin pruebas) | **El método no se usaba en ninguna parte (código muerto)** | Ahora `AuthService.require_role` lo usa + `test_is_admin` | Eliminado |
| `AuthService.current_user` | `data.get("sub", None)` en vez de `""` | El valor por defecto nunca se usaba: el JWT ya exige `sub` | Se simplificó a `data["sub"]` | Ya no existe |
| `rag.retrieve_songs` | `sum(2 for ...)` en vez de `sum(1 for ...)` | **Mutante equivalente:** multiplicar todos los puntajes por 2 no cambia el orden ni el filtro `> 0` | No es posible detectarlo con una prueba | Equivalente (documentado) |
