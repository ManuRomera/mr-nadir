# Informe de revisión · Nádir: Sangre bajo el hielo (edición revisada)

::: resumen
Registro de la revisión integral de la aventura a partir del PDF ilustrado de 111 páginas y de su proyecto editable (docs/texto). Recoge las contradicciones y fallos encontrados con su gravedad, la corrección aplicada y cómo se comprobó; la validación matemática de los tres relojes; quince simulaciones de rescate ejecutadas con el simulador del expediente; la comprobación contra el reglamento oficial de Mothership 1e; los criterios de aceptación y lo que no se ha podido verificar.
Palabras clave: revisión, continuidad, relojes, simulación, Mothership 1e, criterios de aceptación
:::

## Alcance y método

**Fuentes.** El PDF `Nadir-Sangre-bajo-el-hielo-ilustrado.pdf` (111 páginas, generado el 17-10-2026) se maquetó desde el proyecto editable del módulo `mr-nadir`: los capítulos en Markdown de `docs/texto/`, el canon de fichas `docs/biblia/canon.json`, los planos de `tools/maps.py` y el maquetador `tools/build_pdf.py`. Al disponer del proyecto editable, la revisión se aplicó sobre él y se reconstruyó la maquetación original, conservando el diseño de revista científica, la tipografía, las ilustraciones, los retratos y los planos.

**Reglamento.** Se contrastaron las mecánicas con el *Player's Survival Guide* v1.2 y el *Warden's Operations Manual* v1.2 de Mothership 1e, y después, a petición de Manu, con la **Guía de supervivencia del jugador v1.2 en español** y la **Guía del Warden en español** (HTML). La edición española es la v1.2 sin cambios de reglas; solo difiere la terminología (ver «Verificación contra la edición española»).

**Herramientas nuevas.** `tools/relojes.py` simula los relojes minuto a minuto y contiene las quince simulaciones de este informe con una comprobación automática (las tres secuencias de referencia deben salvar a todos; la línea sin intervención debe perder el sello de R-3 hacia las 20:05). El Panel de emergencia de Foundry (`js/nadir.js`) aplica las mismas reglas; se comprobó que da las mismas cifras que el simulador. `tools/plano_operativo.py` genera el plano operativo de C-7.

**Orden de trabajo seguido:** auditoría completa de los once capítulos; registro de problemas; rediseño de los sistemas (relojes, recursos, tiempos, rutas, refuerzos) y su simulación; reescritura narrativa (PNJ, PJ, horror, conflictos); herramientas de mesa y documentos; reconstrucción y verificación visual del PDF.

## Registro de problemas y correcciones

Gravedad: **crítica** (impide jugar o rompe la coherencia del rescate), **alta** (contradicción visible o regla ambigua que obliga a improvisar algo esencial), **media** (incoherencia menor o problema de usabilidad), **baja** (estilo o detalle).

### Relojes, cronología y viabilidad

