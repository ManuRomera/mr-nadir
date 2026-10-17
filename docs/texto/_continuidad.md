# Informe de continuidad

Revisión de coherencia de `docs/texto/*.md` contra el canon (`docs/biblia/NADIR-original.md`, `docs/biblia/BIBLIA-HORROR.md`, `docs/biblia/canon.json`). Regla aplicada: manda el original; las fichas se contrastan con `canon.json`. Ediciones mínimas y localizadas.

## Corregido

| Archivo | Línea | Antes | Después | Motivo (canon) |
|---|---|---|---|---|
| `00-presentacion.md` | 122 | «**Cuatro verdades:**» | «**Verdad:**» | El original (§18, resumen de una página) rotula «Verdad:» y enumera cinco hechos, no cuatro. |
| `06-acto-4.md` | 206 | «4–5 h **por trayecto**» | «4–5 h **ida y vuelta**» | El original (§11.0) dice «cuatro o cinco horas **entre ida y vuelta**»; además el propio doc (06:212) dice «cada viaje… cuatro o cinco horas». |

## Para decidir

| Archivo | Línea | Qué se observa | Sugerencia |
|---|---|---|---|
| `09-documentos.md` | 120 | «el cierre vino **cinco minutos** después». La tabla D05 marca 09:36 (salmuera) → 09:40 (orden de cierre) = 4 min, y el canon fija T+4 min. | Confirmar si es «cuatro minutos» (cierre = la orden de las 09:40) o reformular como «pocos minutos después». |
| `06-acto-4.md` | 120 | «si la **Fuga H-4** ha llegado a 4… **el refugio ya está en Degradado**». Mezcla el reloj C (agua, H-4) con el estado de R-3 (reloj A, CO₂), que son independientes (biblia 2.5 frente a 2.6). | Separar ambos disparadores: el sumidero depende de H-4=4; los síntomas de hipercapnia, de R-3 en Degradado/Crítico. |
| `09-documentos.md` | 13–19 (y 87, 242, 302) | Registro formal en «usted» («Entregue», «No convierta», «No pida»…) frente al «tú» del resto de la obra. Internamente es coherente, pero rompe el registro general. | Unificar a «tú» con el resto del libro. |
| `09-documentos.md` | 226 | D12 registra una «superposición con mensaje de servicio de M. Venn» en el **canal cerrado de alguaciles**, mientras D03 presenta el mensaje de Mara en «RADIO DE SERVICIO». | Aclarar si comparten frecuencia (superposición real) o si deben citarse como canales distintos. |

## Verificado sin hallazgos

- Cifras: 18 en C-7, 3 muertos en T0 (Serrat, Milena Tey, Teo Mahr), 13 en R-3, 2 en P-2; 77 de dotación, 6 campamentos; 12 presos + 4 alguaciles (1:3); R-3 = 10 presos + Mara + Duarte + Inés.
- Horas: T0 09:36; mensaje 09:48; cronología T−120…T+20; respuesta autónoma T+1…T+10.
- Relojes: R-3 ≈10 h (6 kg / 0,585 kg·h), cartucho +2 h; P-2 filtro 5 h y batería 6 h; H-4 1/6.
- Rutas: B-4→C-7 43 km / 2–2,5 h; atajo 1 h 35–2 h 10; Lince-6 6 plazas, 90 UE, 4 kg O₂, 0,22 kg/h; tabla de campamentos (8/43/260/480/700 km).
- Localizaciones [1]–[12] y documentos D01–D14: presentes y coherentes; el bloque de documentos respeta el original.
- Fichas: PNJ, criaturas y pregenerados coinciden con `canon.json` (Combate/Instinto/Salud/Heridas/Armadura y atributos/salvaciones).
- Las cuatro verdades se respetan en todos los archivos (Mara no provocó; los costreros no planean; el bypass de Ivo agravó, no originó; se pueden salvar las 15).
- IDs de figura/lámina/retrato usados una sola vez, sin duplicados; `fig-portada` sin uso.
