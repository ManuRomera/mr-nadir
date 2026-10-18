// MR- Nádir · HUD de la cuadrilla: lo que los jugadores ven y gestionan ellos mismos.
// Trajes (cada uno el suyo), carga del rover y los relojes que ya han descubierto. Lo que pulsan
// se anota en el registro del Guardián (js/nadir.js) a la hora actual; él solo mueve la hora.

import { MOD, CARGA, ACC_JUGADOR, leerEstado, calcular, horas, casillas, fmtHora, fmtDur, pedir, trajes, trajeMin, trajeReal, trajeMax, umbilical, esfuerzo, recambio } from "./nadir.js";

const ETIQUETA = {
  cartR3: "Cartucho → R-3", filtroR3: "Filtro → R-3", dep: "Depurador en R-3", sacaR3: "Sale alguien de R-3",
  cartP2: "Cartucho → P-2", filtroP2: "Filtro → P-2", bombaRover: "Bomba al rover", bombaPortatil: "Bomba a batería portátil",
  auto: "Automatismo listo", sacaP2: "Sale alguien de P-2", v12: "V-12 cerrada (gradual)", alivio: "Alivio de H-4 restituido"
};
// Lo que se oye por radio o se ve en un manómetro: nunca kilos ni reglas
const VOZ_R3 = { Estable: "Inés, por radio: «El ventilador aguanta».", Degradado: "Por radio, toses y voces pastosas. Alguien cuenta catorce.",
  Crítico: "Mara repite frases. Cuesta despertar a alguien.", Grave: "Ya no contesta todo el mundo.", Colapso: "R-3 no contesta." };
const VOZ_P2 = { Estable: "Quiroga habla claro.", Degradado: "Quiroga habla bajo, despacio.", Crítico: "Respuestas cortas. Ivo ya no propone nada.",
  Colapso: "P-2 no contesta.", Evacuada: "P-2 está vacía." };

class HudCuadrilla extends foundry.applications.api.ApplicationV2 {
  static DEFAULT_OPTIONS = {
    id: "mr-nadir-cuadrilla",
    classes: ["mr-nadir-panel", "mr-nadir-cuadrilla"],
    window: { title: "Nádir · Consola de la cuadrilla", icon: "fa-solid fa-users", resizable: true },
    position: { width: 400, height: "auto", top: 80, left: 120 },
    actions: {
      umbilical: HudCuadrilla.#umbilical,
      recambio: HudCuadrilla.#recambio,
      esfuerzo: HudCuadrilla.#esfuerzo,
      carga: (ev, t) => pedir({ tipo: "carga", k: t.dataset.k, d: Number(t.dataset.d) }),
      rover: (ev, t) => pedir({ tipo: "rover", d: Number(t.dataset.d) }),
      accion: (ev, t) => pedir({ tipo: "accion", k: t.dataset.k })
    }
  };