| # | Problema | Gravedad | Sección | Corrección | Justificación | Comprobación |
|---|---|---|---|---|---|---|
| 1 | Nadie en R-3 tenía trajes y el libro no decía cuántos había en el complejo: la evacuación de quince personas por galerías sin aire no era ejecutable con los datos dados | Crítica | Acto IV, logística | Recuento explícito de trajes (4 de B-4, 6 en el vestuario de C-0, 2 de escape en R-3, 1 en P-2, 6 del rover 2) y regla de qué rutas admiten trajes de escape | Sin trajes no hay rescate verificable | Simulaciones 1–5: el recuento cubre a los quince con el rover 2, o con viajes de ida y vuelta por E-1 sin él |
| 2 | La mochila del traje (90 min de esfuerzo) hacía imposible la ruta alta (1 h 30–2 h 30 solo de ida) | Crítica | Rovers, trajes | Traje de faena: perfil del *vaccsuit* del PSG con mochila de 4 h en esfuerzo y 6 h en reposo, recambios en C-0 y en el rover | El plan 2 del propio libro no se podía ejecutar; el PSG da 12 h a un *vaccsuit*, la cifra intermedia conserva la tensión de las umbilicales | Simulación 4 (portillo) |
| 3 | Reloj C (H-4) ambiguo: «sube si la bomba se para 30 min» no decía si era acumulativo, qué pasaba a 60 o 90 min ni cuándo se volvía irreversible | Crítica | Relojes | Regla exacta: +1 por cada 30 min seguidos de bomba parada con V-12 abierta (60 con el alivio restituido); efectos concretos por nivel; a 6, el sello de R-3 falla en 120 min | El original obligaba a improvisar la consecuencia esencial | Tabla 30/60/90/120/150 min; simulación «sin intervención» |
| 4 | No había una relación definida entre V-12, la bomba y H-4: se podía «cerrar V-12» sin saber si la bomba seguía haciendo falta | Alta | Acto III, V-12 | Con V-12 cerrada la bomba deja de ser necesaria y H-4 baja 1 por hora | Hace que la decisión técnica central tenga efecto calculable | Simulaciones 1, 2, 3, 9 |
| 5 | La bomba de P-2 no tenía límite propio salvo la batería; el depósito de decantación (descrito como «subiendo») nunca se llenaba | Media | P-2 | El depósito se llena hacia las 02:40 si la bomba trabaja toda la noche con V-12 abierta | Coherencia física; explica por qué «estabilizar y esperar» exige cerrar V-12 | Simulaciones 4 y 5 |
| 6 | «Filtración industrial activa» detenía el reloj de R-3, pero no existía ningún equipo con ese nombre | Alta | Reloj A | Depurador portátil DP-40 del almacén de Bastión: llega con el rover 2 si se pide y gasta 1 UE/h | Recurso inexistente | Simulación 5 |
| 7 | El estado Crítico de R-3 no tenía consecuencias mecánicas finales: nunca moría nadie por CO₂ | Alta | Reloj A | Estados Crítico, Grave y Colapso basados en la regla de soporte vital del PSG 33.1 ([−], salvación de Cuerpo, salvación de Muerte), con horas exactas | Mantener la letalidad sin muertes arbitrarias | Simulación «prioriza P-2» (una hora en Crítico sin muertes); línea sin intervención |
| 8 | P-2 no tenía consecuencias definidas tras agotar el filtro ni regla de qué pasa si nadie atiende la bomba | Alta | Reloj B | Estados de aire de P-2 y regla de atención: sin automatismo, la bomba se desceba a los 45 min sin nadie consciente | Hace que el aire de P-2 importe para R-3 | Simulación 4 (versión sin aire en P-2: H-4 llega a 6 hacia las 19:50) |
| 9 | Cartucho de rover: «+2 h para R-3» se aplicaba igual con trece que con seis personas, y no se sabía cuánto daba a P-2 | Media | Relojes | Cuenta en kilos y consumo por ocupante; un C-12 da 2 h a R-3 con trece y unas 13 h a P-2 | El reparto de cartuchos se convierte en una decisión real | Tabla de consumo; simulaciones |
| 10 | Energía: el rover gastaba unas 42 UE en llegar y otras tantas en volver, sin ningún punto de recarga en C-7; con 90 UE el regreso era imposible si se usaba el rover para algo más | Alta | Rovers, energía | Banco de emergencia de C-0 (48 UE), batería portátil (12), batería industrial (30), consumos de cada tarea | Los recursos no daban para la solución que el libro proponía | Simulación de referencia: el rover vuelve con 18 UE de margen tras recargar 20 |
| 11 | Viaje de refuerzos incoherente: «2–3 h en salir y una o dos horas adicionales» desde Bastión, cuando C-7 está a 43 km de B-4 y Bastión a 8 km más | Alta | Acto I, refuerzos | Bastión–C-7: 51 km, 2 h 30–3 h. Preparación 2 h con lista justificada, 3 h sin ella | Distancias de la propia tabla de población | Tabla de refuerzos (llegada 14:45 si se piden a las 09:58) |
| 12 | «Viaje C-7 ↔ Bastión 4–5 h ida y vuelta» incompatible con lo anterior | Media | Acto IV | 5–6 h ida y vuelta | Ídem | — |
| 13 | El juego empezaba «a las 09:48 en B-4» pero el temblor de las 09:36 se sentía en la escena 2 | Media | Acto I | La partida empieza unos minutos antes de las 09:36; temblor a las 09:36, mensaje a las 09:48 | Cronología consistente | Guía rápida, Acto I, cronología |
| 14 | El repetidor R-12 perdía la alimentación a las 09:44 (D05) pero transmitía el mensaje de Mara a las 09:48 | Alta | Verdad, D03, D05 | R-12 pierde la línea de C-7 a las 09:44 y aguanta cuatro minutos con su batería de respaldo degradada; se apaga a las 09:48:40 | Contradicción entre documentos | D03, D05, D12-A, información de Elia |
| 15 | Muertes «en T+7 min» frente a un Serrat atrapado a las 09:39 y una radio que abre a las 09:39:02 | Media | Verdad | Teo 09:36, Milena 09:38, Serrat 09:39 | Ídem | Cronología inmutable |
| 16 | Si se ignoraba R-12, desde C-7 se podía seguir hablando con Bastión según algunos pasajes y no según otros | Media | Actos II–III | Sin R-12 no hay enlace C-7–Bastión; B-4 sí llega directo | Consecuencia anunciada de saltarse el repetidor | Tabla de refuerzos |
| 17 | Los cartuchos y filtros «junto al portillo» eran un recurso sin cantidad ni uso | Media | Portillo | Armario de servicio con 2 C-12, conocido por Celia Brax | Recurso existente en el texto, ahora utilizable | Simulaciones 3 y 4 |
| 18 | No existía una cronología de referencia ni una herramienta de recálculo | Crítica | — | Capítulo «Relojes, recursos y cronología» con la secuencia comprobada y el método de recálculo; Hoja de relojes; simulador; Panel de Foundry | Petición explícita | Simulación de referencia (sin muertes) |

