// MR- Nádir · Proyección del casco y marco de alarma del Guardián.
import { MOD, leerEstado, calcular, horas, casillas, fmtHora, fmtDur, trajes, trajeMin, trajeReal, trajeMax } from "./nadir.js";
import { abrirHud } from "./cuadrilla.js";

Hooks.once("init", () => {
  game.settings.register(MOD, "visor", {
    name: "Visor del casco", scope: "client", config: true, type: Boolean, default: true,
    onChange: () => refrescarVisor()
  });
  // El Guardián tiene su barra; el visor solo le sirve para previsualizar, así que empieza apagado.
  game.settings.register(MOD, "visorGM", { scope: "client", config: false, type: Boolean, default: false, onChange: () => refrescarVisor() });
});
const claveVisor = () => (game.user.isGM ? "visorGM" : "visor");

let visor, cristal, conmutador;
function crearVisor() {
  visor = document.createElement("aside");
  visor.id = "mr-nadir-visor";
  visor.setAttribute("aria-label", "Visor del casco");
  visor.classList.toggle("mr-nadir-visor-gm", game.user.isGM);
  conmutador = document.createElement("button");
  conmutador.id = "mr-nadir-visor-boton";
  conmutador.type = "button";
  conmutador.innerHTML = '<i class="fa-solid fa-user-astronaut" aria-hidden="true"></i>';
  conmutador.addEventListener("click", async () => {
    conmutador.disabled = true;
    try { await game.settings.set(MOD, claveVisor(), !game.settings.get(MOD, claveVisor())); }
    finally { conmutador.disabled = false; }
  });
  cristal = document.createElement("div");
  cristal.className = "mr-nadir-cristal mr-nadir-mini";
  const consola = document.createElement("button");
  consola.type = "button";
  consola.className = "mr-nadir-visor-consola";
  consola.title = "Abrir la Consola de la cuadrilla";
  consola.setAttribute("aria-label", consola.title);
  consola.textContent = "☰";
  consola.addEventListener("click", abrirHud);
  const datos = document.createElement("div");
  datos.className = "mr-nadir-visor-datos";
  cristal.append(datos, consola);
  visor.append(conmutador, cristal);
  document.body.append(visor);
}

function trajePersonal(e) {
  const act = game.user.character ?? trajes().find(a => a.isOwner)
    ?? game.actors.find(a => a.type === "character" && a.isOwner);
  const fila = document.createElement("div");
  fila.className = "mr-nadir-visor-traje";
  if (!act) { fila.textContent = "SIN TRAJE ASIGNADO"; return fila; }
  const f = act.getFlag(MOD, "traje"), mochila = f && f.desde !== null;
  const resto = trajeMin(act, e.min), real = trajeReal(act, e.min);
  fila.classList.toggle("mr-nadir-aire-bajo", !!mochila && real <= 30);
  fila.title = act.name;
  const nombre = document.createElement("span");
  nombre.className = "mr-nadir-visor-nombre";
  nombre.textContent = act.name;
  const barra = document.createElement("span");
  barra.innerHTML = casillas(resto / 60, trajeMax(act) / 60);
  const estado = document.createElement("span");
  estado.textContent = `${mochila ? (resto <= 0 ? "SIN AIRE" : `MOCHILA ${fmtDur(real)}`) : "UMBILICAL"}${f?.esf ? " · ESF" : ""}`;
  fila.append(nombre, barra, estado);
  return fila;
}

function datosVisor() {
  const e = leerEstado(), c = calcular(e), h = horas(c);
  const frag = document.createDocumentFragment();
  const cabecera = document.createElement("div");
  cabecera.className = "mr-nadir-visor-cabecera";
  const hora = document.createElement("span");
  hora.textContent = `HORA DE TRAJE ${fmtHora(e.min)}`;
  cabecera.append(hora);
  if (game.settings.get(MOD, "alarmas")[game.user.id]) {
    const alerta = document.createElement("strong");
    alerta.className = "mr-nadir-alerta";
    alerta.setAttribute("role", "status");
    alerta.textContent = "ALERTA";
    cabecera.append(alerta);
  }
  frag.append(cabecera, trajePersonal(e));
  const relojes = document.createElement("div");
  relojes.className = "mr-nadir-visor-relojes";
  const micro = (nombre, barra) => {
    const d = document.createElement("span");
    d.innerHTML = `<span>${nombre}</span>${barra}`;
    relojes.append(d);
  };
  // Nunca se proyectan Atención, el sello ni las próximas consecuencias del Guardián.
  if (e.rev.r3) micro("R-3", casillas(h.r3, 12, { exceso: 6 }));
  if (e.rev.p2) {
    micro("P-2 AIRE", casillas(h.p2, 12, { exceso: 5 }));
    micro(c.bomba ? "BOMBA" : "PARADA", c.bomba ? casillas(h.bat, 12) : "");
  }
  if (e.rev.h4) micro("AGUJA", casillas(c.h4, 6));
  if (e.rev.banco) micro("BANCO", casillas(h.banco, 24));
  if (e.rover2 !== null) micro(`ROVER 2 ${e.min >= e.rover2 ? "EN C-7" : fmtHora(e.rover2)}`, "");
  frag.append(relojes);
  return frag;
}

function refrescarVisor() {
  if (!game.ready) return;
  if (!visor) crearVisor();
  const activo = game.settings.get(MOD, claveVisor());
  conmutador.setAttribute("aria-pressed", String(activo));
  conmutador.title = `Visor del casco: ${activo ? "desactivar" : "activar"}`;
  conmutador.setAttribute("aria-label", conmutador.title);
  // Si se apaga desde los ajustes mientras la consola tiene foco, se devuelve al casco.
  if (!activo && cristal.contains(document.activeElement)) conmutador.focus();
  cristal.hidden = !activo;
  if (activo) cristal.querySelector(".mr-nadir-visor-datos").replaceChildren(datosVisor());
}

function refrescarAlarma() {
  if (!game.ready) return;
  const activa = !game.user.isGM && !!game.settings.get(MOD, "alarmas")[game.user.id];
  let marco = document.getElementById("mr-nadir-alarma");
  if (activa && !marco) {
    marco = document.createElement("div");
    marco.id = "mr-nadir-alarma";
    marco.setAttribute("aria-hidden", "true");
    document.body.append(marco);
  } else if (!activa) marco?.remove();
  refrescarVisor();
}

Hooks.once("ready", refrescarAlarma);
Hooks.on("mrNadirRelojes", refrescarVisor);
Hooks.on("mrNadirAlarmas", refrescarAlarma);
Hooks.on("updateActor", (act, cambios) => {
  if (foundry.utils.hasProperty(cambios, `flags.${MOD}`) || foundry.utils.hasProperty(cambios, `flags.-=${MOD}`)
    || "system" in cambios || "name" in cambios || "ownership" in cambios) refrescarVisor();
});
Hooks.on("updateUser", user => { if (user.id === game.user.id) refrescarVisor(); });
Hooks.on("createActor", refrescarVisor);
Hooks.on("deleteActor", refrescarVisor);
