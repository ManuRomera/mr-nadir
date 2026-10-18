// MR- Nádir · Panel de emergencia del Guardián: hora desde T0 y los relojes del escenario
// (R-3, P-2, Fuga H-4, banco de C-0, rover y Atención de la colonia).
// El estado es un registro de acciones con hora; los relojes se recalculan minuto a minuto
// con las mismas reglas que tools/relojes.py y el capítulo «Relojes, recursos y cronología».
// El Guardián solo mueve la hora: los jugadores anotan sus acciones desde el HUD de la cuadrilla
// (js/cuadrilla.js), que llegan aquí por socket, y el Panel avisa de cada consecuencia.

export const MOD = "mr-nadir";
const T0_MIN = 9 * 60 + 36;          // 09:36
const CO2 = 0.046 / 60;              // kg por persona y minuto
const CARTUCHO = 1.2, FILTRO = 0.3, PURGA = 0.6;
const DEPOSITO_MIN = 1044;           // minutos de bombeo hasta llenar el depósito (≈ 02:40)

// rev: relojes que ya ven los jugadores · carga: lo que lleva la cuadrilla · rover2: minuto de llegada
export const CARGA = { cartucho: "Cartuchos C-12", filtro: "Filtros portátiles", portatil: "Baterías portátiles", recambio: "Recambios de mochila",
  parche: "Parches de traje", traje: "Trajes de reserva", depurador: "Depurador DP-40" };
const ESTADO_INICIAL = { min: 0, ev: [], ue: 90, atencion: 0, rev: {}, carga: Object.fromEntries(Object.keys(CARGA).map(k => [k, 0])), rover2: null };