### Continuidad y documentos

| # | Problema | Gravedad | Sección | Corrección | Justificación | Comprobación |
|---|---|---|---|---|---|---|
| 19 | D12 (registro del canal de Serrat) llegaba hasta las 16:04 y podía entregarse al reparar R-12 hacia las 11:30, anticipando cinco horas de hechos | Crítica | Documentos | D12-A: búfer de R-12 (09:39–09:48:40, lo único que el repetidor pudo retransmitir). D12-B: registro de C-0 en cuatro tramos horarios que solo se entregan cuando han terminado, con cierres alternativos si el agua cubre el traje o si recuperan la radio | Ningún documento puede anticipar el futuro | Comprobado tramo a tramo contra la cronología |
| 20 | D14 (diario de Quiroga) incluía entradas hasta las 18:00, la batería «al cuarenta por ciento» a las 15:00 (se agota a las 15:36) y un deterioro mental que no dependía de lo ocurrido | Crítica | Documentos | Diario por tramos: parte base hasta las 13:20 y variantes condicionadas (contacto, sin aire, con aire, bomba parada, Crítico) | Los registros reflejan las intervenciones de los jugadores | Variantes cruzadas con los estados del reloj B |
| 21 | Lisán: «nunca hubo búsqueda» en un capítulo frente a «dos equipos durante setenta y dos horas» en D13 | Alta | Contexto, D13 | La contradicción se vuelve prueba: el expediente asigna dos equipos sin vehículo; el nuevo D15 (registro de vehículos de Bastión) muestra que no salió ningún rover; el propio expediente sitúa a Lisán en las galerías y lo declara muerto «en superficie». Firma: Vidal | Diferencia documental explicable y con peso (Vidal, Ivo) | Matriz de pistas; Acto IV |
| 22 | D04 atribuía la orden 517-J a un «jefe técnico de C-7 fallecido durante la rotura», un cuarto muerto incompatible con el balance de tres | Alta | D04, Verdad | La firma Anselmo Rius (fuera de turno en Bastión) con visto bueno de Oria; la ejecutan Ulma Senn y Teo Mahr | Balance de dieciocho personas | Comprobación del reparto en PNJ y balance |
| 23 | D03 en «radio de servicio» y D12 en «canal cerrado de alguaciles» con superposición a la misma hora | Media | Documentos | Ambos en el canal de alguaciles, banda C | Coherencia | D03, D12-A |
| 24 | Registro formal de «usted» en las notas de documentos frente al «tú» del resto | Baja | Documentos | Unificado a «tú» | Informe de continuidad anterior | Búsqueda de «use», «conserve», «obligue» |
| 25 | El costrero del filtro abandonado aparecía en una grieta de la superficie al vacío, contra las propias reglas de la especie | Alta | Acto II | El animal asoma por dentro de la tubería, que conserva gas húmedo de la bolsa inferior; los cordones de fuera están liofilizados por el vacío | Se mantiene la ilustración (el gusano está en la boca de la tubería) | Comparado con la imagen |
| 26 | Viento en la superficie («el viento arrastra hielo contra el casco», epílogo del final C), tos oída desde fuera del complejo, «junta que gotea CO₂» en el rover | Alta | Acto IV, Acto II | Sustituidos por fenómenos compatibles con el vacío: balizas parpadeando, tos por la radio local, crujidos transmitidos por el chasis | Superficie sin atmósfera | Búsqueda de «viento», «polvo», «brisa», «tose» |
| 27 | Pie de foto «bajo un cielo blanco de hielo» en una imagen de cielo negro, y descrita como «el segundo rover alejándose» sin rover | Media | Finales | Pie corregido a lo que muestra la imagen | Coherencia texto–ilustración | Imagen revisada |
| 28 | La ilustración de R-12 muestra luces encendidas en un repetidor «sin corriente» | Baja | Acto II | Son las balizas de navegación, con pila propia; el módulo de radio está muerto | Se conserva la imagen | Imagen revisada |
| 29 | Salcedo aparecía sentado fuera de su vehículo sin que se dijera de qué respiraba ni cuánto tiempo | Media | Acto II | Conectado al umbilical de su vehículo, que los mantiene a él y a su ayudante hasta las 15:30; el rover 2 puede recogerlos | Evita una muerte sin causa o un rescate gratuito | Tabla de refuerzos |
| 30 | La «carabina» y la «pistola» reglamentarias no correspondían a armas del PSG y su daño era «según PSG» | Media | PNJ, PJ | Subfusil (SMG del PSG, 2d10) y revólver (1d10+1) | Compatibilidad con 1e | Tabla de armas del PSG |
| 31 | El preso herido de fractura no tenía nombre y los tres heridos de R-3 no estaban definidos | Media | PNJ | Román Kes (tibia rota, no camina), Osian Brev (hemorragia contenida), Inés Calder (pierna) | Logística de evacuación | Estado de supervivientes |
| 32 | Las fichas de PJ aparecían dos veces (capítulos 01 y 10) con textos distintos | Media | Contexto, Cuadrilla | Un único capítulo de PJ; el 01 remite a él | Redundancia y riesgo de contradicción | — |
| 33 | La población: el androide «en Bastión atendiendo otra incidencia» con cuatro jugadores no cuadraba con los nueve de B-4 | Baja | Reparto | Los nueve de B-4 son siempre los mismos; quien no se juega se queda en B-4 (Elia en la radio, Limen custodiando al preso Bruno Isern) | Cifras de población | Tabla de población y reparto |
| 34 | La ficha de Elmo Serrat se maquetaba como si su descripción fuera una línea de estadísticas | Baja | Acto III | Convertida en texto | Defecto de maquetación ya presente en el original | Revisión visual |
| 35 | Los registros dentro de los documentos se maquetaban como un solo párrafo | Media | Maquetación | Cada línea de un documento es un renglón propio | Legibilidad de D05, D12, D14 | Revisión visual |

