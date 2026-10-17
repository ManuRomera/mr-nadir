// MR- Nádir · Panel de emergencia del Guardián: hora desde T0 y los relojes del escenario
// (R-3, P-2, Fuga H-4, energía del rover, cartuchos y Atención de la colonia).
// El estado vive en un ajuste de mundo; sólo el GM lo modifica y puede publicarlo en el chat.

const MOD = "mr-nadir";
const T0_MIN = 9 * 60 + 36;          // 09:36
const INICIO = 12;                   // se empieza a jugar a T+12 min (mensaje de Mara)

const ESTADO_INICIAL = {
  min: INICIO,        // minutos transcurridos desde T0
  r3Extra: 0,         // horas añadidas a R-3 (cartuchos +2 h c/u, mitigaciones)
  r3Pausa: false,     // filtración industrial activa: R-3 no consume
  r3PausaDesde: 0,
  r3Pausado: 0,       // minutos acumulados en pausa
  filtroExtra: 0,     // horas añadidas al filtro de P-2
  bateriaExtra: 0,    // horas añadidas a la batería de P-2
  h4: 1,              // Fuga H-4 (0-6)
  ue: 90,             // energía del rover 1
  cartuchos: 2,       // cartuchos de CO₂ del rover 1
  atencion: 0         // Atención de la colonia (zona actual, 0-6)
};

