// MR- Nádir · Panel de emergencia del Guardián: hora desde T0 y los relojes del escenario
// (R-3, P-2, Fuga H-4, banco de C-0, rover y Atención de la colonia).
// El estado es un registro de acciones con hora; los relojes se recalculan minuto a minuto
// con las mismas reglas que tools/relojes.py y el capítulo «Relojes, recursos y cronología».

const MOD = "mr-nadir";
const T0_MIN = 9 * 60 + 36;          // 09:36
const CO2 = 0.046 / 60;              // kg por persona y minuto
const CARTUCHO = 1.2, FILTRO = 0.3, PURGA = 0.6;
const DEPOSITO_MIN = 1044;           // minutos de bombeo hasta llenar el depósito (≈ 02:40)

const ESTADO_INICIAL = { min: 0, ev: [], ue: 90, atencion: 0 };

const fmtHora = (m) => {
  const t = ((T0_MIN + Math.round(m)) % 1440 + 1440) % 1440;
  return `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
};
const fmtDur = (m) => {
  const s = m < 0 ? "−" : "";
  m = Math.abs(Math.round(m));
  return `${s}${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
};

function estadoR3(kg, n) {
  const h = kg / (0.046 * Math.max(n, 1));
  if (kg > 0) return h > 3 ? "Estable" : "Degradado";
  return -h < 3 ? "Crítico" : -h < 6 ? "Grave" : "Colapso";
}
function estadoP2(kg, n) {
  if (kg > 0) return "Estable";
  const h = -kg / (0.046 * Math.max(n, 1));
  return h < 2 ? "Degradado" : h < 5 ? "Crítico" : "Colapso";
}

/** Recalcula todos los relojes desde T0 hasta e.min aplicando las acciones registradas. */
function calcular(e) {
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
  }
  const nH4 = ["Escurrido · E-1 en 60 min", "Agua al tobillo · E-1 en 60–90 min", "Media pierna · E-1 en 90–120 min · J-17 solo con V-12",
    "Rodilla · E-1 solo con V-12 cerrada · ruta baja lenta", "Cintura · agua en la rejilla de R-3 · E-1 imposible · la radio de Serrat calla",
    "El sello inferior de R-3 rezuma", "Ruta baja inundada · el sello de R-3 falla en 120 min"][s.h4];
  const at = e.atencion >= 6 ? "Defensores o grupo de 3–6" : e.atencion >= 5 ? "Uno prueba el contacto" : e.atencion >= 3 ? "Tres ejemplares convergen"
    : e.atencion >= 2 ? "Un explorador se acerca (5–15 min)" : "Inactiva";
  return { ...s, eR3: estadoR3(s.r3, s.r3n), eP2: s.p2n ? estadoP2(s.p2, s.p2n) : "Evacuada", nH4, at,
    selloEn: s.sello !== null ? s.sello - e.min : null };
}

class PanelEmergencia extends foundry.applications.api.ApplicationV2 {
  static DEFAULT_OPTIONS = {
    id: "mr-nadir-panel",
    classes: ["mr-nadir-panel"],
    window: { title: "Nádir · Panel de emergencia", icon: "fa-solid fa-gauge-high", resizable: true },
    position: { width: 470, height: "auto" },
    actions: {
      tiempo: PanelEmergencia.#tiempo,
      accion: PanelEmergencia.#accion,
      ajustar: PanelEmergencia.#ajustar,
      deshacer: PanelEmergencia.#deshacer,
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
    const b = (t, txt, v = "") => gm ? `<button type="button" data-action="accion" data-t="${t}" data-v="${v}">${txt}</button>` : "";
    const aj = (campo, d, txt) => gm ? `<button type="button" data-action="ajustar" data-campo="${campo}" data-delta="${d}">${txt}</button>` : "";
    const fila = (titulo, valor, nota, botones = "", alerta = false) =>
      `<div class="fila ${alerta ? "alerta" : ""}"><div class="t">${titulo}</div><div class="v">${valor}</div><div class="n">${nota}</div><div class="b">${botones}</div></div>`;
    const fuentes = { p2: "batería de P-2", rover: "rover", portatil: "batería portátil", industrial: "batería industrial", banco: "banco de C-0", parada: "ninguna" };
    const div = document.createElement("div");
    div.className = "mr-nadir-body";
    div.innerHTML = `
      <div class="reloj"><span>T+${fmtDur(e.min)}</span><b>${fmtHora(e.min)}</b></div>
      ${gm ? `<div class="tiempo">${[-10, 10, 30, 60].map(d => `<button type="button" data-action="tiempo" data-delta="${d}">${d > 0 ? "+" : ""}${d} min</button>`).join("")}</div>` : ""}
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
      ${fila("Atención de la colonia", `${e.atencion}/6`, c.at, aj("atencion", -1, "−1") + aj("atencion", 1, "+1") + aj("atencion", 2, "+2"), e.atencion >= 4)}
      ${c.avisos.length ? `<div class="fila"><div class="t">Registro</div><div class="n">${c.avisos.slice(-6).join("<br>")}</div></div>` : ""}
      ${gm ? `<div class="pie"><button type="button" data-action="deshacer">Deshacer</button><button type="button" data-action="chat"><i class="fa-solid fa-comment"></i> Publicar en el chat</button><button type="button" data-action="reiniciar">Reiniciar</button></div>` : ""}`;
    return div;
  }

  _replaceHTML(result, content) { content.replaceChildren(result); }

  static async #tiempo(ev, target) {
    const e = this.estado;
    e.min = Math.max(0, e.min + Number(target.dataset.delta));
    await this.guardar(e);
  }

  static async #accion(ev, target) {
    const e = this.estado, v = target.dataset.v;
    e.ev = [...(e.ev ?? []), { m: e.min, t: target.dataset.t, v: v === "" ? null : (isNaN(Number(v)) ? v : Number(v)) }];
    await this.guardar(e);
  }

  static async #ajustar(ev, target) {
    const e = this.estado, k = target.dataset.campo;
    e[k] = Math.min(6, Math.max(0, Number(e[k]) + Number(target.dataset.delta)));
    await this.guardar(e);
  }

  static async #deshacer() {
    const e = this.estado;
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
    const ok = await foundry.applications.api.DialogV2.confirm({ window: { title: "Reiniciar relojes" }, content: "<p>¿Volver a las 09:36 con los valores iniciales?</p>" });
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