### Mothership 1e

| # | Problema | Gravedad | Corrección | Comprobación |
|---|---|---|---|---|
| 36 | Limen (Android) tenía Miedo 28: la clase da +60 a la salvación de Miedo | Alta | Miedo 80; Cordura 28 y Cuerpo 30 dentro de rango; −10 a Velocidad | PSG, creación de personajes |
| 37 | Gael tenía Miedo 53 (máximo posible para un Marine: 50) y la habilidad «Primeros auxilios», que no existe en 1e | Media | Miedo 48; Atletismo en lugar de Primeros auxilios | PSG |
| 38 | Vera tenía Combate 24 y Miedo 31 fuera de rango; Darío y Elia, Combate 26 y 25 por debajo del mínimo de un Teamster (+5 a todo) | Media | Ajustados a los rangos | PSG |
| 39 | Las habilidades no seguían los paquetes de clase (Teamster sin Equipo industrial ni Gravedad cero; Android sin Lingüística ni Matemáticas; Scientist sin habilidad maestra) | Media | Paquetes de clase completos con sus bonificaciones | PSG, paso 7 |
| 40 | Las mordeduras no aplicaban la regla de armadura: un traje de PA 3 nunca se perforaba | Alta | PSG 28.3: el daño ≥ PA destruye la armadura; el traje perforado se despresuriza en 1d5 asaltos; después rige el PSG 33.1 | PSG |
| 41 | «Fallo de tirada = Estrés y Pánico» mezclados | Baja | Fallo: +1 de Estrés; Pánico con críticos o por circunstancias del PSG | PSG, «Panic Checks» |
| 42 | Las reglas propias del escenario no estaban marcadas como tales | Media | Lista explícita de reglas de escenario en «Reglas de mesa» | — |

### Narrativa, personajes y estilo

