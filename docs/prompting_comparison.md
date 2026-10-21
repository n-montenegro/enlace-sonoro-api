# Prompting techniques comparison

Same requests sent to the `/api/v1/ai` endpoint with three prompting techniques.
Fill in the **Quality (1-5)** column after reading each answer (see criteria at the end).

| # | Request | Technique | Input tokens | Output tokens | Latency (ms) | Quality (1-5) |
|---|---|---|---|---|---|---|
| 1 | Recomiéndame canciones tranquilas para estudiar | zero_shot | 254 | 166 | 2075 | |
| 2 | Recomiéndame canciones tranquilas para estudiar | few_shot | 456 | 89 | 1541 | |
| 3 | Recomiéndame canciones tranquilas para estudiar | chain_of_thought | 301 | 373 | 2385 | |
| 4 | Quiero música para una fiesta con amigos | zero_shot | 212 | 140 | 2159 | |
| 5 | Quiero música para una fiesta con amigos | few_shot | 414 | 90 | 1559 | |
| 6 | Quiero música para una fiesta con amigos | chain_of_thought | 259 | 310 | 2368 | |
| 7 | Necesito canciones con mucha energía para el gimnasio | zero_shot | 252 | 173 | 2367 | |
| 8 | Necesito canciones con mucha energía para el gimnasio | few_shot | 454 | 101 | 1666 | |
| 9 | Necesito canciones con mucha energía para el gimnasio | chain_of_thought | 299 | 350 | 2471 | |
| 10 | Something relaxing to fall asleep | few_shot | 452 | 100 | 1751 | |

## Full answers

### 1. zero_shot — Recomiéndame canciones tranquilas para estudiar

¡Hola! Como asistente musical de Enlace Sonoro, te recomiendo las siguientes canciones de nuestro catálogo para estudiar:

1. **"Lofi Study Session"** de Chillhop Beats (Lo-fi): Es perfecta para estudiar porque el género lo-fi está diseñado específicamente para la concentración y crear un ambiente de fondo relajante sin distracciones.
2. **"Snowman"** de WYS (Lo-fi): Al igual que la anterior, pertenece al género lo-fi, ofreciendo un ritmo suave y tranquilo ideal para mantener el foco durante tus sesiones de estudio.
3. **"Weightless"** de Marconi Union (Ambient): Esta canción de ambient fue creada científicamente para inducir la relajación profunda y reducir la ansiedad, lo que la hace excelente para concentrarse en tareas largas.

### 2. few_shot — Recomiéndame canciones tranquilas para estudiar

Te recomiendo "Lofi Study Session" by Chillhop Beats (Lo-fi), "Snowman" by WYS (Lo-fi), "Clair de Lune" by Claude Debussy (Clasica), "Take Five" by The Dave Brubeck Quartet (Jazz) y "Weightless" by Marconi Union (Ambient): todas son relajantes y sin letras pesadas, perfectas para concentrarte mientras estudias.

### 3. chain_of_thought — Recomiéndame canciones tranquilas para estudiar

1. The user is asking for calm songs to study ("canciones tranquilas para estudiar").
2. This requires genres and tracks that are relaxing, ambient, instrumental, or focused on concentration (such as Lo-fi, Classical, Ambient, or soft Jazz) to avoid distractions while studying.
3. Reviewing the catalog:
   - "Lofi Study Session" by Chillhop Beats (Lo-fi): Perfect for studying (literally in the title).
   - "Snowman" by WYS (Lo-fi): Calm and good for background focus.
   - "Clair de Lune" by Claude Debussy (Clasica): Calm, classical, great for concentration.
   - "Take Five" by The Dave Brubeck Quartet (Jazz): A bit more upbeat/rhythmic, but still chill.
   - "Weightless" by Marconi Union (Ambient): Extremely relaxing, designed to reduce stress and aid focus.

Final recommendation:

¡Hola! Como asistente musical de Enlace Sonoro, aquí tienes algunas canciones tranquilas de nuestro catálogo que son perfectas para estudiar y concentrarte:

- **"Lofi Study Session"** por Chillhop Beats (Lo-fi): Su nombre lo dice todo, es ideal para mantener la concentración.
- **"Snowman"** por WYS (Lo-fi): Un tema suave y relajante para acompañar tus horas de estudio.
- **"Clair de Lune"** por Claude Debussy (Clásica): Una pieza clásica hermosa, delicada y tranquila.
- **"Weightless"** por Marconi Union (Ambient): Considerada una de las canciones más relajantes del mundo, perfecta para entrar en un estado de máxima concentración. 

¡Espero que te ayuden con tus estudios!

### 4. zero_shot — Quiero música para una fiesta con amigos

¡Hola! Para una fiesta con amigos en Enlace Sonoro, te recomiendo las siguientes canciones de nuestro catálogo:

*   **"Gasolina" de Daddy Yankee** (Reggaeton): Es perfecta para encender la fiesta y poner a todos a bailar con su ritmo urbano tan enérgico.
*   **"Levels" de Avicii** (Electronica): Ideal para mantener la energía alta y vibrante con un gran ambiente de baile.
*   **"Blinding Lights" de The Weeknd** (Pop): Un éxito moderno, muy bailable y pegadizo que le encantará a todos tus amigos.

¡Que disfruten mucho de la fiesta!

### 5. few_shot — Quiero música para una fiesta con amigos

