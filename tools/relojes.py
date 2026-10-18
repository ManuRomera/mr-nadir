#!/usr/bin/env python3
"""Simulador de los relojes de «Nádir: Sangre bajo el hielo» (reglas revisadas, edición 3).

Recalcula R-3, P-2, Fuga H-4 y energía minuto a minuto desde T0 (09:36) a partir de una lista
de acciones con hora. Sirve para comprobar las simulaciones del informe y para que el Guardián
recalcule cuando la mesa se desvía.

Uso:  python3 tools/relojes.py            (todos los escenarios + comprobaciones)
      python3 tools/relojes.py referencia (uno solo, con traza cada 30 min)
"""
import sys

T0 = 9 * 60 + 36
CO2_PERSONA = 0.046          # kg/h por persona (13 personas ≈ 0,6 kg/h)
DEPOSITO_MIN = 1044          # minutos de bombeo hasta llenar el depósito de decantación (≈ 03:00)
CARTUCHO = 1.2               # kg de captura (C-12)
FILTRO_ELIA = 0.3            # kg
BOMBA_UE_H = 2.0             # consumo de la bomba de P-2 a potencia reducida
BANCO_BASE = 2.0             # consumo base del banco de emergencia de C-0


def hhmm(m):
    m = int(round(m)) % (24 * 60)
    return "%02d:%02d" % (m // 60, m % 60)


def hora(s):
    h, m = s.split(":")
    m = int(h) * 60 + int(m)
    return m if m >= T0 else m + 24 * 60


class Estado:
    def __init__(self):
        self.r3_kg, self.r3_n, self.r3_dep = 6.0, 13, False   # depurador portátil activo
        self.p2_kg, self.p2_n = 0.46, 2
        self.p2_bat = 12.0                                   # UE de la batería propia de P-2
        self.bomba, self.fuente, self.auto = True, "p2", False
        self.ultima_atencion = T0
        self.h4, self.parada, self.alivio, self.v12 = 1, 0, False, None
        self.deposito = 20                                   # min de bombeo acumulados desde 09:56
        self.j17_tocada = False                              # trabajar J-17 con herramientas impide el resellado
        self.sello_r3 = None                                 # minuto en que fallará el sello (H-4=6)
        self.banco, self.rover, self.portatil, self.industrial = 48.0, None, 12.0, 30.0
        self.log, self.muertes, self.eventos = [], [], set()

    def r3_estado(self):
        horas = self.r3_kg / (CO2_PERSONA * max(self.r3_n, 1))
        if self.r3_kg > 0:
            return "Estable" if horas > 3 else "Degradado"
        deuda = -horas
        return "Crítico" if deuda < 3 else ("Grave" if deuda < 6 else "Colapso")

    def p2_estado(self):
        if self.p2_kg > 0:
            return "Estable"
        deuda = -self.p2_kg / (CO2_PERSONA * max(self.p2_n, 1))
        return "Degradado" if deuda < 2 else ("Crítico" if deuda < 5 else "Colapso")

    def p2_consciente(self):
        return self.p2_n > 0 and self.p2_estado() in ("Estable", "Degradado")


def subir(e, m, motivo):
    if e.h4 >= 6:
        return
    e.h4 += 1
    if e.h4 == 4 and e.r3_n > 0:
        e.log.append((hhmm(m), "H-4 = 4: la salmuera llega a la rejilla de R-3 (escena del sumidero si hay sangre)"))
    e.log.append((hhmm(m), "H-4 sube a %d (%s)" % (e.h4, motivo)))
    if e.h4 == 6 and e.sello_r3 is None:
        e.sello_r3 = m + 120
        e.log.append((hhmm(m), "H-4 = 6: el sello inferior de R-3 fallará a las %s" % hhmm(m + 120)))


def simular(acciones, hasta="08:00", traza=False):
    e = Estado()
    acc = sorted(((hora(t), f, n) for t, f, n in acciones), key=lambda x: x[0])
    k = 0
    for m in range(T0, hora(hasta) + 1):
        while k < len(acc) and acc[k][0] <= m:
            _, f, nota = acc[k]
            f(e, m)
            e.log.append((hhmm(m), nota))
            k += 1
        dt = 1 / 60
        if e.r3_n > 0 and not e.r3_dep:
            e.r3_kg -= CO2_PERSONA * e.r3_n * dt
        if e.r3_n > 0 and e.r3_estado() == "Colapso" and "r3" not in e.eventos:
            e.eventos.add("r3")
            e.muertes.append((hhmm(m), "R-3 en Colapso: empiezan las muertes por hipercapnia"))
        if e.p2_n > 0:
            e.p2_kg -= CO2_PERSONA * e.p2_n * dt
            if e.p2_estado() == "Colapso" and "p2" not in e.eventos:
                e.eventos.add("p2")
                e.muertes.append((hhmm(m), "P-2 en Colapso: muertes por hipercapnia"))
        if e.p2_consciente():
            e.ultima_atencion = m
        if e.bomba:
            if e.fuente == "p2":
                e.p2_bat -= BOMBA_UE_H * dt
                if e.p2_bat <= 0:
                    e.bomba = False
                    e.log.append((hhmm(m), "batería de P-2 agotada: la bomba se para"))
            elif e.fuente == "portatil":
                e.portatil -= BOMBA_UE_H * dt
                if e.portatil <= 0:
                    e.bomba = False
                    e.log.append((hhmm(m), "batería portátil agotada: la bomba se para"))
            elif e.fuente == "industrial":
                e.industrial -= BOMBA_UE_H * dt
                if e.industrial <= 0:
                    e.bomba = False
                    e.log.append((hhmm(m), "batería industrial agotada: la bomba se para"))
            elif e.fuente == "rover":
                e.rover -= BOMBA_UE_H * dt
            elif e.fuente == "banco":
                e.banco -= BOMBA_UE_H * dt
            if e.bomba and e.v12 is None:
                e.deposito += 1
                if e.deposito >= DEPOSITO_MIN:
                    e.bomba = False
                    e.log.append((hhmm(m), "depósito de decantación lleno: la bomba ya no puede desviar"))
            if e.bomba and not e.auto and m - e.ultima_atencion >= 45:
                e.bomba = False
                e.log.append((hhmm(m), "bomba sin atender 45 min: se desceba y se para"))
        e.banco -= BANCO_BASE * dt
        if e.v12 is None:
            if e.bomba:
                e.parada = 0
            else:
                e.parada += 1
                paso = 60 if e.alivio else 30
                if e.parada >= paso:
                    e.parada = 0
                    subir(e, m, "bomba parada %d min" % paso)
        else:
            suelo = 0 if e.alivio else 1
            if e.h4 > suelo and m > e.v12 and (m - e.v12) % 60 == 0:
                e.h4 -= 1
                e.log.append((hhmm(m), "entrada de salmuera cortada: el tramo bajo escurre, H-4 = %d" % e.h4))
        if m == hora("03:36") and not e.j17_tocada and e.h4 > 0:
            e.h4 -= 1
            e.log.append((hhmm(m), "la colonia termina de resellar J-17: H-4 = %d y la bomba deja de ser necesaria" % e.h4))
            if e.v12 is None:
                e.v12 = m
        if e.h4 < 6:
            e.sello_r3 = None
        if e.sello_r3 is not None and m >= e.sello_r3 and e.r3_n > 0:
            e.muertes.append((hhmm(m), "falla el sello de R-3 con %d dentro sin traje" % e.r3_n))
            e.r3_n, e.sello_r3 = 0, None
        if traza and m % 30 == 0:
            print("%s  R-3 %5.2f kg (%2d) %-9s | P-2 %5.2f kg %-9s bat %4.1f bomba %-2s | H-4 %d | banco %4.1f | rover %s" % (
                hhmm(m), e.r3_kg, e.r3_n, e.r3_estado(), e.p2_kg, e.p2_estado() if e.p2_n else "vacía", e.p2_bat,
                "sí" if e.bomba else "NO", e.h4, e.banco, "%.1f" % e.rover if e.rover is not None else "-"))
    return e


# --- acciones -----------------------------------------------------------------------------------
def cartucho_r3(n=1):
    return lambda e, m: setattr(e, "r3_kg", e.r3_kg + CARTUCHO * n)


def cartucho_p2():
    return lambda e, m: setattr(e, "p2_kg", e.p2_kg + CARTUCHO)


def filtro_elia_p2():
    return lambda e, m: setattr(e, "p2_kg", e.p2_kg + FILTRO_ELIA)


def llegada_rover(ue):
    return lambda e, m: setattr(e, "rover", ue)


def bomba_a(fuente, auto=False):
    def f(e, m):
        e.fuente, e.bomba, e.ultima_atencion = fuente, True, m
        e.auto = e.auto or auto
    return f


def automatismo():
    return lambda e, m: setattr(e, "auto", True)


def cerrar_v12(brusco=False):
    def f(e, m):
        e.v12 = m
        if brusco:
            subir(e, m, "cierre brusco de V-12")
        else:
            e.h4 = max(0, e.h4 - 1)
            e.log.append((hhmm(m), "V-12 cerrada con purga gradual: H-4 = %d" % e.h4))
    return f


def restituir_alivio():
    def f(e, m):
        e.alivio = True
        e.h4 = max(0, e.h4 - 1)
    return f


def sacar_r3(n):
    return lambda e, m: setattr(e, "r3_n", e.r3_n - n)


def sacar_p2(n):
    return lambda e, m: setattr(e, "p2_n", e.p2_n - n)


def parar_bomba():
    return lambda e, m: setattr(e, "bomba", False)


def depurador_r3():
    return lambda e, m: setattr(e, "r3_dep", True)


def purga_r3():
    return lambda e, m: setattr(e, "r3_kg", e.r3_kg + 0.6)


def gasto_banco(ue):
    return lambda e, m: setattr(e, "banco", e.banco - ue)


# --- escenarios (los mismos que el informe de revisión) ------------------------------------------
def nota():
    return lambda e, m: None


def cargar_rover(ue):
    return lambda e, m: setattr(e, "rover", e.rover + ue)


ESC = {
    "sin_intervencion": [],
    # 1 · Referencia y Plan 1: 4 PJ, refuerzos pedidos 09:58, ruta R-12 con reparación, V-12 desde C-0 + E-1.
    "referencia": [
        ("13:10", llegada_rover(48), "llegada a C-7 por R-12 reparado (rover 48 UE)"),
        ("13:40", bomba_a("rover"), "rover en la portilla de P-2: alimenta la bomba"),
        ("14:10", cartucho_p2(), "portilla abierta con el actuador: un C-12 entra en P-2"),
        ("14:30", gasto_banco(4), "línea del actuador de V-12 reparada en L-4 (4 UE del banco)"),
        ("14:40", automatismo(), "automatismo de la bomba restablecido (técnico + Ivo)"),
        ("14:45", nota(), "llega el rover 2 de Bastión (6 C-12, batería industrial, depurador, 6 trajes)"),
        ("15:25", cerrar_v12(), "V-12 cerrada desde C-0 en secuencia gradual (14:40–15:25)"),
        ("15:30", sacar_p2(2), "Quiroga e Ivo salen de P-2 con trajes"),
        ("15:30", parar_bomba(), "con V-12 cerrada la bomba deja de ser necesaria"),
        ("16:45", gasto_banco(6), "E-1 igualada (6 UE del banco, 15:30–16:45)"),
        ("17:05", cartucho_r3(1), "primer equipo en R-3 por E-1: un cartucho y trajes"),
        ("17:30", sacar_r3(4), "tanda 1: heridos (Román en camilla, Osian, Inés) y Duarte"),
        ("17:50", sacar_r3(4), "tanda 2"),
        ("18:10", sacar_r3(5), "tanda 3; Mara la última; R-3 vacío"),
        ("18:30", cargar_rover(20), "20 UE de la batería industrial recargan el rover 1; 10 UE quedan para el depurador de C-0"),
        ("18:30", gasto_banco(0), "rover 2 sale con 4 supervivientes; rover 1 sale 18:45 con 5; 6 esperan en C-0 con el depurador"),
    ],
    # 2 · Tres PJ: nadie ayuda en paralelo salvo Quiroga e Ivo una vez libres.
    "tres_pj": [
        ("12:40", llegada_rover(52), "llegada sin reparar R-12 (refuerzos pedidos 10:05; rover 2 a las 14:50)"),
        ("13:10", bomba_a("rover"), "rover alimenta la bomba"),
        ("13:40", cartucho_p2(), "portilla abierta con el actuador; C-12 a P-2"),
        ("14:10", automatismo(), "automatismo con Ivo"),
        ("15:10", gasto_banco(4), "línea del actuador reparada (el técnico y Ivo)"),
        ("15:55", cerrar_v12(), "V-12 cerrada desde C-0"),
        ("16:00", sacar_p2(2), "Quiroga e Ivo se suman al rescate"),
        ("16:00", parar_bomba(), "bomba innecesaria"),
        ("17:30", gasto_banco(6), "E-1 igualada"),
        ("17:50", cartucho_r3(2), "en R-3 con dos cartuchos (uno del rover, otro de Bastión)"),
        ("18:30", sacar_r3(4), "tanda 1"),
        ("19:00", sacar_r3(4), "tanda 2"),
        ("19:30", sacar_r3(5), "tanda 3"),
    ],
    # 3 · Cinco PJ: tres frentes a la vez (P-2, V-12 a mano por la cría, portillo con cartuchos).
    "cinco_pj": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("rover"), "bomba alimentada"),
        ("14:10", cartucho_p2(), "C-12 a P-2"),
        ("14:10", automatismo(), "automatismo"),
        ("15:30", cartucho_r3(3), "Limen y la científica abren el portillo: 3 cartuchos a R-3"),
        ("15:45", cerrar_v12(), "el alguacil y el técnico cierran V-12 a mano"),
        ("16:00", sacar_p2(2), "P-2 evacuada"),
        ("16:00", parar_bomba(), "bomba innecesaria"),
        ("17:15", gasto_banco(6), "E-1 igualada"),
        ("17:40", sacar_r3(6), "tanda 1 por E-1"),
        ("18:00", sacar_r3(7), "tanda 2 por E-1"),
    ],
    # 4 · Plan 2: portillo superior; P-2 recibe aire por la portilla y la bomba sigue atendida.
    "portillo": [
        ("13:10", llegada_rover(49), "llegada a C-7"),
        ("13:40", bomba_a("rover"), "rover alimenta la bomba"),
        ("14:10", cartucho_p2(), "portilla abierta: C-12 a P-2 (Quiroga e Ivo siguen atendiendo)"),
        ("15:55", cartucho_r3(3), "portillo abierto: cartucho de rover + 2 C-12 del armario de servicio"),
        ("16:30", sacar_r3(2), "salen dos"),
        ("17:00", sacar_r3(3), "salen tres"),
        ("17:40", sacar_r3(3), "salen tres (un herido)"),
        ("18:30", sacar_r3(3), "salen tres"),
        ("19:20", sacar_r3(2), "últimos dos (Román en arnés y Mara)"),
        ("19:40", bomba_a("industrial", auto=True), "batería industrial + automatismo; salen Quiroga e Ivo"),
        ("19:40", sacar_p2(2), "P-2 evacuada"),
    ],
    # 5 · Plan 3: estabilizar y esperar refuerzos.
    "estabilizar": [
        ("13:10", llegada_rover(49), "llegada a C-7"),
        ("13:40", bomba_a("rover"), "rover alimenta la bomba"),
        ("14:15", filtro_elia_p2(), "filtro portátil de Elia a P-2"),
        ("15:10", bomba_a("industrial", auto=True), "batería industrial de Bastión + automatismo; rover libre"),
        ("15:10", cartucho_p2(), "cartucho de Bastión a P-2"),
        ("16:40", cartucho_r3(2), "dos cartuchos a R-3 por el portillo"),
        ("17:30", depurador_r3(), "depurador portátil de Bastión instalado en R-3"),
        ("20:30", cerrar_v12(), "el equipo de Bastión, guiado, cierra V-12 antes de que se llene el depósito"),
        ("20:45", sacar_p2(2), "Quiroga e Ivo pasan a C-0"),
    ],
    # 6 · Plan 4 creativo: cable del banco de C-0 a P-2 y dos purgas de R-3.
    "creativo": [
        ("12:40", llegada_rover(52), "llegada"),
        ("13:30", bomba_a("banco"), "carrete de cable: el banco de C-0 alimenta la bomba"),
        ("14:30", cartucho_p2(), "cartucho a P-2"),
        ("16:00", purga_r3(), "purga parcial de R-3 (6 kg de O2)"),
        ("17:00", purga_r3(), "segunda purga"),
        ("17:40", cerrar_v12(), "V-12 cerrada"),
        ("18:10", parar_bomba(), "bomba parada para ahorrar banco"),
        ("18:15", sacar_p2(2), "P-2 evacuada"),
        ("19:00", gasto_banco(6), "E-1 igualada"),
        ("19:15", cartucho_r3(1), "cartucho por E-1"),
        ("19:45", sacar_r3(13), "evacuación por E-1 en tres tandas"),
    ],
    # 7 · Plan 5: retirada a las 15:30 sin relevo (nadie pidió el rover 2).
    "retirada_sin_relevo": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("portatil", auto=True), "batería portátil (12 UE) + automatismo"),
        ("14:10", cartucho_p2(), "cartucho a P-2"),
        ("14:30", nota(), "no llegan al portillo; se retiran a las 15:30"),
    ],
    # 8 · Evacuación parcial: se retiran, pero el rover 2 llegó a las 14:45 y su equipo sigue.
    "evacuacion_parcial": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("portatil", auto=True), "batería portátil + automatismo"),
        ("14:10", cartucho_p2(), "cartucho a P-2"),
        ("15:30", sacar_p2(2), "se llevan a Quiroga e Ivo y se retiran"),
        ("16:00", bomba_a("industrial", auto=True), "el equipo de Bastión cambia a la batería industrial"),
        ("17:30", cartucho_r3(2), "el equipo de Bastión, guiado por radio, llega al portillo: 2 C-12"),
        ("18:30", cartucho_r3(2), "y dos más del armario de servicio"),
        ("19:30", depurador_r3(), "depurador portátil de Bastión pasado por el portillo"),
        ("21:00", cerrar_v12(), "el equipo de Bastión cierra V-12 a mano, guiado por radio"),
    ],
    # 9 · Refuerzos pedidos al llegar a C-7 (rover 2 a las 18:00); sin reparar R-12.
    "refuerzos_tarde": [
        ("12:40", llegada_rover(52), "llegada por R-12 sin repararlo"),
        ("13:15", bomba_a("rover"), "rover alimenta la bomba"),
        ("14:00", cartucho_p2(), "un cartucho a P-2"),
        ("15:40", cerrar_v12(), "V-12 cerrada a mano tras cruzar la cría"),
        ("16:30", cartucho_r3(1), "un cartucho a R-3 por el portillo"),
        ("18:00", cartucho_r3(4), "llegan los refuerzos: cuatro cartuchos más"),
        ("19:30", sacar_r3(13), "evacuación por E-1 tras igualarla"),
        ("19:45", sacar_p2(2), "P-2 evacuada"),
    ],
    # 10 · Fallo de una reparación fundamental: cierre brusco de V-12 y E-1 forzada.
    "fallo_reparacion": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("rover"), "bomba alimentada"),
        ("14:10", cartucho_p2(), "cartucho a P-2"),
        ("15:00", cerrar_v12(brusco=True), "cierre brusco de V-12: golpe de ariete"),
        ("16:00", nota(), "H-4 vuelve a 1 por escurrido; E-1 aún igualable"),
        ("16:30", cartucho_r3(1), "cartucho a R-3 por el portillo"),
        ("18:00", sacar_r3(13), "evacuación por E-1"),
        ("18:15", sacar_p2(2), "P-2 evacuada"),
    ],
    # 11 · Prioriza R-3 y descuida P-2.
    "prioriza_r3": [
        ("12:40", llegada_rover(52), "llegada"),
        ("15:00", cartucho_r3(3), "portillo: tres cartuchos a R-3"),
        ("16:50", bomba_a("rover"), "por fin alimentan la bomba (parada desde 15:36)"),
        ("17:20", cartucho_p2(), "cartucho a P-2"),
        ("18:20", cerrar_v12(), "V-12 cerrada"),
        ("19:30", sacar_r3(13), "evacuación por E-1"),
        ("19:45", sacar_p2(2), "P-2 evacuada"),
    ],
    # 12 · Prioriza P-2 y llega tarde a R-3.
    "prioriza_p2": [
        ("12:40", llegada_rover(52), "llegada"),
        ("13:15", bomba_a("rover"), "bomba alimentada"),
        ("13:50", cartucho_p2(), "cartucho a P-2"),
        ("14:20", automatismo(), "automatismo"),
        ("16:30", cerrar_v12(), "V-12 cerrada a mano"),
        ("17:00", sacar_p2(2), "P-2 evacuada"),
        ("20:30", cartucho_r3(1), "llegan a R-3 por el portillo"),
        ("21:30", sacar_r3(13), "evacuación por E-1"),
    ],
    # 13 · Separación del grupo: el equipo de L-4 queda bloqueado 40 min por la colonia.
    "separacion": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("rover"), "bomba alimentada"),
        ("14:10", cartucho_p2(), "cartucho a P-2; el automatismo queda pendiente"),
        ("15:10", gasto_banco(4), "línea del actuador reparada con 40 min de retraso"),
        ("15:55", cerrar_v12(), "V-12 cerrada"),
        ("17:30", gasto_banco(6), "E-1 igualada"),
        ("17:50", cartucho_r3(1), "cartucho a R-3"),
        ("18:30", sacar_r3(13), "evacuación por E-1"),
        ("18:40", sacar_p2(2), "P-2 evacuada"),
    ],
    # 14 · Ivo descubierto temprano: Vidal ordena detenerlo y la bomba queda 35 min sin atender.
    "ivo_temprano": [
        ("13:10", llegada_rover(49), "llegada"),
        ("13:40", bomba_a("rover"), "bomba alimentada"),
        ("14:10", cartucho_p2(), "cartucho a P-2"),
        ("14:20", sacar_p2(1), "detienen a Ivo y lo sacan; Quiroga queda sola con el hombro"),
        ("15:05", parar_bomba(), "Quiroga falla la tirada de Fuerza: no puede cebar sola y la bomba se para"),
        ("15:40", automatismo(), "Ivo vuelve esposado a terminar el automatismo"),
        ("15:40", bomba_a("rover", auto=True), "la bomba arranca de nuevo"),
        ("16:30", cerrar_v12(), "V-12 cerrada"),
        ("16:35", sacar_p2(1), "Quiroga sale"),
        ("17:45", gasto_banco(6), "E-1 igualada"),
        ("18:00", cartucho_r3(1), "cartucho"),
        ("18:40", sacar_r3(13), "evacuación por E-1"),
    ],
}


def resumen(nombre, e):
    print("== %s ==" % nombre)
    for h, n in e.log:
        print("  %s  %s" % (h, n))
    print("  final: R-3 %.2f kg (%d dentro, %s) · P-2 %s · H-4 %d · banco %.1f UE · rover %s" % (
        e.r3_kg, e.r3_n, e.r3_estado(), e.p2_estado() if e.p2_n else "evacuada", e.h4, e.banco,
        "%.1f UE" % e.rover if e.rover is not None else "-"))
    for h, n in e.muertes or [("—", "sin muertes")]:
        print("  MUERTES %s %s" % (h, n))
    print()


def comprobar():
    e = simular(ESC["sin_intervencion"])
    assert any("sello de R-3" in t and h.startswith("20:0") for h, t in e.muertes), e.muertes
    for n in ("referencia", "tres_pj", "cinco_pj", "portillo", "estabilizar", "creativo"):
        assert not simular(ESC[n]).muertes, (n, simular(ESC[n]).muertes)
    print("comprobaciones: OK")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        resumen(sys.argv[1], simular(ESC[sys.argv[1]], traza=True))
    else:
        for n, a_ in ESC.items():
            resumen(n, simular(a_))
        comprobar()