| # | Problema | Gravedad | Corrección |
|---|---|---|---|
| 43 | Los PNJ colaboraban casi todos de forma automática; los conflictos eran descriptivos | Alta | Cada PNJ con lo que quiere, teme, sabe, sacrificaría, nunca aceptaría, cómo actúa bajo presión, cómo cambia y qué decide por su cuenta. Siete conflictos emergentes en el Acto IV (P-2, Ivo, orden de salida, recursos, custodia, culpa, órdenes contra necesidades). Nuevos PNJ con agenda: Román Kes, Ulma Senn, Osian Brev; Mar Haddi con una tentación concreta |
| 44 | La respuesta autónoma de los PNJ era una lista de tendencias sin efecto en los relojes | Alta | Tabla con horas y condiciones: Duarte esposa a Kroll a las 12:36; Román empieza el rumor; Mara hace la purga; Ivo intenta llegar a V-12 por el túnel a las 15:50 (con tirada y consecuencias); Yusef a la cámara de servicio |
| 45 | Los PJ tenían motivo y vínculo, pero no decisiones propias; el androide era un refuerzo táctico | Alta | Cada PJ con información exclusiva y una decisión que solo él puede tomar. Limen: órdenes de Vidal por el canal institucional, testigo neutral del orden de salida, el que puede quedarse el último. Cada perfil dice qué pasa si no se juega |
| 46 | Los encuentros con la fauna se reducían a «apagar todo y esperar» | Alta | «La colonia responde a vuestras obras»: seis reacciones derivadas de la regla de sellado (V-12 → migración; cerrar la fuga de la cría → el portillo se encostra; igualar E-1 → sellan el marco; L-4 usada → se llena; la portilla ciclada → se vuelve a sellar; sangre → rejilla) y el resellado natural de J-17. Escalera del horror en nueve peldaños |
| 47 | La biología se explicaba entera en el artículo del costrero y se repetía en cada capítulo | Media | Tabla de ritmo del descubrimiento con varias fuentes por pieza |
| 48 | Investigación y rescate iban por separado | Alta | Tabla «Lo que se descubre mientras se trabaja»: cada descubrimiento cambia una decisión práctica |
| 49 | Repeticiones: doce recuadros de «Principios de dirección», 44 construcciones «no es X, es Y», 21 «no fuerces / no conviertas», 5 «porque toca» | Media | Seis principios expuestos una vez; 9, 1 y 0 apariciones respectivamente. Texto: de 47 900 a 42 300 palabras pese a los capítulos nuevos |
| 50 | Para dirigir una escena de C-7 había que consultar cuatro capítulos | Alta | Fichas operativas por localización con estado, personas (ficha en una línea), accesos, peligros, recursos, pistas, acciones con tiempo y coste, consecuencias, cambios por reloj y conexiones |
| 51 | El plano de C-7 era una planta de habitaciones sin atmósferas, agua, conducciones ni estados | Alta | Plano operativo nuevo (página completa) con atmósferas, zonas inundables según H-4, compuertas con estado, rutas, conducciones (línea de producción, drenaje, bypass, línea del actuador), equipos y accesos que cambian. La planta cuadriculada se conserva para Foundry |
| 52 | No había documentos imprimibles separados de las notas del Guardián | Media | Apéndice «Documentos imprimibles» generado automáticamente desde los recuadros de documento, y un PDF aparte de material de juego |

## Validación de los relojes

**R-3.** 6 kg de capacidad a las 09:36; 0,046 kg de CO₂ por persona y hora (13 × 0,046 = 0,6 kg/h). Agotamiento: 6 / 0,6 = 10 h → 19:36. Un C-12 (1,2 kg) da 2 h con trece. El oxígeno (30 kg) dura más de dos días con trece personas a unos 0,035 kg/h cada una, así que no es el factor limitante. Tras el agotamiento, los estados siguen la estimación de un refugio de unos 40 m³ (el CO₂ sube unos 0,75 puntos por hora): síntomas severos a las 3 h, inconsciencia a partir de las 6 h; se modela como Crítico, Grave y Colapso.

**P-2.** 0,46 kg; dos personas a 0,09 kg/h: 5 h → 14:36. Un C-12 da 13 h a dos personas. La bomba gasta 2 UE/h: 12 UE → 6 h → 15:36.

**H-4.** Sin intervención: bomba parada a las 15:36 → 2 (16:06) → 3 (16:36) → 4 (17:06) → 5 (17:36) → 6 (18:06) → sello de R-3 a las 20:06. El simulador da 20:05 por el redondeo de minutos de la batería.

**Banco de C-0.** 48 UE; 2 UE/h; sin extras, dura 24 h. Con V-12 (4) y E-1 (6) se agota hacia las 04:36: suficiente para la espera nocturna de la referencia (el segundo viaje sale hacia la 01:00).

**Rover 1.** Llega con unas 48 UE; alimentar la bomba 2 h cuesta 4; volver a Bastión cuesta unas 46. La referencia recarga 20 UE de la batería industrial y vuelve con margen.

## Simulaciones

Todas ejecutadas con `tools/relojes.py` (que contiene cada escenario). «Recursos» se refiere a lo consumido de la tabla de recursos. Los tiempos de tarea son los del capítulo de sistemas.

