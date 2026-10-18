// MR- Nádir · Instalación automática de la aventura y tutorial guiado.
// - En un mundo vacío, el Guardián activo importa solo la aventura la primera vez.
// - Dos tutoriales (foundry.nue.Tour): «direccion» para el Guardián y «jugadores». Se ofrecen la primera vez y
//   se repiten desde Configuración → «MR- Nádir» o Configuración → Tours.
import { MOD } from "./nadir.js";

const PACK = `${MOD}.aventura`;
const esperar = (ms) => new Promise(r => setTimeout(r, ms));
const api = () => game.modules.get(MOD).api;
const TOURS = [
  { clave: "direccion", ruta: `modules/${MOD}/tours/direccion.json` },
  { clave: "jugadores", ruta: `modules/${MOD}/tours/jugadores.json` }
];

Hooks.once("init", () => {
  // importada: la aventura ya se ha importado (sola o a mano) y no se vuelve a hacer sola.
  game.settings.register(MOD, "importada", { scope: "world", config: false, type: Boolean, default: false });
  game.settings.register(MOD, "tutorialOfrecido", { scope: "client", config: false, type: Boolean, default: false });
});

/* ---------------- Importación ---------------- */

/** Un mundo vacío no tiene personajes, objetos, diarios, listas de reproducción, macros ni tablas, y su única escena,
 *  si la hay, es la de bienvenida que Foundry crea en un mundo nuevo (su fondo está en nue/). */
function mundoVacio() {
  const sinContenido = ["actors", "items", "journal", "playlists", "macros", "tables", "cards"].every(c => !game[c]?.size);
  return sinContenido && game.scenes.contents.every(s => s.background?.src?.startsWith("nue/") && !s.tokens.size);
}

/** Importa la aventura del compendio. `confirmar`: pide confirmación si el mundo ya tiene contenido. */
export async function importarAventura({ confirmar = false } = {}) {
  if (!game.user.isGM) return ui.notifications.warn("Nádir: solo el Guardián puede importar la aventura.");
  const pack = game.packs.get(PACK);
  if (!pack) return ui.notifications.error("Nádir: no encuentro el compendio de la aventura.");
  if (confirmar && !mundoVacio()) {
    const ok = await foundry.applications.api.DialogV2.confirm({
      window: { title: "Importar la aventura", icon: "fa-solid fa-file-import" },
      content: "<p>Este mundo ya tiene contenido. Si importas la aventura se <b>sobrescribirán</b> los documentos de Nádir que hayas cambiado a mano.</p>",
      yes: { label: "Importar", icon: "fa-solid fa-file-import" }, no: { label: "Cancelar" }, rejectClose: false
    });
    if (!ok) return;
  }
  ui.notifications.info("Nádir: importando la aventura. Son unos 30 segundos…");
  const adv = (await pack.getDocuments())[0];
  await adv.import({ dialog: false });
  // La ficha del sistema solo muestra «Respuesta al trauma» con la 1.ª edición activa.
  if (game.settings.settings.has("mosh.firstEdition") && !game.settings.get("mosh", "firstEdition")) {
    await game.settings.set("mosh", "firstEdition", true);
    ui.notifications.info("Nádir: he activado la 1.ª edición de Mothership en el sistema, que es la de la aventura.");
  }
  await game.settings.set(MOD, "importada", true);
  await game.scenes.find(s => s.getFlag(MOD, "slug") === "b4")?.activate();
  ui.notifications.info("Nádir: aventura importada. Empieza por el diario «★ Guion de dirección».");
}

async function instalarSiVacio() {
  if (!game.user.isGM || game.user !== game.users.activeGM) return false;
  if (game.settings.get(MOD, "importada") || !mundoVacio()) return false;
  await importarAventura();
  return true;
}

/* ---------------- Tutorial ---------------- */

const abrirBarra = async (pestana) => { ui.sidebar?.expand?.(); ui[pestana]?.activate?.(); await esperar(300); };
/** Pasos que abren lo que el paso va a señalar. Clave: `<tour>.<id del paso>`. */
const ANTES = {
  "direccion.guias": () => abrirBarra("journal"),
  "direccion.actores": () => abrirBarra("actors"),
  "direccion.escenas": () => abrirBarra("scenes"),
  "direccion.sonido": () => abrirBarra("playlists"),
  "direccion.documentos": () => abrirBarra("journal"),
  "direccion.cierre": () => abrirBarra("settings"),
  // La estación de bombeo tiene relojes y acciones; el Guardián la ve solo él (no cambia la escena de los jugadores).
  "direccion.chips": async () => { await game.scenes.find(s => s.getFlag(MOD, "slug") === "c7-8")?.view(); await esperar(1500); },
  "direccion.acciones": async () => { await esperar(300); },
  "direccion.panel": async () => { api().abrirPanel(); await esperar(700); },
  "direccion.ojo": async () => { api().abrirPanel(); await esperar(500); },
  "direccion.detalle": async () => { api().abrirPanel(); await esperar(500); },
  "direccion.consola": async () => { api().abrirHud?.(); await esperar(700); },
  "jugadores.consola": async () => { api().abrirHud?.(); await esperar(700); },
  "jugadores.traje": async () => { api().abrirHud?.(); await esperar(700); },
  "jugadores.ficha": () => abrirBarra("actors"),
  "jugadores.cierre": () => abrirBarra("settings")
};