  async _renderHTML() {
    const e = leerEstado(), c = calcular(e), h = horas(c), rev = e.rev;
    const btn = (accion, datos, txt, ok = true, titulo = "") =>
      `<button type="button" data-action="${accion}" ${Object.entries(datos).map(([k, v]) => `data-${k}="${v}"`).join(" ")} ${ok ? "" : "disabled"} ${titulo ? `title="${titulo}"` : ""}>${txt}</button>`;
    const sec = (titulo, cuerpo) => `<section><h3>${titulo}</h3>${cuerpo}</section>`;
    const fila = (t, cas, nota, alerta = false, botones = "") =>
      `<div class="rap ${alerta ? "alerta" : ""}"><div class="t">${t}</div><div class="c">${cas}</div><div class="e">${nota}</div><div class="b">${botones}</div></div>`;

    const trajesHtml = trajes().map(a => {
      const resto = trajeMin(a, e.min), real = trajeReal(a, e.min), max = trajeMax(a), f = a.getFlag(MOD, "traje"), suelto = f && f.desde !== null;
      const mio = a.isOwner && !game.user.isGM ? " mio" : "";
      return `<div class="rap traje${mio} ${real <= 30 ? "alerta" : ""}"><div class="t">${a.name}</div>
        <div class="c">${casillas(resto / 60, max / 60)}</div>
        <div class="e">${resto <= 0 ? "<b>SIN AIRE</b>" : `${fmtDur(real)} ${f?.esf ? "en esfuerzo" : "a ritmo normal"}`} · ${suelto ? "con mochila" : "con umbilical"}</div>
        <div class="b">${btn("umbilical", { id: a.id }, suelto ? "Conectar umbilical" : "Pasar a mochila", a.isOwner)}${btn("esfuerzo", { id: a.id }, f?.esf ? "Ritmo normal" : "Esfuerzo", a.isOwner, "En esfuerzo o estrés la mochila dura un tercio")}${btn("recambio", { id: a.id }, "Recambio", a.isOwner && e.carga.recambio > 0, "Gasta un recambio de mochila de la carga (10 min con ayuda)")}</div></div>`;
    }).join("");

    const relojes = [];
    if (rev.r3) relojes.push(fila("Refugio R-3", c.r3n ? casillas(h.r3, 12, { exceso: 6 }) : "—", c.r3n ? (c.dep ? "El depurador portátil zumba. " : "") + VOZ_R3[c.eR3] + ` · ${c.r3n} dentro` : "Vacío.", c.r3n && c.eR3 !== "Estable"));
    if (rev.p2) {
      relojes.push(fila("P-2 · aire", c.p2n ? casillas(h.p2, 12, { exceso: 5 }) : "—", VOZ_P2[c.eP2], !["Estable", "Evacuada"].includes(c.eP2)));
      const fuente = { p2: "su batería", portatil: "la batería portátil", industrial: "la batería industrial", rover: "el rover", banco: "el banco de C-0" }[c.fuente];
      relojes.push(fila("Bomba de P-2", c.bomba ? casillas(h.bat, 12) : "<b class='rojo'>PARADA</b>",
        c.bomba ? `El motor golpea, irregular. Tira de ${fuente}.` : c.v12 !== null ? "Parada. Con V-12 cerrada ya no hace falta." : "El motor ha callado.", !c.bomba && c.v12 === null));
    }
    if (rev.h4) relojes.push(fila("Aguja del tramo bajo", casillas(c.h4, 6), c.v12 !== null ? "V-12 cerrada." : "", c.h4 >= 4));
    if (rev.banco) relojes.push(fila("Banco de C-0", casillas(h.banco, 24), `${Math.max(0, c.banco).toFixed(0)} UE`, c.banco <= 6));
    if (e.rover2 !== null) relojes.push(fila("Rover 2", "", e.min >= e.rover2 ? "En C-7." : `Bastión: «Llegamos hacia las ${fmtHora(e.rover2)}».`));

    const acciones = Object.entries(ACC_JUGADOR).filter(([, a]) => rev[a.rev])
      .map(([k, a]) => btn("accion", { k }, ETIQUETA[k], !a.gasta || e.carga[a.gasta] > 0, a.gasta ? `Gasta: ${CARGA[a.gasta].toLowerCase()}` : "")).join("");

    const carga = Object.entries(CARGA).map(([k, n]) =>
      `<div class="item"><span>${n}</span><b>${e.carga[k] ?? 0}</b>${btn("carga", { k, d: -1 }, "−", (e.carga[k] ?? 0) > 0)}${btn("carga", { k, d: 1 }, "+")}</div>`).join("");

    const div = document.createElement("div");
    div.className = "mr-nadir-body";
    div.innerHTML = `
      <div class="reloj"><span>Hora de traje</span><b>${fmtHora(e.min)}</b></div>
      ${sec("Trajes de faena", trajesHtml || "<p class='vacio'>No hay personajes de jugador.</p>")}
      ${sec("Lo que sabéis de C-7", relojes.join("") || "<p class='vacio'>De C-7 solo tenéis el mensaje cortado de Mara.</p>")}
      ${acciones ? sec("Lo que habéis hecho", `<div class="acc">${acciones}</div><p class="nota">Se anota a la hora actual. El Guardián lo ve y puede anularlo.</p>`) : ""}
      ${sec("Rover 1 y carga", fila("Batería", casillas(c.rover, 18, { paso: 5 }), `${c.rover.toFixed(0)} UE · 1 UE cada 2 km de roca, 1 por km de glaciar, 3/h con gente conectada`, c.rover <= 15,
        btn("rover", { d: -5 }, "−5") + btn("rover", { d: -1 }, "−1") + btn("rover", { d: 5 }, "+5")) + `<div class="carga">${carga}</div>`)}`;
    return div;
  }

  _replaceHTML(result, content) { content.replaceChildren(result); }

  static async #umbilical(ev, t) { const a = game.actors.get(t.dataset.id); if (a?.isOwner) await umbilical(a); }
  static async #esfuerzo(ev, t) { const a = game.actors.get(t.dataset.id); if (a?.isOwner) await esfuerzo(a); }
  static async #recambio(ev, t) { const a = game.actors.get(t.dataset.id); if (a?.isOwner) await recambio(a); }
}

let hud;
export const abrirHud = () => (hud ??= new HudCuadrilla()).render(true);
const refrescar = () => { if (hud?.rendered) hud.render(); };

Hooks.on("mrNadirRelojes", refrescar);
Hooks.on("mrNadirAbrirHud", abrirHud);
Hooks.on("updateActor", (act, cambios) => { if (foundry.utils.hasProperty(cambios, `flags.${MOD}`)) refrescar(); });
Hooks.once("ready", () => { game.modules.get(MOD).api.abrirHud = abrirHud; });

// Botón en los controles de token para todo el mundo
Hooks.on("getSceneControlButtons", (controls) => {
  const tokens = controls.tokens ?? controls.find?.(c => c.name === "token");
  if (!tokens) return;
  const tool = { name: "mr-nadir-cuadrilla", title: "Nádir · Consola de la cuadrilla", icon: "fa-solid fa-users", button: true, onChange: abrirHud, onClick: abrirHud, visible: true };
  if (Array.isArray(tokens.tools)) tokens.tools.push(tool);
  else tokens.tools[tool.name] = { ...tool, order: Object.keys(tokens.tools).length };
});