| # | Escenario | Decisiones clave | Tiempo hasta vaciar R-3 | Recursos | Relojes al final | Consecuencias | Bloqueos detectados y corrección |
|---|---|---|---|---|---|---|---|
| 0 | **Sin intervención** | Nadie llega | — | — | P-2 Colapso 19:36; H-4 6 a las 18:05 | Mueren Quiroga e Ivo (hipercapnia) y los trece de R-3 (fallo del sello, 20:05) si el intento de Ivo por el túnel falla | Sirve de línea base; si Ivo tiene éxito en su tirada, V-12 se cierra a las 17:15 y R-3 sobrevive hasta la hipercapnia (01:36) |
| 1 | **Referencia · Plan 1 (V-12 + E-1) · refuerzos pronto · supervivencia de los quince** | Refuerzos con lista a las 09:58; R-12 reparado; rover a la portilla; V-12 desde C-0; E-1 | 18:10 | 1 C-12 en P-2, 1 en R-3; 10 UE del banco; 4 UE del rover; 20 UE de batería industrial al rover | R-3 nunca pasa de Degradado (desde 16:40); H-4 0 desde 15:25 | Sin muertes; dos viajes a Bastión | Faltaba el recuento de trajes y la energía de regreso (problemas 1 y 10): corregidos y reverificados |
| 2 | **Tres PJ** | Ruta de R-12 sin reparar (refuerzos pedidos desde B-4 a las 10:05); Quiroga e Ivo ayudan en cuanto quedan libres | 19:30 | Ídem más 1 C-12 de Bastión | R-3 Estable al final; H-4 0 desde 15:55 | Sin muertes | Ninguna escena depende de un perfil: la mecánica la hacen Ivo y Quiroga cuando quedan libres |
| 3 | **Cinco PJ** | Tres frentes: P-2, V-12 a mano por la cría, portillo con cartuchos | 18:00 | 2 C-12 del armario + 1 del rover en R-3; 1 en P-2 | R-3 Estable todo el tiempo | Sin muertes; más plazas ocupadas en los rovers (dos viajes) | Con cinco PJ los rovers llevan menos evacuados: el segundo viaje es imprescindible |
| 4 | **Plan 2 (portillo)** | P-2 recibe aire y sigue atendida; evacuación de uno en uno por L-4 | 19:20 | 3 C-12 en R-3, 1 en P-2; batería industrial al final | El depósito de P-2 se llena a las 02:39 (C-7 se inunda después, ya vacío) | Sin muertes; la Atención de L-4 sube con cada ciclo | **Bloqueo real hallado:** sin aire en P-2, sus ocupantes quedan incapacitados, la bomba se desceba y H-4 llega a 6 hacia las 19:50, con R-3 aún ocupado. Corregido haciendo explícita la regla de atención y la advertencia en el plan |
| 5 | **Plan 3 (estabilizar y esperar)** | Energía y aire a P-2; cartuchos y depurador a R-3; V-12 cerrada por el equipo de Bastión a las 20:30 | No se evacúa esa noche | Depurador, batería industrial, 3 C-12 | Todo estable a las 08:00 | Sin muertes | **Bloqueo real:** si nadie cierra V-12, el depósito se llena a las 02:40 y H-4 sube de madrugada. Añadido al plan 3 y al Acto IV |
| 6 | **Plan creativo no previsto** | Carrete de cable del banco de C-0 a la bomba; dos purgas de R-3; V-12; E-1 | 19:45 | 9 UE del banco en la bomba + 6 de E-1; 12 kg de O₂ | El banco se agota hacia las 02:00 | Sin muertes; riesgo de fuego en R-3 tras la segunda purga | El banco se queda corto para la espera nocturna: el grupo tiene que salir antes o recargarlo; anunciado en el capítulo de energía |
| 7 | **Retirada sin relevo** | Batería portátil con automatismo y un C-12 en P-2; nadie pidió el rover 2 | — | 12 UE, 1 C-12 | Bomba parada 19:40; H-4 6 a las 22:09 | Mueren los trece de R-3 a las 00:09; Quiroga e Ivo, de madrugada | Resultado duro pero calculado; no hay muerte automática por retirarse: es la falta de relevo |
| 8 | **Evacuación parcial** | Se retiran a las 15:30 con Quiroga e Ivo; el rover 2 llegó y su equipo sigue guiado por radio | — (R-3 estabilizado) | 4 C-12, depurador, batería industrial | Todo estable al amanecer | Sin muertes | Requiere que el equipo de Bastión cierre V-12 antes de las 02:40 |
| 9 | **Refuerzos pedidos tarde** | Sin R-12 reparado no se puede pedir desde C-7; se piden al volver a cobertura; el rover 2 llega a las 18:00 | 19:30 | 5 C-12 en R-3, 1 en P-2 | R-3 Estable | Sin muertes, pero sin trajes extra hasta las 18:00: la evacuación por el portillo habría sido imposible; por E-1 se hace con viajes de ida y vuelta de trajes | Consecuencia anunciada en el Acto I |
| 10 | **Fallo de una reparación fundamental** | Cierre brusco de V-12 | 18:00 | Ídem referencia | H-4 sube a 2 y vuelve a 1 en una hora | Sin muertes; E-1 tarda más en igualarse | El fallo encarece; no bloquea |
| 11 | **Prioriza R-3** | Portillo con tres cartuchos; P-2 olvidada hasta las 16:50 | 19:30 | 3 C-12 en R-3 | H-4 llega a 3 (bomba parada 74 min); P-2 Degradado | Sin muertes por poco: con 30 minutos más de parada, H-4 4 y escena del sumidero | Funciona como advertencia: el reloj B castiga ignorar P-2 |
| 12 | **Prioriza P-2** | Todo en P-2 y V-12; llegan a R-3 a las 20:30 | 21:30 | 1 C-12 en P-2, 1 en R-3 | R-3 en Crítico casi una hora | Sin muertes, con salvaciones de Cuerpo en R-3 | El reloj A castiga ignorar R-3, pero tarda más: la decisión es real |
| 13 | **Separación del grupo** | El equipo de L-4 queda bloqueado 40 min por la colonia; el automatismo se queda sin hacer | 18:30 | Ídem referencia | Todo estable | Sin muertes; Quiroga e Ivo siguen cebando a mano | La regla de atención exige a alguien consciente en P-2 hasta que se cierre V-12 |
| 14 | **Descubrimiento temprano de la culpa de Ivo** | Vidal ordena detenerlo a las 14:20; Quiroga sola falla la tirada de Fuerza y la bomba se para 35 min | 18:40 | Ídem | H-4 sube a 2 a las 15:34; baja a 1 tras V-12 | Sin muertes; el coste de obedecer la orden es medible | Escena C-2 del Acto IV; Vidal cede ante el dato |