const fmtHora = (m) => {
  const t = (T0_MIN + m) % 1440;
  return `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
};
const fmtDur = (m) => {
  const s = m < 0 ? "−" : "";
  m = Math.abs(Math.round(m));
  return `${s}${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
};

function calcular(e) {
  const pausa = e.r3Pausado + (e.r3Pausa ? e.min - e.r3PausaDesde : 0);
  const r3 = 600 + e.r3Extra * 60 - (e.min - pausa);
  const filtro = 300 + e.filtroExtra * 60 - e.min;
  const bateria = 360 + e.bateriaExtra * 60 - e.min;
  const estadoR3 = r3 > 180 ? "Estable" : r3 > 60 ? "Degradado" : r3 > 0 ? "Degradado (crítico inminente)" : "Crítico";
  const h4 = e.h4 >= 6 ? "E-1 y la ruta baja inundadas; riesgo estructural en R-3"
    : e.h4 >= 4 ? "Daños serios en pasillos inferiores · el sumidero de R-3 se llena" : "Contenida";
  const at = e.atencion >= 6 ? "Defensores o enjambre (3–6) en la zona" : e.atencion >= 4 ? "3 ejemplares convergen"
    : e.atencion >= 2 ? "1 explorador se acerca (5–15 min)" : "Sin respuesta";
  return { r3, filtro, bateria, estadoR3, h4, at, pausa };
}

class PanelEmergencia extends foundry.applications.api.ApplicationV2 {
  static DEFAULT_OPTIONS = {
    id: "mr-nadir-panel",
    classes: ["mr-nadir-panel"],
    window: { title: "Nádir · Panel de emergencia", icon: "fa-solid fa-gauge-high", resizable: true },
    position: { width: 430, height: "auto" },
    actions: {
      tiempo: PanelEmergencia.#tiempo,
      ajustar: PanelEmergencia.#ajustar,
      pausa: PanelEmergencia.#pausa,
      chat: PanelEmergencia.#chat,
      reiniciar: PanelEmergencia.#reiniciar
    }
  };

  get estado() { return foundry.utils.mergeObject(foundry.utils.deepClone(ESTADO_INICIAL), game.settings.get(MOD, "relojes") ?? {}); }

  async guardar(e) {
    if (!game.user.isGM) return ui.notifications.warn("Sólo el Guardián modifica los relojes.");
    await game.settings.set(MOD, "relojes", e);
    this.render();
  }

  async _renderHTML() {
    const e = this.estado, c = calcular(e), gm = game.user.isGM;
    const btn = (accion, campo, delta, txt) => gm ? `<button type="button" data-action="${accion}" data-campo="${campo}" data-delta="${delta}">${txt}</button>` : "";
    const fila = (titulo, valor, nota, botones = "", alerta = false) =>
      `<div class="fila ${alerta ? "alerta" : ""}"><div class="t">${titulo}</div><div class="v">${valor}</div><div class="n">${nota}</div><div class="b">${botones}</div></div>`;
    const div = document.createElement("div");
    div.className = "mr-nadir-body";
    div.innerHTML = `
      <div class="reloj"><span>T+${fmtDur(e.min)}</span><b>${fmtHora(e.min)}</b></div>
      ${gm ? `<div class="tiempo">${[-10, 10, 30, 60].map(d => `<button type="button" data-action="tiempo" data-delta="${d}">${d > 0 ? "+" : ""}${d} min</button>`).join("")}</div>` : ""}
      ${fila("Refugio R-3", fmtDur(c.r3), `${c.estadoR3}${e.r3Pausa ? " · filtración industrial activa" : ""}`,
        btn("ajustar", "r3Extra", 2, "+2 h (cartucho)") + (gm ? `<button type="button" data-action="pausa">${e.r3Pausa ? "Quitar filtración" : "Filtración industrial"}</button>` : ""), c.r3 <= 180)}
      ${fila("P-2 · filtro", fmtDur(c.filtro), c.filtro > 0 ? "Aire aceptable" : "El aire de P-2 se degrada", btn("ajustar", "filtroExtra", 1, "+1 h"), c.filtro <= 60)}
      ${fila("P-2 · batería", fmtDur(c.bateria), c.bateria > 0 ? "La bomba funciona" : "Protección por bajo voltaje: la bomba se para", btn("ajustar", "bateriaExtra", 1, "+1 h"), c.bateria <= 60)}
      ${fila("Fuga H-4", `${e.h4}/6`, c.h4, btn("ajustar", "h4", -1, "−1") + btn("ajustar", "h4", 1, "+1"), e.h4 >= 4)}
      ${fila("Rover 1 · energía", `${e.ue} UE`, "1 UE/2 km fácil · 2 UE/2 km difícil · electrólisis 3 UE/h", btn("ajustar", "ue", -1, "−1") + btn("ajustar", "ue", -5, "−5") + btn("ajustar", "ue", 5, "+5"), e.ue <= 15)}
      ${fila("Cartuchos CO₂", `${e.cartuchos}`, "Cada uno: ~2 h más para R-3", btn("ajustar", "cartuchos", -1, "−1") + btn("ajustar", "cartuchos", 1, "+1"))}
      ${fila("Atención de la colonia", `${e.atencion}/6`, c.at, btn("ajustar", "atencion", -1, "−1") + btn("ajustar", "atencion", 1, "+1") + btn("ajustar", "atencion", 2, "+2"), e.atencion >= 4)}
      ${gm ? `<div class="pie"><button type="button" data-action="chat"><i class="fa-solid fa-comment"></i> Publicar en el chat</button><button type="button" data-action="reiniciar">Reiniciar</button></div>` : ""}`;
    return div;
  }

  _replaceHTML(result, content) { content.replaceChildren(result); }

  static async #tiempo(ev, target) {
    const e = this.estado;
    e.min = Math.max(0, e.min + Number(target.dataset.delta));
    await this.guardar(e);
  }

  static async #ajustar(ev, target) {
    const e = this.estado, k = target.dataset.campo, d = Number(target.dataset.delta);
    e[k] = Number(e[k]) + d;
    if (k === "h4" || k === "atencion") e[k] = Math.min(6, Math.max(0, e[k]));
    if (k === "ue" || k === "cartuchos") e[k] = Math.max(0, e[k]);
    if (k === "r3Extra" && d > 0 && e.cartuchos > 0) e.cartuchos -= 1;
    await this.guardar(e);
  }

  static async #pausa() {
    const e = this.estado;
    if (e.r3Pausa) { e.r3Pausado += e.min - e.r3PausaDesde; e.r3Pausa = false; }
    else { e.r3Pausa = true; e.r3PausaDesde = e.min; }
    await this.guardar(e);
  }

  static async #chat() {
    const e = this.estado, c = calcular(e);
    await ChatMessage.create({
      speaker: { alias: "Nádir · ACE/HRF" },
      content: `<div class="mr-nadir-chat"><h3>Estado de C-7 · ${fmtHora(e.min)} (T+${fmtDur(e.min)})</h3>
        <p><b>R-3:</b> ${c.estadoR3} · margen ${fmtDur(c.r3)}</p>
        <p><b>P-2:</b> filtro ${fmtDur(c.filtro)} · batería ${fmtDur(c.bateria)}</p>
        <p><b>Fuga H-4:</b> ${e.h4}/6 — ${c.h4}</p></div>`
    });
  }

  static async #reiniciar() {
    const ok = await foundry.applications.api.DialogV2.confirm({ window: { title: "Reiniciar relojes" }, content: "<p>¿Volver a T+12 min con los valores iniciales?</p>" });
    if (ok) await this.guardar(foundry.utils.deepClone(ESTADO_INICIAL));
  }
}