export const fmtHora = (m) => {
  const t = ((T0_MIN + Math.round(m)) % 1440 + 1440) % 1440;
  return `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
};
export const fmtDur = (m) => {
  const s = m < 0 ? "−" : "";
  m = Math.abs(Math.round(m));
  return `${s}${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
};

export function estadoR3(kg, n) {
  const h = kg / (0.046 * Math.max(n, 1));
  if (kg > 0) return h > 3 ? "Estable" : "Degradado";
  return -h < 3 ? "Crítico" : -h < 6 ? "Grave" : "Colapso";
}
export function estadoP2(kg, n) {
  if (kg > 0) return "Estable";
  const h = -kg / (0.046 * Math.max(n, 1));
  return h < 2 ? "Degradado" : h < 5 ? "Crítico" : "Colapso";
}

/** Recalcula todos los relojes desde T0 hasta e.min aplicando las acciones registradas.
 *  obs(m, s), si se pasa, recibe el estado al final de cada minuto (para proyectar líneas rojas). */
export function calcular(e, obs) {
  const s = { r3: 6, r3n: 13, dep: false, p2: 0.46, p2n: 2, bat: 12, port: 12, ind: 30, banco: 48, rover: e.ue,
    bomba: true, fuente: "p2", auto: false, atend: 0, h4: 1, parada: 0, alivio: false, v12: null, sello: null, deposito: 20, avisos: [] };
  const ev = [...(e.ev ?? [])].sort((a, b) => a.m - b.m);
  let k = 0;
  const subir = (m, motivo) => {
    if (s.h4 >= 6) return;
    s.h4 += 1;
    s.avisos.push(`${fmtHora(m)} H-4 sube a ${s.h4} (${motivo})`);
    if (s.h4 === 6 && s.sello === null) s.sello = m + 120;
  };
  for (let m = 0; m <= e.min; m++) {
    while (k < ev.length && ev[k].m <= m) {
      const a = ev[k++];
      switch (a.t) {
        case "cartR3": s.r3 += CARTUCHO; break;
        case "filtroR3": s.r3 += FILTRO; break;
        case "purga": s.r3 += PURGA; break;
        case "dep": s.dep = !s.dep; break;
        case "r3n": s.r3n = Math.max(0, s.r3n + a.v); break;
        case "cartP2": s.p2 += CARTUCHO; break;
        case "filtroP2": s.p2 += FILTRO; break;
        case "p2n": s.p2n = Math.max(0, s.p2n + a.v); break;
        case "fuente": s.fuente = a.v; s.bomba = a.v !== "parada"; s.atend = m; break;
        case "auto": s.auto = true; break;
        case "v12": s.v12 = m; s.h4 = Math.max(0, s.h4 - 1); break;
        case "v12golpe": s.v12 = m; subir(m, "cierre brusco de V-12"); break;
        case "alivio": s.alivio = true; s.h4 = Math.max(0, s.h4 - 1); break;
        case "parche": s.h4 = Math.max(0, s.h4 - 1); break;
        case "e1": subir(m, "E-1 forzada"); break;
        case "h4": s.h4 = Math.min(6, Math.max(0, s.h4 + a.v)); break;
        case "banco": s.banco += a.v; break;
        case "rover": s.rover += a.v; break;
      }
    }
    if (m === e.min) break;
    if (s.r3n > 0 && !s.dep) s.r3 -= CO2 * s.r3n;
    if (s.p2n > 0) s.p2 -= CO2 * s.p2n;
    if (s.p2n > 0 && ["Estable", "Degradado"].includes(estadoP2(s.p2, s.p2n))) s.atend = m;
    if (s.bomba) {
      const gasto = 2 / 60;
      if (s.fuente === "p2") { s.bat -= gasto; if (s.bat <= 0) { s.bomba = false; s.avisos.push(`${fmtHora(m)} batería de P-2 agotada`); } }
      else if (s.fuente === "portatil") { s.port -= gasto; if (s.port <= 0) { s.bomba = false; s.avisos.push(`${fmtHora(m)} batería portátil agotada`); } }
      else if (s.fuente === "industrial") { s.ind -= gasto; if (s.ind <= 0) { s.bomba = false; s.avisos.push(`${fmtHora(m)} batería industrial agotada`); } }
      else if (s.fuente === "rover") s.rover -= gasto;
      else if (s.fuente === "banco") s.banco -= gasto;
      if (s.bomba && s.v12 === null && ++s.deposito >= DEPOSITO_MIN) { s.bomba = false; s.avisos.push(`${fmtHora(m)} depósito de decantación lleno`); }
      if (s.bomba && !s.auto && m - s.atend >= 45) { s.bomba = false; s.avisos.push(`${fmtHora(m)} bomba sin atender: se desceba`); }
    }
    s.banco -= 2 / 60;
    if (s.v12 === null) {
      if (s.bomba) s.parada = 0;
      else if (++s.parada >= (s.alivio ? 60 : 30)) { s.parada = 0; subir(m, "bomba parada"); }
    } else if (s.h4 > (s.alivio ? 0 : 1) && m > s.v12 && (m - s.v12) % 60 === 0) s.h4 -= 1;
    if (s.h4 < 6) s.sello = null;
    if (s.sello !== null && m >= s.sello && s.r3n > 0) { s.avisos.push(`${fmtHora(m)} FALLA EL SELLO DE R-3`); s.sello = null; }
    obs?.(m + 1, s);
  }
  const nH4 = ["Escurrido · E-1 en 60 min", "Agua al tobillo · E-1 en 60–90 min", "Media pierna · E-1 en 90–120 min · J-17 solo con V-12",
    "Rodilla · E-1 solo con V-12 cerrada · ruta baja lenta", "Cintura · agua en la rejilla de R-3 · E-1 imposible · la radio de Serrat calla",
    "El sello inferior de R-3 rezuma", "Ruta baja inundada · el sello de R-3 falla en 120 min"][s.h4];
  const at = e.atencion >= 6 ? "Defensores o grupo de 3–6" : e.atencion >= 5 ? "Uno prueba el contacto" : e.atencion >= 3 ? "Tres ejemplares convergen"
    : e.atencion >= 2 ? "Un explorador se acerca (5–15 min)" : "Inactiva";
  return { ...s, eR3: estadoR3(s.r3, s.r3n), eP2: s.p2n ? estadoP2(s.p2, s.p2n) : "Evacuada", nH4, at,
    selloEn: s.sello !== null ? s.sello - e.min : null };
}

/* ---------------- Modo rápido: casillas y consecuencias narrativas ---------------- */

/** Horas que quedan en cada reloj (las casillas del modo rápido: una casilla, una hora). */
export function horas(c) {
  const bat = { p2: c.bat, portatil: c.port, industrial: c.ind }[c.fuente];
  return {
    r3: c.r3n && !c.dep ? c.r3 / (0.046 * c.r3n) : null,             // null: no se gasta
    p2: c.p2n ? c.p2 / (0.046 * c.p2n) : null,
    bat: c.bomba && bat !== undefined ? bat / 2 : null,
    banco: c.banco / 2
  };
}

/** Fila de casillas: llenas = lo que queda; en rojo, lo que se ha pasado de cero. */
export function casillas(valor, total, { exceso = 0, paso = 1 } = {}) {
  if (valor === null) return `<span class="mr-nadir-cas sin">sin gasto</span>`;
  const llenas = Math.max(0, Math.min(total, Math.ceil(valor / paso - 1e-9)));
  const rojas = valor < 0 ? Math.min(exceso, Math.floor(-valor / paso + 1e-9)) : 0;   // como en papel: se tacha al cumplirse la hora
  let h = "";
  for (let i = 0; i < total; i++) h += `<i class="${i < llenas ? "l" : ""}"></i>`;
  for (let i = 0; i < exceso; i++) h += `<i class="x ${i < rojas ? "r" : ""}"></i>`;
  const mas = valor / paso > total ? `<b>+${Math.ceil(valor / paso) - total}</b>` : "";
  return `<span class="mr-nadir-cas" role="img" aria-label="${Math.max(0, valor).toFixed(1)} de ${total}">${h}${mas}</span>`;
}

// Lo que el Guardián dice o aplica cuando un reloj cambia de estado (capítulo «Relojes, recursos y cronología»)
const NARR = {
  r3: { Estable: "R-3 recupera margen.",
    Degradado: "R-3 Degradado: dolor de cabeza y torpeza. +1 Estrés a quien lo constate; los PNJ trabajan con [−] en tareas finas. Alguien cuenta catorce.",
    Crítico: "R-3 Crítico: [−] a todas las tiradas dentro sin casco cerrado; esforzarse exige salvación de Cuerpo (PNJ: Instinto). Mara repite frases.",
    Grave: "R-3 Grave: cada hora, cada ocupante sin traje hace salvación de Cuerpo o queda incapacitado. Los heridos fallan.",
    Colapso: "R-3 Colapso: cada hora, salvación de Muerte de cada incapacitado." },
  p2: { Estable: "P-2 vuelve a respirar.", Evacuada: "P-2 queda vacía.",
    Degradado: "P-2 sin filtro: [−] en tareas finas. Quiroga empieza a quebrarse; habla bajo, como si el raspado pudiera oírla.",
    Crítico: "P-2 Crítico: cada hora, salvación de Instinto o incapacitado. Si caen los dos, nadie atiende la bomba.",
    Colapso: "P-2 Colapso: cada hora, salvación de Muerte de los incapacitados." },
  h4: ["H-4 escurrido: E-1 se iguala en 60 min.", "H-4 en 1: agua al tobillo en el tramo bajo.",
    "H-4 en 2: la aguja del tramo bajo sube; ruido de garganta en H-4. E-1 tarda 90–120 min en igualarse.",
    "H-4 en 3: agua a la rodilla en la ruta baja. E-1 ya solo se iguala con V-12 cerrada.",
    "H-4 en 4: la salmuera llega a la rejilla de R-3 (sumidero, si alguien sangra). E-1 ya no se iguala. La radio de Serrat se ahoga y calla.",
    "H-4 en 5: el sello inferior de R-3 rezuma; el suelo se humedece. Mara ordena preparar la salida por el portillo.",
    "H-4 en 6: crujidos y goteo creciente. El sello inferior de R-3 fallará en 120 minutos; anúncialo."]
};

/** Primeras líneas rojas si nadie hace nada en las próximas horas. */
export function proximas(e, horizonte = 720) {
  const base = calcular(e);
  const prev = { r3: base.eR3, p2: base.eP2 };
  const r = [];
  const fut = calcular({ ...e, min: e.min + horizonte }, (m, s) => {
    if (m <= e.min) return;
    const eR3 = estadoR3(s.r3, s.r3n), eP2 = s.p2n ? estadoP2(s.p2, s.p2n) : "Evacuada";
    if (eR3 !== prev.r3) { prev.r3 = eR3; if (s.r3n) r.push({ m, txt: `R-3 pasa a ${eR3}` }); }
    if (eP2 !== prev.p2) { prev.p2 = eP2; r.push({ m, txt: `P-2 pasa a ${eP2}` }); }
  });
  const hm = (t) => { const [h, mm] = t.split(":").map(Number); return ((h * 60 + mm - T0_MIN) % 1440 + 1440) % 1440; };
  const avisos = fut.avisos.slice(base.avisos.length).map(a => ({ m: hm(a.slice(0, 5)), txt: a.slice(6) }));
  // ponytail: el orden por hora del día falla si el horizonte cruza un día entero; 12 h no llega
  return [...r, ...avisos].sort((a, b) => ((a.m - e.min) % 1440 + 1440) % 1440 - ((b.m - e.min) % 1440 + 1440) % 1440)
    .slice(0, 4).map(x => `${fmtHora(x.m)} ${x.txt}`);
}

/* ---------------- Estado compartido y acciones ---------------- */

export const leerEstado = () => foundry.utils.mergeObject(foundry.utils.deepClone(ESTADO_INICIAL), game.settings.get(MOD, "relojes") ?? {});
const susurroGM = (html) => ChatMessage.create({ whisper: game.users.filter(u => u.isGM).map(u => u.id), speaker: { alias: "Nádir · Panel" },
  content: `<div class="mr-nadir-chat">${html}</div>` });

/** Avisa al Guardián, con la consecuencia ya redactada, de todo lo que ha cambiado entre dos estados. */
async function avisarCambios(antes, despues) {
  if (despues.min <= antes.min) return;
  const a = calcular(antes), b = calcular(despues);
  const l = b.avisos.slice(a.avisos.length);
  if (b.eR3 !== a.eR3 && b.r3n) l.push(NARR.r3[b.eR3]);
  if (b.eP2 !== a.eP2) l.push(NARR.p2[b.eP2]);
  if (b.h4 !== a.h4) l.push(NARR.h4[b.h4]);
  if (a.bomba && !b.bomba) l.push("El golpeteo del motor desaparece de la placa de P-2.");
  if (a.banco > 6 && b.banco <= 6) l.push("Banco de C-0 casi agotado: quedan unas tres horas de luz y depuración.");
  if (despues.rover2 !== null && antes.min < despues.rover2 && despues.min >= despues.rover2) l.push("Llega el rover 2 con Bruna Lasarte y Eloy Cid.");
  for (const act of trajes()) {
    const x = trajeReal(act, antes.min), y = trajeReal(act, despues.min);
    if (x > 30 && y <= 30 && y > 0) l.push(`Traje de ${act.name}: menos de 30 min de mochila.`);
    if (x > 0 && y <= 0) l.push(`Traje de ${act.name}: mochila agotada. PSG 33.1: quince segundos hasta la inconsciencia.`);
  }
  if (l.length) await susurroGM(`<h3>${fmtHora(despues.min)}</h3><p>${l.join("</p><p>")}</p>`);
}

/** El Guardián mueve la hora; todo lo demás se recalcula y se avisa. */
export async function moverHora(delta) {
  if (!game.user.isGM) return;
  const antes = leerEstado(), e = foundry.utils.deepClone(antes);
  e.min = Math.max(0, e.min + Number(delta));
  await game.settings.set(MOD, "relojes", e);
  await avisarCambios(antes, e);
}

/** Muestra un reloj a los jugadores (claves: r3, p2, h4, banco). */
export async function revelar(...claves) {
  if (!game.user.isGM) return;
  const e = leerEstado();
  if (claves.every(k => e.rev[k])) return;
  for (const k of claves) e.rev[k] = true;
  await game.settings.set(MOD, "relojes", e);
}

// Acciones que los jugadores pueden anotar desde el HUD: qué evento crean, qué gastan y cómo se leen
export const ACC_JUGADOR = {
  cartR3: { t: "cartR3", gasta: "cartucho", txt: "instala un cartucho en R-3", rev: "r3" },
  filtroR3: { t: "filtroR3", gasta: "filtro", txt: "pasa un filtro portátil a R-3", rev: "r3" },
  dep: { t: "dep", gasta: "depurador", txt: "monta el depurador portátil en R-3", rev: "r3" },
  sacaR3: { t: "r3n", v: -1, txt: "saca a una persona de R-3", rev: "r3" },
  cartP2: { t: "cartP2", gasta: "cartucho", txt: "mete un cartucho en P-2", rev: "p2" },
  filtroP2: { t: "filtroP2", gasta: "filtro", txt: "mete un filtro portátil en P-2", rev: "p2" },
  bombaRover: { t: "fuente", v: "rover", txt: "conecta el rover a la bomba de P-2", rev: "p2" },
  bombaPortatil: { t: "fuente", v: "portatil", gasta: "portatil", txt: "conecta una batería portátil a la bomba de P-2", rev: "p2" },
  auto: { t: "auto", txt: "restablece el automatismo de la bomba", rev: "p2" },
  sacaP2: { t: "p2n", v: -1, txt: "saca a una persona de P-2", rev: "p2" },
  v12: { t: "v12", txt: "termina de cerrar V-12 de forma gradual", rev: "h4" },
  alivio: { t: "alivio", txt: "restituye el alivio de H-4", rev: "h4" }
};

/** Aplica en el estado del mundo lo que pide un usuario (lo ejecuta el Guardián activo). */
async function aplicar(msg, userId) {
  const e = leerEstado(), quien = game.users.get(userId)?.name ?? "Alguien";
  let txt;
  if (msg.tipo === "accion") {
    const a = ACC_JUGADOR[msg.k];
    if (!a || (a.gasta && !(e.carga[a.gasta] > 0))) return;
    if (a.gasta) e.carga[a.gasta] -= 1;
    const id = foundry.utils.randomID();
    e.ev = [...e.ev, { id, m: e.min, t: a.t, v: a.v ?? null, gasta: a.gasta ?? null }];
    txt = `<b>${quien}</b> ${a.txt} (${fmtHora(e.min)}). @NadirAnular[${id}]{Anular}`;
  } else if (msg.tipo === "carga" && msg.k in CARGA) {
    e.carga[msg.k] = Math.max(0, (e.carga[msg.k] ?? 0) + Math.sign(msg.d));
  } else if (msg.tipo === "rover") {
    const d = Math.max(-45, Math.min(45, Number(msg.d) || 0));
    const id = foundry.utils.randomID();
    e.ev = [...e.ev, { id, m: e.min, t: "rover", v: d }];
    txt = `<b>${quien}</b> anota ${d > 0 ? "+" : ""}${d} UE en el rover 1 (${fmtHora(e.min)}). @NadirAnular[${id}]{Anular}`;
  } else return;
  await game.settings.set(MOD, "relojes", e);
  if (txt) await susurroGM(`<p>${txt}</p>`);
}

/** Lo que pulsa un jugador viaja al Guardián activo; si lo pulsa el Guardián, se aplica directamente. */
export function pedir(msg) {
  if (game.user === game.users.activeGM) return aplicar(msg, game.user.id);
  if (!game.users.activeGM) return ui.notifications.warn("Nádir: no hay ningún Guardián conectado para anotar la acción.");
  game.socket.emit(`module.${MOD}`, { ...msg, userId: game.user.id });
}

/** Quita del registro una acción anotada (botón «Anular» del chat). */
async function anular(id) {
  const e = leerEstado(), ev = e.ev.find(x => x.id === id);
  if (!ev) return ui.notifications.info("Nádir: esa acción ya no está en el registro.");
  e.ev = e.ev.filter(x => x.id !== id);
  if (ev.gasta) e.carga[ev.gasta] = (e.carga[ev.gasta] ?? 0) + 1;
  await game.settings.set(MOD, "relojes", e);
  ui.notifications.info("Nádir: acción anulada.");
}

/* ---------------- Trajes de faena (indicador personal) ---------------- */
// Mochila del traje de vacío del PSG: 12 h en condiciones normales, 4 h bajo esfuerzo (gasta el triple); Limen, 8 h.
// Bandera del actor: { rest: minutos normales que quedaban al último cambio, desde: minuto de juego en que se pasó
// a mochila o null si va con umbilical, esf: true si trabaja con esfuerzo }

const esAndroide = (act) => ["Androide", "Android"].includes(act.system?.class?.value);
export const trajeMax = (act) => (esAndroide(act) ? 480 : 720);
const ritmo = (act, f) => (f?.esf && !esAndroide(act) ? 3 : 1);
export const trajes = () => {
  const pj = game.actors.filter(a => a.type === "character");
  const conJugador = pj.filter(a => a.hasPlayerOwner);
  return conJugador.length ? conJugador : pj;
};
/** Minutos de mochila que quedan, contados en condiciones normales. */
export function trajeMin(act, ahora) {
  const f = act.getFlag(MOD, "traje"), max = trajeMax(act);
  if (!f) return max;
  return Math.max(0, Math.min(max, f.desde === null ? f.rest : f.rest - (ahora - f.desde) * ritmo(act, f)));
}
/** Minutos reales que le quedan al ritmo actual. */
export const trajeReal = (act, ahora) => trajeMin(act, ahora) / ritmo(act, act.getFlag(MOD, "traje"));
async function cambiarTraje(act, cambio) {
  const ahora = leerEstado().min, f = act.getFlag(MOD, "traje") ?? { rest: trajeMax(act), desde: null, esf: false };
  const g = { rest: trajeMin(act, ahora), desde: f.desde === null ? null : ahora, esf: !!f.esf, ...cambio(f, ahora) };
  await act.setFlag(MOD, "traje", g);
}
export const umbilical = (act) => cambiarTraje(act, (f, ahora) => ({ desde: f.desde === null ? ahora : null }));
export const esfuerzo = (act) => cambiarTraje(act, (f) => ({ esf: !f.esf }));
export async function recambio(act) {
  if (!(leerEstado().carga.recambio > 0)) return ui.notifications.warn("Nádir: no queda ningún recambio de mochila en la carga.");
  pedir({ tipo: "carga", k: "recambio", d: -1 });
  await cambiarTraje(act, () => ({ rest: trajeMax(act) }));
}

/* ---------------- Panel de emergencia (Guardián) ---------------- */

let detalleAbierto = false;

class PanelEmergencia extends foundry.applications.api.ApplicationV2 {
  static DEFAULT_OPTIONS = {
    id: "mr-nadir-panel",
    classes: ["mr-nadir-panel"],
    window: { title: "Nádir · Panel de emergencia", icon: "fa-solid fa-gauge-high", resizable: true },
    position: { width: 480, height: "auto" },
    actions: {
      tiempo: PanelEmergencia.#tiempo,
      accion: PanelEmergencia.#accion,
      ajustar: PanelEmergencia.#ajustar,
      revelar: PanelEmergencia.#revelar,
      rover2: PanelEmergencia.#rover2,
      hud: () => abrirHudTodos(),
      deshacer: PanelEmergencia.#deshacer,
      chat: PanelEmergencia.#chat,
      reiniciar: PanelEmergencia.#reiniciar
    }
  };

  get estado() { return leerEstado(); }

  async guardar(e) {
    if (!game.user.isGM) return ui.notifications.warn("Sólo el Guardián modifica los relojes.");
    await game.settings.set(MOD, "relojes", e);
    this.render();
  }

  async _renderHTML() {
    const e = this.estado, c = calcular(e), gm = game.user.isGM, h = horas(c);
    const b = (t, txt, v = "") => gm ? `<button type="button" data-action="accion" data-t="${t}" data-v="${v}">${txt}</button>` : "";
    const aj = (campo, d, txt) => gm ? `<button type="button" data-action="ajustar" data-campo="${campo}" data-delta="${d}">${txt}</button>` : "";
    const ojo = (k) => `<button type="button" class="ojo ${e.rev[k] ? "on" : ""}" data-action="revelar" data-k="${k}" aria-pressed="${!!e.rev[k]}"
      title="${e.rev[k] ? "Los jugadores lo ven en su HUD (pulsa para ocultarlo)" : "Oculto a los jugadores (pulsa para mostrarlo en su HUD)"}"><i class="fa-solid ${e.rev[k] ? "fa-eye" : "fa-eye-slash"}"></i></button>`;
    const fila = (titulo, valor, nota, botones = "", alerta = false) =>
      `<div class="fila ${alerta ? "alerta" : ""}"><div class="t">${titulo}</div><div class="v">${valor}</div><div class="n">${nota}</div><div class="b">${botones}</div></div>`;
    const rapida = (titulo, cas, estado, k, alerta) =>
      `<div class="rap ${alerta ? "alerta" : ""}"><div class="t">${titulo}</div><div class="c">${cas}</div><div class="e">${estado}</div>${k && gm ? ojo(k) : "<span></span>"}</div>`;
    const fuentes = { p2: "batería de P-2", rover: "rover", portatil: "batería portátil", industrial: "batería industrial", banco: "banco de C-0", parada: "ninguna" };
    const prox = proximas(e);
    const div = document.createElement("div");
    div.className = "mr-nadir-body";
    div.innerHTML = `
      <div class="reloj"><span>T+${fmtDur(e.min)}</span><b>${fmtHora(e.min)}</b></div>
      ${gm ? `<div class="tiempo">${[-10, 10, 30, 60].map(d => `<button type="button" data-action="tiempo" data-delta="${d}">${d > 0 ? "+" : ""}${d} min</button>`).join("")}</div>` : ""}
      <div class="rapida">
        ${rapida("R-3", casillas(h.r3, 12, { exceso: 6 }), `${c.eR3} · ${c.r3n} pers.${c.dep ? " · depurador" : ""}`, "r3", c.eR3 !== "Estable")}
        ${rapida("P-2 aire", c.p2n ? casillas(h.p2, 12, { exceso: 5 }) : "—", c.eP2, "p2", !["Estable", "Evacuada"].includes(c.eP2))}
        ${rapida("Bomba", c.bomba ? casillas(h.bat, 12) : "<b class='rojo'>PARADA</b>", `${fuentes[c.fuente] ?? c.fuente}${c.auto ? " · auto" : ""}${c.v12 !== null ? " · V-12 cerrada" : ""}`, "", !c.bomba && c.v12 === null)}
        ${rapida("H-4", casillas(c.h4, 6) + (c.selloEn !== null ? ` ${casillas(c.selloEn / 30, 4)}` : ""), c.selloEn !== null ? `<b>sello en ${fmtDur(c.selloEn)}</b>` : `nivel ${c.h4}`, "h4", c.h4 >= 4)}
        ${rapida("Banco C-0", casillas(h.banco, 24), `${c.banco.toFixed(0)} UE`, "banco", c.banco <= 6)}
        ${rapida("Atención", casillas(e.atencion, 6), c.at, "", e.atencion >= 4)}
        <div class="prox"><b>Si nadie hace nada:</b> ${prox.length ? prox.join(" · ") : "nada cambia en las próximas 12 h"}</div>
        ${e.rover2 !== null ? `<div class="prox"><b>Rover 2:</b> ${e.min >= e.rover2 ? "en C-7" : `llega a las ${fmtHora(e.rover2)}`}</div>` : ""}
      </div>
      ${gm ? `<div class="pie"><button type="button" data-action="hud"><i class="fa-solid fa-users"></i> Abrir el HUD a la cuadrilla</button></div>` : ""}
      <details class="detalle" ${detalleAbierto ? "open" : ""}><summary>Cifras y acciones del Guardián</summary>
      ${fila("Refugio R-3", `${c.r3.toFixed(2)} kg · ${c.r3n}`, `${c.eR3}${c.dep ? " · depurador portátil activo" : ""}`,
        b("cartR3", "+cartucho") + b("filtroR3", "+filtro") + b("purga", "purga") + b("dep", "depurador") + b("r3n", "−1 persona", -1) + b("r3n", "+1", 1), c.eR3 !== "Estable")}
      ${fila("P-2 · aire", c.p2n ? `${c.p2.toFixed(2)} kg · ${c.p2n}` : "—", c.eP2,
        b("cartP2", "+cartucho") + b("filtroP2", "+filtro") + b("p2n", "−1 persona", -1) + b("p2n", "+1", 1), !["Estable", "Evacuada"].includes(c.eP2))}
      ${fila("Bomba de P-2", c.bomba ? "en marcha" : "PARADA", `Fuente: ${fuentes[c.fuente] ?? c.fuente}${c.fuente === "p2" ? ` (${c.bat.toFixed(1)} UE)` : ""}${c.auto ? " · automatismo" : " · sin automatismo: 45 min sin atender y se para"}${c.v12 !== null ? " · V-12 cerrada: ya no es necesaria" : ""}`,
        b("fuente", "rover", "rover") + b("fuente", "portátil", "portatil") + b("fuente", "industrial", "industrial") + b("fuente", "banco", "banco") + b("fuente", "parar", "parada") + b("auto", "automatismo"), !c.bomba && c.v12 === null)}
      ${fila("Fuga H-4", `${c.h4}/6`, c.nH4 + (c.selloEn !== null ? ` · <b>sello de R-3 en ${fmtDur(c.selloEn)}</b>` : ""),
        b("v12", "V-12 gradual") + b("v12golpe", "V-12 de golpe") + b("alivio", "alivio") + b("parche", "parche") + b("e1", "E-1 forzada") + b("h4", "−1", -1) + b("h4", "+1", 1), c.h4 >= 4)}
      ${fila("Banco de C-0", `${c.banco.toFixed(1)} UE`, "2 UE/h fijos · V-12 4 · E-1 6", b("banco", "−4", -4) + b("banco", "−6", -6) + b("banco", "−1", -1), c.banco <= 6)}
      ${fila("Rover 1", `${c.rover.toFixed(1)} UE`, "1 UE/2 km de roca · 1 UE/km de glaciar · 3 UE/h ocupado · 2 UE/h si alimenta la bomba",
        b("rover", "−5", -5) + b("rover", "−1", -1) + b("rover", "+5", 5), c.rover <= 15)}
      ${fila("Rover 2", e.rover2 === null ? "no pedido" : fmtHora(e.rover2), "Con lista justificada: 2 h de preparación + viaje; sin lista: 3 h",
        gm ? `<button type="button" data-action="rover2" data-v="287">pedido ahora, con lista</button><button type="button" data-action="rover2" data-v="347">sin lista</button><button type="button" data-action="rover2" data-v="">anular</button>` : "")}
      ${fila("Atención de la colonia", `${e.atencion}/6`, c.at, aj("atencion", -1, "−1") + aj("atencion", 1, "+1") + aj("atencion", 2, "+2"), e.atencion >= 4)}
      ${c.avisos.length ? `<div class="fila"><div class="t">Registro</div><div class="n">${c.avisos.slice(-6).join("<br>")}</div></div>` : ""}
      ${gm ? `<div class="pie"><button type="button" data-action="deshacer">Deshacer</button><button type="button" data-action="chat"><i class="fa-solid fa-comment"></i> Publicar en el chat</button><button type="button" data-action="reiniciar">Reiniciar</button></div>` : ""}
      </details>`;
    div.querySelector("details").addEventListener("toggle", (ev) => { detalleAbierto = ev.target.open; });
    return div;
  }

  _replaceHTML(result, content) { content.replaceChildren(result); }

  static async #tiempo(ev, target) { await moverHora(Number(target.dataset.delta)); }

  static async #accion(ev, target) {
    const e = this.estado, v = target.dataset.v;
    e.ev = [...(e.ev ?? []), { id: foundry.utils.randomID(), m: e.min, t: target.dataset.t, v: v === "" ? null : (isNaN(Number(v)) ? v : Number(v)) }];
    await this.guardar(e);
  }

  static async #ajustar(ev, target) {
    const e = this.estado, k = target.dataset.campo;
    e[k] = Math.min(6, Math.max(0, Number(e[k]) + Number(target.dataset.delta)));
    await this.guardar(e);
  }

  static async #revelar(ev, target) {
    const e = this.estado, k = target.dataset.k;
    e.rev[k] = !e.rev[k];
    await this.guardar(e);
  }

  static async #rover2(ev, target) {
    const e = this.estado;
    e.rover2 = target.dataset.v === "" ? null : e.min + Number(target.dataset.v);
    await this.guardar(e);
  }

  static async #deshacer() {
    const e = this.estado, ult = (e.ev ?? []).at(-1);
    if (ult?.gasta) e.carga[ult.gasta] = (e.carga[ult.gasta] ?? 0) + 1;
    e.ev = (e.ev ?? []).slice(0, -1);
    await this.guardar(e);
  }

  static async #chat() {
    const e = this.estado, c = calcular(e);
    await ChatMessage.create({
      speaker: { alias: "Nádir · ACE/HRF" },
      content: `<div class="mr-nadir-chat"><h3>Estado de C-7 · ${fmtHora(e.min)}</h3>
        <p><b>R-3:</b> ${c.eR3} · ${c.r3n} personas</p>
        <p><b>P-2:</b> ${c.eP2} · bomba ${c.bomba ? "en marcha" : "parada"}</p>
        <p><b>Fuga H-4:</b> ${c.h4}/6 — ${c.nH4}</p></div>`
    });
  }

  static async #reiniciar() {
    const ok = await foundry.applications.api.DialogV2.confirm({ window: { title: "Reiniciar relojes" }, content: "<p>¿Volver a las 09:36 con los valores iniciales? También se vacían la carga y lo que ven los jugadores.</p>" });
    if (ok) await this.guardar(foundry.utils.deepClone(ESTADO_INICIAL));
  }
}