**Criterio obligatorio cumplido:** las simulaciones 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13 y 14 terminan con las quince personas vivas sin ayudas imposibles, recursos inexistentes, decisiones ocultas del Guardián ni tiempos manipulados. La 1 es la cronología de referencia publicada en el libro.

**Lo que las simulaciones no cubren:** el azar de las tiradas (se supone éxito en las tareas que no lo arriesgan y se modela el fallo en las 10 y 14), los encuentros con la colonia (se modelan como retrasos en la 13), y la duración en tiempo real de mesa, que depende del grupo.

## Verificación contra la edición española (18-10-2026)

Manu sospechó que los personajes seguían una versión anterior. Se comprobó personaje a personaje con la Guía de supervivencia v1.2 en español (hoja de personaje, árbol de habilidades, cargas, Pánico, heridas, oxígeno) y con la Guía del Warden:

- **Características y salvaciones.** Todas caen en rango tras aplicar los modificadores de clase (características 2d10+25, salvaciones 2d10+10; Marine +10 Combate, +10 Cuerpo, +20 Miedo y +1 Heridas; Androide +20 Intelecto, −10 a una característica, +60 Miedo y +1 Heridas; Científico +10 Intelecto, +5 a una, +30 Cordura; Tripulación +5 a todas y +10 a todas las salvaciones). Salud 1d10+10 (11–20), Estrés inicial 2, Heridas máximas 3, 2, 2, 2 y 3: correcto. Respuestas al trauma: correctas.
- **Habilidades.** El árbol del PDF (comprobado a 420 ppp) confirma las cadenas usadas: Geología → Ecología → Planetología; Maquinaria industrial + Reparaciones improvisadas → Reparación mecánica; Informática → Hacking; Entrenamiento militar → Armas de fuego. Los paquetes de clase están completos (Marine: 2 de clase + 1 experta; Androide: 3 de clase + 2 entrenadas; Científico: cadena maestra + 1 entrenada; Tripulación: 2 de clase + 1 entrenada + 1 experta).
- **Reglas.** Armadura (daño menor que los PA se ignora; igual o mayor la destruye), traje de vacío (PA 3, 12 h, descompresión en 1d5 asaltos), oxígeno (15 s y 1d5 min), soporte vital degradado, Pánico, Sangrado, tabla de heridas y salvación de Muerte: correctos.
- **Corregido por esta verificación.** (1) Terminología: clases Androide, Científico y Tripulación (en español el *Teamster* es «Tripulación»); habilidades Maquinaria industrial, Reparaciones improvisadas, Zero G, Conocimiento del Borde y Hacking; tipo de daño «Fuerza bruta»; «bastón aturdidor» en lugar de «porra eléctrica»; «bioscanner» en lugar de «escáner ambiental». (2) Mochila del traje: pasa de 4 h esfuerzo / 6 h reposo a **12 h normales / 4 h bajo esfuerzo**, que es lo que dicen la tabla de armaduras y el tanque de oxígeno del PSG; no cambia ninguna simulación porque todas cuentan el tiempo como esfuerzo. (3) Se precisa en la tabla de reglas cómo funcionan ventaja y desventaja (tirar dos veces) y que 90–99 siempre falla.
- **Sin cambio y por qué.** Los estados Crítico, Grave y Colapso de R-3 y P-2 siguen siendo una adaptación declarada del soporte vital del PSG 33.1 (el manual solo da «[−] a todo» y «salvación de Cuerpo o de Muerte»). Los PNJ de ficha corta usan el formato del propio manual para mascotas y criaturas (Combate, Instinto, Heridas con Salud entre paréntesis). La Guía del Warden no contiene reglas de combate que choquen con lo anterior; sus reglas de la casa (Heridas ablativas, Letalidad, etc.) no se usan.

## Ritmo y duración de mesa

