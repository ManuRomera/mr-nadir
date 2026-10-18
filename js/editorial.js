// Revisión de textos de una partida importada: no reimporta la aventura.
const MOD = "mr-nadir";
const REVISION = "2.4.0";
const SETTING = "revisionEditorial";
const BACKUP = "textoAnterior240";

export function firmaTexto(value) {
  let hash = 0xcbf29ce484222325n;
  for (const byte of new TextEncoder().encode(value)) {
    hash ^= BigInt(byte);
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, "0");
}

/** Solo admite los campos editoriales enumerados en la referencia de esta versión. */
export function cambiosTexto(documento, destino, referencia, campos) {
  const cambios = {};
  const anterior = {};
  let personalizados = 0;
  for (const campo of campos) {
    const actual = foundry.utils.getProperty(documento, campo);
    const nuevo = foundry.utils.getProperty(destino, campo);
    if (typeof actual !== "string" || typeof nuevo !== "string" || actual === nuevo) continue;
    const firmas = referencia[campo] ?? [];
    if (!firmas.includes(firmaTexto(actual))) { personalizados++; continue; }
    cambios[campo] = nuevo;
    anterior[campo] = actual;
  }
  if (Object.keys(cambios).length && !documento.getFlag(MOD, BACKUP)) {
    cambios[`flags.${MOD}.${BACKUP}`] = { revision: REVISION, campos: anterior };
  }
  return { cambios, personalizados };
}

/** Actualiza entradas originales. Conserva textos propios, relojes, estadísticas y escenas. */
export async function actualizarTextos({ revisar = false } = {}) {
  if (!game.user.isGM || game.user.id !== game.users.activeGM?.id) return;
  if (!revisar && game.settings.get(MOD, SETTING) === REVISION) return;
  if (!game.journal.size && !game.actors.size) return;
  const respuesta = await fetch(`modules/${MOD}/assets/editorial/referencia-textos.json`);
  if (!respuesta.ok) throw new Error("No se ha podido leer la referencia de textos de Nádir.");
  const referencia = await respuesta.json();
  if (referencia.revision !== REVISION) throw new Error("La referencia editorial no corresponde a esta versión.");
  const pack = game.packs.get(`${MOD}.aventura`);
  if (!pack) return;
  const aventura = (await pack.getDocuments())[0];
  if (!aventura) return;
  const resultado = { paginas: 0, actores: 0, camposPropios: 0 };
  let encontrados = false;
  for (const entrada of aventura.journal) {
    const diario = game.journal.get(entrada.id ?? entrada._id);
    if (!diario) continue;
    const cambios = [];
    for (const destino of entrada.pages) {
      const id = destino.id ?? destino._id;
      const pagina = diario.pages.get(id);
      const base = referencia.paginas[id];
      if (!pagina || !base) continue;
      encontrados = true;
      const revision = cambiosTexto(pagina, destino, base, ["text.content", "name"]);
      resultado.camposPropios += revision.personalizados;
      if (Object.keys(revision.cambios).length) cambios.push({ _id: id, ...revision.cambios });
    }
    if (cambios.length) {
      await diario.updateEmbeddedDocuments("JournalEntryPage", cambios);
      resultado.paginas += cambios.length;
    }
  }
  for (const destino of aventura.actors) {
    const id = destino.id ?? destino._id;
    const actor = game.actors.get(id);
    const base = referencia.actores[id];
    if (!actor || !base) continue;
    encontrados = true;
    const revision = cambiosTexto(actor, destino, base, ["system.biography", "system.description"]);
    resultado.camposPropios += revision.personalizados;
    if (Object.keys(revision.cambios).length) {
      await actor.update(revision.cambios);
      resultado.actores++;
    }
  }
  if (!encontrados) return;
  // Si una escritura falla, no se marca la revisión: el siguiente inicio reintenta lo pendiente.
  await game.settings.set(MOD, SETTING, REVISION);
  const api = game.modules.get(MOD)?.api;
  if (api) api.ultimaRevisionEditorial = resultado;
  if (resultado.paginas || resultado.actores) {
    ui.notifications.info(`Nádir: textos actualizados (${resultado.paginas} páginas y ${resultado.actores} fichas). Se conservan los textos personalizados y el estado de la partida.`);
  }
  return resultado;
}

Hooks.once("init", () => {
  game.settings.register(MOD, SETTING, { scope: "world", config: false, type: String, default: "" });
});
Hooks.once("ready", () => {
  const api = game.modules.get(MOD)?.api;
  if (api) api.actualizarTextos = actualizarTextos;
  setTimeout(() => actualizarTextos().catch(error => {
    console.error(`${MOD} | No se ha completado la revisión editorial`, error);
    if (game.user.isGM && game.user.id === game.users.activeGM?.id) {
      ui.notifications.warn("Nádir: hay textos pendientes de actualizar. Se reintentará al volver a entrar; los datos de la partida se conservan.");
    }
  }), 1500);
});