Te recomiendo "Gasolina" de Daddy Yankee (Reggaeton) y "Levels" by Avicii (Electronica): sus ritmos enérgicos son ideales para animar una fiesta con amigos. También puedes poner "Blinding Lights" de The Weeknd (Pop) para mantener el ambiente arriba. "Pedro Navaja" no encaja tan bien porque es un tema de salsa más narrativo y pausado para bailar de otra forma.

### 6. chain_of_thought — Quiero música para una fiesta con amigos

1. The user wants music for a party with friends ("música para una fiesta con amigos").
2. This calls for high-energy, upbeat, and danceable music suitable for socializing and dancing, such as Reggaeton, Pop, or Electronica.
3. Matching songs from the catalog:
   - "Gasolina" by Daddy Yankee (Reggaeton - perfect for a party).
   - "Blinding Lights" by The Weeknd (Pop - upbeat and energetic).
   - "Levels" by Avicii (Electronica - high energy, great for dancing).
   - "Pedro Navaja" by Ruben Blades (Salsa - can work for dancing, but the others fit a modern party vibe slightly better; however, it's still festive. I will recommend the highest energy tracks).

¡Hola! Como asistente de Enlace Sonoro, te recomiendo estas canciones de nuestro catálogo que son perfectas para animar una fiesta con amigos:

- **"Gasolina" de Daddy Yankee** (Reggaeton) - Ideal para poner a todos a bailar con un ritmo urbano inconfundible.
- **"Blinding Lights" de The Weeknd** (Pop) - Un éxito enérgico y bailable que le dará un toque moderno a la reunión.
- **"Levels" de Avicii** (Electronica) - Con una energía vibrante, perfecta para mantener el ánimo alto.

¡Disfruta de la fiesta con Enlace Sonoro!

### 7. zero_shot — Necesito canciones con mucha energía para el gimnasio

¡Hola! Soy tu asistente musical en Enlace Sonoro. Para tu entrenamiento en el gimnasio, te recomiendo las siguientes canciones del catálogo que tienen muchísima energía:

- **"Thunderstruck" de AC/DC**: Es un tema de rock puro con un ritmo de guitarra implacable y una intensidad creciente que te dará ese impulso de adrenalina perfecto para levantar pesas o hacer cardio pesado.
- **"Levels" de Avicii**: Al ser un temazo de electrónica con un ritmo rápido y eufórico, es ideal para mantener el ritmo alto durante una sesión de cardio o running.
- **"Gasolina" de Daddy Yankee**: Un clásico del reggaeton con un beat bailable y sumamente enérgico, perfecto para mantener la motivación a tope.

¡Espero que disfrutes tu entrenamiento con estas recomendaciones!

### 8. few_shot — Necesito canciones con mucha energía para el gimnasio

Te recomiendo "Levels" de Avicii (Electronica) y "Thunderstruck" por AC/DC (Rock): sus ritmos enérgicos son ideales para mantenerte activo durante el entrenamiento. "Gasolina" de Daddy Yankee (Reggaeton) y "Blinding Lights" de The Weeknd (Pop) también tienen mucha energía y funcionan muy bien para el gimnasio. "Bohemian Rhapsody" no encaja tan bien porque tiene cambios de ritmo muy variados y pausados.

### 9. chain_of_thought — Necesito canciones con mucha energía para el gimnasio

1. El usuario busca canciones con mucha energía para entrenar en el gimnasio.
2. Para el gimnasio, son ideales las canciones con un ritmo rápido, enérgico y estimulante (como el rock enérgico, la electrónica bailable o el reggaeton).
3. Evaluando el catálogo:
   - "Thunderstruck" de AC/DC (Rock): Excelente para entrenar por su energía y potencia.
   - "Levels" de Avicii (Electronica): Muy bailable y con una vibra sumamente enérgica, perfecta para cardio.
   - "Gasolina" de Daddy Yankee (Reggaeton): Ritmo acelerado y motivacional.
   - "Blinding Lights" de The Weeknd (Pop): Ritmo rápido y bailable.
   - "Bohemian Rhapsody" de Queen: Tiene momentos muy enérgicos, pero su estructura es muy cambiante, aunque se puede incluir.

¡Hola! Soy tu asistente de música en Enlace Sonoro. Para darlo todo en el gimnasio y mantener la energía al máximo, te recomiendo las siguientes canciones de nuestro catálogo:

- **"Thunderstruck" de AC/DC**: Energía pura de rock clásico para empezar con fuerza.
- **"Levels" de Avicii**: Electrónica perfecta con un ritmo vibrante para mantenerte a tope durante el cardio.
- **"Gasolina" de Daddy Yankee**: Un reggaeton con un ritmo rápido ideal para motivarte a moverte.
- **"Blinding Lights" de The Weeknd**: Un pop con una vibra acelerada excelente para mantener el paso.

¡Que tengas un excelente entrenamiento!

### 10. few_shot — Something relaxing to fall asleep

Te recomiendo "Weightless" by Marconi Union (Ambient): is lenta y suave, ideal para dormir. "Lofi Study Session" by Chillhop Beats (Lo-fi), "Snowman" by WYS (Lo-fi), "Clair de Lune" by Claude Debussy (Clasica) y "Take Five" by The Dave Brubeck Quartet (Jazz) también son tranquilas, pero "Weightless" fue específicamente diseñada para reducir la relajación y el estrés.

## Evaluation criteria

- **Grounding:** recommends only songs that exist in the catalog (no invented songs).
- **Relevance:** the songs fit the requested mood or activity.
- **Justification:** explains why each song fits.
- **Format and length:** clear and concise answer.
