// Compila _data/aventura.json a packs/aventura (LevelDB, Adventure) y empaqueta dist/mr-nadir.zip
import fs from "node:fs/promises";
import { createWriteStream } from "node:fs";
import { ClassicLevel } from "classic-level";
import archiver from "archiver";

const manifest = JSON.parse(await fs.readFile("module.json"));
for (const pack of manifest.packs) {
  await fs.rm(pack.path, { recursive: true, force: true });
  const db = new ClassicLevel(pack.path, { valueEncoding: "json" });
  const docs = JSON.parse(await fs.readFile(`_data/${pack.name}.json`));
  for (const d of docs) await db.put(`!adventures!${d._id}`, d);
  await db.close();
  console.log(`pack ${pack.name}: ${docs.length} aventura(s)`);
}
await fs.mkdir("dist", { recursive: true });
const out = createWriteStream("dist/mr-nadir.zip");
const zip = archiver("zip", { zlib: { level: 9 } });
zip.pipe(out);
const done = new Promise((res, rej) => { out.on("close", res); out.on("error", rej); zip.on("error", rej); });
for (const p of ["module.json", "js", "styles", "lang", "packs", "tours", "assets", "LICENSE", "README.md"]) {
  try {
    const st = await fs.stat(p);
    if (st.isDirectory()) zip.directory(p, p); else zip.file(p, { name: p });
  } catch { /* opcional */ }
}
await zip.finalize();
await done;
console.log("dist/mr-nadir.zip");