let panel;
const abrirPanel = () => (panel ??= new PanelEmergencia()).render(true);

Hooks.once("init", () => {
  game.settings.register(MOD, "relojes", {
    scope: "world", config: false, type: Object, default: foundry.utils.deepClone(ESTADO_INICIAL),
    onChange: () => panel?.rendered && panel.render()
  });
});

Hooks.once("ready", async () => {
  game.modules.get(MOD).api = { abrirPanel, calcular, ESTADO_INICIAL };
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
  const doc = game.journal.find(j => j.getFlag(MOD, "doc") === codigo);
  if (!doc) return ui.notifications.warn(`Nádir: documento ${codigo} no encontrado.`);
  const J = foundry.documents?.collections?.Journal ?? globalThis.Journal;
  await J.show(doc, { force: true });
}

async function avanzarReloj(min) {
  const e = foundry.utils.mergeObject(foundry.utils.deepClone(ESTADO_INICIAL), game.settings.get(MOD, "relojes") ?? {});
  e.min = Math.max(0, e.min + Number(min));
  await game.settings.set(MOD, "relojes", e);
  ui.notifications.info(`Nádir: ahora son las ${fmtHora(e.min)} (T+${fmtDur(e.min)}).`);
}

function leerDescripcion(scene = canvas.scene) {
  const j = scene?.journal;
  if (!j) return ui.notifications.warn("Nádir: esta escena no tiene descripción enlazada.");
  j.sheet.render(true, { pageId: scene.journalEntryPage });
}

const ACCIONES = {
  escena: activarEscena, mapa: volverAlMapa, sfx, parar: pararEfectos, musica, doc: mostrarDoc,
  panel: () => abrirPanel(), reloj: avanzarReloj, leer: () => leerDescripcion()
};
const ICONOS = { escena: "fa-panorama", mapa: "fa-map", sfx: "fa-volume-high", musica: "fa-music", doc: "fa-file-lines", panel: "fa-gauge-high", reloj: "fa-clock", parar: "fa-volume-xmark", leer: "fa-book-open" };

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
    pattern: /@Nadir(Escena|Mapa|Sfx|Musica|Doc|Panel|Reloj|Parar)\[([^\]]*)\](?:\{([^}]*)\})?/g,
    enricher: async (match) => {
      const accion = match[1].toLowerCase();
      if (!esGM()) return document.createElement("span");
      const textos = { escena: "Mostrar escena a todos", mapa: "Volver al mapa con todos", sfx: `Efecto: ${match[2]}`, musica: `Música: ${match[2]}`,
        doc: `Mostrar ${match[2]} a los jugadores`, panel: "Panel de emergencia", reloj: `Reloj ${match[2]} min`, parar: "Parar efectos" };
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