let panel;
const abrirPanel = () => (panel ??= new PanelEmergencia()).render(true);
const abrirHudTodos = () => { game.socket.emit(`module.${MOD}`, { tipo: "abrirHud" }); Hooks.callAll("mrNadirAbrirHud"); };

Hooks.once("init", () => {
  game.settings.register(MOD, "relojes", {
    scope: "world", config: false, type: Object, default: foundry.utils.deepClone(ESTADO_INICIAL),
    onChange: () => { if (panel?.rendered) panel.render(); Hooks.callAll("mrNadirRelojes"); }
  });
});

Hooks.once("ready", async () => {
  game.modules.get(MOD).api = { abrirPanel, calcular, moverHora, revelar, pedir, ESTADO_INICIAL };
  game.socket.on(`module.${MOD}`, (msg) => {
    if (msg.tipo === "abrirHud") return Hooks.callAll("mrNadirAbrirHud");
    if (game.user === game.users.activeGM) aplicar(msg, msg.userId);
  });
  if (!game.user.isGM) return;
  // Las macros de la aventura vienen con autor ficticio: el GM se las adjudica.
  for (const m of game.macros) {
    if (m.getFlag(MOD, "macro") && !game.users.get(m._source.author)) await m.update({ author: game.user.id });
  }
});

