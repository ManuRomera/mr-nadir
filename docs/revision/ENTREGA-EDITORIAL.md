# Nádir · Edición editorial

Revisión completa sobre el módulo e3b03a3 (2.3.0).

## Entrega

- Aventura revisada: 87 páginas, identidad de revista científica, atlas único e índice navegable.
- Material de juego: 18 páginas con hojas, documentos recortables y planos.
- Módulo compilado: 42 diarios, 190 páginas, 31 actores, 28 escenas y sus herramientas originales.
- Fuentes de todos los capítulos, las 25 lecturas de escena y el guion.

## Qué se ha revisado

Apertura centrada en la llamada; lugares descritos por lo que se percibe y se descubre; PNJ con peticiones y conductas reconocibles; finales ajustables al resultado real. Se han reducido explicaciones defensivas y repeticiones. El artículo del costrero mantiene el registro científico. Las tablas y los documentos probatorios conservan su redacción.

El PDF añade cuatro esquemas y cinco ilustraciones reutilizadas, con pies de figura. Cada ilustración y cada plano aparecen una sola vez en el volumen principal.

Se han aclarado discordancias de presentación: el inicio del guion precede a la llamada; R-3 tiene tres heridos; los síntomas de CO₂ dependen del reloj; la autonomía de Limen se compara con el consumo humano bajo esfuerzo. Las reglas y sus cifras permanecen intactas.

## Compatibilidad

Comparación contra la aventura del repositorio original: solo cambian el contenido de páginas de diario y las biografías/descripciones de actores. Todos los identificadores, nombres y orden de secciones, botones, escenas, regiones, actores, objetos, estadísticas, tablas, macros, listas de reproducción y carpetas permanecen iguales. Los archivos de funcionamiento y los recursos existentes coinciden con los originales.

105 páginas de diario contienen texto revisado. El informe compatibilidad-editorial.json registra las comprobaciones. El compendio compilado coincide con la aventura validada y el ZIP ha pasado su comprobación de integridad. No se ha ejecutado una importación en Foundry.

## Uso

La edición está preparada en una copia independiente. El módulo instalado y las partidas existentes siguen intactos. El ZIP contiene el mismo módulo 2.3.0 con sus textos revisados, listo para una prueba en un mundo aparte. En mundos ya importados, cambiar los archivos del módulo conserva los datos del mundo y sus diarios importados; el compendio contiene la edición nueva.

No se ha publicado una release ni se han enviado cambios a GitHub.

## Reproducción

La copia de fuentes incluye arte y planos de apoyo. Las dependencias del módulo se declaran en package.json. tools/build_foundry.py genera la aventura; scripts/build.mjs compila el compendio y el ZIP; tools/build_editorial.py genera ambos PDF y aplica las láminas de cierre. Los generadores originales del módulo permanecen intactos.
