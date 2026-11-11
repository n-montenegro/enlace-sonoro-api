"""
prompts.py - Las 3 técnicas de prompting que pide la guía.

  zero_shot        -> solo la instrucción y la pregunta, sin ejemplos.
  few_shot         -> la instrucción + 2 ejemplos de pregunta/respuesta para que el modelo imite el formato.
  chain_of_thought -> se le pide al modelo razonar paso a paso antes de recomendar.

En las 3 técnicas se inserta el CONTEXTO recuperado por el RAG (las canciones del catálogo).
"""

TECHNIQUES = ("zero_shot", "few_shot", "chain_of_thought")

SYSTEM_INSTRUCTION = (
    "You are the music assistant of Enlace Sonoro, a music player app. "
    "Recommend songs ONLY from the catalog provided in the prompt. "
    "Never invent songs that are not in the catalog. "
    "If no song fits the request, say so honestly. "
    "Answer in the same language the user writes in."
)

FEW_SHOT_EXAMPLES = """Example 1
Catalog:
- [id 10] "Weightless" by Marconi Union (genre: Ambient, 8:09)
- [id 11] "Gasolina" by Daddy Yankee (genre: Reggaeton, 3:12)
User: Quiero algo para dormir
Assistant: Te recomiendo "Weightless" de Marconi Union (Ambient): es lenta y suave, ideal para dormir. "Gasolina" no encaja porque es muy enérgica.

Example 2
Catalog:
- [id 20] "Thunderstruck" by AC/DC (genre: Rock, 4:52)
- [id 21] "Clair de Lune" by Debussy (genre: Clasica, 5:05)
User: Music for the gym
Assistant: I recommend "Thunderstruck" by AC/DC (Rock): its fast rhythm keeps your energy up while training."""


def build_prompt(technique: str, question: str, context: str) -> str:
    if technique == "zero_shot":
        return (
            f"Catalog:\n{context}\n\n"
            f"User request: {question}\n"
            "Recommend the most suitable songs from the catalog and briefly explain why."
        )

    if technique == "few_shot":
        return (
            "Follow the style of these examples.\n\n"
            f"{FEW_SHOT_EXAMPLES}\n\n"
            "Now your turn\n"
            f"Catalog:\n{context}\n"
            f"User: {question}\n"
            "Assistant:"
        )

    if technique == "chain_of_thought":
        return (
            f"Catalog:\n{context}\n\n"
            f"User request: {question}\n\n"
            "Think step by step before answering:\n"
            "1. What activity or mood does the user describe?\n"
            "2. Which musical characteristics fit it (genre, energy, tempo)?\n"
            "3. Which catalog songs match those characteristics, and which do not?\n"
            "Then write your final recommendation with a short justification."
        )

    raise ValueError(f"Unknown technique: {technique}")