// Botón en los controles de token (sólo GM)
Hooks.on("getSceneControlButtons", (controls) => {
  if (!game.user?.isGM) return;
  const tokens = controls.tokens ?? controls.find?.(c => c.name === "token");
  if (!tokens) return;
  const tool = { name: "mr-nadir-panel", title: "Nádir · Panel de emergencia", icon: "fa-solid fa-gauge-high", button: true, onChange: abrirPanel, onClick: abrirPanel, visible: true };
  if (Array.isArray(tokens.tools)) tokens.tools.push(tool);
  else tokens.tools[tool.name] = { ...tool, order: Object.keys(tokens.tools).length };
});

/* ============================================================================================
 * Escenas, zonas, audio y botones del Guardián
 * Escenas con flags mr-nadir: { slug, tipo: "imagen"|"mapa", mapa, nombre, sfx: [claves manuales] }
 * Playlists: flags mr-nadir.rol = "sfx" | "musica" | "escena"; cada sonido lleva flags mr-nadir.clave
 * ============================================================================================ */

const esGM = () => game.user?.isGM;
const escena = (slug) => game.scenes.find(s => s.getFlag(MOD, "slug") === slug);
const playlistRol = (rol) => game.playlists.find(p => p.getFlag(MOD, "rol") === rol);