class TourNadir extends foundry.nue.Tour {
  async _preStep() {
    await super._preStep();
    const paso = this.currentStep;
    try { await ANTES[`${this.id}.${paso.id}`]?.(); } catch (e) { console.warn(`${MOD} | tutorial: no se pudo preparar «${paso.id}»`, e); }
    // Un elemento que no existe (p. ej. la barra en una escena sin relojes) no debe romper el tour: el paso sale centrado.
    if (paso.selector && !document.querySelector(paso.selector)) paso.selector = "";
  }
}

async function registrarTours() {
  for (const { clave, ruta } of TOURS) {
    try { game.tours.register(MOD, clave, await TourNadir.fromJSON(ruta)); }
    catch (e) { console.error(`${MOD} | no se pudo registrar el tour «${clave}»`, e); }
  }
}

export async function empezarTutorial(clave = game.user.isGM ? "direccion" : "jugadores") {
  const tour = game.tours.get(`${MOD}.${clave}`);
  if (!tour) return ui.notifications.warn("Nádir: no encuentro ese tutorial.");
  // Foundry solo admite un tour a la vez: se cierra el activo y se reinicia el nuestro.
  for (const otro of game.tours.contents) if (otro !== tour && otro.status === foundry.nue.Tour.STATUS.IN_PROGRESS) await otro.exit();
  await tour.reset();
  return tour.start();
}

/** La primera vez se ofrece (una vez por navegador), como hace Foundry con su tutorial de bienvenida. */
async function ofrecerTutorial() {
  if (game.settings.get(MOD, "tutorialOfrecido")) return;
  await game.settings.set(MOD, "tutorialOfrecido", true);
  const gm = game.user.isGM;
  const quiere = await foundry.applications.api.DialogV2.confirm({
    window: { title: gm ? "¿Te enseño las herramientas de Nádir?" : "¿Te enseño tu visor?", icon: "fa-solid fa-graduation-cap" },
    content: gm
      ? "<p>Hay un tutorial guiado de unos cinco minutos con todo lo del módulo: la barra, el Panel, la consola de la cuadrilla, el visor y la alarma. Puedes repetirlo desde Configuración → «MR- Nádir» o Configuración → Tours.</p>"
      : "<p>Hay un tutorial de dos minutos sobre tu visor de casco, tu traje y lo que puedes hacer. Puedes repetirlo desde Configuración → «MR- Nádir» o Configuración → Tours.</p>",
    yes: { label: "Empezar el tutorial", icon: "fa-solid fa-graduation-cap" }, no: { label: "Ahora no" }, rejectClose: false
  });
  if (quiere) empezarTutorial();
}

/* ---------------- Configuración → MR- Nádir ---------------- */

Hooks.on("renderSettings", (app, html) => {
  const raiz = html instanceof HTMLElement ? html : html[0];
  const sitio = raiz?.querySelector("section.settings");
  if (!sitio || raiz.querySelector(".mr-nadir-ajustes")) return;
  const gm = game.user.isGM;
  const sec = document.createElement("section");
  sec.className = "mr-nadir-ajustes flexcol";
  sec.innerHTML = `<h4 class="divider">MR- Nádir</h4>
    <button type="button" data-nadir="tutorial"><i class="fa-solid fa-graduation-cap" inert></i> Tutorial ${gm ? "del Guardián" : "de jugadores"}</button>
    ${gm ? '<button type="button" data-nadir="tutorial-jugadores"><i class="fa-solid fa-user-astronaut" inert></i> Tutorial de jugadores</button>' : ""}
    ${gm ? '<button type="button" data-nadir="ayuda"><i class="fa-solid fa-circle-question" inert></i> Guía de las herramientas</button>' : ""}
    ${gm ? '<button type="button" data-nadir="importar"><i class="fa-solid fa-file-import" inert></i> Importar la aventura</button>' : ""}`;
  sec.addEventListener("click", (ev) => {
    const accion = ev.target.closest("button[data-nadir]")?.dataset.nadir;
    if (accion === "tutorial") empezarTutorial();
    else if (accion === "tutorial-jugadores") empezarTutorial("jugadores");
    else if (accion === "importar") importarAventura({ confirmar: true });
    else if (accion === "ayuda") {
      const guia = game.journal.find(j => j.getFlag(MOD, "ayuda"));
      if (guia) guia.sheet.render(true); else ui.notifications.warn("Nádir: importa primero la aventura para tener la guía.");
    }
  });
  sitio.after(sec);
});

Hooks.once("ready", async () => {
  await registrarTours();
  Object.assign(api(), { importarAventura, empezarTutorial });
  let recienInstalada = false;
  try { recienInstalada = await instalarSiVacio(); }
  catch (e) { console.error(`${MOD} | la instalación automática ha fallado`, e); ui.notifications.error("Nádir: la importación automática ha fallado. Puedes hacerla desde Configuración → MR- Nádir."); }
  setTimeout(ofrecerTutorial, recienInstalada ? 1500 : 3000);
});
