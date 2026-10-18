# Nádir · Edición 2.4.0

Aventura para Mothership 1.2. Libro completo de 91 páginas y material de juego de 19 páginas.

La maquetación conserva el formato de revista científica, los pies de figura y el atlas. Se han corregido los saltos entre títulos y contenido, las tablas que abrían huecos en las columnas y los encabezados de las fichas. Se añaden 18 ilustraciones reutilizadas sin repetirse y tres esquemas en los espacios libres. Los planos de superficie se presentan apaisados.

La revisión conserva reglas, cifras, identificadores y estructura de la aventura original 2.3.0: 42 diarios, 190 páginas, 31 actores, 17 objetos y 28 escenas. Hay 106 páginas de diario con texto revisado. Los informes adjuntos registran la comparación y la comprobación de 238 títulos, integridad del texto e imágenes únicas.

## Actualización de Foundry

La versión 2.4.0 incorpora una actualización automática de los textos originales al entrar el Guardián. Solo sustituye campos que coinciden con las versiones originales conocidas. Conserva los textos personalizados y guarda una copia de los campos sustituidos. No modifica heridas, inventario, escenas, tokens, relojes ni progreso de la partida. No requiere reimportar la aventura.

Las comprobaciones de actualización cubren notas personalizadas, estadísticas, inventario, copia anterior, reintento tras fallo, permisos e idempotencia. Son pruebas automatizadas con documentos simulados; no se ha importado ni modificado un mundo del usuario.

## Fuentes

Los capítulos editables están en docs/texto. tools/build_editorial.py produce ambos PDF; tools/build_foundry.py genera la aventura; scripts/build.mjs compila el compendio y el ZIP. La publicación adjunta ambos PDF, el manifiesto y el módulo instalable.