async function activarEscena(slug) {
  const s = escena(slug);
  if (!s) return ui.notifications.warn(`Nádir: no encuentro la escena «${slug}». ¿Has importado la aventura?`);
  await s.activate();
  if (REVELA_ESCENA[slug]) await revelar(...REVELA_ESCENA[slug]);
}

async function volverAlMapa(mapa) {
  mapa = mapa || canvas.scene?.getFlag(MOD, "mapa") || "c7";
  return activarEscena(mapa);
}

async function sfx(clave) {
  const pl = playlistRol("sfx");
  const snd = pl?.sounds.find(s => s.getFlag(MOD, "clave") === clave);
  if (!snd) return ui.notifications.warn(`Nádir: efecto «${clave}» no encontrado.`);
  if (snd.playing) await pl.stopSound(snd);
  await pl.playSound(snd);
}

async function pararEfectos() {
  const pl = playlistRol("sfx");
  if (pl) await pl.stopAll();
}

async function musica(clave) {
  const pl = playlistRol("musica");
  const snd = pl?.sounds.find(s => s.getFlag(MOD, "clave") === clave);
  if (!snd) return;
  for (const s of pl.sounds) if (s.playing && s !== snd) await pl.stopSound(s);
  await pl.playSound(snd);
}

async function mostrarDoc(codigo) {
  // «D12-B» muestra la primera parte; «D12-B/3», la tercera (registros por tramos o variantes)
  const [cod, parte] = codigo.split("/");
  const doc = game.journal.find(j => j.getFlag(MOD, "doc") === cod && (!parte || j.getFlag(MOD, "parte") === Number(parte)));
  if (!doc) return ui.notifications.warn(`Nádir: documento ${codigo} no encontrado.`);
  const J = foundry.documents?.collections?.Journal ?? globalThis.Journal;
  await J.show(doc, { force: true });
  if (REVELA_DOC[cod]) await revelar(...REVELA_DOC[cod]);
}