| Acto | Tiempo de mesa estimado | Decisiones y descubrimientos principales |
|---|---|---|
| I | 45–60 min | Quién va, cuándo y cómo pedir refuerzos, qué cargar; primera pista orgánica |
| II | 45–75 min | Ruta, R-12, Salcedo, filtro abandonado, la radio de Serrat |
| III | 2 h 30–3 h 30 | P-2, V-12, E-1 o el portillo; nueve piezas de la verdad; reacciones de la colonia |
| IV | 1 h 30–2 h 30 | Siete conflictos, orden de salida, transporte, finales |

Total: 5 h 30–8 h 45. La previsión de 6–9 horas se mantiene.

## Mothership 1e: comprobado y no comprobado

**Comprobado en el PSG v1.2:** rangos de creación (2d10+25, 2d10+10, 1d10+10), modificadores y paquetes de habilidades de clase, respuestas al trauma, Estrés inicial 2, chequeos de Pánico, regla de armadura y destrucción, *vaccsuit* (PA 3, 12 h, despresurización en 1d5 asaltos), oxígeno (15 s y 1d5 min), soporte vital degradado, armas (SMG, revólver, porra eléctrica), tipos de herida.

**Prerrequisitos de habilidades:** verificados en el árbol de la edición española (ver arriba). **No comprobado:** no existe en el manual una regla específica de hipercapnia: la del escenario es una adaptación declarada de la de soporte vital.

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Todos los relojes funcionan de forma consistente | Sí: reglas exactas; simulador y panel de Foundry dan las mismas cifras |
| Los planes de rescate han sido simulados | Sí: cinco planes y diez pruebas adicionales |
| Existe al menos una solución verificable para salvar a los quince | Sí: cronología de referencia |
| Los recursos y tiempos de viaje permiten ejecutarla | Sí: trajes, energía, cartuchos y viajes contados |
| No hay registros que anticipen hechos futuros | Sí: D12 y D14 por tramos y variantes |
| Contradicciones de continuidad corregidas | Sí: 52 entradas del registro |
| Los PNJ actúan según motivaciones propias | Sí: fichas de motivación y respuesta autónoma con efectos |
| Los protagonistas tienen decisiones personales significativas | Sí: una por PJ |
| Las escenas ofrecen alternativas reales | Sí: cada ficha tiene varias acciones con coste |
| El horror aumenta sin vulnerar la biología | Sí: escalera del horror y reacciones derivadas de la regla de sellado |
| Se puede dirigir con tres, cuatro o cinco jugadores | Sí: simulaciones 1–3 y «si no se juega» |
| Las reglas están identificadas | Sí: lista de reglas de escenario y referencias al PSG |
| Planos y documentos utilizables | Sí: plano operativo a página completa; documentos imprimibles |
| Repeticiones innecesarias eliminadas | Sí: métricas en la entrada 49 |
| Se conserva la identidad visual y narrativa | Sí: misma maquetación, ilustraciones, retratos y voz |
| Los cambios no han provocado contradicciones nuevas | Revisado con búsquedas cruzadas y el simulador; la prueba definitiva es una partida real |
| Lista para una prueba de juego real | Sí, con las salvedades siguientes |

## Pendiente y no verificado

1. **Módulo de Foundry.** El guion de dirección, las lecturas y las escenas del módulo (`docs/v2/`) siguen redactados con las reglas anteriores; el paquete de Foundry no se ha regenerado, y el constructor numera los documentos por orden de aparición, lo que choca con los nuevos D12-A, D12-B y D15. El Panel de emergencia (`js/nadir.js`) ya aplica las reglas nuevas. Adaptar el resto es el siguiente paso natural.
2. **Prueba de juego.** Todo lo anterior está comprobado sobre el papel y con el simulador; falta una partida real, sobre todo para medir el tiempo de mesa del Acto III y la carga de los conflictos del Acto IV.
3. **Edición española:** verificada; los textos usan ya su terminología.
4. **Ilustraciones.** No se ha sustituido ninguna; dos se han justificado con texto (filtro abandonado y luces de R-12). No hay ilustración del atracadero ni del armario del portillo.
5. **Cifras de diseño ficticias** (tolerancias del costrero, autonomía de los trajes de faena, capacidad de los cartuchos) son convenciones del escenario, coherentes entre sí, no datos reales.

## Entregables

- `build/Nadir-Sangre-bajo-el-hielo.pdf`: la aventura revisada completa (copia en la carpeta de la aventura).
- `build/Nadir-Material-de-juego.pdf`: herramientas del Guardián, documentos imprimibles, hojas de PJ y planos.
- `docs/texto/*.md`: versión editable en Markdown (dos capítulos nuevos: «Relojes, recursos y cronología» y «Herramientas del Guardián»).
- `docs/revision/INFORME-DE-REVISION.md` y su PDF: este informe.
- `tools/relojes.py`, `tools/plano_operativo.py`, `js/nadir.js` (panel), `docs/biblia/canon.json` (fichas).