async function avanzarReloj(min) {
  await moverHora(min);
  ui.notifications.info(`Nádir: ahora son las ${fmtHora(leerEstado().min)}.`);
}

// Lo que ven los jugadores en su HUD se abre solo cuando el Guardián enseña la pieza que lo justifica
const REVELA_DOC = { D05: ["h4"], D06: ["r3"], D07: ["p2"], D14: ["p2"] };
const REVELA_ESCENA = { "c7-1": ["banco", "h4"], "c7-7": ["r3"], "c7-8": ["p2"] };

function leerDescripcion(scene = canvas.scene) {
  const j = scene?.journal;
  if (!j) return ui.notifications.warn("Nádir: esta escena no tiene descripción enlazada.");
  j.sheet.render(true, { pageId: scene.journalEntryPage });
}

const ACCIONES = {
  escena: activarEscena, mapa: volverAlMapa, sfx, parar: pararEfectos, musica, doc: mostrarDoc,
  panel: () => abrirPanel(), reloj: avanzarReloj, leer: () => leerDescripcion(), anular
};
const ICONOS = { escena: "fa-panorama", mapa: "fa-map", sfx: "fa-volume-high", musica: "fa-music", doc: "fa-file-lines", panel: "fa-gauge-high", reloj: "fa-clock", anular: "fa-rotate-left", parar: "fa-volume-xmark", leer: "fa-book-open" };

function boton(accion, arg, texto) {
  const a = document.createElement("a");
  a.className = `mr-nadir-btn mr-nadir-${accion}`;
  a.dataset.accion = accion;
  a.dataset.arg = arg ?? "";
  a.innerHTML = `<i class="fa-solid ${ICONOS[accion] ?? "fa-bolt"}"></i> ${texto}`;
  a.title = "Sólo el Guardián";
  return a;
}

Hooks.once("init", () => {
  CONFIG.TextEditor.enrichers.push({
    id: "mr-nadir",
    pattern: /@Nadir(Escena|Mapa|Sfx|Musica|Doc|Panel|Reloj|Parar|Anular)\[([^\]]*)\](?:\{([^}]*)\})?/g,
    enricher: async (match) => {
      const accion = match[1].toLowerCase();
      if (!esGM()) return document.createElement("span");
      const textos = { escena: "Mostrar escena a todos", mapa: "Volver al mapa con todos", sfx: `Efecto: ${match[2]}`, musica: `Música: ${match[2]}`,
        doc: `Mostrar ${match[2]} a los jugadores`, panel: "Panel de emergencia", reloj: `Reloj ${match[2]} min`, parar: "Parar efectos", anular: "Anular" };
      return boton(accion, match[2], match[3] || textos[accion]);
    }
  });
  document.addEventListener("click", (ev) => {
    const a = ev.target.closest?.(".mr-nadir-btn");
    if (!a) return;
    ev.preventDefault();
    ev.stopPropagation();
    if (!esGM()) return;
    ACCIONES[a.dataset.accion]?.(a.dataset.arg);
  }, true);
});

/* ---------------- Aviso de zona (lo llama el script de cada región del mapa) ---------------- */
async function zona(slug, token) {
  if (game.user !== game.users.activeGM) return;
  if (!token?.actor?.hasPlayerOwner) return;
  const s = escena(slug);
  const nombre = s?.getFlag(MOD, "nombre") ?? slug;
  const pagina = s?.journal ? `@UUID[${s.journal.uuid}.JournalEntryPage.${s.journalEntryPage}]{Leer descripción}` : "";
  await ChatMessage.create({
    whisper: game.users.filter(u => u.isGM).map(u => u.id),
    speaker: { alias: "Nádir · zona" },
    content: `<div class="mr-nadir-chat"><p><b>${token.name}</b> entra en <b>${nombre}</b>.</p>
      <p>@NadirEscena[${slug}]{Mostrar escena a todos} ${pagina}</p></div>`
  });
}

/* ---------------- Barra del Guardián en escenas de imagen ---------------- */
function quitarHud() { document.getElementById("mr-nadir-hud")?.remove(); }

function ponerHud(scene) {
  quitarHud();
  if (!esGM() || !scene) return;
  const tipo = scene.getFlag(MOD, "tipo");
  if (!tipo) return;
  const hud = document.createElement("div");
  hud.id = "mr-nadir-hud";
  const titulo = document.createElement("span");
  titulo.className = "t";
  titulo.textContent = scene.getFlag(MOD, "nombre") ?? scene.name;
  hud.append(titulo);
  if (tipo === "imagen") hud.append(boton("mapa", scene.getFlag(MOD, "mapa"), "Volver al mapa"));
  hud.append(boton("leer", "", "Descripción"));
  for (const k of scene.getFlag(MOD, "sfx") ?? []) {
    const [clave, nombre] = Array.isArray(k) ? k : [k, k];
    hud.append(boton("sfx", clave, nombre));
  }
  hud.append(boton("parar", "", ""));
  if (tipo === "mapa") hud.append(boton("panel", "", "Panel"));
  document.body.append(hud);
}

/* ---------------- Pantalla de fósforo y radar en los mapas ---------------- */
function quitarCrt() { document.getElementById("mr-nadir-crt")?.remove(); }

function ponerCrt(scene) {
  quitarCrt();
  if (scene?.getFlag(MOD, "tipo") !== "mapa") return;
  const d = document.createElement("div");
  d.id = "mr-nadir-crt";
  d.innerHTML = `<div class="barrido"></div><div class="lineas"></div>`;
  document.body.append(d);
}

function eco(tokenDoc) {
  if (!canvas.ready || canvas.scene?.getFlag(MOD, "tipo") !== "mapa") return;
  const obj = tokenDoc.object;
  if (!obj?.visible) return;
  const { x, y } = obj.center;
  const g = new PIXI.Graphics();
  canvas.interface.addChild(g);
  const t0 = performance.now();
  const max = canvas.grid.size * 4;
  const tick = () => {
    const k = (performance.now() - t0) / 1400;
    g.clear();
    if (k >= 1 || g.destroyed) { canvas.app.ticker.remove(tick); g.destroy(); return; }
    for (const off of [0, 0.25]) {
      const kk = Math.max(0, k - off);
      g.lineStyle(3, 0x7dff9a, (1 - kk) * 0.7).drawCircle(x, y, 10 + kk * max);
    }
  };
  canvas.app.ticker.add(tick);
}

Hooks.on("canvasReady", (c) => { ponerHud(c.scene); ponerCrt(c.scene); });
Hooks.on("updateToken", (doc, changes) => { if ("x" in changes || "y" in changes) eco(doc); });
Hooks.on("updateScene", (scene) => { if (scene.id === canvas.scene?.id) ponerHud(scene); });

Hooks.once("ready", () => {
  Object.assign(game.modules.get(MOD).api, { activarEscena, volverAlMapa, sfx, pararEfectos, musica, mostrarDoc, avanzarReloj, zona, leerDescripcion });
});
